import ipywidgets as widgets

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.connections import get_backend
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.config.onprem import get_onprem
from exasol.nb_connector.ui.config.saas import get_saas
from exasol.nb_connector.ui.docker.docker_db import docker_db_configuration


def configure_db(conf: Secrets) -> widgets.Widget:
    """
    Creates a db configuration UI, depending on the choice of the database.
    """
    storage_backend = get_backend(conf)
    if storage_backend == StorageBackend.saas:
        return get_saas(conf)
    elif conf.get(CKey.use_itde, "True") == "True":
        return docker_db_configuration(conf)
    else:
        return get_onprem(conf)
