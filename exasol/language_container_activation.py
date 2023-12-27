from typing import Dict
import re

from exasol.secret_store import Secrets

ACTIVATION_KEY_PREFIX = "language_container_activation_"


def get_activation_sql(conf: Secrets) -> str:
    """
    Merges multiple language container activation commands found in the secret
    store and returns a unified command. The resulting activation command will
    include the union of script languages found in different commands.

    For details on how an activation command may look like please refer to
    https://docs.exasol.com/db/latest/database_concepts/udf_scripts/adding_new_packages_script_languages.htm

    The secret store entries containing language activation commands should
    have keys with a common prefix. This prefix is defined in ACTIVATION_KEY_PREFIX.

    The language container activation commands are expected to have overlapping
    sets of script languages. The urls of script languages with the same alias
    found in multiple activation commands should be identical, otherwise a
    RuntimeException will be raised.
    """

    merged_langs: Dict[str, str] = {}
    pattern = re.compile(
        r"\A\s*ALTER\s+SESSION\s+SET\s+SCRIPT_LANGUAGES" r"\s*=\s*'(.+?)'\s*;?\s*\Z",
        re.IGNORECASE,
    )
    # Iterate over all entries that look like language container activation commands.
    for key, value in conf.items():
        if key.startswith(ACTIVATION_KEY_PREFIX):
            # Extract language definitions from the activation command
            match = pattern.match(value)
            if match is not None:
                # Iterate over script languages
                all_languages = match.group(1)
                for lang_definition in all_languages.split():
                    alias, lang_url = lang_definition.split("=", maxsplit=1)
                    # If this language alias has been encountered before, the url
                    # must be identical, otherwise the merge fails.
                    if alias in merged_langs:
                        if merged_langs[alias].casefold() != lang_url.casefold():
                            error = (
                                "Unable to merge multiple language container activation commands. "
                                f"Found incompatible definitions for the language alias {alias}."
                            )
                            raise RuntimeError(error)
                    else:
                        merged_langs[alias] = lang_url

    # Build and return a new SQL command for merged language container activation.
    merged_langs_str = " ".join(f"{key}={value}" for key, value in merged_langs.items())
    return f"ALTER SESSION SET SCRIPT_LANGUAGES='{merged_langs_str}';"
