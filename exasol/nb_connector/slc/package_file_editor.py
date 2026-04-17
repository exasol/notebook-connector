from pathlib import Path
import logging

from exasol.exaslpm.model.package_file_config import (
    CondaPackage,
    PipPackage,
)
from exasol.exaslpm.pkg_mgmt.package_file_session import PackageFileSession
from exasol.nb_connector.slc.slc_error import SlcError

logger = logging.getLogger(__name__)


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
    session = PackageFileSession(file_path)
    build_step = session.package_file_config.find_build_step(build_step)
    phase = build_step.find_phase(phase)

    if package_definition is PipPackage:
        container = phase.pip
    elif package_definition is CondaPackage:
        container = phase.conda
    else:
        container = None

    if container is not None:
        for package in packages:
            try:
                container.add_package(package)
            except ValueError:
                existing = container.find_package(package.name, raise_if_not_found=False)
                if existing is not None and existing.version == package.version:
                    logger.warning(
                        "Package already exists: %s==%s. Skipping.",
                        package.name,
                        package.version,
                    )
                else:
                    raise SlcError(
                        f"Package already exists with a different version: "
                        f"'{package.name}'. Existing: {existing.version if existing else 'unknown'}, "
                        f"Requested: {package.version}"
                    )

    session.commit_changes()
