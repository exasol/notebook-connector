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
    slc_name="STRANGE",
    description="color",
) -> ConfigurationItem:
    return ConfigurationItem(
        secrets=secrets,
        key_prefix=key_prefix,
        slc_name=slc_name,
        description=description,
    )


def test_key():
    ci = configuration_item(Mock())
    assert ci.key == "SLC_P_STRANGE"


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
        match="color for SLC name STRANGE",
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
        match="does not contain a color for SLC name STRANGE",
    ):
        ci.value
