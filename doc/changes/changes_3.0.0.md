# 3.0.0 - 2026-06-16

## Summary

## Security Issues

This release fixes vulnerabilities by updating dependencies:

| Dependency | Vulnerability | Affected | Fixed in |
|------------|---------------|----------|----------|
| black | CVE-2026-32274 | 25.12.0 | 26.3.1 |
| cryptography | PYSEC-2026-35 | 46.0.5 | 46.0.6 |
| cryptography | PYSEC-2026-36 | 46.0.5 | 46.0.7 |
| cryptography | PYSEC-2026-36 | 46.0.5 | 46.0.7 |
| cryptography | PYSEC-2026-35 | 46.0.5 | 46.0.6 |
| cryptography | GHSA-537c-gmf6-5ccf | 46.0.5 | 48.0.1 |
| gitpython | CVE-2026-42215 | 3.1.46 | 3.1.47 |
| gitpython | CVE-2026-42284 | 3.1.46 | 3.1.47 |
| gitpython | CVE-2026-44244 | 3.1.46 | 3.1.49 |
| gitpython | GHSA-mv93-w799-cj2w | 3.1.46 | 3.1.50 |
| idna | CVE-2026-45409 | 3.11 | 3.15 |
| jupyter-server | PYSEC-2026-67 | 2.17.0 | 2.18.0 |
| jupyter-server | PYSEC-2026-68 | 2.17.0 | 2.18.0 |
| jupyter-server | PYSEC-2026-69 | 2.17.0 | 2.18.0 |
| jupyter-server | PYSEC-2026-67 | 2.17.0 | 2.18.0 |
| jupyter-server | PYSEC-2026-69 | 2.17.0 | 2.18.0 |
| jupyter-server | PYSEC-2026-68 | 2.17.0 | 2.18.0 |
| jupyter-server | CVE-2026-40110 | 2.17.0 | 2.18.0 |
| jupyterlab | PYSEC-2026-164 | 4.5.6 | 4.5.7 |
| jupyterlab | PYSEC-2026-164 | 4.5.6 | 4.5.7 |
| jupyterlab | CVE-2026-42557 | 4.5.6 | 4.5.7 |
| mistune | PYSEC-2026-168 | 3.2.0 | 3.2.1 |
| mistune | PYSEC-2026-168 | 3.2.0 | 3.2.1 |
| mistune | CVE-2026-33079 | 3.2.0 | 3.2.1 |
| mistune | CVE-2026-44897 | 3.2.0 | 3.2.1 |
| nbconvert | CVE-2026-39378 | 7.17.0 | 7.17.1 |
| nbconvert | CVE-2026-39377 | 7.17.0 | 7.17.1 |
| nltk | CVE-2026-33230 | 3.9.3 | 3.9.4 |
| nltk | CVE-2026-33231 | 3.9.3 | 3.9.4 |
| notebook | CVE-2026-40171 | 7.5.5 | 7.5.6 |
| pillow | PYSEC-2026-165 | 12.1.1 | 12.2.0 |
| pillow | PYSEC-2026-165 | 12.1.1 | 12.2.0 |
| pillow | CVE-2026-40192 | 12.1.1 | 12.2.0 |
| pillow | CVE-2026-42309 | 12.1.1 | 12.2.0 |
| pillow | CVE-2026-42310 | 12.1.1 | 12.2.0 |
| pillow | CVE-2026-42311 | 12.1.1 | 12.2.0 |
| pip | PYSEC-2026-196 | 26.0.1 | 26.1.2 |
| pip | CVE-2026-3219 | 26.0.1 | 26.1 |
| pip | CVE-2026-6357 | 26.0.1 | 26.1 |
| pyasn1 | CVE-2026-30922 | 0.6.2 | 0.6.3 |
| pygments | CVE-2026-4539 | 2.19.2 | 2.20.0 |
| requests | CVE-2026-25645 | 2.32.5 | 2.33.0 |
| sagemaker | GHSA-5r2p-pjr8-7fh7 | 2.257.1 | 3.4.0 |
| sagemaker | CVE-2026-8596 | 2.257.1 | 2.257.2 |
| sagemaker | CVE-2026-8597 | 2.257.1 | 2.257.2 |
| tornado | CVE-2026-49854 | 6.5.5 | 6.5.6 |
| tornado | CVE-2026-49853 | 6.5.5 | 6.5.6 |
| tornado | CVE-2026-49855 | 6.5.5 | 6.5.6 |
| tornado | GHSA-pw6j-qg29-8w7f | 6.5.5 | 6.5.7 |
| urllib3 | PYSEC-2026-142 | 2.6.3 | 2.7.0 |
| urllib3 | PYSEC-2026-142 | 2.6.3 | 2.7.0 |
| urllib3 | PYSEC-2026-141 | 2.6.3 | 2.7.0 |

* #376: Fixed vulnerabilities by updating dependencies
* #406: Fixed vulnerabilities by updating dependencies

## Bug Fixes

* #413: Fixed Luigi signal handling in notebook DockerDB startup and SLC build
* #416: Fixed wrong access store search path in `first_steps.ipynb`
* #417: Normalized access-store notebook paths and exported `NOTEBOOKS` from `ai-lab start`
* #426: Added PIP section manually to conda slc package definition

## Refactorings

* #379: Converted `ai-lab/te_init_ui.ipynb` to `py` and added unit and integration tests
* #382: Moved notebooks from ai-lab into notebook-connector including tests
* #392: Used unique job names in CI matrix build
* #387: Added CI workflow for test/notebooks
* #401: Split as stable and unstable in CI workflow for normal and large tests
* #408: Removed sagemaker related code and tests
* #410: Updated Documentation for CLIs and Python APIs in notebook-connector
* #414: Added examples and explanations for features in documentation

## Features

* #421: Enable SaaS SLC deploy

## Dependency Updates

### `main`

* Added dependency `click:8.4.1`
* Updated dependency `exasol-integration-test-docker-environment:5.0.0` to `6.2.0`
* Updated dependency `exasol-saas-api:2.9.0` to `2.10.0`
* Removed dependency `exasol-sagemaker-extension:0.11.7`
* Updated dependency `exasol-script-languages-container-tool:3.6.1` to `4.1.0`
* Updated dependency `exasol-text-ai-extension:0.2.1` to `0.3.0`
* Updated dependency `gitpython:3.1.46` to `3.1.50`
* Added dependency `ipyfilechooser:0.6.0`
* Added dependency `ipywidgets:8.1.8`
* Added dependency `jupyterlab:4.5.8`
* Added dependency `matplotlib:3.10.9`
* Added dependency `pexpect:4.9.0`
* Updated dependency `polars:1.39.0` to `1.41.2`
* Added dependency `psutil:7.2.2`
* Added dependency `scikit-learn:1.7.2`
* Added dependency `stopwatch-py:2.0.1`
* Added dependency `wordcloud:1.9.6`

### `dev`

* Updated dependency `exasol-toolbox:5.1.1` to `8.2.0`
* Added dependency `nbclient:0.11.0`
* Added dependency `nbformat:5.10.4`
* Updated dependency `notebook:7.5.5` to `7.5.7`
* Added dependency `pytest-check-links:0.10.1`
* Updated dependency `pytest-exasol-backend:1.4.0` to `1.4.1`
* Updated dependency `pytest-ipywidgets:1.57.3` to `1.57.4`
* Added dependency `starlette:0.52.1`
* Added dependency `testbook:0.4.2`
* Added dependency `types-pyyaml:6.0.12.20260518`
