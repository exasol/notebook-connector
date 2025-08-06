from unittest.mock import Mock


SESSION_ATTS = {
    "SLC_FLAVOR": "SLC flavor",
    "SLC_LANGUAGE_ALIAS": "SLC language alias",
    "SLC_DIR": "SLC working directory",
}

def secrets_without(key: str):
    def func(self, k: str):
        if k != key:
            return "value"
        raise AttributeError("")

    return Mock(__getitem__=func)
