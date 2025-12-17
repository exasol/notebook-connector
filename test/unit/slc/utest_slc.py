import contextlib
import logging
import textwrap
from collections.abc import Generator
from pathlib import Path
from test.unit.slc.util import (
    SlcSecretsMock,
    not_raises,
)
from typing import (
    Callable,
)
from unittest import mock
from unittest.mock import (
    Mock,
    create_autospec,
)

import pytest
import requests
from _pytest.monkeypatch import MonkeyPatch
from exasol.slc.models.compression_strategy import CompressionStrategy

from exasol.nb_connector.slc import (
    constants,
    script_language_container,
    workspace,
)
from exasol.nb_connector.slc.git_access import GitAccess
from exasol.nb_connector.slc.script_language_container import (
    PipPackageDefinition,
    ScriptLanguageContainer,
)
from exasol.nb_connector.slc.slc_flavor import (
    SlcError,
    SlcFlavor,
)
from exasol.nb_connector.slc.workspace import current_directory


@pytest.fixture
def sample_slc_name() -> str:
    return "CUDA"


@pytest.fixture
def git_access_mock(monkeypatch: MonkeyPatch):
    @contextlib.contextmanager
    def context(flavor: str):
        def create_dir(url: str, dir: Path, branch: str):
            (dir / constants.FLAVORS_PATH_IN_SLC_REPO / flavor).mkdir(parents=True)
            return Mock()

        mock = create_autospec(GitAccess)
        monkeypatch.setattr(workspace, "GitAccess", mock)
        monkeypatch.setattr(script_language_container, "GitAccess", mock)
        mock.clone_from_recursively.side_effect = create_dir
        yield mock

    return context


class SlcFactory:
    """
    Provides a context to create an instance of ScriptLanguageContainer in
    a temporary directory and simulating the SLC Git repo to be cloned inside.
    """

    def __init__(self, path: Path, creation_method: Callable, git_access_mock):
        self.path = path
        self.creation_method = creation_method
        self.git_access_mock = git_access_mock

    @contextlib.contextmanager
    def context(
        self, slc_name: str, flavor: str
    ) -> Generator[ScriptLanguageContainer, None, None]:
        with self.git_access_mock(flavor):
            secrets = SlcSecretsMock(slc_name)
            with current_directory(self.path):
                yield self.creation_method(
                    secrets,
                    name=slc_name,
                    flavor=flavor,
                )


@pytest.fixture
def slc_factory_create(tmp_path, git_access_mock):
    return SlcFactory(tmp_path, ScriptLanguageContainer.create, git_access_mock)


@pytest.fixture
def slc_factory_create_or_open(tmp_path, git_access_mock):
    return SlcFactory(tmp_path, ScriptLanguageContainer.create_or_open, git_access_mock)


def _validate_slc(flavor_name, sample_slc_name, slc, path):
    assert slc.language_alias == f"custom_slc_{sample_slc_name}"
    assert slc.secrets.SLC_FLAVOR_CUDA == flavor_name
    checkout_dir = path / constants.WORKSPACE_DIR / sample_slc_name / "git-clone"
    assert slc.checkout_dir == checkout_dir
    assert slc.flavor_path.is_dir()
    assert (
        slc.flavor_path
        == checkout_dir / constants.FLAVORS_PATH_IN_SLC_REPO / flavor_name
    )
    assert slc.custom_pip_file.parts[-3:] == (
        "flavor_customization",
        "packages",
        "python3_pip_packages",
    )
    assert slc.compression_strategy == CompressionStrategy.GZIP


@pytest.fixture
def slc_factory_create_select_method(request, tmp_path, git_access_mock):
    return SlcFactory(tmp_path, request.param, git_access_mock)


@pytest.mark.parametrize(
    "slc_factory_create_select_method",
    [ScriptLanguageContainer.create, ScriptLanguageContainer.create_or_open],
    indirect=True,
)
def test_create(
    sample_slc_name,
    caplog,
    slc_factory_create_select_method,
):
    flavor = "Strawberry"
    with slc_factory_create_select_method.context(sample_slc_name, flavor) as testee:
        pass

    _validate_slc(
        flavor, sample_slc_name, testee, slc_factory_create_select_method.path
    )


