Selecting the Versions for SLCT and SLCR
****************************************

NC contains multiple dependencies including the following

+-----------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------------------------------------------------+
| Dependency                                                                              | Defined in                                                     | Example                                               |
+=========================================================================================+================================================================+=======================================================+
| ``script-languages-container-tool`` (SLCT)                                              | File `pyproject.toml <slct_dep_>`_                             | ``exasol-script-languages-container-tool = "^1.0.0"`` |
+-----------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------------------------------------------------+
| A release of the Exasol Script Languages Containers ``script-languages-release`` (SLCR) | File `exasol/nb_connector/slct/constants.py <slc_constants_>`_ | ``SLC_RELEASE_TAG = "9.1.0"``                         |
+-----------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------------------------------------------------+

.. _slct_dep: https://github.com/exasol/notebook-connector/blob/main/pyproject.toml
.. _slc_constants: https://github.com/exasol/notebook-connector/blob/main/exasol/nb_connector/slc/constants.py

Additionally, each version of the SLCR depends on a specific version of the
SLCT, see the SLCR release letters and the file ``pyproject.toml`` used by any
specific released version of the SLCR.

Conclusion: Whenever you update the major version of
``script-languages-container-tool`` in ``pyproject.toml`` you will need to
update the referenced tag of SLCR in ``slct_manager.py``.

Example
=======

For the versions named in the table above

* `SLCR version 9.1.0 <slcr_910_>`_ in the release letter, section
  "_Script-Language-Container-Tool (Exaslct)_" states "_This release uses
  version 1.0.0 of the container tool._"

* When clicking on the commit `60492ad <slc_commit_>`_ and "Browse files", then
  SLCR's file `pyproject.toml <slc_pyproject_>`_ shows
  ``exasol-script-languages-container-tool = "^1.0.0"``

.. _slcr_910: https://github.com/exasol/script-languages-release/releases/tag/9.1.0
.. _slc_commit: https://github.com/exasol/script-languages-release/commit/abd3c4b3fff220215ddd75ff98284e6076d44671#diff-50c86b7ed8ac2cf95bd48334961bf0530cdc77b5a56f852c5c61b89d735fd711R28
.. _slc_pyproject: https://github.com/exasol/script-languages-release/blob/60492ade8679948ddbaddee47596c04b16959344/pyproject.toml#L28

In this case, the dependencies shown in the table above, are ✅ **valid** as
NC's file ``pyproject.toml`` depends on the same major version of SLCT.

General instructions
====================

Check if the referred version of SLCR is also compatible with the version of SLCT:

1. Go to `SLCR releases
   <https://github.com/exasol/script-languages-release/releases>`_.

2. Search for the SLCR version referenced in NC's file
   ``exasol/nb_connector/slc/constants.py``.

3. Check if in the SLCR release, file ``pyproject.toml``, dependency
   ``script-languages-container-tools`` has the same major version.

Impact on NC Tests
==================

Some of the tests of the Notebook Connector, especially the integration tests,
may depend on particular properties of a particular SLCR release, e.g. a
particular flavor to be present.

In consequence, updating the SLCR version potentially may require updating the
NC tests as well, e.g. the name of the flavor used in the tests.
