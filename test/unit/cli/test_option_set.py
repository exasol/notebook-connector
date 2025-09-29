from dataclasses import dataclass
from pathlib import Path
from test.unit.cli.scs_mock import (
    scs_mock,
    ScsPatcher,
)

import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.cli.options import (
    DOCKER_DB_OPTIONS,
    ONPREM_OPTIONS,
    SAAS_OPTIONS,
)
from exasol.nb_connector.cli.param_wrappers import ScsArgument
from exasol.nb_connector.cli.processing import option_set
from exasol.nb_connector.cli.processing.option_set import (
    SELECT_BACKEND_OPTION,
    USE_ITDE_OPTION,
    BackendSelector,
    OptionSet,
    ScsCliError,
    get_option_set,
)


@pytest.fixture
def scs_patcher(monkeypatch):
    return ScsPatcher(monkeypatch, module=option_set)


@dataclass
class Scenario:
    name: str
    backend: StorageBackend
    use_itde: bool
    params: list[ScsArgument]


TEST_SCENARIOS = [
    Scenario("SaaS", StorageBackend.saas, True, SAAS_OPTIONS),
    Scenario("SaaS", StorageBackend.saas, False, SAAS_OPTIONS),
    Scenario("Docker", StorageBackend.onprem, True, DOCKER_DB_OPTIONS),
    Scenario("on-premise", StorageBackend.onprem, False, ONPREM_OPTIONS),
]


def test_empty_backend_configuration():
    testee = BackendSelector(scs_mock())
    assert not testee.knows_backend
    assert not testee.knows_itde_usage
    assert not testee.is_valid
    for s in TEST_SCENARIOS:
        assert testee.allows(s.backend, s.use_itde)


@pytest.mark.parametrize(
    "backend, use_itde",
    [
        (StorageBackend.saas, None),
        (StorageBackend.onprem, None),
        (None, True),
        (None, False),
    ],
)
def test_partial_backend_configuration(backend, use_itde):
    scs = scs_mock(backend, use_itde)
    testee = BackendSelector(scs)
    assert testee.knows_backend == (backend is not None)
    assert testee.knows_itde_usage == (use_itde is not None)
    assert not testee.is_valid
    for s in TEST_SCENARIOS:
        assert testee.allows(s.backend, s.use_itde)


@pytest.mark.parametrize("scenario", TEST_SCENARIOS)
def test_valid_backend_configuration(scenario):
    scs = scs_mock(scenario.backend, scenario.use_itde)
    testee = BackendSelector(scs)
    assert testee.knows_backend
    assert testee.knows_itde_usage
    assert testee.backend_name == scenario.name
    assert testee.use_itde == scenario.use_itde
    assert testee.is_valid
    for s in TEST_SCENARIOS:
        expected = scenario == s
        assert testee.allows(s.backend, s.use_itde) == expected


def test_option_set_backend_unknown(capsys, scs_patcher):
    scs_patcher.patch()
    actual = get_option_set(Path("/fictional/scs"))
    assert actual is None
    message = "Error: SCS /fictional/scs does not contain any backend."
    assert message in capsys.readouterr().out


def test_option_set_use_itde_unknown(capsys, scs_patcher):
    scs_patcher.patch(StorageBackend.saas)
    actual = get_option_set(Path("/fictional/scs"))
    assert actual is None
    message = "does not contain whether to use an Exasol Docker instance"
    assert message in capsys.readouterr().out


def test_option_set_valid(scs_patcher):
    scs_patcher.patch(StorageBackend.saas, True)
    actual = get_option_set(Path("/fictional/scs"))
    assert isinstance(actual, OptionSet)


@pytest.mark.parametrize("scenario", TEST_SCENARIOS)
def test_find_option(scenario, scs_patcher):
    scs_patcher.patch(scenario.backend, scenario.use_itde)
    testee = get_option_set(Path("/fictional/scs"))
    assert testee.options == [SELECT_BACKEND_OPTION, USE_ITDE_OPTION] + scenario.params
    actual = [testee.find_option(p.arg_name) for p in scenario.params]
    assert actual == scenario.params


def test_find_unknown_option(scs_patcher):
    scs_patcher.patch(StorageBackend.saas, True)
    testee = get_option_set(Path("/fictional/scs"))
    with pytest.raises(ScsCliError):
        testee.find_option("unknown_arg")


def test_dynamic_defaults(scs_patcher, capsys):
    scs_patcher.patch(StorageBackend.onprem, False)
    testee = get_option_set(Path("/fictional/scs"))
    actual = testee.set_dynamic_defaults(
        {
            "bucketfs_host": "some-host",
            "bucketfs_port": 9999,
            "bucketfs_host_internal": None,
            "bucketfs_port_internal": None,
        }
    )
    output = capsys.readouterr().out
    for infix in ["host", "port"]:
        a = f"bucketfs_{infix}"
        b = f"bucketfs_{infix}_internal"
        assert actual[a] == actual[b]
        a = a.replace("_", "-")
        b = b.replace("_", "-")
        assert f"Using --{a} as default for --{b}" in output


@pytest.mark.parametrize("scenario", TEST_SCENARIOS)
def test_check_failure(scenario, scs_patcher, capsys):
    options = [
        o.cli_option(full=True) for o in scenario.params if o.scs_key and o.scs_required
    ]
    scs_patcher.patch(scenario.backend, scenario.use_itde)
    testee = get_option_set(Path("/fictional/scs"))
    assert not testee.check()
    assert capsys.readouterr().out == (
        f"Error: {len(options)} options are not"
        f" yet configured: {', '.join(options)}.\n"
    )


@pytest.mark.parametrize("scenario", TEST_SCENARIOS)
def test_check_success(scenario, scs_patcher, capsys):
    options = [o for o in scenario.params if o.scs_key and o.scs_required]
    scs_mock = scs_patcher.patch(scenario.backend, scenario.use_itde)
    for o in options:
        scs_mock.save(o.scs_key, "value")
    testee = get_option_set(Path("/fictional/scs"))
    assert testee.check()
    assert capsys.readouterr().out == (
        f"Configuration is complete for an Exasol {scenario.name} instance.\n"
    )
