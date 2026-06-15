Database Connection Examples
############################

All connection helpers accept a
:py:class:`~exasol.nb_connector.secret_store.Secrets` object and derive every
parameter from it automatically.  You can override individual parameters via
``**kwargs`` which are forwarded to the underlying library.  Make sure the SCS
contains at least ``db_host_name``, ``db_port``, ``db_user``, and
``db_password`` before opening a connection (see :doc:`secret-store-examples`).

.. important::
   ``open_pyexasol_connection`` does **not** set a default schema even when
   ``db_schema`` is stored in the SCS.  Pass ``schema="MY_SCHEMA"`` explicitly,
   or use ``open_sqlalchemy_connection`` / ``open_ibis_connection`` which do
   apply ``db_schema`` automatically.

pyexasol
********

``open_pyexasol_connection`` wraps the `pyexasol
<https://pypi.org/project/pyexasol>`_ driver and is the recommended choice for
raw SQL execution and UDF-related work.  It supports the context-manager
protocol (``with`` statement), which closes the connection automatically when
the block exits — preferred for short-lived queries.  For longer-lived
connections (e.g., when setting up UDF scripts), open the connection manually
and call ``conn.close()`` explicitly.

.. code-block:: python

    from exasol.nb_connector.connections import open_pyexasol_connection

    # Context-manager usage (connection closed automatically)
    with open_pyexasol_connection(my_secrets, schema="MY_SCHEMA") as conn:
        rows = conn.execute("SELECT * FROM MY_TABLE LIMIT 10").fetchall()
        print(rows)

    # Manual usage (useful for UDF/extension setup where connection is reused)
    conn = open_pyexasol_connection(my_secrets, compression=True)
    conn.execute("CREATE SCHEMA IF NOT EXISTS MY_SCHEMA")
    conn.close()

SQLAlchemy
**********

``open_sqlalchemy_connection`` returns a standard ``sqlalchemy.Engine``.  It is
the right choice when working with tools that expect SQLAlchemy, such as
``pandas.read_sql``, SQLAlchemy ORM models, or `Alembic
<https://alembic.sqlalchemy.org/en/latest/>`_ migrations.  The ``db_schema`` stored in
the SCS is automatically set as the connection's default schema.

.. code-block:: python

    import pandas as pd
    from exasol.nb_connector.connections import open_sqlalchemy_connection

    engine = open_sqlalchemy_connection(my_secrets)
    # db_schema is set as the default schema automatically
    df = pd.read_sql("SELECT * FROM MY_TABLE LIMIT 10", engine)
    print(df)

Ibis
****

``open_ibis_connection`` returns an `ibis
<https://ibis-project.org>`_ connection backed by the Exasol dialect.  Ibis
provides a portable dataframe API that lets you write queries once and run them
on many SQL engines.  Like the SQLAlchemy helper, it applies ``db_schema``
automatically so you can immediately list or query tables without specifying
the schema each time.

.. code-block:: python

    from exasol.nb_connector.connections import open_ibis_connection

    conn = open_ibis_connection(my_secrets)

    # List all tables in the configured schema
    print(conn.list_tables())

    # Build and execute a lazy query — ibis compiles it to SQL internally
    df = conn.table("MY_TABLE").limit(10).execute()
    print(df)
