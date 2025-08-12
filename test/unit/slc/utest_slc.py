import contextlib
from pathlib import Path

from exasol.slc.models.compression_strategy import CompressionStrategy

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
from _pytest.monkeypatch import MonkeyPatch

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
