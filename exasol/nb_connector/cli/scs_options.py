import re

import click

from exasol.nb_connector.secret_store import Secrets


class ScsOption:
    """
    CLI option for saving and checking values to the Secure Configuration
    Storage (SCS).

    In addition to the arguments supported by click.option() this class
    supports the following additional

    Parameters:
        scs_key:
            The related key in SCS or None if the option is not be be stored
            in the SCS.

        scs_alternative_key:
            An alternative key for options that can are optional in case another
            option is provided.

        scs_required:
            Whether this option is required to be stored in the SCS or only
            optional.
    """

    def __init__(
        self,
        *args,
        scs_key: str | None = None,
        scs_alternative_key: str | None = None,
        scs_required: bool = True,
        **kwargs,
    ):
        self._args = args
        self._kwargs = dict(kwargs)
        self.scs_key = scs_key
        self.scs_alternative_key = scs_alternative_key
        self.scs_required = scs_required

    @property
    def cli_option(self) -> str:
        return self._args[0]

    @property
    def param_name(self) -> str:
        for arg in self._args:
            if not arg.startswith("--"):
                return arg
        return re.sub(r"/--.*$", "", self.cli_option)[2:].replace("-", "_")

    def click_option(self, func):
        decorate = click.option(*self._args, **self._kwargs)
        return decorate(func)

    def needs_entry(self, scs: Secrets) -> bool:
        def has_value():
            alt = self.scs_alternative_key
            return scs.get(self.scs_key) is not None or (
                alt and scs.get(alt) is not None
            )

        return self.scs_key and self.scs_required and not has_value()

    def __repr__(self) -> str:
        cls_name = type(self).__name__
        return f"{cls_name}<{self.cli_option}>"


def click_options(scs_options: list[ScsOption]):
    def decorated(func):
        for o in reversed(scs_options):
            func = o.click_option(func)
        return func

    return decorated
