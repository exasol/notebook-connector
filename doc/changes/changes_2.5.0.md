# 2.5.0 - 2026-03-13

## Summary

This release converts the former ipynb files to python files, simplifying testing and importing. Additionally, this release enables accessing the Secure Configuration Storage in multiple threads.

## Features

* #354: Converted ipynb to python for `utils/jupysql_init`
* #343: Converted ipynb to python for `main_config_ui` and automated tests

## Bugfixes

* #327: Fixed Multiple CD workflows
* #344: Enabled SCS to be used by multiple threads

## Refactorings

* #305: Replacing store magic with normal file access
* #356: Added pytest-benchmark Plugin and measured performance of SCS access
* #345: Refactored `main_config_ui` and improved UI folder structure for better maintainability
* #346: Added integration tests for docker_db main configuration UI
* #363: Simplified the UI test folder structure for better accessibility and maintainability
* #364: Added unit tests for `main_config_ui`
* #358: Added integration tests for `jupysql` initialization

## Dependency Updates

### `main`
* Updated dependency `exasol-saas-api:2.6.0` to `2.8.0`
* Updated dependency `exasol-sagemaker-extension:0.11.6` to `0.11.7`
* Updated dependency `exasol-script-languages-container-tool:3.6.0` to `3.6.1`
* Added dependency `jupysql:0.11.1`
* Added dependency `tenacity:8.5.0`

### `dev`
* Updated dependency `notebook:7.5.3` to `7.5.4`
* Updated dependency `pytest:7.4.4` to `8.4.2`
* Updated dependency `pytest-dependency:0.6.0` to `0.6.1`
* Updated dependency `pytest-exasol-backend:1.2.4` to `1.3.0`
* Updated dependency `pytest-ipywidgets:1.57.2` to `1.57.3`

### `performance`
* Added dependency `pytest-benchmark:5.2.3`
