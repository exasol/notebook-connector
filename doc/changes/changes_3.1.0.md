# 3.1.0 - 2026-10-14

## Summary

In this release we updated to the new Transformers-Extension 5.2.0

## Security Issues

This release fixes vulnerabilities by updating dependencies:

| Dependency | Vulnerability | Affected | Fixed in |
|------------|---------------|----------|----------|
| anyio | PYSEC-2026-4025 | 4.14.0 | 4.14.2 |
| anyio | PYSEC-2026-4023 | 4.14.0 | 4.14.2 |
| anyio | PYSEC-2026-4024 | 4.14.0 | 4.14.2 |
| cryptography | PYSEC-2026-3552 | 49.0.0 | 50.0.0 |
| cryptography | PYSEC-2026-3552 | 49.0.0 | 50.0.0 |
| gitpython | PYSEC-2026-3947 | 3.1.50 | 3.1.51 |
| gitpython | PYSEC-2026-3984 | 3.1.50 | 3.1.60 |
| gitpython | PYSEC-2026-3982 | 3.1.50 | 3.1.60 |
| gitpython | PYSEC-2026-3981 | 3.1.50 | 3.1.53 |
| gitpython | PYSEC-2026-3836 | 3.1.50 | 3.1.51 |
| gitpython | PYSEC-2026-3995 | 3.1.50 | 3.1.54 |
| gitpython | PYSEC-2026-3951 | 3.1.50 | 3.1.55 |
| gitpython | PYSEC-2026-3783 | 3.1.50 | 3.1.58 |
| gitpython | PYSEC-2026-3984 | 3.1.50 | 3.1.60 |
| gitpython | PYSEC-2026-3785 | 3.1.50 | 3.1.59 |
| gitpython | PYSEC-2026-3786 | 3.1.50 | 3.1.59 |
| gitpython | PYSEC-2026-3783 | 3.1.50 | 3.1.58 |
| gitpython | PYSEC-2026-3787 | 3.1.50 | 3.1.59 |
| gitpython | PYSEC-2026-3788 | 3.1.50 | 3.1.59 |
| gitpython | PYSEC-2026-3784 | 3.1.50 | 3.1.58 |
| gitpython | PYSEC-2026-3786 | 3.1.50 | 3.1.59 |
| gitpython | PYSEC-2026-3787 | 3.1.50 | 3.1.59 |
| gitpython | PYSEC-2026-3788 | 3.1.50 | 3.1.59 |
| gitpython | PYSEC-2026-3837 | 3.1.50 | 3.1.59 |
| gitpython | PYSEC-2026-3840 | 3.1.50 | 3.1.58 |
| gitpython | PYSEC-2026-3836 | 3.1.50 | 3.1.51 |
| gitpython | PYSEC-2026-3838 | 3.1.50 | 3.1.58 |
| gitpython | PYSEC-2026-3839 | 3.1.50 | 3.1.51 |
| gitpython | PYSEC-2026-3841 | 3.1.50 | 3.1.58 |
| gitpython | PYSEC-2026-3837 | 3.1.50 | 3.1.59 |
| gitpython | PYSEC-2026-3843 | 3.1.50 | 3.1.58 |
| gitpython | PYSEC-2026-3949 | 3.1.50 | 3.1.57 |
| gitpython | PYSEC-2026-3951 | 3.1.50 | 3.1.55 |
| gitpython | PYSEC-2026-3953 | 3.1.50 | 3.1.54 |
| gitpython | PYSEC-2026-3952 | 3.1.50 | 3.1.54 |
| gitpython | PYSEC-2026-3950 | 3.1.50 | 3.1.56 |
| gitpython | PYSEC-2026-3948 | 3.1.50 | 3.1.57 |
| jupyter-server | PYSEC-2026-366 | 2.19.0 | 2.20.0 |
| jupyter-server | PYSEC-2026-366 | 2.19.0 | 2.20.0 |
| jupyter-server | PYSEC-2026-4054 | 2.19.0 | 2.21.0 |
| jupyterlab | PYSEC-2026-3671 | 4.5.8 | 4.5.10 |
| jupyterlab | PYSEC-2026-3672 | 4.5.8 | 4.5.10 |
| jupyterlab | PYSEC-2026-3670 | 4.5.8 | 4.5.10 |
| jupyterlab | PYSEC-2026-3672 | 4.5.8 | 4.5.10 |
| jupyterlab | PYSEC-2026-3670 | 4.5.8 | 4.5.10 |
| jupyterlab | PYSEC-2026-3671 | 4.5.8 | 4.5.10 |
| jupyterlab | CVE-2026-67338 | 4.5.8 | 4.5.9 |
| jupyterlab | GHSA-h5v5-8746-g7mm | 4.5.8 | 4.5.10 |
| jupyterlab | CVE-2026-73626 | 4.5.8 | 4.5.10 |
| mistune | PYSEC-2026-2652 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2217 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2214 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2215 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2212 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2216 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2213 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2218 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2211 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2210 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2652 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2216 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2215 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2210 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2214 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2217 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2218 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2213 | 3.2.1 | 3.3.0 |
| mistune | PYSEC-2026-2211 | 3.2.1 | 3.3.0 |
| msgpack | PYSEC-2026-3625 | 1.2.0 | 1.2.1 |
| msgpack | PYSEC-2026-3625 | 1.2.0 | 1.2.1 |
| nltk | PYSEC-2026-3583 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3582 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3584 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3583 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3582 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3584 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-597 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3723 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3722 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3728 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3734 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3736 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3739 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3738 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3735 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3737 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3730 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3741 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3733 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3731 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3749 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3748 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3750 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3751 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3749 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3752 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3741 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3739 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3738 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3790 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3723 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3722 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3790 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3730 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3728 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3733 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3748 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3734 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3737 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3735 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3736 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3752 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3750 | 3.9.4 | 3.10.0 |
| nltk | PYSEC-2026-3751 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3868 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3871 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3870 | 3.9.4 | 3.10.1 |
| nltk | PYSEC-2026-3869 | 3.9.4 | 3.10.3 |
| nltk | PYSEC-2026-3954 | 3.9.4 | 3.10.0 |
| pillow | PYSEC-2026-2253 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-2255 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-2257 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-2256 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-2254 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3453 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3451 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3452 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3493 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-2254 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-2253 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-2256 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-2255 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3454 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3451 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3494 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3452 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3495 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3496 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3453 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3454 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3495 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3496 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3494 | 12.2.0 | 12.3.0 |
| pillow | PYSEC-2026-3493 | 12.2.0 | 12.3.0 |
| pip | PYSEC-2026-3721 | 26.1.2 | 26.2 |
| pip | PYSEC-2026-3721 | 26.1.2 | 26.2.0 |
| pyasn1 | PYSEC-2026-3456 | 0.6.3 | 0.6.4 |
| pyasn1 | PYSEC-2026-3457 | 0.6.3 | 0.6.4 |
| pyasn1 | PYSEC-2026-3456 | 0.6.3 | 0.6.4 |
| pyasn1 | PYSEC-2026-3457 | 0.6.3 | 0.6.4 |
| pyasn1 | PYSEC-2026-3455 | 0.6.3 | 0.6.4 |
| pyasn1 | PYSEC-2026-3455 | 0.6.3 | 0.6.4 |
| setuptools | PYSEC-2026-3447 | 81.0.0 | 83.0.0 |
| setuptools | PYSEC-2026-3447 | 81.0.0 | 83.0.0 |
| soupsieve | PYSEC-2026-4170 | 2.8.4 | 2.9.0 |
| soupsieve | PYSEC-2026-4171 | 2.8.4 | 2.9.0 |
| sqlparse | PYSEC-2026-3697 | 0.5.5 | 0.6.0 |
| sqlparse | PYSEC-2026-3696 | 0.5.5 | 0.6.0 |
| sqlparse | PYSEC-2026-3698 | 0.5.5 | 0.6.0 |
| sqlparse | PYSEC-2026-3699 | 0.5.5 | 0.6.0 |
| sqlparse | PYSEC-2026-3698 | 0.5.5 | 0.6.0 |
| sqlparse | PYSEC-2026-3697 | 0.5.5 | 0.6.0 |
| sqlparse | PYSEC-2026-3699 | 0.5.5 | 0.6.0 |
| sqlparse | PYSEC-2026-3696 | 0.5.5 | 0.6.0 |
| sqlparse | PYSEC-2026-3923 | 0.5.5 | 0.6.0 |
| torch | PYSEC-2025-194 | 2.12.0 | 2.13.0 |
| tornado | PYSEC-2026-3928 | 6.5.7 | 6.5.8 |
| tornado | GHSA-chx6-46f5-w4vp | 6.5.7 | 6.5.9 |
| tornado | GHSA-c2m8-h5v5-343r | 6.5.7 | 6.5.9 |
| tornado | GHSA-3hv7-mjh2-fv65 | 6.5.7 | 6.5.9 |
| tornado | GHSA-wwv5-g3v4-889x | 6.5.7 | 6.5.8 |
| tornado | GHSA-8423-8fgw-73vq | 6.5.7 | 6.5.8 |
| transformers | PYSEC-2026-2288 | 4.57.6 | 5.0.0rc3 |
| transformers | PYSEC-2026-2289 | 4.57.6 | 5.3.0 |
| transformers | PYSEC-2026-2288 | 4.57.6 | 5.0.0 |
| transformers | PYSEC-2026-2289 | 4.57.6 | 5.3.0 |
| transformers | PYSEC-2026-2290 | 4.57.6 | 5.5.0 |
| transformers | PYSEC-2026-3929 | 4.57.6 | 5.10.0 |
| urllib3 | PYSEC-2026-4177 | 2.7.0 | 2.8.0 |
| urllib3 | PYSEC-2026-4176 | 2.7.0 | 2.8.0 |
| urllib3 | PYSEC-2026-4175 | 2.7.0 | 2.8.0 |
| virtualenv | PYSEC-2026-4011 | 21.5.1 | 21.7.12 |
| virtualenv | PYSEC-2026-4012 | 21.5.1 | 21.7.11 |
| virtualenv | PYSEC-2026-4014 | 21.5.1 | 21.7.12 |
| virtualenv | PYSEC-2026-4013 | 21.5.1 | 21.7.13 |
| virtualenv | PYSEC-2026-4011 | 21.5.1 | 21.7.12 |
| virtualenv | PYSEC-2026-4012 | 21.5.1 | 21.7.11 |
| virtualenv | PYSEC-2026-4013 | 21.5.1 | 21.7.13 |
| virtualenv | PYSEC-2026-4014 | 21.5.1 | 21.7.12 |

