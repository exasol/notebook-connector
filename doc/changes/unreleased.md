# Unreleased

## Features

* #89: Enabled connecting a new AI-Lab container to the Docker DB network when the latter container restarts.
* #103: Enabled SaaS connections for both the database and the BucketFS.
* #110: Added the support of SaaS to the extension wrappers.
  * Added SaaS configuration parameters in a call to the language container deployer.
  * Changed how the bucketfs parameters are stored in a connection object.

## Bugfixes

* AI-Lab#230: Fixed AI-Lab connection via SQLAlchemy.
  * Enabled fingerprints in the host name.
  * Fixed handling of special characters in the password.
* #99: Fixed protocol and TLS certificate verification option when creating a connection object with BucketFS credentials.
* #108: Supplied the BucketFS service name when opening an on-prem bucketfs bucket.

## Refactorings

* #93: Refactoring the ITDE manager interface.
* #94: Adding an integration test for restart_itde() in a container.
* #95: Adding an integration test for get_itde_status() in a container.
* #105: Added the new configuration element - storage_backend.
* #116: Restricted compatibility to python &ge; 3.10.
