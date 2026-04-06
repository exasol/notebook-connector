# Hugging Face credentials UI
# This is not supposed to be used on its own.

import ipywidgets as widgets

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.config import generic


def get_hf_config(secrets: Secrets) -> widgets.Widget:
    input_rows = [
        (
            "Access token",
            widgets.Password(value=ai_lab_config.get(CKey.huggingface_token)),
            CKey.huggingface_token,
        )
    ]

    return generic.get_config(secrets, [input_rows], ["Hugging Face Access Parameters"])
