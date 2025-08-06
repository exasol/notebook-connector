import contextlib
from pathlib import Path
from test.unit.slc.util import (
    SESSION_ATTS,
    secrets_without,
)
from unittest.mock import (
    Mock,
    call,
    create_autospec,
)

import pytest
from _pytest.monkeypatch import MonkeyPatch
from git import Repo

from test.unit.slc.util import SecretsMock

import exasol.nb_connector.slc.script_language_container
from exasol.nb_connector.secret_store import Secrets

from exasol.nb_connector.slc.constants import SLC_RELEASE_TAG
from exasol.nb_connector.slc.script_language_container import (
    ScriptLanguageContainer,
    SlcSessionError,
)


def test_create(secrets):
    my_flavor = "Vanilla"
    my_language = "Spanish"
    my_dir = Path("xtest")
    testee = ScriptLanguageContainer.create(
        secrets,
        name="CUDA",
        flavor=my_flavor,
        language_alias=my_language,
    )
    assert secrets.SLC_FLAVOR_CUDA == my_flavor
    assert secrets.SLC_LANGUAGE_ALIAS_CUDA == my_language
    assert Path(secrets.SLC_DIR_CUDA).parts[-2:] == (".slc_checkout", "CUDA")
    assert testee.flavor_path.endswith(my_flavor)


@pytest.mark.parametrize ("prefix, description", SESSION_ATTS.items())
def test_missing_property(sample_session, prefix, description):
    """
    Secrets does not contain the specified property for the current SLC
    session.  The test expects ScriptLanguageContainer to raise an
    SlcSessionError.
    """
    secrets = secrets_without(sample_session, prefix)
    with pytest.raises(
        SlcSessionError, match=f"does not contain an {description}"
    ):
        ScriptLanguageContainer(secrets, sample_session)


@pytest.mark.parametrize("name", ["", None])
def test_empty_session_name(name):
    """
    Verify empty string or None are not accepted as name of a
    ScriptLanguageContainer.
    """
    secrets = Mock()
    with pytest.raises(SlcSessionError):
        ScriptLanguageContainer(secrets, name=name)


@pytest.fixture
def slc_with_tmp_checkout_dir(sample_session, tmp_path) -> ScriptLanguageContainer:
    mock = SecretsMock(
        sample_session, {
            "SLC_DIR": str(tmp_path),
            "SLC_FLAVOR": "Vanilla",
        }
    )
    return ScriptLanguageContainer(mock, name=sample_session, verify=False)


def test_slc_repo_not_available(slc_with_tmp_checkout_dir):
    assert not slc_with_tmp_checkout_dir.slc_repo_available()


def test_clone_repo(
    slc_with_tmp_checkout_dir: ScriptLanguageContainer,
    monkeypatch: MonkeyPatch,
    caplog,
):
    repo_mock = create_autospec(Repo)
    monkeypatch.setattr(
        exasol.nb_connector.slc.script_language_container,
        "Repo",
        repo_mock,
    )
    testee = slc_with_tmp_checkout_dir
    testee.clone_slc_repo()
    assert repo_mock.clone_from.called
    assert "Cloning into" in caplog.text
    assert "Fetching submodules" in caplog.text


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
    client.images.list.return_value = [
        image_mock(tag) for tag in image_tags
    ]

    @contextlib.contextmanager
    def context():
        yield client

    return context


def test_docker_images(sample_session, monkeypatch):
    """
    This test mocks the Docker client simulating to return a list of
    Docker images to be available on the current system.

    The test then verifies the ScriptLanguageContainer under test to return
    only the Docker images with each image's first tag starting with the
    expected image name and the flavor.
    """
    image_name = "exasol/script-language-container"
    flavor = "template-Exasol-all-python-3.10-conda"
    secrets = SecretsMock(sample_session, {"SLC_FLAVOR": flavor})
    prefix = f"{image_name}:{flavor}"
    expected = [
        f"{prefix}-build_run_123",
        f"{prefix}-test_456",
    ]
    image_tags = expected + [
        f"{image_name}:other_tag-x-1",
        f"exasol/other-image:{flavor}-suffix-1"
    ]
    monkeypatch.setattr(
        exasol.nb_connector.slc.script_language_container,
        "ContextDockerClient",
        mock_docker_client_context(image_tags),
    )
    testee = ScriptLanguageContainer(secrets, name=sample_session, verify=False)
    assert testee.docker_images == expected