def test_repo_missing(sample_slc_name, tmp_path):
    with current_directory(tmp_path):
        secrets = SlcSecretsMock.create(sample_slc_name, "aflavor")
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
def test_legal_names(name, slc_factory_create):
    flavor = "Strawberry"
    with not_raises(SlcError):
        with slc_factory_create.context(slc_name=name, flavor=flavor) as slc:
            assert slc.flavor == flavor


@pytest.fixture
def slc_with_tmp_checkout_dir(
    sample_slc_name, slc_factory_create
) -> Generator[ScriptLanguageContainer, None, None]:
    with slc_factory_create.context(slc_name=sample_slc_name, flavor="Vanilla") as slc:
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


def test_docker_image_tags(monkeypatch: MonkeyPatch, slc_factory_create):
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
    with slc_factory_create.context("MY_SLC", flavor) as slc:
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
    available_flavors = ScriptLanguageContainer.list_available_flavors()
    expected_flavors = [
        "template-Exasol-8-python-3.10-cuda-conda",
        "template-Exasol-all-python-3.10",
        "template-Exasol-all-python-3.10-conda",
        "template-Exasol-all-python-3.12",
        "template-Exasol-all-r-4",
    ]
    assert available_flavors == expected_flavors


def test_slc_create_or_open_exists_in_secret_store(
    caplog, sample_slc_name, tmp_path, git_access_mock
):
    flavor_name = "Strawberry"
    flavor = SlcFlavor(sample_slc_name)
    secrets = SlcSecretsMock(sample_slc_name)
    flavor.save(secrets, flavor_name)

    with current_directory(tmp_path):
        with git_access_mock(flavor_name) as _git_access_mock:
            with caplog.at_level(logging.INFO):
                slc = ScriptLanguageContainer.create_or_open(
                    secrets, sample_slc_name, flavor_name
                )
                assert f"Secure Configuration Storage already contains a flavor for SLC name {sample_slc_name}."
                assert _git_access_mock.clone_from_recursively.called

                _validate_slc(flavor_name, sample_slc_name, slc, tmp_path)


def test_slc_create_or_open_workspace_exists(
    sample_slc_name, caplog, slc_factory_create, git_access_mock
):
    flavor = "Strawberry"
    with caplog.at_level(logging.INFO):
        with git_access_mock(flavor) as _git_access_mock:
            with slc_factory_create.context(sample_slc_name, flavor) as testee:
                ScriptLanguageContainer.create_or_open(
                    testee.secrets, sample_slc_name, flavor
                )
                assert not _git_access_mock.clone_from_recursively.called
                assert f"Secure Configuration Storage already contains a flavor for SLC name {sample_slc_name}."
                assert f"Secure Configuration Storage already contains a compression strategy for SLC name {sample_slc_name}."
                assert f"Directory '{testee.checkout_dir}' is not empty. Skipping checkout...."

                _validate_slc(flavor, sample_slc_name, testee, slc_factory_create.path)


def write_package_file(file_path: Path, trailing_newline: bool):
    content = textwrap.dedent(
        """
    package_a|v1.2.3
    package_b|v4.5.6
    package_c|v5.6.7
    """
    ).lstrip("\n")
    if not trailing_newline:
        content = content.rstrip("\n")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)


@pytest.fixture(
    params=[True, False], ids=["with_trailing_newline", "without_trailing_newline"]
)
def slc_with_packages(request, sample_slc_name, slc_factory_create):
    flavor = "Strawberry"
    with slc_factory_create.context(sample_slc_name, flavor) as testee:
        write_package_file(testee.custom_pip_file, request.param)
        write_package_file(testee.custom_conda_file, request.param)
        yield testee


