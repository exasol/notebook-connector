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

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
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
        ws1 = Workspace.for_slc(sample_slc_name, secrets)

    with current_directory(workspace_dir2) as _:
        ws2 = Workspace.for_slc(sample_slc_name, secrets)
        assert (
            ws2.root_dir == workspace_dir1 / constants.WORKSPACE_DIR / sample_slc_name
        )
