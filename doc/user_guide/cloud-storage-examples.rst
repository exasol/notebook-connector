Cloud Storage Extension Examples
#################################

The `cloud-storage-extension
<https://github.com/exasol/cloud-storage-extension>`_ lets Exasol UDFs read
and write data from S3, Azure Blob Storage, and Google Cloud Storage using
``IMPORT`` and ``EXPORT`` statements.

The setup involves four steps: download the extension JAR, upload it to
BucketFS, compute the UDF-visible path to the JAR, and finally deploy the UDF
scripts into the database schema.

Step 1 – Download the extension JAR
*************************************

Use ``retrieve_jar`` to download the latest Cloud Storage Extension JAR from
GitHub.  This is a small helper step inside the larger deployment workflow:
resolve the latest release artifact for the extension and save it locally.
Specifying a ``storage_path`` keeps the file in a known location so you can
inspect it or reuse it across sessions.

.. code-block:: python

    import pathlib
    from exasol.nb_connector.github import Project, retrieve_jar
    from exasol.nb_connector.cloud_storage import setup_scripts
    from exasol.nb_connector.connections import (
        open_pyexasol_connection,
        open_bucketfs_bucket,
        get_udf_bucket_path,
    )

    jar_path = retrieve_jar(Project.CLOUD_STORAGE_EXTENSION, storage_path=pathlib.Path("/tmp"))

If you need to inspect the exact version before downloading, call
``get_latest_version_and_jar_url`` first:

.. code-block:: python

    from exasol.nb_connector.github import get_latest_version_and_jar_url

    version, jar_url = get_latest_version_and_jar_url(Project.CLOUD_STORAGE_EXTENSION)
    print(version)
    print(jar_url)

Step 2 – Upload the JAR to BucketFS
*************************************

Open a BucketFS bucket using the credentials stored in the SCS and upload the
JAR file.  The ``bucket.upload(name, file_object)`` call streams the file
directly to BucketFS without buffering the entire content in memory.  The
first argument is the name (path) inside the bucket — here we use
``jar_path.name`` to keep it at the bucket root.

.. code-block:: python

    from exasol.nb_connector.connections import open_bucketfs_bucket

    bucket = open_bucketfs_bucket(my_secrets)
    with open(jar_path, "rb") as f:
        bucket.upload(jar_path.name, f)

Step 3 – Build the UDF-visible JAR path
*****************************************

BucketFS files are mounted inside UDF containers under a fixed prefix.
``get_udf_bucket_path`` returns this prefix for the configured bucket
(e.g. ``/buckets/bfsdefault/default``).  Appending the file name gives the
absolute path that the ``setup_scripts`` call must pass to the database so
it knows where to find the JAR at UDF execution time.

.. code-block:: python

    from exasol.nb_connector.connections import get_udf_bucket_path

    udf_jar_path = get_udf_bucket_path(my_secrets) + "/" + jar_path.name
    # e.g. /buckets/bfsdefault/default/exasol-cloud-storage-extension-2.8.0.jar

Step 4 – Deploy the UDF scripts
*********************************

``setup_scripts`` creates the ``IMPORT_PATH``, ``IMPORT_METADATA``,
``EXPORT_PATH``, and related UDF scripts in the given schema.  Pass the
database connection, the schema name, and the UDF-visible JAR path computed
above.  After this call completes, cloud storage can be used in SQL statements
from any session that activates the schema.

.. code-block:: python

    from exasol.nb_connector.cloud_storage import setup_scripts
    from exasol.nb_connector.connections import open_pyexasol_connection

    with open_pyexasol_connection(my_secrets, schema="MY_SCHEMA") as conn:
        setup_scripts(conn, schema_name="MY_SCHEMA", bucketfs_jar_path=udf_jar_path)
