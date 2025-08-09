# Unreleased

## Summary

This release of the Notebook Connector comes with breaking changes in the `SlctManager`:
* The class has been renamed to `ScriptLanguageContainer`.
* Some public methods or and attributes have been
  * renamed
    * `flavor_name` to `flavor`
    * `flavor_dir` to `flavor_path`
    * `upload()` to `deploy()`
    * `slc_docker_images()` to `docker_images()`
    * `clean_all_images()` to `clean_docker_images()`
  * removed
    * `check_slc_repo_complete()`
    * `clone_slc_repo()`
* The handling of Secure Configuration Storage and the SlcSession have been changed.

See the NC User Guide for details.

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
