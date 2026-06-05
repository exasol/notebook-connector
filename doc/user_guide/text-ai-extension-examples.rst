Text AI Extension Examples
###########################

The Text AI Extension provides ready-to-use UDFs for named-entity recognition,
zero-shot classification, and semantic feature extraction, powered by
large language models running inside the Exasol database.

**Prerequisites in the SCS** – same as for the Transformers Extension: full
DB connection parameters and full BucketFS parameters (see
:doc:`secret-store-examples`).

Step 1 – Deploy a License
*************************

``deploy_license`` uploads a Text AI license and registers it with the
extension.  The Notebook Connector bundles a community license that covers
non-commercial and evaluation use, so you can call the function with no extra
arguments to use it.  For other deployments, supply either the path to a
Text AI license file (``license_file``) or the license content as a string
(``license_content``).

.. code-block:: python

    from exasol.nb_connector.text_ai_extension_wrapper import deploy_license

    # Use the built-in community license (no arguments required)
    deploy_license(my_secrets)

    # Supply your own license file from disk
    from pathlib import Path
    deploy_license(my_secrets, license_file=Path("text-ai-license.yaml"))

    # Supply the license content directly as a string
    deploy_license(my_secrets, license_content="signature: ...")

Step 2 – Initialize the Extension
*********************************

``initialize_text_ai_extension`` performs the full installation in one call:

1. Downloads the extension's Script Language Container (SLC) and uploads it
   to BucketFS (``install_slc=True``).
2. Downloads the three default Hugging Face models and uploads them to BucketFS
   so that UDFs can use them offline (``install_models=True``).
3. Creates the UDF scripts in the configured schema (``install_scripts=True``).

Any of the three steps can be skipped by passing its flag as ``False``.  This
is useful for incremental updates — e.g., pass ``install_slc=False`` to only
refresh the UDF scripts without re-uploading the container.

You can also pin a specific extension version with ``version=`` or supply a
locally downloaded or otherwise available container archive with
``container_file=``.

.. code-block:: python

    from exasol.nb_connector.text_ai_extension_wrapper import initialize_text_ai_extension

    # Full installation with latest version
    initialize_text_ai_extension(my_secrets)

    # Pin a specific version
    initialize_text_ai_extension(my_secrets, version="1.2.3")

    # Install from a local container file and skip model download
    from pathlib import Path
    initialize_text_ai_extension(
        my_secrets,
        container_file=Path("/tmp/txaie.tar.gz"),
        install_models=False,
    )

Step 3 – Run an Extraction
**************************

The ``Extraction`` class wraps one or more UDF calls.  Provide an
*extractor* that defines which UDFs to invoke, for example
``NamedEntityExtractor`` for NER or one of the default extractors from the
Text AI package.  More advanced workflows can compose multiple extractors into
pipelines, for example by feeding a ``SourceTableExtractor`` into a
``StandardExtractor`` via ``PipelineExtractor``.  If the workflow should fan
out into parallel branches after the source step, use ``BranchExtractor``.

Text AI extraction is incremental: it processes only source rows for which no
results have been written yet.  The output tables therefore act as persistent
storage for prior extraction results and are re-used across runs.

Depending on the extractor, TXAIE can create more than one table.  Besides a
main output table, some workflows also create support and lookup tables that
store normalized intermediate results.  This is the same table layout used in
the bundled preprocessing notebooks.

Calling ``extraction.run(my_secrets)`` opens a database connection, activates
the Text AI language container for the session, and executes the extraction
SQL against the configured source and output tables.

.. code-block:: python

    from exasol.nb_connector.text_ai_extension_wrapper import Extraction
    from exasol.ai.text.extractors.named_entity_extractor import NamedEntityExtractor

    # Configure the extractor and the output table
    extraction = Extraction(
        extractor=NamedEntityExtractor(),
        output="MY_SCHEMA.EXTRACTION_RESULTS",
    )

    # Execute the extraction — results are written to the output table
    extraction.run(my_secrets)

Pipeline extraction example
***************************

If you want a reusable preprocessing workflow rather than a single UDF call,
compose multiple extractors into a ``PipelineExtractor`` and then wrap the
pipeline in ``Extraction``.

.. code-block:: python

    from exasol.nb_connector.text_ai_extension_wrapper import Extraction
    from exasol.ai.text.extraction.abstract_extraction import Defaults, Output
    from exasol.ai.text.extractors.extractor import PipelineExtractor
    from exasol.ai.text.extractors.source_table_extractor import (
        NameSelector,
        SchemaSource,
        SourceTableExtractor,
        TableSource,
    )
    from exasol.ai.text.extractors.standard_extractor import StandardExtractor

    src_extractor = SourceTableExtractor(
        source=TableSource(
            source=SchemaSource("MY_SCHEMA"),
            table_names=NameSelector(["CUSTOMER_SUPPORT_TICKETS"]),
        )
    )
    std_extractor = StandardExtractor()

    extraction = Extraction(
        extractor=PipelineExtractor(steps=[src_extractor, std_extractor]),
        output=Output(db_schema="MY_SCHEMA"),
        defaults=Defaults(),
    )

    extraction.run(my_secrets)

In this pattern, each pipeline step can create its own output and support
tables.  Re-running the pipeline is incremental as long as the previous output
tables are still present.

Branch extraction example
*************************

If you want to run multiple extractor branches from the same source data,
wrap them in a ``BranchExtractor`` and then use that as one of the steps in a
pipeline.

.. code-block:: python

    from exasol.nb_connector.text_ai_extension_wrapper import Extraction
    from exasol.ai.text.extraction.abstract_extraction import Defaults, Output
    from exasol.ai.text.extractors.extractor import BranchExtractor, PipelineExtractor
    from exasol.ai.text.extractors.named_entity_extractor import NamedEntityExtractor
    from exasol.ai.text.extractors.source_table_extractor import (
        NameSelector,
        SchemaSource,
        SourceTableExtractor,
        TableSource,
    )
    from exasol.ai.text.extractors.topic_classifier_extractor import TopicClassifierExtractor

    src_extractor = SourceTableExtractor(
        source=TableSource(
            source=SchemaSource("MY_SCHEMA"),
            table_names=NameSelector(["CUSTOMER_SUPPORT_TICKETS"]),
        )
    )
    branched_extractors = BranchExtractor(
        steps=[
            NamedEntityExtractor(),
            TopicClassifierExtractor(),
        ]
    )

    extraction = Extraction(
        extractor=PipelineExtractor(steps=[src_extractor, branched_extractors]),
        output=Output(db_schema="MY_SCHEMA"),
        defaults=Defaults(),
    )

    extraction.run(my_secrets)

Each branch writes its own derived results, while the shared source and audit
tables still support incremental re-runs across the whole workflow.
