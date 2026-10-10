"""Storage boundary used by local and Azure-backed silo workers."""

from abc import ABC, abstractmethod
from pathlib import Path
import re


def object_name(name):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError("invalid object name")
    if name.startswith("/") or any(p in {"", ".", ".."} for p in name.split("/")):
        raise ValueError("invalid object path")
    return name


class BlobStore(ABC):
    @abstractmethod
    def list(self) -> list[str]:
        """Return object names visible in this silo only."""

    @abstractmethod
    def read(self, name: str) -> bytes:
        """Read one object from this silo."""


class LocalBlobStore(BlobStore):
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def _path(self, name: str) -> Path:
        candidate = (self.root / object_name(name)).resolve()
        if self.root not in candidate.parents:
            raise ValueError("object escapes silo root")
        return candidate

    def list(self) -> list[str]:
        return sorted(
            str(path.relative_to(self.root))
            for path in self.root.rglob("*")
            if path.is_file() and self.root in path.resolve().parents
        )

    def read(self, name: str) -> bytes:
        return self._path(name).read_bytes()

    def write(self, name, value):
        path = self._path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(value)


class AzureBlobStore(BlobStore):
    """One explicit container, managed identity only; no SAS or account keys."""

    def __init__(self, account, container, managed_identity_client_id=None):
        if not re.fullmatch(r"[a-z0-9]{3,24}", account) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]", container):
            raise ValueError("explicit Azure account and container required")
        from azure.identity import ManagedIdentityCredential
        from azure.storage.blob import ContainerClient
        credential = (ManagedIdentityCredential(client_id=managed_identity_client_id)
                      if managed_identity_client_id else ManagedIdentityCredential())
        self.client = ContainerClient(f"https://{account}.blob.core.windows.net", container,
                                      credential=credential)

    def list(self):
        return sorted(blob.name for blob in self.client.list_blobs())

    def read(self, name):
        return self.client.download_blob(object_name(name)).readall()

    def write(self, name, value):
        self.client.upload_blob(object_name(name), value, overwrite=False)
