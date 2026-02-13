import contextlib
import logging
import sqlite3
import threading
from pathlib import Path
from unittest.mock import Mock

import pytest
import sqlcipher3.dbapi2 as sqlcipher
import tenacity

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import (
    InvalidPassword,
    Secrets,
)

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    return tmp_path / "sample_database.db"


@pytest.mark.skip(
    """This test case is no longer valid.  The constructur will
always create the file on the fly if it doesn't exist."""
)
def test_no_database_file(secrets):
    assert not secrets.db_file.exists()


def test_database_file_created(secrets):
    assert secrets.get("any_key") is None
    assert secrets.db_file.exists()


def test_value(secrets):
    value = "my value"
    secrets.save("key", value).close()
    assert secrets.get("key") == value


def test_db_user(secrets):
    name = "Beethoven"
    secrets.save(CKey.db_user, name).close()
    assert secrets.get(CKey.db_user) == name


def test_dup_values(secrets):
    # Here we test that it is possible to save the same value with different keys
    value = "my value"
    secrets.save("key1", value).save("key2", value).close()
    assert secrets.get("key1") == value
    assert secrets.get("key2") == value


def test_default_value(secrets):
    default_value = "my_value"
    assert secrets.get("unknown_value", default_value) == default_value


def test_update(secrets):
    initial = "initial value"
    secrets.save("key", initial).close()
    other = "other value"
    secrets.save("key", other).close()
    assert secrets.get("key") == other


def test_wrong_password(sample_file):
    secrets = Secrets(sample_file, "correct password")
    secrets.save("key", "my value").close()
    with pytest.raises(InvalidPassword, match="master password is incorrect"):
        Secrets(sample_file, "wrong password")


def test_plain_access_fails(sample_file):
    """
    This test sets up a secret store, secured by a master password and
    verifies that plain access to the secret store using sqlite3 without
    encryption raises a DatabaseError.
    """
    secrets = Secrets(sample_file, "correct password")
    secrets.save("key", "my value").close()
    con = sqlite3.connect(sample_file)
    cur = con.cursor()
    with pytest.raises(sqlite3.DatabaseError) as ex:
        cur.execute("SELECT * FROM sqlite_master")
    cur.close()
    assert str(ex.value) == "file is not a database"


def test_access_key_as_attribute(secrets):
    secrets.save("key", "value")
    assert secrets.key == "value"


def test_access_non_existing_key_as_attribute(secrets):
    with pytest.raises(AttributeError) as ex:
        secrets.non_existing_key
    assert str(ex.value) == 'Unknown key "non_existing_key"'


@pytest.fixture
def secrets_with_names(secrets):
    secrets.save("electrician", "John")
    secrets.save("musician", "Linda")
    secrets.save("prime_minister", "Rishi")
    return secrets


def test_keys_iterator(secrets_with_names):
    professions = list(secrets_with_names.keys())
    assert professions == ["electrician", "musician", "prime_minister"]


def test_values_iterator(secrets_with_names):
    people = list(secrets_with_names.values())
    assert people == ["John", "Linda", "Rishi"]


def test_items_iterator(secrets_with_names):
    people_and_prof = list(secrets_with_names.items())
    assert people_and_prof == [
        ("electrician", "John"),
        ("musician", "Linda"),
        ("prime_minister", "Rishi"),
    ]


def test_remove_key(secrets):
    secrets.save("key", "value")
    secrets.remove("key")
    assert secrets.get("key") is None


def test_remove_db_schema(secrets):
    secrets.save(CKey.db_schema, "the_schema")
    secrets.remove(CKey.db_schema)
    assert secrets.get(CKey.db_schema) is None


# todo: benchmark
def test_performance(secrets):
    """
    duration of range(0, 20) in seconds:
    0.24 old implementation
    7.90 separate connection (32 times slower)
    0.14 connection pool (runtime 58 %)
    """
    for i in range(0, 20):
        key = f"key-{i}"
        value = f"value {i}"
        secrets.save(key, value)
        assert value == secrets.get(key)


class AccessThread(threading.Thread):
    def __init__(self, id: int, secrets: Secrets):
        super().__init__(target=self.access_scs)
        self.id = f"T{id}"
        self._secrets = secrets

    def access_scs(self):
        for i in range(0, 20):
            self._secrets.save("key", self.id)
            dict(self._secrets.items())


@contextlib.contextmanager
def not_raises(exception):
    try:
        yield
    except exception:
        raise pytest.fail(f"Did raise {exception}")


@pytest.mark.slow
def test_multithreads(secrets):
    """
    Verify multiple threads concurrently accessing the same secret store.
    """
    threads = [AccessThread(i, secrets) for i in range(0, 200)]
    with not_raises(Exception):
        for t in threads:
            t.start()
        for t in threads:
            t.join()


def cursor_mock(side_effect):
    mock = Mock()
    mock.execute.side_effect = side_effect
    return mock


@pytest.mark.parametrize(
    "side_effect, expected",
    [
        (Exception("message"), Exception),
        (sqlcipher.OperationalError("any"), sqlcipher.OperationalError),
    ],
)
def test_execute_no_retry(secrets, side_effect, expected):
    cursor = cursor_mock(side_effect)
    with pytest.raises(expected):
        secrets._execute("statement", cur=cursor)


DATABASE_LOCKED = sqlcipher.OperationalError("database is locked")


def test_execute_retry_once(secrets):
    cursor = cursor_mock([DATABASE_LOCKED, None])
    secrets._execute("statement", cur=cursor)
    assert cursor.execute.call_count == 2


def test_execute_retry_timeout(secrets):
    cursor = cursor_mock(DATABASE_LOCKED)
    with pytest.raises(tenacity.RetryError):
        secrets._execute("statement", cur=cursor)
    assert cursor.execute.call_count == 5
