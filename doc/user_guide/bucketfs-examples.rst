BucketFS Examples
#################

BucketFS is Exasol's distributed file system that is accessible from inside
UDF scripts.  You use it to store model files, JARs, configuration data, and
any other large assets that UDFs need at runtime.  The Notebook Connector
provides two APIs for BucketFS: a lower-level bucket API and a higher-level
`PathLike <https://exasol.github.io/bucketfs-python/main/api.html#exasol.bucketfs._path.PathLike>`_
interface.  For the underlying BucketFS client API, see the
`bucketfs-python API reference <https://exasol.github.io/bucketfs-python/main/api.html>`_.

Configuration
*************

Before calling any BucketFS helper you must store the BucketFS connection
parameters in the SCS.  When using ITDE (the local Docker database), these
keys are populated automatically by ``bring_itde_up`` — you only need to set
them manually for a self-hosted on-premise Exasol installation.  The same
helpers also work with Exasol SaaS when you store the SaaS settings
(``storage_backend``, ``saas_url``, ``saas_account_id``, ``saas_token``, and
``saas_database_id`` or ``saas_database_name``) in the SCS instead.

``bfs_host_name`` is optional; when absent it falls back to ``db_host_name``.
``bfs_encryption`` should be set to ``"True"`` in production environments.

.. code-block:: python

    from exasol.nb_connector.ai_lab_config import AILabConfig as CKey

    my_secrets.save(CKey.bfs_host_name,  "192.168.1.10")  # optional; falls back to db_host_name
    my_secrets.save(CKey.bfs_port,       "2580")
    my_secrets.save(CKey.bfs_service,    "bfsdefault")
    my_secrets.save(CKey.bfs_bucket,     "default")
    my_secrets.save(CKey.bfs_user,       "w")
    my_secrets.save(CKey.bfs_password,   "write")
    my_secrets.save(CKey.bfs_encryption, "False")

Uploading and Accessing Files via the Bucket API
************************************************

``open_bucketfs_bucket`` returns a bucket object from the
`exasol-bucketfs <https://pypi.org/project/exasol-bucketfs>`_ library.  Call
``bucket.upload(target_path, file_object)`` to stream a local file into
BucketFS.  The ``target_path`` is the path inside the bucket — it is relative
to the bucket root.  For more details on bucket objects and helper utilities
such as ``exasol.bucketfs.as_string`` and ``exasol.bucketfs.as_file``, see the
`bucketfs-python user guide <https://exasol.github.io/bucketfs-python/main/user_guide/user_guide.html>`_.

``get_udf_bucket_path`` returns the absolute path that Exasol UDFs use to
read files from this bucket (e.g. ``/buckets/bfsdefault/default``).  Append
the relative ``target_path`` used during upload to build the full UDF path.

.. code-block:: python

    from exasol.nb_connector.connections import (
        get_udf_bucket_path,
        open_bucketfs_bucket,
    )

    bucket = open_bucketfs_bucket(my_secrets)

    # Upload a local file into the "models/" sub-directory of the bucket
    with open("my_model.pkl", "rb") as f:
        bucket.upload("models/my_model.pkl", f)

    # Print the path that UDFs can use to access this bucket
    print(get_udf_bucket_path(my_secrets))
    # e.g.  /buckets/bfsdefault/default

PathLike Interface
******************

``open_bucketfs_location`` returns a ``PathLike`` object that supports the
``/`` operator for path joining, similar to ``pathlib.Path``.  Use ``.write``
to upload bytes and ``.read`` to download them.  This API is more Pythonic
than the raw bucket API and is preferred when you need to compose paths
programmatically.  The
`bucketfs-python PathLike docs <https://exasol.github.io/bucketfs-python/main/api.html#exasol.bucketfs._path.PathLike>`_
cover the supported operations in more detail.

.. code-block:: python

    from exasol.nb_connector.connections import open_bucketfs_location

    # Get a root location pointing at the bucket configured in the SCS
    location = open_bucketfs_location(my_secrets)

    # Write bytes to data/file.txt inside the bucket
    (location / "data" / "file.txt").write(b"hello bucketfs")

    # Read the same file back as bytes
    content = (location / "data" / "file.txt").read()
