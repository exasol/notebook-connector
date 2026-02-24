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
