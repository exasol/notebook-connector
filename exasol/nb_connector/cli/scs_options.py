import click

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey


class ScsArgument:
    """
    Represents a CLI argument for the SCS command which should not be
    stored into the SCS.
    """

    def __init__(self, *args, scs_key: CKey | None = None, **kwargs):
        self._args = args
        self.scs_key = scs_key
        self._kwargs = dict(kwargs)

    def decorate(self, func):
        decorator = click.argument(*self._args, **self._kwargs)
        return decorator(func)


class ScsOption(ScsArgument):
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
        scs_key: CKey | None = None,
        scs_alternative_key: CKey | None = None,
        scs_required: bool = True,
        **kwargs,
    ):
        super().__init__(*args, scs_key=scs_key, **kwargs)
        self.scs_key = scs_key
        self.scs_alternative_key = scs_alternative_key
        self.scs_required = scs_required

    def decorate(self, func):
        decorator = click.option(*self._args, **self._kwargs)
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


def click_options(scs_options: list[ScsOption]):
    def multi_decorator(func):
        for o in reversed(scs_options):
            func = o.decorate(func)
        return func

    return multi_decorator
