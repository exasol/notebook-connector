import contextlib
import json
from pathlib import Path
from test.unit.slc.util import (
    SecretsMock,
    not_raises,
)
from unittest.mock import (
    Mock,
    create_autospec,
)

import git
import pytest
import requests
from _pytest.monkeypatch import MonkeyPatch
from exasol.slc.models.compression_strategy import CompressionStrategy

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc import (
    constants,
    script_language_container,
    workspace,
)
from exasol.nb_connector.slc.script_language_container import ScriptLanguageContainer
from exasol.nb_connector.slc.slc_flavor import (
    SlcError,
    SlcFlavor,
)
from exasol.nb_connector.slc.workspace import current_directory


@pytest.fixture
def sample_slc_name() -> str:
    return "CUDA"


@pytest.fixture
def git_repo_mock(monkeypatch: MonkeyPatch):
    mock = create_autospec(git.Repo)
    monkeypatch.setattr(workspace, "Repo", mock)
    return mock


def simulate_clone(flavor: str):
    """
    This function can be set as side effect to method clone_from of the
    git_repo_mock for simulating a successful checkout to the
    ScriptLanguageContainer.
    """

    def create_dir(url: str, dir: Path, branch: str):
        (dir / constants.FLAVORS_PATH_IN_SLC_REPO / flavor).mkdir(parents=True)
        return Mock()

    return create_dir


class SlcFactory:
    """
    Provides a context to create an instance of ScriptLanguageContainer in
    a temporary directory and simulating the SLC Git repo to be cloned inside.
    """

    def __init__(self, path: Path, git_repo_mock: Mock):
        self.path = path
        self.git_repo_mock = git_repo_mock

    @contextlib.contextmanager
    def context(self, slc_name: str, flavor: str):
        secrets = SecretsMock(slc_name)
        self.git_repo_mock.clone_from.side_effect = simulate_clone(flavor)
        with current_directory(self.path):
            yield ScriptLanguageContainer.create(
                secrets,
                name=slc_name,
                flavor=flavor,
            )


@pytest.fixture
def slc_factory(tmp_path, git_repo_mock):
    return SlcFactory(tmp_path, git_repo_mock)


def test_create(
    sample_slc_name,
    monkeypatch: MonkeyPatch,
    caplog,
    slc_factory,
):
    flavor = "Strawberry"
    with slc_factory.context(sample_slc_name, flavor) as testee:
        pass

    assert slc_factory.git_repo_mock.clone_from.called
    assert "Cloning into" in caplog.text
    assert "Fetching submodules" in caplog.text

    assert testee.language_alias == f"custom_slc_{sample_slc_name}"
    assert testee.secrets.SLC_FLAVOR_CUDA == flavor
    checkout_dir = (
        slc_factory.path / constants.WORKSPACE_DIR / sample_slc_name / "git-clone"
    )
    assert testee.checkout_dir == checkout_dir
    assert testee.flavor_path.is_dir()
    assert (
        testee.flavor_path == checkout_dir / constants.FLAVORS_PATH_IN_SLC_REPO / flavor
    )
    assert testee.custom_pip_file.parts[-3:] == (
        "flavor_customization",
        "packages",
        "python3_pip_packages",
    )
    assert testee.compression_strategy == CompressionStrategy.GZIP


def test_repo_missing(sample_slc_name):
    secrets = SecretsMock.for_slc(sample_slc_name, Path())
    with pytest.raises(SlcError, match="SLC Git repository not checked out"):
        ScriptLanguageContainer(secrets, sample_slc_name)


@pytest.mark.parametrize(
    "name",
    [
        "",
        "SPACE CHARACTER",
        "SPECIAL-",
        "/",
        ":",
        "&",
        "1_NUMBER_PREFIX",
        "_UNDERSCORE_PREFIX",
    ],
)
def test_illegal_names(name):
    secrets = Mock()
    with pytest.raises(
        SlcError,
        match='name ".*" doesn\'t match regular expression',
    ):
        ScriptLanguageContainer(secrets, name=name)


