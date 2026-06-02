import exasol.nb_connector.cli.groups as groups_module


def test_scs_entrypoint_uses_scs_command_group():
    assert groups_module.scs_cli.name == "scs"


def test_ai_lab_entrypoint_uses_ai_lab_command_group():
    assert groups_module.ai_lab_cli.name == "ai-lab"
