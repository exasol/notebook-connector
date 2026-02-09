import sqlite3
from pathlib import Path

import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import (
    InvalidPassword,
    Secrets,
)


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
    range(0, 20):
    old implementation: 0.24 seconds
    new implementation 7.9 seconds (3% speed)
    """
    for i in range(0, 20):
        key = f"key-{i}"
        value = f"value {i}"
        secrets.save(key, value)
        assert value == secrets.get(key)
