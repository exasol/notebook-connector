import enum


class PackageManager(enum.Enum):
    """
    Supported Python package managers.
    """

    PIP = "pip"
    CONDA = "conda"
