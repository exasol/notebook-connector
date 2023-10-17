# Exasol Notebook Connector

Connection configuration management and additional tools for Jupyter notebook applications provided by Exasol company.

[![PyPI Version](https://img.shields.io/pypi/v/exasol-notebook-connector)](https://pypi.org/project/exasol-notebook-connector/)
[![License](https://img.shields.io/pypi/l/exasol-notebook-connector)](https://opensource.org/licenses/MIT)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/exasol-notebook-connector)](https://pypi.org/project/exasol-notebook-connector)
[![Last Commit](https://img.shields.io/github/last-commit/exasol/notebook-connector)](https://pypi.org/project/exasol-notebook-connector/)

## Features

Exasol Notebook Connector (ENC) currently contains a **Secret Store** that can be used in Jupyter notebook applications to store arbitrary credentials and configuration items, such as user names, passwords, URLs, etc.

By that users of such notebook applications
* need to enter their credentials and configuration items only once
* can store them in a secure, encrypted, and persistent file based on SQLite and [coleifer/sqlcipher3](https://github.com/coleifer/sqlcipher3)
* can use these credentials and configuration items in their notebook applications
