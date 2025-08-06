from pathlib import Path

from exasol.nb_connector.language_container_activation import ACTIVATION_KEY_PREFIX

DEFAULT_ALIAS = "ai_lab_default"  # unused
PATH_IN_BUCKET = "container"

SLC_ACTIVATION_KEY_PREFIX = ACTIVATION_KEY_PREFIX + "slc_"
"""
Activation SQL for the Custom SLC will be saved in the Secure
Configuration Storage with this key.
"""

FLAVORS_PATH_IN_SLC_REPO = Path("flavors")
"""Path to flavors within the script-languages-release repository"""

SLC_RELEASE_TAG = "9.6.0"
"""
Using the SLC_RELEASE 9.6.0 because we are limited to slc-tool 3.*. (see pyproject.toml)
Check the developer guide (./doc/developer-guide.md) for more information.
"""

SLC_CHECKOUT_DIR = ".slc_checkout"
