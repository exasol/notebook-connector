import logging
from pathlib import Path

from exasol.exaslpm.model.package_file_config import (
    CondaPackage,
    PipPackage,
)
from exasol.exaslpm.pkg_mgmt.package_file_session import PackageFileSession

from exasol.nb_connector.slc.slc_error import SlcError

logger = logging.getLogger(__name__)


def _get_container(phase_obj, package_definition):
    if package_definition is PipPackage:
        return phase_obj.pip
    if package_definition is CondaPackage:
        return phase_obj.conda
    raise SlcError(f"Package type not supported: {package_definition}")


def _add_package(container, package):
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
    build_step_obj = session.package_file_config.find_build_step(build_step)
    phase_obj = build_step_obj.find_phase(phase)
    container = _get_container(phase_obj, package_definition)

    if container is not None:
        for package in packages:
            _add_package(container, package)

    session.commit_changes()
