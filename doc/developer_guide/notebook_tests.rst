Tests for Jupyter Notebooks
===========================

File ``nb_tests.yaml`` contains the definition of the tests for Jupyter
Notebooks in multiple groups. Each group of tests can be selected by
specifying a *selector*, which is identical to the top-level key in the Yaml
file:

* ``notebooks-generic``
* ``gpu``

The tests are run in the CI and guarded by two dedicated manual approvals in
addition to the general manual approval for running the *Slow checks*.

* Each test group may contain  ``jobs`` or nested children ``groups``.
* Each group may define attribute defaults for the contained jobs,
  e.g. ``runner``.
* Each nested group and each job can overide one or multiple of these
  attributes.

In the following example

* The job for file ``test_a.py`` defines a custom name
* The job for file ``test_b.py`` overrides the group's default runner ``R1`` by ``R2``.

.. code-block:: yaml

    top-level-group-a1:
      runner: R1
      require_success: true
      jobs:
        - file: test_a.py
          name: "Special Name"
        - file: test_b.py
          runner: R2

Please note the attribute ``require_success`` which can be ``true`` or ``false``.

If a test with ``require_success: false`` fails, the CI will report it but
still allow merging a pull request to the default branch.

The name of each test job is derived from the file name by stripping off
prefix ``test_`` and suffix ``.py``, replacing underscores ``_`` by spaces and
capitalizing the words with ``.title()``. Alternatively you can specify a name
with attribute ``name``.
