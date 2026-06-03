Script Language Container (SLC) Examples
##########################################

Script Language Containers (SLCs) are Linux container based Python
environments that
Exasol UDF scripts execute inside.  By building a custom SLC you can include
any Python package your UDFs depend on without modifying the database server.
The Notebook Connector automates the three-step process: register → build &
upload → activate.

**Required extra:** ``pip install "notebook-connector[slc]"``

Step 1 – Register an SLC instance
***********************************

Call ``ScriptLanguageContainer.create()`` once per SLC.  This method:

* Clones the `script-languages-release <https://github.com/exasol/script-languages-release>`_
  git repository to the local file system.
* Saves the chosen ``flavor`` in the SCS under the given ``name``.
* Derives a unique language alias (``CUSTOM_SLC_<NAME>``) that will be used
  when activating the container in the database.

The ``name`` must be unique across all SLCs registered in the same SCS, and
the ``flavor`` must match a directory name inside the cloned repository (e.g.
``python3-ds-EXASOL-7.1.0``).

.. code-block:: python

    from exasol.nb_connector.slc import ScriptLanguageContainer

    ScriptLanguageContainer.create(
        secrets=my_secrets,
        name="my_slc",
        flavor="python3-ds-EXASOL-7.1.0",
    )
    # The resulting language alias will be: CUSTOM_SLC_MY_SLC

Step 2 – Build and upload the SLC
***********************************

Instantiate ``ScriptLanguageContainer`` with the same ``name`` used during
``create()``.  Calling ``deploy()`` builds the container image from the local
clone, packages it as a tar archive, streams the archive to BucketFS, and
stores the resulting language activation definition in the SCS.

.. code-block:: python

    from exasol.nb_connector.slc import ScriptLanguageContainer

    slc = ScriptLanguageContainer(secrets=my_secrets, name="my_slc")
    slc.deploy()

Step 3 – Activate the language in the database
************************************************

After deployment you must activate the language alias in the current session
before any UDF that uses it can run.  There are two ways:

* ``get_activation_sql`` returns the raw ``ALTER SESSION SET
  SCRIPT_LANGUAGES='...'`` statement.  Run it on any connection to activate
  all registered SLCs for that session.
* ``open_pyexasol_connection_with_lang_definitions`` opens a connection and
  immediately executes the activation statement, so the returned connection
  is ready to call UDFs straight away.

.. code-block:: python

    from exasol.nb_connector.language_container_activation import (
        get_activation_sql,
        open_pyexasol_connection_with_lang_definitions,
    )

    # Print the ALTER SESSION statement — useful for debugging or manual execution
    print(get_activation_sql(my_secrets))

    # Open a connection that has already activated all registered SLCs
    conn = open_pyexasol_connection_with_lang_definitions(my_secrets)
    conn.execute("SELECT MY_UDF() FROM DUAL")

.. note::
   ``get_activation_sql`` merges language definitions stored in the SCS
   (keys prefixed with ``language_container_activation_``) with whatever is
   already registered in the database at session level, then returns a single
   ``ALTER SESSION SET SCRIPT_LANGUAGES='...'`` statement.
