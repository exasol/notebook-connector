# Exasol Notebook Connector 0.3.0, released 2024-09-09

Code name: Support existing DockerDB and bug fixes

## Summary

This release adds support to use an instance of the DockerDB provided externally and fixes some minor bugs.

## Features

* #131: Let the `itde_manager` use an instance of the DockerDB provided externally.

## Bugfixes

* #133: Fixed the following defects:
  - Using the `allow_override` option when deploying a language container.
  - Storing internal bucket-fs host and port in a bucket-fs connection object.

## Refactoring

* 125: Pin Script-Language-Release repository to tag 8.2.0