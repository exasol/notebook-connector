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

Full One-Shot Setup
*******************

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

Deploying Only UDF Scripts
**************************

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
be present there before the UDFs can use them.

For a working end-to-end model-loading workflow, use the bundled
Transformers notebooks as the source of truth for the supported steps.

Running a UDF From SQL
**********************

The deployed Transformers Extension is consumed from SQL.  Before running any
TE UDF, activate the language container in the current session.  The Python
helper ``get_activation_sql`` returns the required ``ALTER SESSION`` statement.

.. code-block:: python

    from exasol.nb_connector.language_container_activation import get_activation_sql

    print(get_activation_sql(my_secrets))

Then run the SQL UDFs directly.  The examples below assume that the model is
already available in BucketFS and that ``initialize_te_extension`` has already
created the BucketFS ``CONNECTION`` object stored in
``CKey.bfs_connection_name``.

Text Generation
===============

.. code-block:: sql

    SELECT MY_SCHEMA.TE_TEXT_GENERATION_UDF(
        NULL,
        'TE_BFS_SYS',
        'models',
        'gpt2',
        'Exasol can',
        32,
        TRUE
    );

Fill-Mask Prediction
====================

.. code-block:: sql

    WITH MODEL_OUTPUT AS (
        SELECT MY_SCHEMA.TE_FILLING_MASK_UDF(
            NULL,
            'TE_BFS_SYS',
            'models',
            'bert-base-uncased',
            'Exasol is a [MASK] database.',
            5
        )
    )
    SELECT filled_text, score, rank, error_message
    FROM MODEL_OUTPUT
    ORDER BY score DESC;

Sequence Classification
=======================

Use ``TE_SEQUENCE_CLASSIFICATION_SINGLE_TEXT_UDF`` for one input text and
``TE_SEQUENCE_CLASSIFICATION_TEXT_PAIR_UDF`` when the model compares two texts.

.. code-block:: sql

    WITH MODEL_OUTPUT AS (
        SELECT MY_SCHEMA.TE_SEQUENCE_CLASSIFICATION_SINGLE_TEXT_UDF(
            NULL,
            'TE_BFS_SYS',
            'models',
            'arpanghoshal/EkmanClassifier',
            'Oh my God!',
            'HIGHEST'
        )
    )
    SELECT label, score, rank, error_message
    FROM MODEL_OUTPUT;

.. code-block:: sql

    WITH MODEL_OUTPUT AS (
        SELECT MY_SCHEMA.TE_SEQUENCE_CLASSIFICATION_TEXT_PAIR_UDF(
            NULL,
            'TE_BFS_SYS',
            'models',
            'arpanghoshal/EkmanClassifier',
            'Oh my God!',
            'I lost my purse.',
            'ALL'
        )
    )
    SELECT label, score, rank, error_message
    FROM MODEL_OUTPUT
    ORDER BY score DESC;

Zero-Shot Text Classification
=============================

.. code-block:: sql

    WITH MODEL_OUTPUT AS (
        SELECT MY_SCHEMA.TE_ZERO_SHOT_TEXT_CLASSIFICATION_UDF(
            NULL,
            'TE_BFS_SYS',
            'models',
            'facebook/bart-large-mnli',
            'Notebook Connector simplifies Exasol AI workflows.',
            'documentation,databases,networking',
            'ALL'
        )
    )
    SELECT label, score, error_message
    FROM MODEL_OUTPUT
    ORDER BY score DESC;

Question Answering
==================

.. code-block:: sql

    WITH MODEL_OUTPUT AS (
        SELECT MY_SCHEMA.TE_QUESTION_ANSWERING_UDF(
            NULL,
            'TE_BFS_SYS',
            'models',
            'distilbert-base-cased-distilled-squad',
            'What does Notebook Connector simplify?',
            'Notebook Connector simplifies Exasol AI workflows.',
            5
        )
    )
    SELECT answer, score, error_message
    FROM MODEL_OUTPUT
    ORDER BY score DESC;

Token Classification
====================

.. code-block:: sql

    WITH MODEL_OUTPUT AS (
        SELECT MY_SCHEMA.TE_TOKEN_CLASSIFICATION_UDF(
            NULL,
            'TE_BFS_SYS',
            'models',
            'dslim/bert-base-NER',
            'Exasol is headquartered in Nuremberg.',
            NULL
        )
    )
    SELECT start_pos, end_pos, word, entity, error_message
    FROM MODEL_OUTPUT
    ORDER BY start_pos, end_pos;

Translation
===========

.. code-block:: sql

    WITH MODEL_OUTPUT AS (
        SELECT MY_SCHEMA.TE_TRANSLATION_UDF(
            NULL,
            'TE_BFS_SYS',
            'models',
            't5-small',
            'Hello world',
            'en',
            'de',
            32
        )
    )
    SELECT translation_text, error_message
    FROM MODEL_OUTPUT;

Model Management
================

Use ``TE_LIST_MODELS_UDF`` to inspect installed models and
``TE_DELETE_MODEL_UDF`` to remove a model from BucketFS.

.. code-block:: sql

    SELECT MY_SCHEMA.TE_LIST_MODELS_UDF(
        'TE_BFS_SYS',
        'models'
    );

.. code-block:: sql

    SELECT MY_SCHEMA.TE_DELETE_MODEL_UDF(
        'TE_BFS_SYS',
        'models',
        'arpanghoshal/EkmanClassifier',
        'text-classification'
    );

Using Text Columns From a Table
===============================

When the input texts already live in a database table, pass the text column
instead of a string literal.  This is the normal batch-processing mode for TE
UDFs.

.. code-block:: sql

    WITH MODEL_OUTPUT AS (
        SELECT MY_SCHEMA.TE_ZERO_SHOT_TEXT_CLASSIFICATION_UDF(
            NULL,
            'TE_BFS_SYS',
            'models',
            'facebook/bart-large-mnli',
            MY_TEXT_COLUMN,
            'positive,negative,neutral',
            'HIGHEST'
        )
        FROM MY_TEXT_TABLE
    )
    SELECT label, score, error_message
    FROM MODEL_OUTPUT
    ORDER BY score DESC;
