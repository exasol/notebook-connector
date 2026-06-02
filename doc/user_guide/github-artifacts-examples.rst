GitHub Release Artifacts Examples
##################################

The ``exasol.nb_connector.github`` module provides helpers for fetching the
latest release of an Exasol extension JAR from GitHub without manually
navigating GitHub's releases page.  This is typically the first step before
uploading a JAR to BucketFS and deploying its UDF scripts.

``Project`` is an enum that identifies a supported extension.  Currently
supported values are:

* ``Project.CLOUD_STORAGE_EXTENSION``
* ``Project.KAFKA_CONNECTOR_EXTENSION``

Querying the latest version
****************************

``get_latest_version_and_jar_url`` contacts the GitHub Releases API and
returns a tuple of ``(version_string, download_url)``.  Use this when you
want to display or log the current version before downloading, or to check
whether a newer version is available compared to what is already in BucketFS.

.. code-block:: python

    from exasol.nb_connector.github import (
        Project,
        get_latest_version_and_jar_url,
        retrieve_jar,
    )

    project = Project.CLOUD_STORAGE_EXTENSION

    version, jar_url = get_latest_version_and_jar_url(project)
    print(f"Latest version: {version}")
    print(f"Download URL:   {jar_url}")

Downloading the JAR
********************

``retrieve_jar`` downloads the JAR to a local directory.  By default it uses
a local cache directory so the JAR is not re-downloaded on repeated calls.
Pass ``use_local_cache=False`` to force a fresh download even if a cached copy
exists.  Use ``storage_path`` to control where the file is saved; when omitted
it uses a temporary directory managed by the library.

.. code-block:: python

    import pathlib

    # Download to the current directory (cached by default)
    jar_path = retrieve_jar(project)
    print(f"Downloaded to: {jar_path}")

    # Download to a specific directory, bypass cache
    jar_path = retrieve_jar(
        project,
        use_local_cache=False,
        storage_path=pathlib.Path("/tmp/jars"),
    )