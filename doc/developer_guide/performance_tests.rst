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

