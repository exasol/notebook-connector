import exasol.nb_connector.cli.main as main_module


def test_scs_main_invokes_scs_cli(monkeypatch):
    called = []

    monkeypatch.setattr(main_module, "scs_cli", lambda: called.append("scs"))

    main_module.scs_main()

    assert called == ["scs"]


def test_ai_lab_main_invokes_ai_lab_cli(monkeypatch):
    called = []

    monkeypatch.setattr(main_module, "ai_lab_cli", lambda: called.append("ai-lab"))

    main_module.ai_lab_main()

    assert called == ["ai-lab"]
