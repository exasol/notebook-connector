# 2.3.0 - 2025-12-17
This release includes several improvements of the `ScriptLanguagesContainer` interfaces which aim to improve robustness to manage the Script-Languages-Container in the related notebooks. Also, it added the UI implementation for the SCS main configuration. Besides, there were several internal improvements. 


## Documentation

* #304: Described UI test categories in Developer Guide

## Refactoring

* #314: Added more robust for class ScriptLanguageContainer
* #316: Implemented consistency check for workspace in ScriptLanguageContainer.create()

## Features

* #297: Added UI tests for the SCS main configuration dialog and a dedicated GitHub workflow
* #287: working examples for functional UI
* #319: Add restore_package_file method to class ScriptLanguagesContainer
* #318: Added method to generate and store language_definition
* #317: Implemented reuse of workspace directory

## Dependency Updates

### `main`
* Updated dependency `exasol-integration-test-docker-environment:4.4.1` to `5.0.0`
* Updated dependency `exasol-saas-api:2.4.0` to `2.6.0`
* Updated dependency `exasol-script-languages-container-tool:3.4.1` to `3.5.0`
* Added dependency `pickleshare:0.7.5`
* Updated dependency `polars:1.35.2` to `1.36.1`
* Updated dependency `sqlcipher3-binary:0.5.4` to `0.5.4.post2`
* Updated dependency `yaspin:3.3.0` to `3.4.0`

### `dev`
* Added dependency `notebook:7.5.0`
* Updated dependency `pytest-exasol-backend:1.2.2` to `1.2.4`
* Updated dependency `pytest-ipywidgets:1.54.0` to `1.55.1`
