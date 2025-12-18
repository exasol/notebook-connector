import logging
from pathlib import Path

from exasol.nb_connector.slc.package_types import (
    CondaPackageDefinition,
    PipPackageDefinition,
)
from exasol.nb_connector.slc.slc_error import SlcError


def _read_packages(file_path: Path, package_definition: type) -> list:
    packages = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue  # skip empty or commented lines
            # Take everything before the '|' as package name
            package, version = line.split("|", 1)
            packages.append(package_definition(package, version))
    return packages


def _ends_with_newline(file_path: Path) -> bool:
    content = file_path.read_text()
    return content.endswith("\n")


def _filter_packages(
    original_packages: list[PipPackageDefinition] | list[CondaPackageDefinition],
    new_packages: list[PipPackageDefinition] | list[CondaPackageDefinition],
) -> list[PipPackageDefinition | CondaPackageDefinition]:
    filtered_packages = []
    for package in new_packages:
        add_package = True
        for original_package in original_packages:
            if package.pkg == original_package.pkg:
                add_package = False
                if package.version == original_package.version:
                    logging.warning("Package already exists: %s", original_package)
                else:
                    raise SlcError(
                        "Package already exists: %s but with different version",
                        original_package,
                    )
        if add_package:
            filtered_packages.append(package)
    return filtered_packages


def append_packages(
    file_path: Path,
    package_definition: type,
    packages: list[PipPackageDefinition] | list[CondaPackageDefinition],
):
    """
    Appends packages to the custom packages file.
    """
    original_packages = _read_packages(file_path, package_definition)
    filtered_packages = _filter_packages(original_packages, packages)
    ends_with_newline = _ends_with_newline(file_path)
    if filtered_packages:
        with open(file_path, "a") as f:
            if not ends_with_newline:
                f.write("\n")
            for p in filtered_packages:
                print(f"{p.pkg}|{p.version}", file=f)
