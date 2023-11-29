from pathlib import Path


def upward_file_search(file_name: str) -> str:
    """
    Looks for a specified file starting from the current directory upward the file hierarchy.
    Hence, the last place to find the file is the root.

    Returns the full path of the file if found.
    Otherwise, raises a ValueError exception.
    """

    dir = Path().resolve()
    while dir.name:
        maybe_file = dir / file_name
        if maybe_file.is_file():
            return str(maybe_file)
        dir = dir.parent
    raise ValueError(f"Cannot find {file_name}")
