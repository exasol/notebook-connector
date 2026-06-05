:octicon:`terminal` Command Line Interface for the Secure Configuration Storage (SCS)
#####################################################################################

Notebook Connector installs the ``scs`` command line interface for managing
Secure Configuration Storage files.

The ``scs`` CLI exposes three commands:

* ``check``
* ``configure``
* ``show``

Help
****

Use ``--help`` on the top-level command or any subcommand to inspect the
currently available command tree and options.

.. code-block:: shell

    scs --help
    scs configure --help
    scs configure onprem --help
    scs configure saas --help
    scs configure docker-db --help
    scs show --help
    scs check --help

Master Password and SCS File
****************************

As said in the User Guide, the SCS is secured by a *master password*.

To avoid the master password or any other secret to show up in the history of
your command line shell (e.g. ``~/.bash_history``) the CLI only allows the
following methods for entering any secret value:

* Interactive typing, the typed characters will be invisible
* Setting a related environment variable, which is useful for automating the
  SCS usage

All commands operate on an SCS file. If the file does not exist then the CLI
will create it. The CLI needs the master password for creating a new encrypted
file but also for accessing an existing encrypted file.

Master password and SCS file can be specified by using the following
environment variables:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Name
     - Value
   * - ``SCS_FILE``
     - Path to the encrypted SCS file.
   * - ``SCS_MASTER_PASSWORD``
     - Master password for creating or accessing the encrypted SCS file.


.. _configure:

Command ``configure``
*********************

The CLI command ``configure`` requires a subcommand for specifying the variant
of Exasol database instance you want to connect to. The CLI supports 3
different variants:

* ``onprem``
* ``saas``
* ``docker-db``

Common ``configure`` options
============================

These options are available on every ``configure`` subcommand:

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Option
     - Meaning
   * - ``SCS_FILE``
     - Positional path to the encrypted SCS file. Can also be provided via
       the ``SCS_FILE`` environment variable.
   * - ``--overwrite-backend`` / ``--no-overwrite-backend``
     - Whether to overwrite a different backend already stored in the SCS.
   * - ``--db-schema``
     - Database schema for installing UDFs of Exasol extensions.

Command ``configure onprem``
============================

Use ``configure onprem`` for an Exasol on-premise instance.

.. code-block:: shell

    scs configure onprem <SCS file>

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Option
     - Meaning
   * - ``--db-host-name``
     - Database connection host name.
   * - ``--db-port``
     - Database connection port. Default: ``8563``.
   * - ``--db-username``
     - Database user name.
   * - ``--db-password``
     - Database password. Secret option. Related environment variable:
       ``SCS_EXASOL_DB_PASSWORD``.
   * - ``--db-use-encryption`` / ``--no-db-use-encryption``
     - Whether to encrypt communication with the database. Default:
       ``--db-use-encryption``.
   * - ``--bucketfs-host``
     - BucketFS host name.
   * - ``--bucketfs-host-internal``
     - BucketFS internal host name. Default: ``localhost``.
   * - ``--bucketfs-port``
     - BucketFS port. Default: ``2580``.
   * - ``--bucketfs-port-internal``
     - BucketFS internal port. Default: ``2580``.
   * - ``--bucketfs-user``
     - BucketFS user name. Default: ``w``.
   * - ``--bucketfs-password``
     - BucketFS write password. Secret option. Related environment variable:
       ``SCS_BUCKETFS_PASSWORD``.
   * - ``--bucketfs-name``
     - BucketFS service name, for example ``bfsdefault``.
   * - ``--bucket``
     - BucketFS bucket name, for example ``default``.
   * - ``--bucketfs-use-encryption`` / ``--no-bucketfs-use-encryption``
     - Whether to encrypt communication with BucketFS. Default:
       ``--bucketfs-use-encryption``.
   * - ``--ssl-use-cert-validation`` / ``--no-ssl-use-cert-validation``
     - Whether to validate SSL certificates. Default:
       ``--ssl-use-cert-validation``.
   * - ``--ssl-cert-path``
     - Path to a trusted CA file or directory.

Command ``configure saas``
==========================

Use ``configure saas`` for an Exasol SaaS instance.

