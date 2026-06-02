Text AI Extension Examples
###########################

The Text AI Extension provides ready-to-use UDFs for named-entity recognition,
zero-shot classification, and semantic feature extraction, powered by
large language models running inside the Exasol database.

**Prerequisites in the SCS** – same as for the Transformers Extension: full
DB connection parameters and full BucketFS parameters (see
:doc:`secret-store-examples`).

Step 1 – Deploy a license
**************************

``deploy_license`` uploads a license file to BucketFS and registers it with
the extension.  The Notebook Connector bundles a community license that covers
non-commercial and evaluation use — call the function with no extra arguments
to use it.  For commercial deployments, supply either the path to a license
file (``license_file``) or the license XML content as a string
(``license_content``).

.. code-block:: python

    from exasol.nb_connector.text_ai_extension_wrapper import deploy_license

    # Use the built-in community license (no arguments required)
    deploy_license(my_secrets)

    # Supply your own license file from disk
    from pathlib import Path
    deploy_license(my_secrets, license_file=Path("license.xml"))

    # Supply the license content directly as a string
    deploy_license(my_secrets, license_content="<license>...</license>")

Step 2 – Initialize the extension
***********************************

``initialize_text_ai_extension`` performs the full installation in one call:

1. Downloads the extension's Script Language Container (SLC) from GitHub and
   uploads it to BucketFS (``install_slc=True``).
2. Downloads the three default Hugging Face models and uploads them to BucketFS
   so that UDFs can use them offline (``install_models=True``).
3. Creates the UDF scripts in the configured schema (``install_scripts=True``).

Any of the three steps can be skipped by passing its flag as ``False``.  This
is useful for incremental updates — e.g., pass ``install_slc=False`` to only
refresh the UDF scripts without re-uploading the container.

You can also pin a specific extension version with ``version=`` or supply a
locally built container archive with ``container_file=``.

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

Step 3 – Run an extraction
***************************

The ``Extraction`` class wraps a UDF call.  Provide an *extractor* that
defines which UDF to invoke (e.g. ``NamedEntityExtractor`` for NER) and an
``output`` table name where results will be written.  Calling
``extraction.run(my_secrets)`` opens a database connection and executes the
extraction SQL, reading from any source table you configure on the extractor.

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
