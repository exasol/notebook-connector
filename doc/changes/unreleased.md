# Unreleased

## Summary

This release fixes vulnerabilities by updating dependencies:

| Dependency   | Affected | Vulnerability       | Fixed in      | Updated to |
|--------------|----------|---------------------|---------------|------------|
| black        | 25.12.0  | CVE-2026-32274      | 26.3.1        | 23.3.1     |
| cryptography | 45.0.7   | CVE-2026-26007      | 46.0.5        | 46.0.6     |
| cryptography | 45.0.7   | CVE-2026-34073      | 46.0.6        | 46.0.6     |
| nltk         | 3.9.2    | CVE-2025-14009      | 3.9.3         | 3.9.4      |
| nltk         | 3.9.2    | CVE-2026-33230      | 3.9.4         | 3.9.4      |
| protobuf     | 4.25.8   | CVE-2026-0994       | 5.29.6,6.33.5 | 5.29.6     |
| pyasn1       | 0.6.1    | CVE-2026-23490      | 0.6.2         | 0.6.3      |
| pyasn1       | 0.6.1    | CVE-2026-30922      | 0.6.3         | 0.6.3      |
| pygments     | 2.19.2   | CVE-2026-4539       | 2.20.0        | 2.20.0     |
| requests     | 2.32.5   | CVE-2026-25645      | 2.33.0        | 2.33.1     |
| sagemaker    | 2.254.1  | CVE-2026-1778       | 2.256.0,3.1.1 | 2.257.1    |
| sagemaker    | 2.254.1  | CVE-2026-1777       | 2.256.0,3.2.0 | 2.257.1    |
| sagemaker    | 2.254.1  | GHSA-5r2p-pjr8-7fh7 | 3.4.0         | 2.257.1    |
| tornado      | 6.5.4    | GHSA-78cv-mqj4-43f7 | 6.5.5         | 6.5.5      |
| tornado      | 6.5.4    | CVE-2026-31958      | 6.5.5         | 6.5.5      |

For the following vulnerable packages there is no update available, yet:

| Dependency | Affected | Vulnerability       | Fixed in | Updated to |
|------------|----------|---------------------|----------|------------|
| nltk       | 3.9.2    | CVE-2026-33231      |          |            |
| nltk       | 3.9.2    | GHSA-rf74-v2fm-23pw |          |            |

## Security Issues

* #376: Fixed vulnerabilities by updating dependencies

## Refactorings

* #379: Converted `ai-lab/te_init_ui.ipynb` to `py` and added unit and integration tests
* #382: Moved notebooks from ai-lab into notebook-connector including tests 
