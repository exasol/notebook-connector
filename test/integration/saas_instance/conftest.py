from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.secret_store import Secrets


@pytest.fixture(scope="session")
def saas_secrets(
    tmp_path_factory,
    saas_host,
    saas_pat,
    saas_account_id,
    backend_aware_saas_database_id,
) -> Generator[Secrets, None, None]:
    """
    Creates a temporary Secrets store pre-configured for a SaaS backend.
    Requires the following environment variables to be set:
      SAAS_HOST, SAAS_PAT, SAAS_ACCOUNT_ID
    and the pytest-exasol-backend plugin to provide the saas fixtures.
    """
    store_path = tmp_path_factory.mktemp("saas_config") / "saas_secrets.sqlite"
    secrets = Secrets(store_path, master_password="saas-test-pw")
    secrets.save(CKey.storage_backend, StorageBackend.saas.name)
    secrets.save(CKey.saas_url, saas_host)
    secrets.save(CKey.saas_token, saas_pat)
    secrets.save(CKey.saas_account_id, saas_account_id)
    secrets.save(CKey.saas_database_id, backend_aware_saas_database_id)
    secrets.save(CKey.db_schema, "SAAS_INTEGRATION_TEST")
    yield secrets
