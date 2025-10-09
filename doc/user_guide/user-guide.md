# User Guide

## Installing the Notebook Connector (NC)

Most of NC's dependencies are declared as "optional" in file `pyproject.toml`.

Here is a comprehensive list of all NC's optional dependency categories (aka. "extras"):

| Package        | Description                                                                                                                                                                                                                                                   |
|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `sqlalchemy`   | [SQLAlchemy dialect](https://pypi.org/project/sqlalchemy_exasol/) for Exasol databases                                                                                                                                                                        |
| `pyexasol`     | Python driver for [connecting to Exasol databases](https://pypi.org/project/pyexasol/)                                                                                                                                                                        |
| `bucketfs`     | [Python API](https://pypi.org/project/exasol-bucketfs/) to interact with Exasol [Bucketfs-Service(s)](https://docs.exasol.com/db/latest/database_concepts/bucketfs/bucketfs.htm)                                                                              |
| `docker-db`    | For starting a [Docker instance of the Exasol database](https://pypi.org/project/exasol-integration-test-docker-environment/)                                                                                                                                 |
| `slc`          | For [building](https://pypi.org/project/exasol-script-languages-container-tool/) custom [Script Language Containers](https://github.com/exasol/script-languages-release) for [Exasol UDFs](https://docs.exasol.com/db/7.1/database_concepts/udf_scripts.htm)  |
| `ibis`         | Portable Python dataframe library [ibis-framework](https://pypi.org/project/ibis-framework/)                                                                                                                                                                  |
| `transformers` | An [Exasol extension](https://pypi.org/project/exasol-transformers-extension/) for using state-of-the-art pretrained machine learning models via the [Hugging Face Transformers API](https://github.com/huggingface/transformers)                                                                            |
| `sagemaker`    | An [Exasol extension](https://pypi.org/project/exasol-sagemaker-extension/) to interact with [AWS SageMaker](https://pypi.org/project/sagemaker/) from inside the database                                                                                                                           |

You can install selected dependencies using the following syntax
```shell
pip install "notebook-connector [slc, docker-db]"
```

You can also retrieve a list of all NC's dependency categories with the following command line, see [stackoverflow/64685527](https://stackoverflow.com/questions/64685527/pip-install-with-all-extras):

```shell
pip install --dry-run --ignore-installed --quiet --report=- \
  exasol-notebook-connector \
  | jq --raw-output '.install[0].metadata.provides_extra|join(",")'
```

## Secure Configuration Storage (SCS)

NC provides a _Secure Configuration Storage_ for configuring a connection to
an Exasol database with support for on-premise, SaaS, and Docker-DB instances.

Besides the connection data such as host, port, user, and password the SCS can
also store arbitrary additional configuration items, such as URL endpoints,
credentials, etc. in particular for interacting with cloud services.

The SCS keeps all these configuration options across multiple sessions
encrypted and secured by a master password. The SCS is based on
[coleifer/sqlcipher3](https://github.com/coleifer/sqlcipher3) which uses an
encrypted version of an SQLite database. The database is stored in an
ordinary, yet encrypted, file and allows storing the configuration items as
string in a simple key-value style.

Other Exasol products e.g. the [MCP
Server](https://github.com/exasol/mcp-server) accept the SCS for connecting to
an Exasol database instance.

For convenient, yet flexible usage, the SCS can be accessed by a Python API
and also offers a command line interface for interactive use by humans.

See [SCS command line interface](scs-cli.rst) for detailed instructions.

## Managing Script Language Containers (SLCs)

NC supports building different flavors of [Exasol Script Language Containers](https://github.com/exasol/script-languages-release) (SLCs) using the [script-languages-container-tool](https://github.com/exasol/script-languages-container-tool).

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

