from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.connections import get_backend
from exasol.nb_connector.secret_store import Secrets


def get_bool(scs: Secrets, key: str | CKey) -> bool:
    return scs.get(key, "False") == "True"


class BackendSelector:
    """
    Based on an instance of Secrets (SCS) this class provides the
    following features:

    * Tell whether a particular backend is properly selected.

    * Access the properties of the selection using proper types StorageBackend
      and bool.

    * Get the user-friendly display name of the selected backend, e.g. "Docker".

    * Check if another backend selection is allowed wrt. to the current,
      i.e. "matches". This is also fine if no backend is selected, yet.
    """

    def __init__(self, scs: Secrets):
        self._scs = scs

    @property
    def knows_backend(self) -> bool:
        return bool(self._scs.get(CKey.storage_backend))

    @property
    def knows_itde_usage(self) -> bool:
        return bool(self._scs.get(CKey.use_itde))

    @property
    def backend(self) -> StorageBackend:
        return get_backend(self._scs)

    @property
    def backend_name(self) -> str:
        if self.backend == StorageBackend.saas:
            return "SaaS"
        if self.use_itde:
            return "Docker"
        return "on-premise"

    @property
    def use_itde(self) -> bool:
        return get_bool(self._scs, CKey.use_itde)

    @property
    def is_valid(self) -> bool:
        return self.knows_backend and self.knows_itde_usage

    def allows(self, backend: StorageBackend, use_itde: bool) -> bool:
        if not self.is_valid:
            return True
        return backend == self.backend and use_itde == self.use_itde
