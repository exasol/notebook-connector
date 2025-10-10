:octicon:`person` User Guide
############################

Installing the Notebook Connector (NC)
**************************************

Most of NC's dependencies are declared as "optional" in file
``pyproject.toml``.

Here is a comprehensive list of all NC's optional dependency categories
(aka. "extras"):

+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| Package          | Description                                                                                                                                          |
+==================+======================================================================================================================================================+
| ``sqlalchemy``   | `SQLAlchemy dialect <sql_alchemy_>`_ for Exasol databases                                                                                            |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``pyexasol``     | Python driver for `connecting to Exasol databases <pyexasol_>`_                                                                                      |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``bucketfs``     | `Python API <bfs_python_>`_ to interact with Exasol `Bucketfs-Service(s) <bucketfs_>`_                                                               |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``docker-db``    | For starting a `Docker instance of the Exasol database <itde_>`_                                                                                     |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``slc``          | For `building <slct_>`_ custom `Script Language Containers <slcr_>`_ for `Exasol UDFs <udfs_>`_                                                      |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``ibis``         | Portable Python dataframe library `ibis-framework <ibis_>`_                                                                                          |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``transformers`` | An `Exasol extension <te_ext_>`_ for using state-of-the-art pretrained machine learning models via the `Hugging Face Transformers API <hface_>`_     |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``sagemaker``    | An `Exasol extension <sm_ext_>`_ to interact with `AWS SageMaker <sagemaker_>`_ from inside the database                                             |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+

.. _sql_alchemy: https://pypi.org/project/sqlalchemy_exasol
.. _pyexasol: https://pypi.org/project/pyexasol
.. _bfs_python: https://pypi.org/project/exasol-bucketfs
.. _bucketfs: https://docs.exasol.com/db/latest/database_concepts/bucketfs/bucketfs.htm
.. _itde: https://pypi.org/project/exasol-integration-test-docker-environment
.. _slct: https://pypi.org/project/exasol-script-languages-container-tool
.. _slcr: https://github.com/exasol/script-languages-release
.. _udfs: https://docs.exasol.com/db/7.1/database_concepts/udf_scripts.htm
.. _ibis: https://pypi.org/project/ibis-framework
.. _te_ext: https://pypi.org/project/exasol-transformers-extension
.. _hface: https://github.com/huggingface/transformers
.. _sm_ext: https://pypi.org/project/exasol-sagemaker-extension
.. _sagemaker: https://pypi.org/project/sagemaker


You can install selected dependencies using the following syntax

.. code-block:: shell

    pip install "notebook-connector [slc, docker-db]"

You can also retrieve a list of all NC's dependency categories with the
following command line, see `stackoverflow/64685527
<https://stackoverflow.com/questions/64685527/pip-install-with-all-extras>`_:

.. code-block:: shell

    pip install --dry-run --ignore-installed --quiet --report=- \
      exasol-notebook-connector \
      | jq --raw-output '.install[0].metadata.provides_extra|join(",")'

Managing Script Language Containers (SLCs)
******************************************

The Notebook Connector (NC) supports building different flavors of `Exasol
Script Languages Containers
<https://github.com/exasol/script-languages-release>`_ using the
`script-languages-container-tool
<https://github.com/exasol/script-languages-container-tool>`_.

The specific options for building an SLC are stored in the Secure
Configuration Storage (SCS).  Each SLC is identified by an arbitrary unique
name used as index into the SCS for finding the related options.

You can set the SLC options using the class method
``ScriptLanguageContainer.create()``, with parameters

* ``secrets``: The SCS

* ``name``: The name of the SLC instance (will be converted to upper-case and must be unique)

* ``flavor``: The name of a template as provided by the `Exasol Script
  Language Containers <https://github.com/exasol/script-languages-release>`_.

Method ``create()`` will then

* Select a Language Alias for executing UDF scripts inside the SLC

  * See section *Define your own script aliases* on `docs.exasol.com
    <https://docs.exasol.com/db/latest/database_concepts/udf_scripts/adding_new_packages_script_languages.htm>`_.

  * The Language Alias will use prefix ``custom_slc_`` followed by the
    specified name

  * Consecutive call to method ``deploy()`` will overwrite the SLC using the
    same Language Alias.

* Save the ``flavor`` to the SCS indexed by the SLC's name.

* Raise an error if the name has already been used.

* Clone the SLC Git repository to the local file system.

The constructor of class ``ScriptLanguageContainer`` verifies the SCS to
contain the flavor and the SLC repository to be cloned to the local file
system.
