import luigi.configuration

from exasol.nb_connector import luigi_utils


def test_disable_luigi_worker_shutdown_handler_restores_worker_config(monkeypatch):
    config = luigi.configuration.get_config()
    section = "worker"
    option = "no_install_shutdown_handler"
    had_section = config.has_section(section)
    had_option = config.has_option(section, option)
    original_value = config.get(section, option) if had_option else None

    fake_thread = object()
    fake_main_thread = object()
    monkeypatch.setattr(luigi_utils.threading, "current_thread", lambda: fake_thread)
    monkeypatch.setattr(luigi_utils.threading, "main_thread", lambda: fake_main_thread)

    try:
        with luigi_utils.temporarily_disable_luigi_worker_shutdown_handler():
            assert config.getboolean(section, option)

        assert config.has_section(section) is had_section
        if had_option and original_value is not None:
            assert config.get(section, option) == original_value
        else:
            assert not config.has_option(section, option)
    finally:
        if had_option and original_value is not None:
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, option, original_value)
        else:
            if config.has_option(section, option):
                config.remove_option(section, option)
            if not had_section and config.has_section(section):
                config.remove_section(section)
