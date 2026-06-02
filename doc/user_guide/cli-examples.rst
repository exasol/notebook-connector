Command Line Interface (CLI) Examples
######################################

The Notebook Connector ships two CLI tools: ``ai-lab`` and ``scs``.
See their dedicated pages for the full option reference:

* :doc:`ai-lab-cli` – start JupyterLab and deploy bundled notebooks.
* :doc:`scs-cli` – create and manage the Secure Configuration Storage.

Typical on-premise workflow
****************************

The following steps show how to configure the connector for an on-premise
Exasol database, verify the setup, and then launch JupyterLab.

**Step 1 – Create and populate the SCS for an on-premise database**

The ``scs configure onprem`` command creates an encrypted configuration file
(``my_config.db``) and stores all connection details inside it.  The master
password is read from the environment variable ``SCS_MASTER_PASSWORD`` so it
is never echoed to the terminal.  Replace the placeholder values with your
actual database host, port, credentials, and BucketFS settings.

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

**Step 2 – Verify the configuration is complete and reachable**

The ``scs check`` command validates that all required keys are present in the
store.  Adding ``--connect`` also opens a real TCP connection to the database
and BucketFS to confirm network reachability before running any notebooks.

.. code-block:: shell

    scs check --connect my_config.db

**Step 3 – Inspect stored settings**

Use ``scs show`` to print a human-readable view of every key stored in the
configuration file.  Secret values such as passwords are automatically masked
so they are not accidentally exposed in logs or screenshots.

.. code-block:: shell

    scs show my_config.db

**Step 4 – Launch JupyterLab with the bundled notebooks**

``ai-lab start`` launches a JupyterLab server and makes the bundled Exasol
notebooks available under the directory specified by ``--notebook-dir``.
The ``--port`` flag lets you pick a custom port if the default (8888) is
already in use.

.. code-block:: shell

    ai-lab start --notebook-dir ~/work/notebooks --port 9999

Typical SaaS workflow
**********************

For Exasol SaaS, the database host and credentials are derived from your
account ID and personal access token (PAT).  Export the PAT as an environment
variable so it is never written to disk in plain text.  After configuring,
run ``scs check --connect`` to confirm that the SaaS endpoint is reachable
from your machine.

.. code-block:: shell

    export SCS_MASTER_PASSWORD="my-strong-password"
    export SCS_EXASOL_SAAS_TOKEN="<your-pat>"

    scs configure saas my_saas_config.db \
        --saas-account-id "<your-account-id>" \
        --saas-database-name "my-database" \
        --db-schema MY_SCHEMA

    scs check --connect my_saas_config.db

Typical workflow for a local Docker database
*********************************************

The ``docker-db`` sub-command stores the desired memory and disk sizes for the
Docker container in the configuration file.  The database is not started here —
use :doc:`itde-examples` to bring the container up via the Python API after the
configuration is saved.

.. code-block:: shell

    scs configure docker-db my_docker_config.db \
        --db-mem-size 4 \
        --db-disk-size 10

    # Then start the database via the Python API (see :doc:`itde-examples`)