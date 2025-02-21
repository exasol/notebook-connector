# Notebook Connector Developer Guide

## How to Release?

Creating a new release of the NC requires 4 steps

1. Update version number
2. Prepare the release
3. Merge your pull request to the default branch
4. Create and push a tag to GitHub

### Update version number

1. Update version in file `pyproject.toml` or call `poetry version <version>`
2. Call `poetry run version-check version.py --fix`

The second command will update the version number in file `version.py`.

### Prepare the Release

```shell
poetry run nox -s release:prepare <additional-options> <version>
```

Optional additional CLI options are
* `--no-branch` if working on a branch
* `--no-pr` if you already created a pull request or plan to do so manually after preparing the release
