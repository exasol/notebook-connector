from unittest.mock import (
    Mock,
    call,
)

import pytest

from exasol.nb_connector.slc.slc_session import (
    ConfigurationItem,
    SlcError,
)


def configuration_item(
    secrets: Mock,
    key_prefix="SLC_P",
    session_name="Strange",
    description="SLC color",
) -> ConfigurationItem:
    return ConfigurationItem(
        secrets=secrets,
        key_prefix=key_prefix,
        session_name=session_name,
        description=description,
    )


def test_key():
    ci = configuration_item(Mock())
    assert ci.key == "SLC_P_Strange"


def test_save_success():
    secrets = Mock(get=Mock(return_value=None))
    ci = configuration_item(secrets)
    ci.save(value="xxx")
    assert secrets.save.call_args == call(ci.key, "xxx")


def test_save_failure():
    secrets = Mock(get=Mock(return_value=True))
    ci = configuration_item(secrets)
    with pytest.raises(
        SlcError,
        match="SLC color for session Strange",
    ):
        ci.save(value="xxx")


def test_value_success():
    secrets = Mock(__getitem__=Mock(return_value="some value"))
    ci = configuration_item(secrets)
    assert ci.value == "some value"


def test_value_failure():
    secrets = Mock(__getitem__=Mock(side_effect=AttributeError))
    ci = configuration_item(secrets)
    with pytest.raises(
        SlcError,
        match="does not contain an SLC color for session Strange",
    ):
        ci.value
