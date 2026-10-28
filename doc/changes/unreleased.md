# Unreleased

## Summary

This release
* Drops the support for Python 3.10.
* Uses Python 3.12 flavors instead of 3.10:
  * `template-Exasol-all-python-3.12` in the Script Language Container notebook [configure_slc_repository.ipynb](https://github.com/exasol/notebook-connector/blob/main/exasol/nb_connector/resources/notebooks/script_languages_container/configure_slc_repository.ipynb)
  * `template-Exasol-8-python-3.12-cuda-conda` in the GPU notebook [gpu_in_udf/setup.ipynb](https://github.com/exasol/notebook-connector/blob/main/exasol/nb_connector/resources/notebooks/gpu_in_udf/setup.ipynb)
* Unpins the dependencies to ITDE and SLCT that were pinned in the context of ticket #424.

The release also improves the error messages when locating Jar files in GitHub releases, which is used for the Cloud Storage notebook.

## Refactorings

* #425: Unpinned the dependencies to ITDE and SLCT
* #387: Removed upper bound for dev dependency to starlette
* #485: Improved error messages when locating Jar files in GitHub releases.
* #488: Updated SLC dependencies
* #489: Updated Python toolbox and GitHub runners
