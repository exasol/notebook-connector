import sqlite3

import pytest

from exasol.secret_store import (
    InvalidPassword,
    Secrets,
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


def test_update(secrets):
    initial = "initial value"
    secrets.save("key", initial).close()
    other = "other value"
    secrets.save("key", other).close()
    assert secrets.get("key") == other


def test_wrong_password(sample_file):
    secrets = Secrets(sample_file, "correct password")
    secrets.save("key", "my value").close()
    invalid = Secrets(sample_file, "wrong password")
    with pytest.raises(InvalidPassword) as ex:
        invalid.get("key")
    assert "master password is incorrect" in str(ex.value)


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
