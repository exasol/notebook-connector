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

Uploading a Hugging Face model to BucketFS
*******************************************

UDFs cannot reach the internet at runtime, so models must be uploaded to
BucketFS before they can be used.  ``upload_model`` downloads the specified
model from the Hugging Face Hub (or reads it from a local ``cache_dir`` if
already downloaded) and pushes all model files to BucketFS under the
sub-directory configured in ``CKey.bfs_model_subdir`` (default: ``models``).

Give each model its own ``cache_dir`` to avoid mixing files from different
models in the same directory.

.. code-block:: python

    from exasol.nb_connector.transformers_extension_wrapper import upload_model

    upload_model(
        my_secrets,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        cache_dir="/tmp/model_cache/all-MiniLM-L6-v2",
    )

.. note::
   The Hugging Face token stored under ``CKey.huggingface_token`` is forwarded
   automatically to the Hub client, so gated models are accessible without
   extra configuration once the token is saved in the SCS.

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