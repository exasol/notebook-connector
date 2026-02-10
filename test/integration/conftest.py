from collections.abc import Iterator
from test.utils.integration_test_utils import _setup_itde_impl
from typing import Iterator

import pytest


@pytest.fixture
def setup_itde(secrets) -> Iterator[None]:
    """
    Brings up the ITDE and takes it down when the tests are completed or failed.
    Creates a schema and saves its name in the secret store.
    The scope is per test function.
    """
    yield from _setup_itde_impl(secrets)


@pytest.fixture(scope="module")
def setup_itde_module(secrets_module) -> Iterator[None]:
    """
    Brings up the ITDE and takes it down when the tests are completed or failed.
    Creates a schema and saves its name in the secret store.
    The scope is per test module.
    """
    yield from _setup_itde_impl(secrets_module)
