from test.unit.slc.util import (
    SlcSecretsMock,
)

import pytest

from exasol.nb_connector.slc import (
    constants,
)
from exasol.nb_connector.slc.workspace import (
    Workspace,
    current_directory,
)


@pytest.fixture
def sample_slc_name() -> str:
    return "CUDA"


def test_workspace_reuses_directory(sample_slc_name, tmp_path):
    secrets = SlcSecretsMock(sample_slc_name)
    workspace_dir1 = tmp_path / "ws1"
    workspace_dir2 = tmp_path / "ws2"

    workspace_dir1.mkdir()
    workspace_dir2.mkdir()

    with current_directory(workspace_dir1) as _:
        Workspace.for_slc(sample_slc_name, secrets)

    with current_directory(workspace_dir2) as _:
        ws2 = Workspace.for_slc(sample_slc_name, secrets)
        assert (
            ws2.root_dir == workspace_dir1 / constants.WORKSPACE_DIR / sample_slc_name
        )
