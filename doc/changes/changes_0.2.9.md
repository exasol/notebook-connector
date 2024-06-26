# Exasol Notebook Connector 0.2.9, released T.B.D.

## Summary

Post-release fixes.

## Changes

* AI-Lab#230: Connection via SQLAlchemy fails
  - Enables fingerprints in the host name.
  - Handles correctly special characters in the password. 
* #89: Connecting a new AI-Lab container to the Docker DB network when the latter container restarts.
* #93: Refactoring the ITDE manager interface.
* #94: Adding an integration test for restart_itde() in a container.
* #95: Adding an integration test for get_itde_status() in a container.
* #99: Setting the correct protocol and TLS certificate verification option when creating a
       connection object with BucketFS credentials.