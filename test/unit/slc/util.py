from unittest.mock import Mock


def secrets_without(key: str):
    def func(self, k: str):
        if k != key:
            return "value"
        raise AttributeError("")

    return Mock(__getitem__=func)
