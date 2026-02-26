import ipywidgets as widgets

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.connections import get_backend
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.config.onprem_or_saas_db import (
    onprem_configuration,
    saas_configuration,
)
from exasol.nb_connector.ui.docker.docker_db import docker_db_configuration


def db_configuration(conf: Secrets) -> widgets.Widget:
    """
    Creates a db configuration UI, depending on the choice of the database.
    """
    storage_backend = get_backend(conf)
    if storage_backend == StorageBackend.saas:
        return saas_configuration(conf)
    elif conf.get(CKey.use_itde, "True") == "True":
        return docker_db_configuration(conf)
    else:
        return onprem_configuration(conf)
