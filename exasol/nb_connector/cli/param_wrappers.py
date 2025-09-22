"""
Wrappers for adding custom properties to click parameters, e.g. SCS key.
"""

import click

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey


class ScsArgument:
    """
    Represents a CLI argument for the SCS command.
    """

    def __init__(self, *args, scs_key: CKey | None = None, **kwargs):
        self._args = args
        self.scs_key = scs_key
        self._kwargs = dict(kwargs)

    def decorate(self, func):
        """
        This method is to be called when decorating the functions in the
        actual CLI declaration. Hence, ScsArgument calls click.argument()
        under the hood.
        """
        decorator = click.argument(*self._args, **self._kwargs)
        return decorator(func)


class ScsOption(ScsArgument):
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
        *args,
        scs_key: CKey | None = None,
        scs_alternative_key: CKey | None = None,
        scs_required: bool = True,
        get_default_from: str | None = None,
        **kwargs,
    ):
        super().__init__(*args, scs_key=scs_key, **kwargs)
        self.scs_alternative_key = scs_alternative_key
        self.scs_required = scs_required
        self.get_default_from = get_default_from

    def decorate(self, func):
        """
        This method is to be called when decorating the functions in the
        actual CLI declaration. ScsOption calls click.option().
        """
        decorator = click.option(
            *self._args,
            **self._kwargs,
            show_default=True,
        )
        return decorator(func)


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
        metavar: str = "PASSWORD",
    ):
        super().__init__(
            name,
            metavar=metavar,
            type=bool,
            is_flag=True,
            help=f"{prompt}  [env var: {envvar}]",
            scs_key=scs_key,
        )
        self.envvar = envvar
        self.prompt = prompt
        self.name = name


def add_params(scs_options: list[ScsArgument]):
    def multi_decorator(func):
        for o in reversed(scs_options):
            func = o.decorate(func)
        return func

    return multi_decorator
