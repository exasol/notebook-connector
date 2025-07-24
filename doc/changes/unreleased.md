# Unreleased

## Summary

This release comes with a breaking change in class `SlctManager`.  Since version 1.0.0 the constructor of `SlctManager` requires to specify the additional parameter `session`.

Please see the [Notebook Connector User Guide](https://github.com/exasol/notebook-connector/blob/main/doc/user_guide/user-guide.md) for details.

## Features

* #213: Added Support for multiple templates wrt. to sessions

## Refactorings

* #211: Modularized execution of integration tests in CI
