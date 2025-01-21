# 0.4.0 - 2024-10-23

## Summary
Fixes of vulnerabilities, several bugs and python-toolbox workflows update.

## Security Issues

* #146: Fixed vulnerabilities by updating dependencies

### Bug fixing

* #143: itde_manager.bring_itde_up() fails if the container is not connected to the network it is assumed to be connected to.
* #149: Fix DB version not taken into account in CI.
* #129: Fix bucketfs putfile issue on SaaS.