def test_add_new_pip_package(slc_with_packages):
    slc_with_packages.append_custom_pip_packages(
        [PipPackageDefinition("package_d", "v10.0")]
    )
    expected_content = textwrap.dedent(
        """
    package_a|v1.2.3
    package_b|v4.5.6
    package_c|v5.6.7
    package_d|v10.0
    """
    ).lstrip("\n")
    assert slc_with_packages.custom_pip_file.read_text() == expected_content


def test_add_existing_pip_package_same_version(caplog, slc_with_packages):
    with caplog.at_level(logging.INFO):
        slc_with_packages.append_custom_pip_packages(
            [PipPackageDefinition("package_a", "v1.2.3")]
        )
        expected_content = textwrap.dedent(
            """
        package_a|v1.2.3
        package_b|v4.5.6
        package_c|v5.6.7
        """
        )
        assert (
            slc_with_packages.custom_pip_file.read_text().strip()
            == expected_content.strip()
        )
        assert (
            "Package already exists: PipPackageDefinition(pkg='package_a', version='v1.2.3')"
            in caplog.text
        )


def test_add_existing_pip_package_different_version(caplog, slc_with_packages):
    with pytest.raises(SlcError, match=r"Package already exists"):
        slc_with_packages.append_custom_pip_packages(
            [PipPackageDefinition("package_a", "v9.9.9")]
        )


@pytest.fixture
def git_access_mock_checkout_fails(monkeypatch: MonkeyPatch):
    @contextlib.contextmanager
    def context(flavor: str):
        def create_dir(url: str, dir: Path, branch: str):
            (dir / constants.FLAVORS_PATH_IN_SLC_REPO / flavor).mkdir(parents=True)
            return Mock()

        def checkout_recursively(path: Path) -> None:
            raise Exception("something went wrong")

        mock = create_autospec(GitAccess)
        monkeypatch.setattr(workspace, "GitAccess", mock)
        mock.clone_from_recursively.side_effect = create_dir
        mock.checkout_recursively.side_effect = checkout_recursively
        yield mock

    return context


def test_make_fresh_clone_if_repo_is_corrupt(
    caplog, tmp_path, sample_slc_name, git_access_mock_checkout_fails
):
    """
    Validate that ScriptLanguageContainer.create_or_open() creates a fresh working copy
    if GitAccessIf.checkout_recursively() raises an exception.
    """

    flavor = "Strawberry"
    slc_factory = SlcFactory(
        tmp_path, ScriptLanguageContainer.create, git_access_mock_checkout_fails
    )

    with slc_factory.context(slc_name=sample_slc_name, flavor=flavor) as slc:
        assert slc.workspace.git_clone_path.is_dir()
        marker = slc.workspace.git_clone_path / "test.txt"
        marker.write_text("marker")
        assert marker.exists()
        ScriptLanguageContainer.create_or_open(
            slc.secrets,
            sample_slc_name,
            flavor,
        )
        assert not marker.exists()
        assert (
            f"Git repository is inconsistent: something went wrong. Doing a fresh clone..."
            in caplog.text
        )


def test_restore_pip_package_file(sample_slc_name, slc_factory_create, git_access_mock):
    flavor = "Strawberry"
    with slc_factory_create.context(slc_name=sample_slc_name, flavor=flavor) as slc:
        with git_access_mock(flavor) as git_access:
            slc.restore_custom_pip_file()
            assert git_access.checkout_file.mock_calls == [
                mock.call(
                    slc.workspace.git_clone_path / "script-languages",
                    Path("flavors")
                    / flavor
                    / "flavor_customization"
                    / "packages"
                    / "python3_pip_packages",
                )
            ]


def test_restore_conda_package_file(
    sample_slc_name, slc_factory_create, git_access_mock
):
    flavor = "Strawberry"
    with slc_factory_create.context(slc_name=sample_slc_name, flavor=flavor) as slc:
        with git_access_mock(flavor) as git_access:
            slc.restore_custom_conda_file()
            assert git_access.checkout_file.mock_calls == [
                mock.call(
                    slc.workspace.git_clone_path / "script-languages",
                    Path("flavors")
                    / flavor
                    / "flavor_customization"
                    / "packages"
                    / "conda_packages",
                )
            ]
