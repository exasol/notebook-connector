import logging
from pathlib import Path

import yaml
from exasol.exaslpm.model.package_file_config import (
    CondaPackage,
    PackageFile,
    PipPackage,
)
from exasol.exaslpm.model.serialization import to_yaml_str

from exasol.nb_connector.slc.slc_error import SlcError


def append_packages(
    file_path: Path,
    package_definition: type,
    packages: list[PipPackage] | list[CondaPackage],
    build_step: str,
    phase: str,
) -> None:
    """
    Appends packages to the custom packages file.
    """
    with file_path.open("r", encoding="utf-8") as f:
        package_file = PackageFile.model_validate(yaml.safe_load(f))

    build_step = package_file.find_build_step(build_step)
    phase = build_step.find_phase(phase)

    if package_definition is PipPackage:
        container = phase.pip
    elif package_definition is CondaPackage:
        container = phase.conda
    else:
        container = None

    if container is not None:
        for package in packages:
            existing = container.find_package(
                package.name, raise_if_not_found=False
            )
            if existing is not None:
                if existing.version == package.version:
                    logging.warning("Package already exists: %s", package)
                else:
                    raise SlcError(
                        f"Package already exists: {package} but with different version"
                    )
            else:
                container.add_package(package)

    file_path.write_text(to_yaml_str(package_file))
