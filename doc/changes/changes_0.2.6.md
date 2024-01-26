# Exasol Notebook Connector 0.2.6, released t.b.d

## Summary

This release adds the extension wrappers, the ITDE manager and makes full use of the configuration enumeration.

## Changes

* #50: [Add iterable features to the secret store](https://github.com/exasol/notebook-connector/issues/50)
* #52: [Make data conversion utility for the secret store commonly accessible](https://github.com/exasol/notebook-connector/issues/52)
* #55: [Unified language activation SQL command](https://github.com/exasol/notebook-connector/pull/55)
* #56: [Transformers extension wrapper](https://github.com/exasol/notebook-connector/pull/56)
* #47: [Create a Sagemaker Extension wrapper](https://github.com/exasol/notebook-connector/issues/47)
* #60: [Start using the AILabConfig internally](https://github.com/exasol/notebook-connector/issues/60)
* #65: [Renamed "bucket-fs" to "BucketFS" in docstrings](https://github.com/exasol/notebook-connector/issues/65)
* #68: [Modify language activation mechanism](https://github.com/exasol/notebook-connector/issues/68)
* #70: [Improve the itde_manager](https://github.com/exasol/notebook-connector/issues/70)
  * Do more elaborate check of the docker container status. Return two flags - exists and running.
  * Add a new function - `start_itde` that re-starts an existing docker container.
* #63: [Integration tests for cloud-storage-extension code](https://github.com/exasol/notebook-connector/issues/63)
* #75: Connect the current docker container with the ITDE docker network in bring_itde_up
