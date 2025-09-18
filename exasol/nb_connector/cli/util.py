# from enum import Enum

def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


# class Backend(Enum):
#     ONPREM = "onprem"
#     SAAS = "saas"
#     DOCKER_DB = "docker-db"
#
#     @classmethod
#     def help(cls):
#         return [x.value for x in cls]
