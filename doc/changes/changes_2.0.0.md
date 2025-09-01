# 2.0.0 - 2025-09-01

This release disables the certificate check for the importer when starting a docker db using the ITDE (this is a temporary fix until the notebook connector updated to pyexasol >=1.0.0). Also, the installation of AI models has been refactored which resulted in breaking API changes. The used Script-Language-Container version was updated to 10.0.0. Besides, there were internal improvements.


## Refactorings

 - #244: Updated PTB to 1.9.0
 - #247: Start ITDE with disabled certificate check for importer
 - #242: Refactoring of install_model
 - #246: Use SLC 10.0.0

## Features

 - #250: Added export function which does not copy container file to export directory

## Dependency Updates

### `dev`
* Updated dependency `exasol-toolbox:1.7.4` to `1.9.0`
