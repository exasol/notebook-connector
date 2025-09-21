from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.cli.param_wrappers import (
    ScsOption,
    ScsSecretOption,
)

BUCKETFS_OPTIONS = [
    ScsOption(
        "--bucketfs-host",
        metavar="HOST",
        type=str,
        default="localhost",
        help="BucketFS host name",
        scs_key=CKey.bfs_host_name,
    ),
    ScsOption(
        "--bucketfs-host-internal",
        metavar="HOST",
        type=str,
        help="BucketFS Internal Host Name [defaults to --bucketfs-host]",
        scs_key=CKey.bfs_internal_host_name,
        get_default_from="bucketfs_host"
    ),
    ScsOption(
        "--bucketfs-port",
        metavar="PORT",
        type=int,
        default=2580,
        help="BucketFS port",
        scs_key="bucketfs_port",
    ),
    ScsOption(
        "--bucketfs-port-internal",
        metavar="PORT",
        type=int,
        help="BucketFS internal port [defaults to --bucketfs-port]",
        scs_key=CKey.bfs_internal_port,
        get_default_from="bucketfs_port"
    ),
    ScsOption(
        "--bucketfs-user",
        metavar="USERNAME",
        type=str,
        # should we add "w" as default here?
        help="BucketFS user name",
        scs_key=CKey.bfs_user,
    ),
    ScsSecretOption(
        "--bucketfs-password",
        envvar="SCS_BUCKETFS_PASSWORD",
        prompt="BucketFS write password",
        scs_key=CKey.bfs_password,
    ),
    ScsOption(
        "--bucketfs-name",
        metavar="BFS_SERVICE",
        type=str,
        default="bfsdefault",
        help="BucketFS service name",
        scs_key="bucketfs_name",
    ),
    ScsOption(
        "--bucket",
        metavar="BUCKET",
        type=str,
        default="default",
        help="BucketFS bucket name",
        scs_key=CKey.bfs_bucket,
    ),
    ScsOption(
        "--bucketfs-use-encryption/--no-bucketfs-use-encryption",
        type=bool,
        default=True,
        help="Whether to encrypt communication with the BucketFS or not",
        scs_key=CKey.bfs_encryption,
    ),
]
