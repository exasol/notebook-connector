:octicon:`terminal` Command Line Interface for the Secure Configuration Storage (SCS)
#####################################################################################

You can invoke Notebook Connector's command line interface for the Secure
Configuration Storage (SCS) by running ``poetry run scs``.

The command line interface for accessing the SCS offers 3 main commands

* ``configure``: :ref:`Add or update <configure>` configuration items in the SCS.

* ``show``: :ref:`Show <show>` the currently configured database connection.

* ``check``: :ref:`Check <check>` whether the configuration is complete and
  optionally verify the configuration by connecting to the configured Exasol
  database instance.

Help
****

By adding option ``--help`` each of the commands will print extensive usage
information, here is an example:

.. code-block:: shell

    Usage: scs configure [OPTIONS] COMMAND [ARGS]...

      Add configuration options to the Secure Configuration Storage.

    Options:
      --help  Show this message and exit.

    Commands:
      docker-db  Configure connection to an Exasol Docker instance.
      onprem     Configure connection to an Exasol on-premise instance.
      saas       Configure connection to an Exasol SaaS instance.

Master Password and SCS File
****************************

As said in the User Guide, the SCS is secured by a *master password*.

To avoid the master password or any other secret to show up in the history of
your command line shell (e.g. ``~/.bash_history``) the CLI only allows the
following methods for entering any secret value:

* Interactive typing, the typed characters will be invisible

* Setting a related environment variable, which is useful for automating the SCS usage

Additionally all of the CLI commands require to specify the file containing
the SCS. If the file does not exist then the CLI will create it.  The CLI
needs the master password for creating a new encrypted file but also for
accessing an existing encrypted file.

Master password and SCS file can be specified by using the following
environment variables:

+-------------------------+------------------------------------------------------------------+
| Name                    | Value                                                            |
+=========================+==================================================================+
| ``SCS_FILE``            | Path to the encrypted SCS file                                   |
+-------------------------+------------------------------------------------------------------+
| ``SCS_MASTER_PASSWORD`` | Master password for creating or accessing the encrypted SCS file |
+-------------------------+------------------------------------------------------------------+


.. _configure:

Command ``configure``
*********************

The CLI command ``configure`` requires a subcommand for specifying the variant
of Exasol database instance you want to connect to. The CLI supports 3
different variants:

* ``onprem``
* ``saas``
* ``docker-db``

Here is the CLI command for configuring a connection to an Exasol SaaS
instance:

.. code-block:: shell

    scs configure saas <SCS file>

The available configuration options are specific to each of the instance
variants. Variant ``onprem`` requires to specify ``--db-host-name``, for
instance, while variant ``saas`` requires ``--saas-token``.

Use the CLI help to show all available options, incl. default values and also
related environment variables for secrets, e.g. ``SCS_EXASOL_DB_PASSWORD`` for
``--db-password``:

.. code-block:: shell

    scs configure onprem --help
    scs configure saas --help
    scs configure docker-db --help


Incremental Configuration
-------------------------

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

.. code-block:: shell

    scs check --connect <SCS file>

Here is the output when having started configuring a connection to an Exasol
SaaS instance without providing any further options, yet:

.. code-block:: shell

    Error: 5 options are not yet configured:
    --saas-account-id, --saas-database-id,
    --saas-database-name, --saas-token, --db-schema.
