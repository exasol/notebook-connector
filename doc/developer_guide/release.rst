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
