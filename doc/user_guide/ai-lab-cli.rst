:octicon:`terminal` AI Lab Command Line Interface
#################################################

Notebook Connector installs the ``ai-lab`` command line interface for working
with the bundled Jupyter notebooks.

The top-level ``ai-lab`` command exposes exactly two subcommands:

* ``start`` starts JupyterLab and deploys the bundled notebooks into the
  notebook root directory if they are not present yet.
* ``deploy-notebooks`` copies the bundled notebooks to a target directory
  without starting JupyterLab.

Help
****

Use ``--help`` on the top-level command or any subcommand to inspect the
current option set.

.. code-block:: shell

    ai-lab --help
    ai-lab start --help
    ai-lab deploy-notebooks --help

Command ``start``
*****************

Command ``start`` launches JupyterLab by invoking ``python -m jupyter lab``.
Before JupyterLab starts, Notebook Connector copies the bundled notebooks into
the notebook root directory and leaves existing files unchanged.

.. code-block:: shell

    ai-lab start

Common options:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Option
     - Meaning
   * - ``--port``
     - JupyterLab listen port. Default: ``8888``.
   * - ``--ip``
     - Bind address. Default: ``localhost``. Use ``0.0.0.0`` for remote
       access.
   * - ``--notebook-dir``
     - Notebook root directory. If omitted, the current working directory is
       used. Missing directories are created.
   * - ``--no-browser``
     - Prevent JupyterLab from opening in the default browser.

Examples:

.. code-block:: shell

    ai-lab start --port 9999 --ip 0.0.0.0
    ai-lab start --notebook-dir ~/work/notebooks --no-browser

Failure cases:

* If JupyterLab is not installed, the command exits with an install hint for
  ``poetry install --all-extras``.
* If ``--notebook-dir`` points to a file instead of a directory, the command
  exits with an error.

Command ``deploy-notebooks``
****************************

Command ``deploy-notebooks`` copies the packaged notebooks to a target
directory and reports how many files were copied or skipped.

.. code-block:: shell

    ai-lab deploy-notebooks --target-dir ~/notebooks

Options:

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Option
     - Meaning
   * - ``--target-dir``
     - Required destination directory.
   * - ``--overwrite`` / ``--no-overwrite``
     - Overwrite existing files in the target directory. Default:
       ``--no-overwrite``.

If ``--overwrite`` is not set, existing files are preserved and counted as
skipped.
