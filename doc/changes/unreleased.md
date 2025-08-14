# Unreleased

## Summary

This release of the Notebook Connector evolves the prior `SlctManager` interface to
* Support building SLCs with GPU support, requiring a special flavor, e.g. [template-Exasol-8-python-3.10-cuda-conda](https://github.com/exasol/script-languages/tree/master/flavors/template-Exasol-8-python-3.10-cuda-conda)
* Incl. isolating various SLC sessions regarding flavors, Git clones and working directories.

The release comes with breaking changes:
* Class `SlctManager` has been renamed to `ScriptLanguagesContainer`.
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

* #236: Improved flavor check and renamed class ScriptLanguageContainer 
