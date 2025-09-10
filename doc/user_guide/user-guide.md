# Notebook Connector User Guide

## Installing the Notebook Connector (NC)

Most of NC's dependencies are declared as "optional" in file `pyproject.toml`.

Here is a comprehensive list of all NC's optional dependency categories (aka. "extras"):
| Package | pypi | Description |
|---------|------|-------------|
| `sqlalchemy`   | [sqlalchemy_exasol](https://pypi.org/project/sqlalchemy_exasol/) | SQLAlchemy dialect for Exasol databases |
| `pyexasol`     | [pyexasol](https://pypi.org/project/pyexasol/) | Python driver for connecting to Exasol databases |
| `bucketfs`     | [exasol-bucketfs](https://pypi.org/project/exasol-bucketfs/) | Python API to interact with Exasol [Bucketfs-Service(s)](https://docs.exasol.com/db/latest/database_concepts/bucketfs/bucketfs.htm)
| `itde`         | [exasol-integration-test-docker-environment](https://pypi.org/project/exasol-integration-test-docker-environment/) | A docker-based environment for integration tests with EXASOL databases |
| `slc`          | [exasol-script-languages-container-tool](https://pypi.org/project/exasol-script-languages-container-tool/) | Support for building [Script Language Containers](https://github.com/exasol/script-languages-release) for [Exasol UDFs](https://docs.exasol.com/db/7.1/database_concepts/udf_scripts.htm) |
| `ibis`         | [ibis-framework](https://pypi.org/project/ibis-framework/) | Portable Python dataframe library |
| `transformers` | [exasol-transformers-extension](https://pypi.org/project/exasol-transformers-extension/) | An Exasol extension for using state-of-the-art pretrained machine learning models via the Hugging Face Transformers API |
| `sagemaker`| [exasol-sagemaker-extension](https://pypi.org/project/exasol-sagemaker-extension/) | An Exasol extension to interact with AWS SageMaker from inside the database |

You can install selected dependencies using the following syntax
```shell
pip install "notebook-connector [slc, itde]"
```

You can also retrieve a list of all NC's dependency categories with the following command line, see [stackoverflow/64685527](https://stackoverflow.com/questions/64685527/pip-install-with-all-extras):

```shell
pip install --dry-run --ignore-installed --quiet --report=- \
  exasol-notebook-connector \
  | jq --raw-output '.install[0].metadata.provides_extra|join(",")'
```

## Managing Script Language Containers (SLCs)

The Notebook Connector (NC) supports building different flavors of [Exasol Script Language Containers](https://github.com/exasol/script-languages-release) (SLCs) using the [script-languages-container-tool](https://github.com/exasol/script-languages-container-tool).

The specific options for building an SLC are stored in the Secure Configuration Storage (SCS).  Each SLC is identified by an arbitrary unique name used as index into the SCS for finding the related options.

You can set the SLC options using the class method `ScriptLanguageContainer.create()`, with parameters
* `secrets`: The SCS
* `name`: The name of the SLC instance
  * will be converted to upper-case and must be unique
* `flavor`: The name of a template as provided by the [Exasol Script Language Containers](https://github.com/exasol/script-languages-release).

Method `create()` will then
* Select a Language Alias for executing UDF scripts inside the SLC
  * See section _Define your own script aliases_ on [docs.exasol.com](https://docs.exasol.com/db/latest/database_concepts/udf_scripts/adding_new_packages_script_languages.htm).
  * The Language Alias will use prefix `custom_slc_` followed by the specified name
  * Consecutive call to method `deploy()` will overwrite the SLC using the same Language Alias.
* Save the `flavor` to the SCS indexed by the SLC's name.
* Raise an error if the name has already been used.
* Clone the SLC Git repository to the local file system.

The constructor of class `ScriptLanguageContainer` verifies the SCS to contain the flavor and the SLC repository to be cloned to the local file system.

