# Unreleased

## Summary

This release of the Notebook Connector comes with breaking changes in the `SlctManager`:
* The class has been renamed to `ScriptLanguageContainer`.
* Some public methods have been renamed.
  * `upload()` to `deploy()`
  * `slc_docker_images()` to `docker_images()`
  * `clean_all_images()` to `clean_docker_images()`
  * `check_slc_repo_complete()` to `slc_repo_available()`

* The handling of Secure Configuration Storage and the SlcSession have been changed.

See the NC User Guide for details.

## Features

* #213: Added Support to specify the SLC flavor via a session parameter
* #205: Added GPU support to ITDE manager
* #220: Refactored class `SlctManager`

## Documentation

* #217: Used defined term "Secure Configuration Storage" throughout all documents

## Refactorings

* #211: Modularized execution of integration tests in CI
* #208: Widened version constraints for:
   * exasol-saas-api from ">=0.9.0,<1.0.0" to ">=0.9.0,<3"
   * exasol-bucketfs from "^1.0.0" to ">=1,<3"

