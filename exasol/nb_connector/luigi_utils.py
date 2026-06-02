from __future__ import annotations

import threading
from contextlib import contextmanager

import luigi.configuration

_LUIGI_WORKER_SECTION = "worker"
_LUIGI_WORKER_NO_INSTALL_SHUTDOWN_HANDLER = "no_install_shutdown_handler"


@contextmanager
def temporarily_disable_luigi_worker_shutdown_handler():
    """
    Luigi installs a SIGUSR1 worker handler by default.

    That is fine in the main thread, but Jupyter/Solara callbacks may execute in a
    non-main thread where signal registration raises ValueError.
    """
    if threading.current_thread() is threading.main_thread():
        yield
        return

    config = luigi.configuration.get_config()
    had_section = config.has_section(_LUIGI_WORKER_SECTION)
    had_option = config.has_option(
        _LUIGI_WORKER_SECTION, _LUIGI_WORKER_NO_INSTALL_SHUTDOWN_HANDLER
    )
    original_value = (
        config.get(_LUIGI_WORKER_SECTION, _LUIGI_WORKER_NO_INSTALL_SHUTDOWN_HANDLER)
        if had_option
        else None
    )

    if not had_section:
        config.add_section(_LUIGI_WORKER_SECTION)
    config.set(
        _LUIGI_WORKER_SECTION,
        _LUIGI_WORKER_NO_INSTALL_SHUTDOWN_HANDLER,
        "True",
    )
    try:
        yield
    finally:
        if had_option and original_value is not None:
            config.set(
                _LUIGI_WORKER_SECTION,
                _LUIGI_WORKER_NO_INSTALL_SHUTDOWN_HANDLER,
                original_value,
            )
        else:
            config.remove_option(
                _LUIGI_WORKER_SECTION, _LUIGI_WORKER_NO_INSTALL_SHUTDOWN_HANDLER
            )
            if not had_section:
                config.remove_section(_LUIGI_WORKER_SECTION)
