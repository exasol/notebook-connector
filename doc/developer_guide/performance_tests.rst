Performance Tests
*****************

NC contains performance tests for measuring the latency when accessing the
Secure Configuration Storage (SCS). The tests are using ``pytest-benchmark``
as :ref:`optional dependency <benchmark_dependency>`.

You can run the performance tests by calling Nox session ``test:performance``,
providing the pytest file as CLI argument. NC will save the results to a Json
file named ``_<file>-results.json`` in the same folder as the original Pytest
file:

.. code-block:: shell

    poetry run -- nox -s test:performance -- test/performance/benchmark.py

The results based on the initial implementation of the SCS are committed as a
baseline and for each pull request NC runs the performance tests via GitHub
workflow ``performance-checks.yml`` to identify future performance
degradation.
