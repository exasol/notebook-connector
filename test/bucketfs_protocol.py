import enum


class BucketFSProtocol(enum.Enum):
    """
    Supported protocols for BucketFS.
    """

    HTTP = "http"
    HTTPS = "https"

    def __str__(self):
        # this allows using `choices` in argparse
        return self.value
