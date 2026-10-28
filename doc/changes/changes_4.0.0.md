# 4.0.0 - 2026-10-28

## Summary

This release

* Drops the support for Python 3.10.
* Uses Python 3.12 flavors instead of 3.10:
  * `template-Exasol-all-python-3.12` in the Script Language Container notebook [configure_slc_repository.ipynb](https://github.com/exasol/notebook-connector/blob/main/exasol/nb_connector/resources/notebooks/script_languages_container/configure_slc_repository.ipynb)
  * `template-Exasol-8-python-3.12-cuda-conda` in the GPU notebook [gpu_in_udf/setup.ipynb](https://github.com/exasol/notebook-connector/blob/main/exasol/nb_connector/resources/notebooks/gpu_in_udf/setup.ipynb)
* Unpins the dependencies to ITDE and SLCT that were pinned in the context of ticket #424.

The release also improves the error messages when locating Jar files in GitHub releases, which is used for the Cloud Storage notebook.

## Security Issues

This release fixes vulnerabilities by updating dependencies:

| Dependency | Vulnerability | Affected | Fixed in |
|------------|---------------|----------|----------|
| aiohttp | CVE-2026-111063 | 3.14.3 | 3.14.4 |
| aiohttp | CVE-2026-111064 | 3.14.3 | 3.14.4 |
| aiohttp | CVE-2026-111065 | 3.14.3 | 3.14.4 |
| aiohttp | CVE-2026-111066 | 3.14.3 | 3.14.4 |
| aiohttp | CVE-2026-111748 | 3.14.3 | 3.14.4 |
| aiohttp | CVE-2026-111749 | 3.14.3 | 3.14.4 |
| aiohttp | CVE-2026-111750 | 3.14.3 | 3.14.4 |
| aiohttp | GHSA-2g87-pp6c-29x5 | 3.14.3 | 3.14.4 |
| black | CVE-2026-114134 | 26.5.1 | 26.10.1 |
| certifi | PYSEC-2026-4320 | 2026.7.22 | 2026.10.18 |
| certifi | PYSEC-2026-4320 | 2026.7.22 | 2026.10.19 |
| filelock | CVE-2026-112907 | 3.32.7 | 4.2.1 |
| filelock | CVE-2026-112913 | 3.32.7 | 4.2.1 |
| filelock | CVE-2026-112940 | 3.32.7 | 4.2.1 |
| gitpython | CVE-2026-110855 | 3.1.62 | 3.2.0 |
| gitpython | CVE-2026-110856 | 3.1.62 | 3.2.0 |
| gitpython | CVE-2026-110857 | 3.1.62 | 3.2.0 |
| gitpython | CVE-2026-110858 | 3.1.62 | 3.2.0 |
| gitpython | CVE-2026-110859 | 3.1.62 | 3.2.0 |
| gitpython | CVE-2026-114145 | 3.1.62 | 3.2.1 |
| jupyterlab | CVE-2026-102832 | 4.6.3 | 4.5.11 |
| jupyterlab | PYSEC-2026-4055 | 4.6.3 | 4.5.11 |
| jupyterlab | PYSEC-2026-4056 | 4.6.3 | 4.5.11 |
| jupyterlab | PYSEC-2026-4057 | 4.6.3 | 4.5.11 |
| msgpack | CVE-2026-114613 | 1.2.2 | 1.2.3 |
| multidict | PYSEC-2026-4244 | 6.9.0 | 6.9.1 |
| notebook | PYSEC-2026-4112 | 7.6.2 | 7.6.3 |
| pillow | CVE-2026-112390 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112391 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112393 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112395 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112399 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112400 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112401 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112404 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112406 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112891 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112892 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112893 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112894 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112895 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112897 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112899 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-112900 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-96638 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-96640 | 12.3.0 | 13.0.0 |
| pillow | CVE-2026-96778 | 12.3.0 | 13.0.0 |
| pillow | GHSA-78g4-xqwv-q3g8 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4326 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4327 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4328 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4329 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4330 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4331 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4332 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4333 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4334 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4335 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4336 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4337 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4338 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4339 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4340 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4341 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4342 | 12.3.0 | 13.0.0 |
| pillow | PYSEC-2026-4343 | 12.3.0 | 13.0.0 |
| pylint | CVE-2026-114608 | 4.0.8 | 4.0.9 |
| setuptools | GHSA-xmj3-9gf7-h52w | 84.0.0 | 84.1.0 |
| starlette | PYSEC-2026-161 | 0.52.1 | 1.0.1 |
| starlette | PYSEC-2026-2280 | 0.52.1 | 1.1.0 |
| starlette | PYSEC-2026-2281 | 0.52.1 | 1.1.0 |
| starlette | PYSEC-2026-248 | 0.52.1 | 1.3.0 |
| starlette | PYSEC-2026-249 | 0.52.1 | 1.3.1 |
| virtualenv | CVE-2026-113714 | 21.9.0 | 21.14.9 |
| virtualenv | CVE-2026-113715 | 21.9.0 | 21.14.9 |
| virtualenv | CVE-2026-113717 | 21.9.0 | 21.14.9 |
| virtualenv | CVE-2026-113718 | 21.9.0 | 21.14.9 |
| virtualenv | CVE-2026-113720 | 21.9.0 | 21.14.9 |
| virtualenv | CVE-2026-113722 | 21.9.0 | 21.14.9 |
| virtualenv | CVE-2026-113723 | 21.9.0 | 21.14.9 |
| virtualenv | CVE-2026-113725 | 21.9.0 | 21.14.7 |
| virtualenv | CVE-2026-113726 | 21.9.0 | 21.14.4 |
| virtualenv | CVE-2026-113732 | 21.9.0 | 21.14.2 |
| virtualenv | CVE-2026-113776 | 21.9.0 | 21.14.2 |

## Refactorings

* #425: Unpinned the dependencies to ITDE and SLCT
* #387: Removed upper bound for dev dependency to starlette
* #485: Improved error messages when locating Jar files in GitHub releases.
* #488: Updated SLC dependencies
* #489: Updated Python toolbox and GitHub runners

## Dependency Updates

### `main`

* Updated dependency `exasol-bucketfs:2.3.0` to `2.3.1`
* Updated dependency `exasol-integration-test-docker-environment:6.1.0` to `6.5.1`
* Updated dependency `exasol-script-languages-container-tool:4.0.3` to `4.4.0`
* Updated dependency `exasol-text-ai-extension:0.4.1` to `0.4.2`
* Updated dependency `gitpython:3.1.62` to `3.2.1`
* Updated dependency `jupyterlab:4.6.3` to `4.6.4`
* Updated dependency `sqlalchemy-exasol:7.1.4` to `7.2.0`

### `dev`

* Updated dependency `exasol-toolbox:11.0.0` to `12.0.0`
* Updated dependency `notebook:7.6.2` to `7.6.3`
* Updated dependency `pytest-ipywidgets:1.62.0` to `1.64.1`
* Updated dependency `pytest-mock:3.15.1` to `3.17.0`
* Removed dependency `starlette:0.52.1`
