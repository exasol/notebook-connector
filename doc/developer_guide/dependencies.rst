Dependencies
************

NC has dependencies in multiple different groups

* Mandatory productive
* Optional productive (aka. "extras")
* Mandatory dev dependencies
* Optional dev dependencies

Mandatory Productive Dependencies
=================================

These dependencies are mandatory, always installed, and are required for
productive usage of NC, for example ``exasol-saas-api``.

In file ``pyproject.toml`` these are in group ``[project]``, ``dependencies``.

Optional Productive Dependencies (aka. "extras")
================================================

These dependencies are optional, but required for specific productive
scenarios, for example ``sqlalchemy``.

In file ``pyproject.toml`` these are in group
``[project.optional-dependencies]``.

See :ref:`install_nc`.

Mandatory Dev Dependencies
==========================

These dependencies are only required during development, for example
``pytest``.  They are installed when using ``poetry install`` but not
contained in the package built by this project and published on pypi.

In file ``pyproject.toml`` these are in group
``[tool.poetry.group.dev.dependencies]``.


Optional Dev Dependencies
=========================

These dependencies are only required for *specific tasks* during development,
e.g. when updating performance measurements.

They are installed when using ``poetry install --with <dep>``, see also
`Poetry docs <pep_735_>`_.

.. _pep_735: https://python-poetry.org/docs/managing-dependencies/#group-include-pep735

Currently there is only one such group, called ``performance``.  In file
``pyproject.toml`` the group is defined like

.. literalinclude:: ../../pyproject.toml
   :language: toml
   :start-at: [tool.poetry.group.performance]
   :end-at: # end of optional dev dependencies

`Pytest Benchmark <pytest-benchmark_>`_ is used for measuring the performance
when accessing the Secure Configuration Storage. It is added as optional dev
dependency to avoid interferences as reported in `project Pyexasol
<pyexasol_benchmark_>`_.

.. _pytest-benchmark: https://pytest-benchmark.readthedocs.io/en/latest/
.. _pyexasol_benchmark:
   https://exasol.github.io/pyexasol/master/developer_guide.html#performance-tests
