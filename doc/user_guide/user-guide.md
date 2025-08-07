# Notebook Connector User Guide

## Managing Script Language Containers (SLCs)

The Notebook Connector (NC) supports building different flavors of [Exasol Script Language Containers](https://github.com/exasol/script-languages-release) (SLCs) using the [script-languages-container-tool](https://github.com/exasol/script-languages-container-tool).

NC supports using multiple SLCs, each with its specific options, clustered in so-called _SLC Sessions_ and stored in the Secure Configuration Storage (SCS).  Each SCL session is identified by an arbitrary unique name used as index into the SCS for finding the SLC options related to the session.

You can set the SLC options using the class method `ScriptLanguageContainer.create()`, which expects the following parameters
* `secrets`: The SCS
* `name`: The name of the SLC session.
* `flavor`: The name of a template as provided by the [Exasol Script Language Containers](https://github.com/exasol/script-languages-release).
* `language_alias`: Used for executing UDF scripts inside the SLC, see section _Define your own script aliases_ on [docs.exasol.com](https://docs.exasol.com/db/latest/database_concepts/udf_scripts/adding_new_packages_script_languages.htm).

Method `create()` additionally will select `checkout_dir`&mdash;a unique path in the local file system for cloning the SLC Git repository.

Before returning an instance of class `ScriptLanguageContainer` method `create()` will
* Save the SLC options `flavor`, `language_alias`, and `checkout_dir` in the SCS&mdash;all indexed by the session name.
* Checkout (i.e. `git clone`) the SLC Git repository to the `checkout_dir` in the local file system.

Method `create()` raises an error if the SCS already contains one of the SLC options as this indicates the session name to be non-unique.

The constructor of class `ScriptLanguageContainer` verifies the SCS to contain the SLC options for the current session and the SLC repository to be checked out (cloned) in the local file system.
