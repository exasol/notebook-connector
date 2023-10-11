import pytest
from exasol.secret_store import InvalidPassword, Secrets
from sqlcipher3 import dbapi2 as sqlcipher


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
