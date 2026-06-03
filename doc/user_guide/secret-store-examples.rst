Secure Configuration Storage (SCS) Examples
############################################

``Secrets`` is the central configuration object used by **every** API in the
Notebook Connector.  It stores key-value pairs in an AES-encrypted SQLite
database on disk.  You must create or open a ``Secrets`` instance before
calling any other API.

Unless stated otherwise, the snippets below work both in Jupyter notebooks and
in regular Python files.

Opening or creating a store
****************************

Import ``Secrets`` from ``exasol.nb_connector.secret_store`` and provide a
file path together with a master password.  If the file does not yet exist it
is created automatically.  The ``AILabConfig`` enum (aliased to ``CKey`` here)
provides all recognised key names, and ``StorageBackend`` lets you switch
between on-premise and SaaS modes.

.. code-block:: python

    from pathlib import Path
    from exasol.nb_connector.secret_store import Secrets
    from exasol.nb_connector.ai_lab_config import AILabConfig as CKey, StorageBackend

    my_secrets = Secrets(
        db_file=Path("my_config.db"),
        master_password="my-strong-password",
    )

.. note::
   If the file already exists the ``master_password`` must match the one used
   when it was first created, otherwise
   :py:class:`~exasol.nb_connector.secret_store.InvalidPassword` is raised.

Saving and reading values
**************************

All values are stored as strings. Use enum members from
:py:class:`~exasol.nb_connector.ai_lab_config.AILabConfig` as keys.

Call ``my_secrets.save(key, value)`` to persist a setting.  The value is
always a string — numeric ports and boolean flags must be quoted.  Use
``my_secrets.get(key)`` to retrieve a value; it returns ``None`` when the key
is absent, or you can supply a second argument as a default.

.. code-block:: python

    from exasol.nb_connector.ai_lab_config import AILabConfig as CKey

    my_secrets.save(CKey.db_host_name, "192.168.1.10")
    my_secrets.save(CKey.db_port,      "8563")
    my_secrets.save(CKey.db_user,      "sys")
    my_secrets.save(CKey.db_password,  "exasol")
    my_secrets.save(CKey.db_schema,    "MY_SCHEMA")

    host   = my_secrets.get(CKey.db_host_name)           # returns None if absent
    schema = my_secrets.get(CKey.db_schema, "MY_SCHEMA") # with a default

Iterating and Removing
**********************

``my_secrets.items()`` returns all stored key-value pairs as an iterable,
which is useful for debugging or exporting the configuration.
``my_secrets.remove(key)`` permanently deletes a single entry from the store.

.. code-block:: python

    from exasol.nb_connector.ai_lab_config import AILabConfig as CKey

    for key, value in my_secrets.items():
        print(key, "->", value)

    my_secrets.remove(CKey.db_password)

Choosing the backend (on-prem vs. SaaS)
*****************************************

The ``storage_backend`` key tells every connection helper whether to use the
on-premise database parameters or the SaaS account parameters.  Set it to
``StorageBackend.onprem.name`` (the default when the key is absent) for a
self-hosted database, or to ``StorageBackend.saas.name`` and supply the four
SaaS-specific keys shown below.

.. code-block:: python

    from exasol.nb_connector.ai_lab_config import AILabConfig as CKey, StorageBackend

    # On-prem (default when key is absent)
    my_secrets.save(CKey.storage_backend, StorageBackend.onprem.name)

    # SaaS
    my_secrets.save(CKey.storage_backend, StorageBackend.saas.name)
    my_secrets.save(CKey.saas_url,           "https://cloud.exasol.com")
    my_secrets.save(CKey.saas_account_id,    "<your-account-id>")
    my_secrets.save(CKey.saas_token,         "<your-pat>")
    my_secrets.save(CKey.saas_database_name, "my-database")

To query which backend is currently active, call ``get_backend``.  This is
useful to branch logic in notebooks that need to work in both modes.

.. code-block:: python

    from exasol.nb_connector.connections import get_backend

    print(get_backend(my_secrets))   # StorageBackend.onprem or StorageBackend.saas

All supported configuration keys
**********************************

The table below lists every key understood by the Notebook Connector APIs.
Keys that are not relevant to your setup (e.g. SaaS keys when using on-prem)
can simply be left unset.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Key
     - Purpose
   * - ``db_host_name``
     - On-prem DB host
   * - ``db_port``
     - On-prem DB port (default ``8563``)
   * - ``db_user``
     - DB user name
   * - ``db_password``
     - DB password
   * - ``db_schema``
     - Default DB schema for UDF scripts
   * - ``db_encryption``
     - ``"True"`` / ``"False"`` – enable TLS for DB connections
   * - ``cert_vld``
     - ``"True"`` / ``"False"`` – validate server TLS certificate
   * - ``trusted_ca``
     - Path to a trusted CA file or directory
   * - ``client_cert`` / ``client_key``
     - Client TLS certificate and private key paths
   * - ``bfs_host_name``
     - BucketFS host (defaults to ``db_host_name`` when absent)
   * - ``bfs_port``
     - BucketFS port (default ``2580``)
   * - ``bfs_service``
     - BucketFS service name (e.g. ``bfsdefault``)
   * - ``bfs_bucket``
     - BucketFS bucket name (e.g. ``default``)
   * - ``bfs_user``
     - BucketFS user
   * - ``bfs_password``
     - BucketFS password
   * - ``bfs_encryption``
     - ``"True"`` / ``"False"`` – TLS for BucketFS
   * - ``saas_url``
     - SaaS service URL (e.g. ``https://cloud.exasol.com``)
   * - ``saas_account_id``
     - SaaS account ID
   * - ``saas_database_id``
     - SaaS database ID (alternative to ``saas_database_name``)
   * - ``saas_database_name``
     - SaaS database name
   * - ``saas_token``
     - SaaS personal access token (PAT)
   * - ``storage_backend``
     - ``"onprem"`` or ``"saas"`` – which backend to use
   * - ``mem_size``
     - Docker-DB memory in GiB (ITDE)
   * - ``disk_size``
     - Docker-DB disk in GiB (ITDE)
   * - ``accelerator``
     - ``"none"`` or ``"nvidia"`` (ITDE GPU support)
   * - ``huggingface_token``
     - Hugging Face user access token (needed for gated models)
   * - ``bfs_model_subdir``
     - Sub-directory inside the bucket for model storage (default ``models``)
   * - ``bfs_connection_name``
     - Name of the Exasol CONNECTION object for BucketFS credentials
