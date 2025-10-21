"""
Wrappers for adding custom properties to click parameters, e.g. SCS key.
"""

import getpass
import os
import re
from abc import abstractmethod
from typing import Any

import click

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.cli import reporting as report
from exasol.nb_connector.secret_store import Secrets


class ScsParam:
    """
    Abstract base class for ScsArgument and ScsOption.
    """

    def __init__(self, scs_key: CKey | None = None, **kwargs):
        self.scs_key = scs_key
        self._kwargs = dict(kwargs)

    def cli_option(self, full=False) -> str:
        return ""

    @property
    def arg_name(self) -> str:
        return ""

    def needs_entry(self, scs: Secrets) -> bool:
        return False

    @property
    def default(self) -> Any:
        return self._kwargs.get("default")

    def displayed_value(self, scs: Secrets) -> str | None:
        return None

    @abstractmethod
    def decorate(self, func):
        """
        This method is to be called when decorating the functions in the
        actual CLI declaration.
        """
        pass


class ScsArgument(ScsParam):
    """
    Represents a CLI argument for the SCS command.
    """

    def __init__(self, name: str, scs_key: CKey | None = None, **kwargs):
        super().__init__(scs_key, **kwargs)
        self.name = name

    @property
    def arg_name(self) -> str:
        return self.name

    def decorate(self, func):
        """
        This method is to be called when decorating the functions in the
        actual CLI declaration. Hence, ScsArgument calls click.argument()
        under the hood.
        """
        decorator = click.argument(self.name, **self._kwargs)
        return decorator(func)


class ScsOption(ScsParam):
    """
    CLI option for saving and checking values to the Secure Configuration
    Storage (SCS).

    In addition to the args supported by click.option() this class supports
    the following additional

    Parameters:
        scs_key:
            The related key in SCS or None if the option is not be stored in
            the SCS. ScsArgument For exaemple, ScsArgument scs_file is not to
            be stored in the SCS.

        scs_alternative_key:
            An alternative key for ScsOptions that are optional in case
            another option is provided. For example, for --saas-database-id
            you can specify --saas-database-name instead and vice-versa.

        scs_required:
            Whether this option is required to be stored in the SCS or only
            optional. This applies to --ssl-cert-path, for example.
    """

    def __init__(
        self,
        cli_option,
        *args,
        scs_key: CKey | None = None,
        scs_alternative_key: CKey | None = None,
        scs_required: bool = True,
        default: Any = None,
        help: str | None = None,
        **kwargs,
    ):
        _help = help if default is None else f"{help} [default: {default}]"
        super().__init__(scs_key=scs_key, help=_help, default=None, **kwargs)
        self._cli_option = cli_option
        self._args = args
        self.scs_alternative_key = scs_alternative_key
        self.scs_required = scs_required
        self._default = default

    def cli_option(self, full=False) -> str:
        raw = self._cli_option
        return raw if full else re.sub(r"/--.*$", "", raw)

    @property
    def default(self) -> Any:
        return self._default

    @property
    def arg_name(self) -> str:
        for arg in self._args:
            if not arg.startswith("--"):
                return arg
        name = self.cli_option()
        return name[2:].replace("-", "_")

    def decorate(self, func):
        """
        This method is to be called when decorating the functions in the
        actual CLI declaration. ScsOption calls click.option().
        """
        decorator = click.option(
            self._cli_option,
            *self._args,
            **self._kwargs,
            show_default=True,
        )
        return decorator(func)

    def displayed_value(self, scs: Secrets) -> str | None:
        return scs.get(self.scs_key) if self.scs_key else None

    def needs_entry(self, scs: Secrets) -> bool:
        """
        Return True, if the current option is configured to be saved to
        the SCS but SCS does not yet contain a value.
        """

        def has_value() -> bool:
            if not self.scs_key:
                return False
            if scs.get(self.scs_key) is not None:
                return True
            if alt := self.scs_alternative_key:
                return scs.get(alt) is not None
            return False

        return bool(self.scs_key) and self.scs_required and not has_value()

    def __repr__(self) -> str:
        cls_name = type(self).__name__
        return f"{cls_name}<{self.cli_option(full=True)}>"


class ScsSecretOption(ScsOption):
    """
    Represents a CLI option to be stored into SCS.
    """

    def __init__(
        self,
        name: str,
        envvar: str,
        prompt: str,
        scs_key: CKey,
        *args,
        metavar: str = "PASSWORD",
        **kwargs,
    ):
        super().__init__(
            name,
            *args,
            metavar=metavar,
            type=bool,
            is_flag=True,
            help=f"{prompt}  [env var: {envvar}]",
            scs_key=scs_key,
            **kwargs,
        )
        self.envvar = envvar
        self.prompt = prompt
        self.name = name

    def displayed_value(self, scs: Secrets) -> str | None:
        return "****" if self.scs_key and scs.get(self.scs_key) else None

    def get_secret(self, interactive: Any) -> str:
        """
        If interactive is True and the related environment variable is not
        set then ask for the secret interactively.
        """
        if value := os.getenv(self.envvar):
            report.info(f"Reading {self.name} from environment variable {self.envvar}.")
            return value
        if not interactive:
            return ""
        prompt = f"{self.prompt} (option {self.name}): "
        return getpass.getpass(prompt)


def add_params(scs_options: list[ScsArgument]):
    def multi_decorator(func):
        for o in reversed(scs_options):
            func = o.decorate(func)
        return func

    return multi_decorator
