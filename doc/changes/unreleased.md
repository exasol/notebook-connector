# Unreleased

## Bugfix
* #182: Updated LATEST_KNOWN_VERSION to be dynamically fetched with importlib.metadata for
transformers_extension_wrapper & sagemaker_extension_wrapper

## Security
* #198: Updated requests from >=2.32.0 to >=2.32.4 due to CVE-2024-47081 and
transformers from ^4.50.0 to ^4.52.1 due to CVE-2025-3933 and CVE-2025-3777

## Internal
* Relocked poetry dependencies to resolve CVE-2025-47287 and CVE-2025-47273
* #198: Relocked poetry dependencies to resolve CVE-2025-50181 and CVE-2025-50182 for transitive dependency urllib3