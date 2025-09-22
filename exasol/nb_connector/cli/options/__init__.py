from exasol.nb_connector.cli.options.bucketfs import BUCKETFS_OPTIONS
from exasol.nb_connector.cli.options.common import (
    COMMON_OPTIONS,
    SCS_OPTIONS,
)
from exasol.nb_connector.cli.options.docker_db import EXTRA_DOCKER_DB_OPTIONS
from exasol.nb_connector.cli.options.onprem import ONPREM_DB_OPTIONS
from exasol.nb_connector.cli.options.saas import EXTRA_SAAS_OPTIONS
from exasol.nb_connector.cli.options.ssl import SSL_OPTIONS

DOCKER_DB_OPTIONS = SCS_OPTIONS + EXTRA_DOCKER_DB_OPTIONS + COMMON_OPTIONS

SAAS_OPTIONS = SCS_OPTIONS + EXTRA_SAAS_OPTIONS + SSL_OPTIONS + COMMON_OPTIONS

ONPREM_OPTIONS = (
    SCS_OPTIONS + ONPREM_DB_OPTIONS + BUCKETFS_OPTIONS + SSL_OPTIONS + COMMON_OPTIONS
)
