Command Line Interface (CLI) Examples
#####################################

The Notebook Connector ships two CLI tools: ``ai-lab`` and ``scs``.
See their dedicated pages for the full option reference:

* :doc:`ai-lab-cli` – start JupyterLab and deploy bundled notebooks.
* :doc:`scs-cli` – create and manage the Secure Configuration Storage.

This page focuses on end-to-end ``ai-lab`` workflows.  For CLI examples that
create, inspect, or validate SCS files directly, see :doc:`scs-cli`.

Typical AI Lab Workflow After Configuration
*******************************************

The following steps show how to start from an already configured environment,
deploy the bundled notebooks into a local directory, and then launch
JupyterLab.  Create or update the SCS separately via :doc:`scs-cli`.

**Step 1 – Copy the Bundled Notebooks to a Target Directory**

Use ``ai-lab deploy-notebooks`` when you want a local copy of the packaged
notebooks in a directory that you manage yourself, without starting JupyterLab
through Notebook Connector.  This is useful when you already run your own
JupyterLab environment and simply want to use the bundled notebooks there.

.. code-block:: shell

    ai-lab deploy-notebooks --target-dir ~/work/notebooks

**Step 2 – Launch JupyterLab on the Default Port**

``ai-lab start`` launches JupyterLab and copies the bundled notebooks into the
notebook root directory if they are not present yet.

.. code-block:: shell

    ai-lab start --notebook-dir ~/work/notebooks

**Step 3 – Launch JupyterLab With Remote Access or a Custom Port**

``ai-lab start`` launches a JupyterLab server and makes the bundled Exasol
notebooks available under the directory specified by ``--notebook-dir``.
The ``--port`` flag lets you pick a custom port if the default (49494) is
already in use.  You do not pass the SCS file to ``ai-lab start`` itself;
the notebooks opened inside JupyterLab work with the SCS separately.

.. code-block:: shell

    ai-lab start --notebook-dir ~/work/notebooks --port 9999 --ip 0.0.0.0 --no-browser
