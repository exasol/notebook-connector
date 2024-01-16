"""
Bucketfs-related functions.
"""
import logging
import pathlib

import exasol.bucketfs as bfs  # type: ignore

_logger = logging.getLogger(__name__)


def put_file(
    bucket: bfs.Bucket, file_path: pathlib.Path, skip_if_exists: bool = True
) -> pathlib.Path:
    """
    Uploads given file into bucketfs
    :param bucket: bucket to use
    :param file_path: local file path to uplaod. File have to exist.
    :param skip_if_exists: Do not upload if file already present in the bucketfs.
    :return: Path in the bucketfs.
    """
    if not file_path.exists():
        raise ValueError(f"Local file doesn't exist: {file_path}")
    local_name = file_path.name
    if skip_if_exists and local_name in list(bucket):
        _logger.info("File %s is already present in the bucketfs", local_name)
    else:
        _logger.info("Uploading file %s to bucketfs", local_name)
        with file_path.open("rb") as file:
            bucket.upload(local_name, file)
    return pathlib.Path("/buckets/bfsdefault/") / bucket.name / local_name