@pytest.mark.parametrize("name", ["ABC", "ABC_123", "abc", "abc_123"])
def test_legal_names(name, slc_factory):
    flavor = "Strawberry"
    with not_raises(SlcError):
        with slc_factory.context(slc_name=name, flavor=flavor) as slc:
            assert slc.flavor == flavor


@pytest.fixture
def slc_with_tmp_checkout_dir(sample_slc_name, slc_factory) -> ScriptLanguageContainer:
    with slc_factory.context(slc_name=sample_slc_name, flavor="Vanilla") as slc:
        yield slc


def test_non_unique_name(slc_with_tmp_checkout_dir):
    existing_slc = slc_with_tmp_checkout_dir
    with pytest.raises(
        SlcError,
        match="already contains a flavor for SLC name",
    ):
        ScriptLanguageContainer.create(
            existing_slc.secrets,
            existing_slc.name,
            flavor="Strawberry",
        )


def mock_docker_client_context(image_tags: list[str]):
    """
    Mock a docker client simulating to return a list of images with each
    image's first tag set to one of the specified image_tags.

    Return a context initializing and providing the mocked docker client.
    """

    def image_mock(tag: str):
        return Mock(tags=[tag])

    client = Mock()
    client.images = Mock()
    client.images.list = Mock()
    client.images.list.return_value = [image_mock(tag) for tag in image_tags]

    @contextlib.contextmanager
    def context():
        yield client

    return context


def test_docker_image_tags(monkeypatch: MonkeyPatch, slc_factory):
    """
    This test mocks the Docker client simulating to return a list of
    Docker images to be available on the current system.

    The test then verifies the ScriptLanguageContainer under test to return
    only the Docker images with each image's first tag starting with the
    expected image name and the flavor.
    """
    image_name = "exasol/script-language-container"
    flavor = "template-Exasol-all-python-3.10-conda"
    prefix = f"{image_name}:{flavor}"
    expected = [
        f"{prefix}-build_run_123",
        f"{prefix}-test_456",
    ]
    image_tags = expected + [
        f"{image_name}:other_tag-x-1",
        f"exasol/other-image:{flavor}-suffix-1",
    ]
    monkeypatch.setattr(
        script_language_container,
        "ContextDockerClient",
        mock_docker_client_context(image_tags),
    )
    with slc_factory.context("MY_SLC", flavor) as slc:
        assert slc.docker_image_tags == expected


