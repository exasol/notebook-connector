import logging
import random
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

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


def access_scs(secrets: Secrets):
    for i in range(0, 5):
        print(f'{i+1} {secrets}')
        time.sleep(0.1)

@dataclass
class Result:
    iteration: int
    key: str
    written: str
    read: str

    def __str__(self) -> str:
        if self.written == self.read:
            return (
                f'Iteration {self.iteration} successfully used key {self.key}'
                f' to write and read value {self.written}.'
            )
        return (
            f'Iteration {self.iteration} used key {self.key},'
            f' wrote {self.written}, but read {self.read}.'
        )


class AccessThread(threading.Thread):
    def __init__(self, id: str, secrets: Secrets, sleep: int = 0, iterations: int = 0):
        super().__init__(target=self.access_scs)
        self.id = id
        self._secrets = secrets
        self._sleep = sleep or random.randint(1, 10) / 100
        self._iterations = iterations or random.randint(4, 8)
        self.results: list[Result] = []

    @property
    def random_key(self) -> str:
        i = random.randint(0, 2) + 1
        return f'K{i}'

    def access_scs(self):
        for i in range(0, self._iterations):
            time.sleep(self._sleep)
            key = self.random_key
            written = self.id
            self._secrets.save(key, written)
            time.sleep(self._sleep)
            read = self._secrets.get(key)
            result = Result(i, key, written, read)
            self.results.append(result)
            LOG.info(f'thread {self.id}: {result}')

def test_multithreads(secrets):
    """
    Verify multiple threads concurrently accessing the same secret store.
    """
    threads = [AccessThread(f"T{i}", secrets) for i in range(0,20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    for t in threads:
        for r in t.results:
            assert r.written == r.read, f'Thread {t.id}: {r}'
