# Exasol Notebook Connector 0.2.9, released T.B.D.

## Summary

Post-release fixes.

## Changes

* AI-Lab#230: Connection via SQLAlchemy fails
  - Enables fingerprints in the host name.
  - Handles correctly special characters in the password. 
* #89: Connecting a new AI-Lab container to the Docker DB network when the latter container restarts.
* #93: Refactoring the ITDE manager interface.