import nox

# imports all nox task provided by the toolbox
from exasol.toolbox.nox.tasks import *  # pylint: disable=wildcard-import disable=unused-wildcard-import

# default actions to be run if nothing is explicitly specified with the -s option
nox.options.sessions = ["format:fix"]


@nox.session(python=False)
def start_database(session):
    session.run(
        "itde",
        "spawn-test-environment",
        "--environment-name",
        "test",
        "--database-port-forward",
        "8563",
        "--bucketfs-port-forward",
        "2580",
        "--db-mem-size",
        "8GB",
        "--nameserver",
        "8.8.8.8",
    )
