# 2.2.0 - 2025-10-21

## Summary

This release fixes a bug which caused the SCS CLI to overwrite user values by default values.  Fixing the bug also led to some updates regarding the default values for specific CLI options:

| Instance type | Option                     | Old default                        | New default                    |
|---------------|----------------------------|------------------------------------|--------------------------------|
| on-premise    | `--bucketfs-host-internal` | `get_default_from="bucketfs_host"` | `localhost` (individual)       |
| on-premise    | `--bucketfs-port-internal` | `get_default_from="bucketfs_port"` | `2580` (individual)            |
| on-premise    | `--bucketfs-host`          | `localhost`                        | (none)                         |
| on-premise    | `--bucketfs-name`          | `bfsdefault`                       | (none)                         |
| on-premise    | `--bucket`                 | `default`                          | (none)                         |
| on-premise    | `--db-host-name`           | `localhost`                        | (none)                         |
| docker-db     | `--db-mem-size`            | `2`                                | `8`                            |

## Bugfixes

* #285: Fixed bug overwriting user input for SCS options by default values