@pytest.fixture
def requests_get_mock(monkeypatch: MonkeyPatch):
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            "name": "README.md",
            "path": "flavors/README.md",
            "sha": "c31e9f0e08f389210b6fc12920f26b535c570575",
            "size": 4944,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/README.md?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/README.md",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/c31e9f0e08f389210b6fc12920f26b535c570575",
            "download_url": "https://raw.githubusercontent.com/exasol/script-languages-release/9.7.0/flavors/README.md",
            "type": "file",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/README.md?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/c31e9f0e08f389210b6fc12920f26b535c570575",
                "html": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/README.md",
            },
        },
        {
            "name": "standard-EXASOL-all-java-11",
            "path": "flavors/standard-EXASOL-all-java-11",
            "sha": "1d2bce195d16a83d65f45c1dd5a9f9e34b16fd28",
            "size": 0,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/standard-EXASOL-all-java-11?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/standard-EXASOL-all-java-11",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/trees/1d2bce195d16a83d65f45c1dd5a9f9e34b16fd28",
            "download_url": None,
            "type": "dir",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/standard-EXASOL-all-java-11?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/trees/1d2bce195d16a83d65f45c1dd5a9f9e34b16fd28",
                "html": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/standard-EXASOL-all-java-11",
            },
        },
        {
            "name": "standard-EXASOL-all-java-17",
            "path": "flavors/standard-EXASOL-all-java-17",
            "sha": "e521b9bfdd414c62056e4cb8edbc8112d8807ff6",
            "size": 0,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/standard-EXASOL-all-java-17?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/standard-EXASOL-all-java-17",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/trees/e521b9bfdd414c62056e4cb8edbc8112d8807ff6",
            "download_url": None,
            "type": "dir",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/standard-EXASOL-all-java-17?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/trees/e521b9bfdd414c62056e4cb8edbc8112d8807ff6",
                "html": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/standard-EXASOL-all-java-17",
            },
        },
        {
            "name": "standard-EXASOL-all-python-3.10",
            "path": "flavors/standard-EXASOL-all-python-3.10",
            "sha": "458b5f2b8d97c23f978304675d983f82a8e08323",
            "size": 0,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/standard-EXASOL-all-python-3.10?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/standard-EXASOL-all-python-3.10",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/trees/458b5f2b8d97c23f978304675d983f82a8e08323",
            "download_url": None,
            "type": "dir",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/standard-EXASOL-all-python-3.10?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/trees/458b5f2b8d97c23f978304675d983f82a8e08323",
                "html": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/standard-EXASOL-all-python-3.10",
            },
        },
        {
            "name": "standard-EXASOL-all-r-4.4",
            "path": "flavors/standard-EXASOL-all-r-4.4",
            "sha": "af73bc131e05265b5d8caffd9ba260d71de8dfc1",
            "size": 0,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/standard-EXASOL-all-r-4.4?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/standard-EXASOL-all-r-4.4",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/trees/af73bc131e05265b5d8caffd9ba260d71de8dfc1",
            "download_url": None,
            "type": "dir",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/standard-EXASOL-all-r-4.4?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/trees/af73bc131e05265b5d8caffd9ba260d71de8dfc1",
                "html": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/standard-EXASOL-all-r-4.4",
            },
        },
        {
            "name": "standard-EXASOL-all",
            "path": "flavors/standard-EXASOL-all",
            "sha": "245830f932f73cdaf6c7fd2498a2475f6424e6ac",
            "size": 0,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/standard-EXASOL-all?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/standard-EXASOL-all",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/trees/245830f932f73cdaf6c7fd2498a2475f6424e6ac",
            "download_url": None,
            "type": "dir",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/standard-EXASOL-all?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/trees/245830f932f73cdaf6c7fd2498a2475f6424e6ac",
                "html": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/standard-EXASOL-all",
            },
        },
        {
            "name": "template-Exasol-8-python-3.10-cuda-conda",
            "path": "flavors/template-Exasol-8-python-3.10-cuda-conda",
            "sha": "0dfb2ccd82936f0dcb1edca352ae0a05adfa2af8",
            "size": 68,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/template-Exasol-8-python-3.10-cuda-conda?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/template-Exasol-8-python-3.10-cuda-conda",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/0dfb2ccd82936f0dcb1edca352ae0a05adfa2af8",
            "download_url": "https://raw.githubusercontent.com/exasol/script-languages-release/9.7.0/flavors/template-Exasol-8-python-3.10-cuda-conda",
            "type": "symlink",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/template-Exasol-8-python-3.10-cuda-conda?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/0dfb2ccd82936f0dcb1edca352ae0a05adfa2af8",
                "html": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/template-Exasol-8-python-3.10-cuda-conda",
            },
        },
        {
            "name": "template-Exasol-all-python-3.10",
            "path": "flavors/template-Exasol-all-python-3.10",
            "sha": "35cf44356fa359c420aeaab680861a38fd9f574a",
            "size": 60,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/template-Exasol-all-python-3.10?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/template-Exasol-all-python-3.10",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/35cf44356fa359c420aeaab680861a38fd9f574a",
            "download_url": "https://raw.githubusercontent.com/exasol/script-languages-release/9.7.0/flavors/template-Exasol-all-python-3.10",
            "type": "symlink",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/template-Exasol-all-python-3.10?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/35cf44356fa359c420aeaab680861a38fd9f574a",
                "html": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/template-Exasol-all-python-3.10",
            },
        },
        {
            "name": "template-Exasol-all-python-3.10-conda",
            "path": "flavors/template-Exasol-all-python-3.10-conda",
            "sha": "d43273557b778fb95dde456f70acbd187defcc11",
            "size": 66,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/template-Exasol-all-python-3.10-conda?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/template-Exasol-all-python-3.10-conda",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/d43273557b778fb95dde456f70acbd187defcc11",
            "download_url": "https://raw.githubusercontent.com/exasol/script-languages-release/9.7.0/flavors/template-Exasol-all-python-3.10-conda",
            "type": "symlink",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/template-Exasol-all-python-3.10-conda?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/d43273557b778fb95dde456f70acbd187defcc11",
                "html": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/template-Exasol-all-python-3.10-conda",
            },
        },
        {
            "name": "template-Exasol-all-python-3.12",
            "path": "flavors/template-Exasol-all-python-3.12",
            "sha": "53ce9768bed6879e2cb7184b97e8cb3db44760c5",
            "size": 60,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/template-Exasol-all-python-3.12?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/template-Exasol-all-python-3.12",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/53ce9768bed6879e2cb7184b97e8cb3db44760c5",
            "download_url": "https://raw.githubusercontent.com/exasol/script-languages-release/9.7.0/flavors/template-Exasol-all-python-3.12",
            "type": "symlink",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/template-Exasol-all-python-3.12?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/53ce9768bed6879e2cb7184b97e8cb3db44760c5",
                "html": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/template-Exasol-all-python-3.12",
            },
        },
        {
            "name": "template-Exasol-all-r-4",
            "path": "flavors/template-Exasol-all-r-4",
            "sha": "8e44732984669e2828801918562442f4b1335229",
            "size": 0,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/template-Exasol-all-r-4?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/template-Exasol-all-r-4",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/trees/8e44732984669e2828801918562442f4b1335229",
            "download_url": None,
            "type": "dir",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/template-Exasol-all-r-4?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/trees/8e44732984669e2828801918562442f4b1335229",
                "html": "https://github.com/exasol/script-languages-release/tree/9.7.0/flavors/template-Exasol-all-r-4",
            },
        },
        {
            "name": "test-Exasol-8-cuda-ml",
            "path": "flavors/test-Exasol-8-cuda-ml",
            "sha": "3f25325a7564abedcc5d59d585087c7a48ab1d9e",
            "size": 50,
            "url": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/test-Exasol-8-cuda-ml?ref=9.7.0",
            "html_url": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/test-Exasol-8-cuda-ml",
            "git_url": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/3f25325a7564abedcc5d59d585087c7a48ab1d9e",
            "download_url": "https://raw.githubusercontent.com/exasol/script-languages-release/9.7.0/flavors/test-Exasol-8-cuda-ml",
            "type": "symlink",
            "_links": {
                "self": "https://api.github.com/repos/exasol/script-languages-release/contents/flavors/test-Exasol-8-cuda-ml?ref=9.7.0",
                "git": "https://api.github.com/repos/exasol/script-languages-release/git/blobs/3f25325a7564abedcc5d59d585087c7a48ab1d9e",
                "html": "https://github.com/exasol/script-languages-release/blob/9.7.0/flavors/test-Exasol-8-cuda-ml",
            },
        },
    ]
    monkeypatch.setattr(requests, "get", Mock(return_value=mock_response))


def test_list_available_flavors(requests_get_mock):
    available_flavors = ScriptLanguagesContainer.list_available_flavors()
    expected_flavors = [
        "template-Exasol-8-python-3.10-cuda-conda",
        "template-Exasol-all-python-3.10",
        "template-Exasol-all-python-3.10-conda",
        "template-Exasol-all-python-3.12",
        "template-Exasol-all-r-4",
    ]
    assert available_flavors == expected_flavors
