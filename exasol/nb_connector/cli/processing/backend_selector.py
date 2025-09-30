from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.connections import get_backend
from exasol.nb_connector.secret_store import Secrets


class BackendSelector:
    """
    Based on an instance of Secrets (SCS) this class provides the
    following features:

    * Tell whether a particular backend is properly selected.

    * Access the properties of the selection using proper types StorageBackend
      and bool.

    * Get the user-friendly display name of the selected backend, e.g. "Docker".

    * Checks if a proposed backend conflicts with the previously made selection.
    """

    def __init__(self, scs: Secrets):
        self._scs = scs

    @property
    def backend(self) -> StorageBackend:
        return get_backend(self._scs)

    @property
    def use_itde(self) -> bool:
        return self._scs.get(CKey.use_itde, "False") == "True"

    @property
    def backend_name(self) -> str:
        if self.backend == StorageBackend.saas:
            return "SaaS"
        if self.use_itde:
            return "Docker"
        return "on-premise"

    @property
    def knows_backend(self) -> bool:
        """
        Tells whether the current backend selection unambiguously points
        to saas, onprem, or docker.
        """
        backend = self._scs.get(CKey.storage_backend)
        if not backend:
            return False
        if self.backend == StorageBackend.saas:
            return True
        use_itde = self._scs.get(CKey.use_itde)
        return use_itde is not None

    def matches(self, backend: StorageBackend, use_itde: bool) -> bool:
        """
        Tells whether the currently selected backend matches the specified
        one.  If no backend has been selected yet (property knows_backend is
        False), then the selection is rated to be matching, as well.
        """
        if not self.knows_backend:
            return True
        return backend == self.backend and use_itde == self.use_itde
