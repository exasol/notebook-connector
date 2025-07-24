# Unreleased

## Summary

<!--
Current implementation no longer requires a breaking change.

This release comes with a breaking change in class `SlctManager`.  Since version 1.0.0 the constructor of `SlctManager` requires to specify the additional parameter `session`.

Please see the [Notebook Connector User Guide](https://github.com/exasol/notebook-connector/blob/main/doc/user_guide/user-guide.md) for details.
-->

## Features

* #213: Added Support to specify the SLC flavor via a session parameter

## Refactorings

* #211: Modularized execution of integration tests in CI
* #208: Widened version constraints for:
   * exasol-saas-api from ">=0.9.0,<1.0.0" to ">=0.9.0,<3"
   * exasol-bucketfs from "^1.0.0" to ">=1,<3"

## Features
* #205: Added GPU support to ITDE manager