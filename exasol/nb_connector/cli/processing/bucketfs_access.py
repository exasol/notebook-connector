import random
import string
import traceback

import exasol.bucketfs as bfs

import exasol.nb_connector.cli.reporting as report
from exasol.nb_connector.cli.processing.option_set import ScsCliError
from exasol.nb_connector.connections import open_bucketfs_location
from exasol.nb_connector.secret_store import Secrets


def random_string(length: int = 10) -> str:
    return "".join(random.choice(string.ascii_uppercase) for _ in range(length))


def random_file_name(other_than: list[str]) -> str:
    result = None
    while result is None or result in other_than:
        infix = random_string()
        result = f"probe-{infix}.txt"
    return result


def verify_bucketfs_access(scs: Secrets) -> None:
    bfs_root = open_bucketfs_location(scs)
    existing = [f.name for f in bfs_root.iterdir()]
    file = bfs_root / random_file_name(other_than=existing)
    content = random_string(length=100)
    try:
        file.write(content.encode())
        actual = bfs.as_string(file.read())
        if actual != content:
            raise ScsCliError(f'{file} contains "{actual}" instead of "{content}".')
        report.success(
            "Access to the BucketFS of the configured database instance was successful."
        )
    except Exception as ex:
        stacktrace = traceback.format_exc()
        raise ScsCliError(f"Couldn't access the BucketFS: {stacktrace}") from ex
    finally:
        file.rm()
