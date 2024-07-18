# Unreleased

## Changes

* #103 Enabled SaaS connections for both the database and the BucketFS.
* #105 Added the new configuration element - storage_backend.
* #108 Supplied the BucketFS service name when opening an on-prem bucketfs bucket. 
* #110 Added the support of SaaS to the extension wrappers.
    - Added SaaS configuration parameters in a call to the language container deployer.
    - Changed how the bucketfs parameters are stored in a connection object.
* #123 Added a function that opens a connection to Ibis.
