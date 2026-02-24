from dataclasses import dataclass
from pathlib import Path
from test.unit.cli.scs_mock import (
    ScsMock,
    ScsPatcher,
)

import pytest

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
    testee = BackendSelector(ScsMock())
    assert not testee.knows_backend
    for s in TEST_SCENARIOS:
        assert testee.matches(s.backend, s.use_itde)


@pytest.mark.parametrize(
    "backend, use_itde",
    [
        (StorageBackend.onprem, None),
        (None, True),
        (None, False),
    ],
)
def test_partial_backend_configuration(backend, use_itde):
    scs = ScsMock(backend, use_itde)
    testee = BackendSelector(scs)
    assert not testee.knows_backend
    for s in TEST_SCENARIOS:
        assert testee.matches(s.backend, s.use_itde)


@pytest.mark.parametrize("scenario", TEST_SCENARIOS)
def test_valid_backend_configuration(scenario):
    scs = ScsMock(scenario.backend, scenario.use_itde)
    testee = BackendSelector(scs)
    assert testee.knows_backend
    assert testee.backend_name == scenario.name
    for s in TEST_SCENARIOS:
        expected = (scenario.backend, scenario.use_itde) == (s.backend, s.use_itde)
        assert testee.matches(s.backend, s.use_itde) == expected


@pytest.mark.parametrize("backend", [StorageBackend.onprem, None])
def test_option_set_backend_unknown(backend, capsys, scs_patcher):
    scs_patcher.patch(backend)
    with pytest.raises(ScsCliError, match="SCS .* does not contain any backend"):
        get_option_set(Path("/fictional/scs"))


@pytest.mark.parametrize(
    "backend, use_itde",
    [
        (StorageBackend.saas, None),
        (StorageBackend.onprem, True),
        (StorageBackend.onprem, False),
    ],
)
def test_option_set_valid(backend, use_itde, scs_patcher):
    scs_patcher.patch(backend, use_itde)
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


@pytest.mark.parametrize("scenario", TEST_SCENARIOS)
def test_check_failure(scenario, scs_patcher, capsys):
    options = [
        o.cli_option(full=True) for o in scenario.params if o.scs_key and o.scs_required
    ]
    scs_patcher.patch(scenario.backend, scenario.use_itde)
    expected = f"{len(options)} options are not yet configured: {', '.join(options)}"
    testee = get_option_set(Path("/fictional/scs"))
    with pytest.raises(ScsCliError, match=expected):
        testee.check()


@pytest.mark.parametrize("scenario", TEST_SCENARIOS)
def test_check_success(scenario, scs_patcher, capsys):
    options = [o for o in scenario.params if o.scs_key and o.scs_required]
    scs_mock = scs_patcher.patch(scenario.backend, scenario.use_itde)
    for o in options:
        scs_mock.save(o.scs_key, "value")
    get_option_set(Path("/fictional/scs")).check()
    assert (
        f"Configuration is complete for an Exasol {scenario.name} instance"
        in capsys.readouterr().out
    )
