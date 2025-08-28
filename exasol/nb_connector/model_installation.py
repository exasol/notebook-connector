import os
from dataclasses import dataclass
from typing import Any

from exasol.ai.text.extractors.bucketfs_model_repository import BucketFSRepository
from exasol.ai.text.impl.utils.transformers_utils import download_transformers_model
from yaspin import yaspin

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.connections import open_bucketfs_location
from exasol.nb_connector.extension_wrapper_common import (
    encapsulate_bucketfs_credentials,
)
from exasol.nb_connector.secret_store import Secrets

PATH_IN_BUCKET = "ai-lab"
""" Location in BucketFS bucket to upload data for Extensions, e.g. its language container. """

CHECKMARK = "\u2705"
"""
Checkmark symbol for signalling success after an operation using an
animated spinner from https://github.com/pavdmyt/yaspin.
"""

# Models will be uploaded into this directory in BucketFS.
DEF_BFS_MODELS_DIR = "models"



@dataclass
class TransformerModel:
    name: str
    task_type: str
    factory: Any



def _interactive_usage() -> bool:
    return os.environ.get("INTERACTIVE", "True").lower() == "true"


def _ensure_subdir_config_value(conf: Secrets) -> str:
    if value := conf.get(CKey.bfs_model_subdir):
        return value
    conf.save(CKey.bfs_model_subdir, DEF_BFS_MODELS_DIR)
    return DEF_BFS_MODELS_DIR


def install_model(conf: Secrets, model: TransformerModel) -> None:
    """
    Download and install the specified Huggingface model.
    """
    bucketfs_location = open_bucketfs_location(conf) / PATH_IN_BUCKET
    with yaspin(text=f"- Huggingface model {model.name}") as spinner:
        if not _interactive_usage():
            spinner.hide()
        download_transformers_model(
            bucketfs_location=bucketfs_location,
            sub_dir=_ensure_subdir_config_value(conf),
            task_type=model.task_type,
            model_name=model.name,
            model_factory=model.factory,
        )
    spinner.ok(CHECKMARK)


def create_bfs_connection(conf: Secrets, bfs_conn_name: str) -> None:
    """
    Creates a connection object in the database encapsulating
    a location in the BucketFS and BucketFS access credentials.
    The path in the bucket is the hard-coded value for models.
    Parameters:
         conf:
            The secret store.
        bfs_conn_name:
            The name of the new bucketfs connection.
    """
    encapsulate_bucketfs_credentials(
        conf, path_in_bucket=PATH_IN_BUCKET, connection_name=bfs_conn_name
    )
    _ensure_subdir_config_value(conf)


def create_model_repository(conf: Secrets, bfs_conn_name: str) -> BucketFSRepository:
    """
    Creates a BucketFSRepository encapsulating using the sub-directory from the secret store.
    Parameters:
         conf:
            The secret store.
        bfs_conn_name:
            The name of the new bucketfs connection.
    """
    return BucketFSRepository(
        connection_name=bfs_conn_name,
        sub_dir=_ensure_subdir_config_value(conf),
    )
