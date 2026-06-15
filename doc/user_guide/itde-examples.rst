Local Docker Database (ITDE) Examples
#####################################

The *Integration Test Docker Environment* (ITDE) starts a fully functional
Exasol database inside a Docker container.  It is the easiest way to get a
development database running locally without a cloud account or a dedicated
server.  ITDE manages the Docker lifecycle and, importantly, automatically
writes all generated connection parameters back into the SCS so that every
other Notebook Connector API works out of the box.

**Required extra:** ``pip install "notebook-connector[docker-db]"``

Starting the Database
*********************

Import all lifecycle functions from ``itde_manager``.  Before calling
``bring_itde_up`` you can optionally store the desired container memory
(``mem_size``) and disk size (``disk_size``) in GiB in the SCS; both default
to sensible values when absent.

Calling ``bring_itde_up`` pulls the Exasol Docker image if necessary, creates
the container, and waits until the database is ready to accept connections.
After it returns, the SCS contains all 13 connection keys needed by the other
APIs — you do not need to configure anything manually.

.. code-block:: python

    from exasol.nb_connector.itde_manager import (
        bring_itde_up,
        get_itde_status,
        ItdeContainerStatus,
        restart_itde,
        take_itde_down,
    )
    from exasol.nb_connector.ai_lab_config import AILabConfig as CKey

    # Optional: set memory and disk size before starting (defaults: 4 GiB / 10 GiB)
    my_secrets.save(CKey.mem_size,  "4")
    my_secrets.save(CKey.disk_size, "10")

    # Pull the image (if needed) and start the Docker database
    bring_itde_up(my_secrets)

.. note::
   After ``bring_itde_up`` the SCS is automatically populated with
   ``db_host_name``, ``db_port``, ``bfs_host_name``, ``bfs_port``,
   ``db_user``, ``db_password``, ``bfs_user``, ``bfs_password``,
   ``bfs_service``, ``bfs_bucket``, ``db_encryption``, ``bfs_encryption``,
   and ``cert_vld``.  All other connection helpers therefore work without any
   further manual configuration.

Checking the Status
*******************

``get_itde_status`` returns an ``ItdeContainerStatus`` flag.  The possible
values are ``ABSENT`` (container does not exist), ``STOPPED`` (container
exists but is not running), ``RUNNING`` (container process is alive),
``VISIBLE`` (database port is open), and ``READY`` (both ``RUNNING`` and
``VISIBLE``).  Wait for ``READY`` before sending queries.

.. code-block:: python

    from exasol.nb_connector.itde_manager import (
        ItdeContainerStatus,
        get_itde_status,
    )

    status = get_itde_status(my_secrets)
    if status == ItdeContainerStatus.READY:
        print("Docker DB is up and reachable")
    else:
        print(f"Current status: {status}")

Restarting a Stopped Container
******************************

If the container was stopped (e.g. after a system reboot) you can restart it
with ``restart_itde``.  This is much faster than calling ``bring_itde_up``
again because the container and its data volumes already exist — only the
Docker process needs to be resumed.

.. code-block:: python

    from exasol.nb_connector.itde_manager import restart_itde

    restart_itde(my_secrets)

Shutting Down
*************

``take_itde_down`` removes the ITDE connection settings from the SCS.  By
default it also stops and removes the Docker container together with its
volumes and networks, freeing the related disk space.  Pass
``stop_db=False`` if the Docker-DB instance should remain intact, for example
when it was provided externally or when you want to inspect it manually.

.. code-block:: python

    from exasol.nb_connector.itde_manager import take_itde_down

    # Full teardown: stop container, remove volumes and networks
    take_itde_down(my_secrets)

    # Keep the Docker container but remove the ITDE connection entries from the SCS
    take_itde_down(my_secrets, stop_db=False)
