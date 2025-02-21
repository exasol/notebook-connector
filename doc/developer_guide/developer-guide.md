# Notebook Connector Developer Guide

## How to Release?

Creating a new release of the NC requires 4 steps

1. [Prepare the release](#prepare-the-release)
2. Merge your pull request to the default branch
3. [Create and push a tag to GitHub](#creating-a-git-tag-and-pushing-it-to-github)

### Prepare the Release

```shell
poetry run nox -s release:prepare <additional-options> <version>
```

Optional additional CLI options are
* `--no-branch` if already working on a branch
* `--no-pr` if you already created a pull request or plan to do so manually after preparing the release

The command uses the nox task `project:fix` of the [Python Tool
Box](https://github.com/exasol/python-toolbox/) (PTB) and
* Optionally creates a branch
* Optionally creates a pull request
* Updates the [version number](#updating-the-version-number-without-preparing-a-release) and the Change Log

Updating the Change Log includes
* Moving file `doc/changes/unreleased.md` to a filename reflecting the specified version, e.g. `doc/changes/changes_1.2.3.md`
* Updating the list of changes files in `doc/changes/changelog.md`
* Adding the current date at the top of the changelog as the date of the release
* Creating a new file `doc/changes/unreleased.md`

### Creating a Git Tag and Pushing it to GitHub

Use the following commands to create a Git Tag and push it to GitHub:

```shell
TAG=<version>
git tag "$TAG"
git push origin "$TAG"
```

Pushing the new tag to GitHub will trigger GitHub workflow `ci-cd.yml`.

The workflow completely automates the release process, incl.
* Creating a release on GitHub and
* Publishing the release to [PyPi](https://pypi.org/)

## Updating the Version Number Without Preparing a Release

You can use the following commands to manually update the version number without preparing a release:

1. Update version in file `pyproject.toml` or call `poetry version <version>`
2. Call `poetry run version-check version.py --fix`

The second command will update the version number in file `version.py`.

## Selecting the Versions for SLCT and SLCR

NC contains multiple dependencies including the following

| Dependency | Defined in | Example |
|------------|------------|---------|
| `script-languages-container-tool` (SLCT) | File [pyproject.toml](https://github.com/exasol/notebook-connector/blob/main/pyproject.toml) | `exasol-script-languages-container-tool = "^1.0.0"` |
| A release of the Exasol default Script Language Container `script-languages-release` (SLCR) | File [exasol/nb_connector/nb_connector/slct_manager.py](https://github.com/exasol/notebook-connector/blob/main/exasol/nb_connector/slct_manager.py) | `SLC_RELEASE_TAG = "9.1.0"` |

Additionally, each version of the SLCR depends on a specific version of the SLCT, see the SLCR release letters and the file `pyproject.toml` used by any specific released version of the SLCR.

### Example

For the versions named in the table above

* [SLCR version 9.1.0](https://github.com/exasol/script-languages-release/releases/tag/9.1.0) in the release letter, section  "_Script-Language-Container-Tool (Exaslct)_" states "_This release uses version 1.0.0 of the container tool._"
* When clicking on the commit [60492ad](https://github.com/exasol/script-languages-release/blob/60492ade8679948ddbaddee47596c04b16959344/pyproject.toml#L28) and "Browse files", then SLCR's file [pyproject.toml](https://github.com/exasol/script-languages-release/commit/abd3c4b3fff220215ddd75ff98284e6076d44671#diff-50c86b7ed8ac2cf95bd48334961bf0530cdc77b5a56f852c5c61b89d735fd711R28) shows `exasol-script-languages-container-tool = "^1.0.0"`

In this case the dependencies shown in the table above are ✅ **valid** as NC's file `pyproject.toml` depends on the same major version of SLCT.

### General instructions

Check if the referred version of SLCR is also compatible with the version of SLCT:

1. Go to [SLCR releases](https://github.com/exasol/script-languages-release/releases)
2. Search for the SLCR version referenced in NC's file `exasol/nb_connector/slct_manager.py`
3. Check if in the SLCR release, file  `pyproject.toml`, dependency `script-languages-container-tools` has the same major version
