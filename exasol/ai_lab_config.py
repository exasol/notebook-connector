from enum import Enum


class AILabConfig(Enum):
    use_itde = 'USE_ITDE'
    db_host_name = 'EXTERNAL_HOST_NAME'
    db_port = 'DB_PORT'
    db_schema = 'SCHEMA'
    db_user = 'USER'
    db_password = 'PASSWORD'
    db_encryption = 'ENCRYPTION'
    cert_vld = 'CERTIFICATE_VALIDATION'
    trusted_ca = 'TRUSTED_CA'
    client_cert = 'CLIENT_CERTIFICATE'
    client_key = 'PRIVATE_KEY'
    bfs_host_name = 'BUCKETFS_HOST_NAME'
    bfs_port = 'BUCKETFS_PORT'
    bfs_service = 'BUCKETFS_SERVICE'
    bfs_bucket = 'BUCKETFS_BUCKET'
    bfs_user = 'BUCKETFS_USER'
    bfs_password = 'BUCKETFS_PASSWORD'
    bfs_encryption = 'BUCKETFS_ENCRYPTION'
    mem_size = 'MEMORY_SIZE'
    disk_size = 'DISK_SIZE'