.. code-block:: shell

    scs configure saas <SCS file>

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Option
     - Meaning
   * - ``--saas-url``
     - Exasol SaaS service URL. Default: ``https://cloud.exasol.com``.
   * - ``--saas-account-id``
     - Exasol SaaS account ID.
   * - ``--saas-database-id``
     - Exasol SaaS database ID. Can be used instead of
       ``--saas-database-name``.
   * - ``--saas-database-name``
     - Exasol SaaS database name. Can be used instead of
       ``--saas-database-id``.
   * - ``--saas-token``
     - Exasol SaaS personal access token. Secret option. Related environment
       variable: ``SCS_EXASOL_SAAS_TOKEN``.
   * - ``--ssl-use-cert-validation`` / ``--no-ssl-use-cert-validation``
     - Whether to validate SSL certificates. Default:
       ``--ssl-use-cert-validation``.
   * - ``--ssl-cert-path``
     - Path to a trusted CA file or directory.

Command ``configure docker-db``
===============================

Use ``configure docker-db`` for an Exasol Docker instance managed via ITDE.

.. code-block:: shell

    scs configure docker-db <SCS file>

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Option
     - Meaning
   * - ``--db-mem-size``
     - Database memory size in GiB. Default: ``8``.
   * - ``--db-disk-size``
     - Database disk size in GiB. Default: ``2``.
   * - ``--accelerator``
     - Hardware acceleration. Default: ``none``.

Typical workflows
=================

On-premise workflow
-------------------

The following steps show how to create an encrypted SCS file for an
on-premise Exasol database, verify that all required values are present, and
optionally check network reachability before opening any notebooks.

.. code-block:: shell

    export SCS_MASTER_PASSWORD="my-strong-password"

    scs configure onprem my_config.db \
        --db-host-name 192.168.1.10 \
        --db-port 8563 \
        --db-username sys \
        --db-schema MY_SCHEMA \
        --bucketfs-host 192.168.1.10 \
        --bucketfs-port 2580 \
        --bucketfs-name bfsdefault \
        --bucket default

    scs check --connect my_config.db
    scs show my_config.db

SaaS workflow
-------------

For Exasol SaaS, the database host and credentials are derived from your
account ID and personal access token (PAT).  Export the PAT as an environment
variable so it is never written to disk in plain text.

.. code-block:: shell

    export SCS_MASTER_PASSWORD="my-strong-password"
    export SCS_EXASOL_SAAS_TOKEN="<your-pat>"

    scs configure saas my_saas_config.db \
        --saas-account-id "<your-account-id>" \
        --saas-database-name "my-database" \
        --db-schema MY_SCHEMA

    scs check --connect my_saas_config.db
    scs show my_saas_config.db

Local Docker database workflow
------------------------------

Use ``configure docker-db`` to store the desired ITDE sizing values in the
SCS.  This command prepares the local setup but does not start the Docker
database by itself.  Start the container later via the Python API described
in :doc:`itde-examples`.

.. code-block:: shell

    scs configure docker-db my_docker_config.db \
        --db-mem-size 4 \
        --db-disk-size 10

Incremental Configuration
=========================

CLI command ``configure`` allows you to configure the database connection
partially and add more configuration items incrementally at a later point in
time.

That is, if you currently only know the host of the database, then you can
save this to the SCS and add the password later on.

.. _show:

Command ``show``
****************

With CLI command ``show`` you can inspect the configuration items already
available in the SCS.

In the output passwords and other sensitive data are replaced by asterisks
``****``.

.. code-block:: shell

    scs show <SCS file>

Here is the output for a partially configured connection to an Exasol SaaS instance:

.. code-block:: shell

    backend: saas
    use_itde: False
    --saas-url: https://cloud.exasol.com
    --saas-token: ****
    --ssl-use-cert-validation: True


.. _check:

Command ``check``
*****************

With command ``check`` you can check whether the configuration is complete or
whether there are still some items missing.

With option ``--connect`` the command also verifies the configuration by
connecting to the configured Exasol database instance, executing a SQL
statement and accessing the BucketFS.

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Option
     - Meaning
   * - ``--connect`` / ``--no-connect``
     - Verify that connecting to the configured Exasol database instance
       succeeds. Default: ``--no-connect``.

.. code-block:: shell

    scs check --connect <SCS file>

Here is the output when having started configuring a connection to an Exasol
SaaS instance without providing any further options, yet:

.. code-block:: shell

    Error: 5 options are not yet configured:
    --saas-account-id, --saas-database-id,
    --saas-database-name, --saas-token, --db-schema.
