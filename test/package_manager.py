import enum


class PackageManager(enum.Enum):
    """
    Supported Python package managers.
    """

    PIP = "pip"
    CONDA = "conda"

    def __str__(self):
        # this allows using `choices` in argparse
        return self.value
