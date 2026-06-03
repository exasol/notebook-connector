Transformers Extension Examples
################################

The Transformers Extension runs `Hugging Face <https://huggingface.co>`_
transformer models as Exasol UDFs, letting you apply NLP models directly
inside SQL queries at database scale.

**Required extra:** ``pip install "notebook-connector[transformers]"``

**Prerequisites in the SCS** before calling any function in this module:

* Full DB connection parameters (``db_host_name``, ``db_port``, ``db_user``,
  ``db_password``, ``db_schema``).
* Full BucketFS parameters (``bfs_host_name``, ``bfs_port``, ``bfs_service``,
  ``bfs_bucket``, ``bfs_user``, ``bfs_password``).
* Optional: ``huggingface_token`` for gated / private models.

Full one-shot setup
********************

``initialize_te_extension`` is the main entry point.  In a single call it:

1. Downloads the pre-built Script Language Container (SLC) for the Transformers
   Extension from GitHub and uploads it to BucketFS.
2. Creates an Exasol ``CONNECTION`` object that encapsulates the BucketFS
   credentials so UDFs can read from BucketFS without hard-coded passwords.
3. Creates a second ``CONNECTION`` object for the Hugging Face token (when
   ``huggingface_token`` is set in the SCS).
4. Deploys all UDF scripts (``TE_METADATA_READER``, ``TE_MODEL_DOWNLOADER``,
   ``TE_TRANSFORMER``, etc.) into the configured schema.

Each step can be skipped individually by passing the corresponding flag as
``False``, which is useful when re-running setup after a partial failure.

.. code-block:: python

    from exasol.nb_connector.transformers_extension_wrapper import initialize_te_extension

    initialize_te_extension(my_secrets)
    # Optional flags (all default to True):
    # run_deploy_container=True            – upload the language container to BucketFS
    # run_deploy_scripts=True              – create UDF scripts in the schema
    # run_encapsulate_bfs_credentials=True – create the BucketFS CONNECTION object
    # run_encapsulate_hf_token=True        – create the Hugging Face CONNECTION object
    # allow_override=True                  – overwrite existing language alias if present

Deploying only UDF scripts
***************************

If the SLC is already in BucketFS (e.g. you are updating the scripts after a
code change) you can redeploy only the UDF scripts without re-uploading the
container.  ``LANGUAGE_ALIAS`` is the pre-defined alias used by the Transformers
Extension SLC; pass it as ``language_alias`` so the scripts reference the
correct container.

.. code-block:: python

    from exasol.nb_connector.transformers_extension_wrapper import (
        LANGUAGE_ALIAS,
        deploy_scripts,
    )

    deploy_scripts(my_secrets, language_alias=LANGUAGE_ALIAS)

Uploading a Hugging Face Model to BucketFS
******************************************

Transformer UDFs read model files from BucketFS, so the model artifacts must
be present there before the UDFs can use them.  The helper functions
``upload_model`` and ``upload_model_from_cache`` in
``exasol.nb_connector.transformers_extension_wrapper`` are intended to cover
that step.

``upload_model`` downloads a model into a local ``cache_dir`` by calling the
Hugging Face client libraries and then forwards to
``upload_model_from_cache``.

At the moment, ``upload_model_from_cache`` is not implemented in this code
base and raises ``NotImplementedError``.  So this section documents the role
of these helpers, but not a complete working workflow in Notebook Connector
itself.

If you need a working end-to-end model-loading example today, use the bundled
Transformers notebooks as the source of truth for the supported workflow.

Running a UDF from SQL
**********************

The deployed Transformers Extension is consumed from SQL.  One example is the
``TE_TEXT_GENERATION_UDF`` shown in the bundled notebook examples.  The query
below assumes that the required model is already present in BucketFS and that
``initialize_te_extension`` has already created the BucketFS ``CONNECTION``
object stored in ``CKey.bfs_connection_name``.

.. code-block:: python

    from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
    from exasol.nb_connector.connections import open_pyexasol_connection
    from exasol.nb_connector.language_container_activation import get_activation_sql

    sql = f"""
    SELECT {my_secrets.db_schema}.TE_TEXT_GENERATION_UDF(
        NULL,
        '{my_secrets.get(CKey.bfs_connection_name)}',
        '{my_secrets.get(CKey.bfs_model_subdir)}',
        'gpt2',
        'Exasol can',
        32,
        True
    )
    """

    with open_pyexasol_connection(my_secrets, compression=True) as conn:
        conn.execute(get_activation_sql(my_secrets))
        result = conn.execute(sql).fetchone()
        print(result)
