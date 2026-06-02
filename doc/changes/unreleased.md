# Unreleased

## Summary

## Security Issues

* #376: Fixed vulnerabilities by updating dependencies
* #406: Fixed vulnerabilities by updating dependencies

## Bug Fixes

* #413: Fixed Luigi signal handling in notebook DockerDB startup and SLC build
* #416: Fixed wrong access store search path in `first_steps.ipynb`

## Refactorings

* #379: Converted `ai-lab/te_init_ui.ipynb` to `py` and added unit and integration tests
* #382: Moved notebooks from ai-lab into notebook-connector including tests
* #392: Used unique job names in CI matrix build
* #387: Added CI workflow for test/notebooks
* #401: Split as stable and unstable in CI workflow for normal and large tests
* #408: Removed sagemaker related code and tests
* #410: Updated Documentation for CLIs and Python APIs in notebook-connector
