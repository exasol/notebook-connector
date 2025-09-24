from exasol.nb_connector.cli.options.bucketfs import BUCKETFS_OPTIONS
from exasol.nb_connector.cli.options.common import (
    COMMON_OPTIONS,
    SAVE_OPTIONS,
    SCS_OPTIONS,
)
from exasol.nb_connector.cli.options.docker_db import EXTRA_DOCKER_DB_OPTIONS
from exasol.nb_connector.cli.options.onprem import ONPREM_DB_OPTIONS
from exasol.nb_connector.cli.options.saas import EXTRA_SAAS_OPTIONS
from exasol.nb_connector.cli.options.ssl import SSL_OPTIONS


def _wrap(options):
    return SCS_OPTIONS + SAVE_OPTIONS + options + COMMON_OPTIONS


DOCKER_DB_OPTIONS = _wrap(EXTRA_DOCKER_DB_OPTIONS)

SAAS_OPTIONS = _wrap(EXTRA_SAAS_OPTIONS + SSL_OPTIONS)

ONPREM_OPTIONS = _wrap(ONPREM_DB_OPTIONS + BUCKETFS_OPTIONS + SSL_OPTIONS)
