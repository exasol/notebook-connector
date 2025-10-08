# Unreleased

## Summary

This release marks most of the NC's dependencies in file `pyproject.toml` as _optional_.  Please see updated installation instructions in the NC User Guide.

Additionally the release includes a CLI for populating the Secure Configuration Storage (SCS).

## Features

* #258: Added initial SCS CLI
* #263: Added functions for handling a set of options for SCS CLI
* #267: Implemented modify operations for the SCS
* #269: Implemented showing SCS content
* #271: Implemented checking SCS content
* #274: Added verification of access to BucketFS

## Refactorings

* #253: Made dependencies optional in file `pyproject.toml`
* #260: Added unit tests for CLI param wrappers
* #265: Fixed type hints in tests
* #251: Re-enabled SaaS integration tests
