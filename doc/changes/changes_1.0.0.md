# 1.0.0 - 2025-08-18
## Summary

This release of the Notebook Connector evolves the prior `SlctManager` interface to
* Support building SLCs with GPU support, requiring a special flavor, e.g. [template-Exasol-8-python-3.10-cuda-conda](https://github.com/exasol/script-languages/tree/master/flavors/template-Exasol-8-python-3.10-cuda-conda)
* Incl. isolating various SLC sessions regarding flavors, Git clones and working directories.

The release comes with breaking changes:
* Class `SlctManager` has been renamed to `ScriptLanguageContainer`.
* Some public methods or and attributes have been
  * renamed
    * `flavor_name` to `flavor`
    * `flavor_dir` to `flavor_path`
    * `upload()` to `deploy()`
    * `slc_docker_images()` to `docker_image_tags()`
    * `clean_all_images()` to `clean_docker_images()`
  * removed
    * `check_slc_repo_complete()`
    * `clone_slc_repo()`
* The handling of Secure Configuration Storage has been changed to support using multiple SLC flavors.

Additionally, the new `ScriptLanguageContainer` class supports adding conda packages to conda based flavors.

Also, the release contains several internal improvements.

See the NC [User Guide](../user_guide/user-guide.md) for details.

## Features

* #213: Added Support to specify the SLC flavor via a session parameter
* #205: Added GPU support to ITDE manager
* #220: Replaced implementation on using SLCs by Gen.2

## Documentation

* #217: Used defined term "Secure Configuration Storage" throughout all documents
* Updated figure on SLC flavor

## Refactorings

* #211: Modularized execution of integration tests in CI
* #208: Widened version constraints for:
   * exasol-saas-api from ">=0.9.0,<1.0.0" to ">=0.9.0,<3"
   * exasol-bucketfs from "^1.0.0" to ">=1,<3"
* #226: Used `LanguageDefinitionsBuilder` to create the SLC activation statement
* #38: Renamed `connections.open_bucketfs_connection` to `connections.open_bucketfs_bucket`
* #231: Implemented clean up all Script-Languages-Container related docker images 
* #236: Added check to validate if flavor exists in cloned slc-rel repository
* #238: Changed path of SLC workspace directory
* #234: Reduced ITDE log level in NC
* #235: Cleaned up ai lab config

## Dependency Updates

### `main`
* Updated dependency `exasol-bucketfs:1.0.1` to `2.0.0`
* Updated dependency `exasol-integration-test-docker-environment:3.4.0` to `4.2.0`
* Updated dependency `exasol-saas-api:0.10.0` to `2.2.0`
* Updated dependency `exasol-script-languages-container-tool:1.1.0` to `3.4.1`
* Updated dependency `gitpython:3.1.44` to `3.1.45`
* Updated dependency `requests:2.32.3` to `2.32.4`
* Updated dependency `types-requests:2.32.0.20250602` to `2.32.4.20250611`

### `dev`
* Updated dependency `exasol-toolbox:1.4.0` to `1.7.4`
* Updated dependency `pytest-exasol-backend:0.3.3` to `1.1.0`
