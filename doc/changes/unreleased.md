# Unreleased

## Summary

This release marks most of the NC's dependencies in file `pyproject.toml` as _optional_.  Please see updated installation instructions in the NC User Guide.

Additionally the release includes a CLI for populating the Secure Configuration Storage (SCS).

## Features

* #258: Added initial SCS CLI
* #263: Add option mapper for SCS CLI

## Refactorings

* #253: Made dependencies optional in file `pyproject.toml`
* #260: Added unit tests for CLI param wrappers