## Features

* #464: Updated to transformers-extension 5.2.0 and added new udfs to notebooks
* #475: Added check to verify version compatibility to sklearn Notebooks

## Refactorings

* #433: Reorganized the tests for Jupyter Notebooks
  * Please see the Developer Guide for details.
* #440: Updated to exasol-toolbox 10.2.1
* #473: Re-enabled check-workflows in the `checks.yml` to ensure workflows stay up-to-date and updated dependencies
* #483: Removed obsolete AWS secret declarations and forwarding from the notebook test workflow

## Dependency updates

* #475: Updated to pyexasol version 2.3.2, sqlalchemy-exasol version 7.1.4

## Dependency Updates

### `main`

* Updated dependency `click:8.4.1` to `8.5.0`
* Updated dependency `exasol-bucketfs:2.2.0` to `2.3.0`
* Updated dependency `exasol-text-ai-extension:0.3.0` to `0.4.1`
* Updated dependency `exasol-transformers-extension:3.0.0` to `5.2.1`
* Updated dependency `gitpython:3.1.50` to `3.1.62`
* Updated dependency `ibis-framework:11.0.0` to `12.0.0`
* Updated dependency `ipywidgets:8.1.8` to `8.1.9`
* Updated dependency `jupyterlab:4.5.8` to `4.6.3`
* Updated dependency `matplotlib:3.11.0` to `3.11.2`
* Updated dependency `polars:1.41.2` to `1.44.2`
* Updated dependency `pyexasol:1.3.0` to `2.3.2`
* Updated dependency `scikit-learn:1.9.0` to `1.9.1`
* Updated dependency `sqlalchemy-exasol:5.2.0` to `7.1.4`
* Added dependency `sqlglot:30.17.0`
* Updated dependency `yaspin:3.4.0` to `3.5.1`

### `dev`

* Updated dependency `exasol-toolbox:9.0.0` to `11.0.0`
* Updated dependency `nbformat:5.10.4` to `5.11.1`
* Updated dependency `notebook:7.5.7` to `7.6.2`
* Updated dependency `pytest-ipywidgets:1.57.5` to `1.62.0`
* Updated dependency `types-pyyaml:6.0.12.20260518` to `6.0.12.20260906`

### `performance`

* Updated dependency `pytest-benchmark:5.2.3` to `5.3.0`
