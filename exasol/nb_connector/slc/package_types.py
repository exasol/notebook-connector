from collections import namedtuple

PipPackageDefinition = namedtuple("PipPackageDefinition", ["pkg", "version"])
CondaPackageDefinition = namedtuple("CondaPackageDefinition", ["pkg", "version"])
