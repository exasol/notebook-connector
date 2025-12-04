:octicon:`tools` Developer Guide
################################

How to Release?
***************

Creating a new release of the NC requires 3 steps

1. Prepare the release

2. Merge your pull request to the default branch

3. Trigger the release process

.. code-block:: shell

    poetry run -- nox -s release:prepare -- --type {major,minor,patch}
    poetry run -- nox -s release:trigger

For further information, please refer to section `How to Release
<https://exasol.github.io/python-toolbox/main/user_guide/features/creating_a_release.html>`_
in the PTB's User Guide.

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


UI Tests
********

NC's UI tests are using ``ipwidgets`` which depends on `solara
<https://solara.dev/>`_. There is also a `playwright pytest-plugin
<https://pypi.org/project/pytest-playwright/>`_ but NC does not have an
explicit python dependency to it.

Solara is able to create snapshots of the actual displayed UI and to compare
the snapshot with an expectation.

NC uses the following directories for storing the screenshots:

* Folder ``ui_snapshots/`` reference (aka. expected) screenshots
* Folder ``test-results/`` actual screenshots, excluded in ``.gitignore``

Solara only keeps the actual screenshot if different from the expected.


Setup and Execution

To run UI tests using ``Playwright``, follow these steps to ensure all
dependencies are installed and snapshots are updated correctly.

1. **Install Playwright browser binaries**

   This command installs the required browser (Chromium) for Playwright:

   .. code-block:: bash

      playwright install chromium

2. **Install system dependencies for Playwright**

   This is necessary especially on Linux systems to ensure all required libraries are available:

   .. code-block:: bash

      playwright install-deps

3. **Run UI tests and update Solara snapshots**

   Use the following command to run UI tests and update the reference
   (aka. expected) snapshots used for visual comparison by ``solara``:

   .. code-block:: bash

      pytest test/integration/ui/*.py --solara-update-snapshots

   This will overwrite existing snapshots with new ones generated during the test.


Different Categories of UI Test Cases
=====================================

The UI tests with solara and playwright come in multiple categories, differing
in:

* In which folder are the tests located?
* Which fixtures are used?
* Can they take screenshots?
* Can they execute `store magic <https://ipython.readthedocs.io/en/stable/config/extensions/storemagic.html>`_?
* What is the return value of ``IPython.get_ipython()``?

.. list-table:: Categories of UI tests
   :header-rows: 1
   :stub-columns: 1

   * -
     - UI unit tests
     - Solara Tests with Fixtures
     - Visual UI Tests
   * - Located in folder
     - ``test/unit/ui/``
     - ``test/unit/ui/``
     - ``test/integration/ui/``
   * - Fixtures
     - none
     - ``kernel_context`` ``no_kernel_context``
     -  ``solara_test`` ``page_session`` ``assert_solara_snapshot``
   * - Take Screenshots?
     - no
     - no
     - yes
   * - Execute Store magic?
     - no (patching ``get_ipython`` is possible)
     - no
     - no
   * - Return value of ``IPython .get_ipython()``
     - ``None``, but can be patched for verifying the call to store magic
     - ``None``, tests use ipywidgets and fixture ``kernel_context``
     - ``None``, tests use playwright and solara
   * - Example
     - ``test_access_store_ui _store_read_and_write``
     - ``test_notebook_widget``
     - ``test_widget_button_solara``
