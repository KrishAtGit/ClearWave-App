from datetime import timedelta
from typing import Protocol
from urllib.parse import quote
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobSasPermissions, ContentSettings, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient
from app.security import now

class AudioStore(Protocol):
    async def save(self, key: str, data: bytes, content_type: str) -> None: ...
    async def delete(self, ky: str)-> None: ...
    async def signed_url(slf, key: str, expires_in: timedelta) -> str: ...
    async def close(self) -> None: ...

class BlobAudioStore:
    def __init__(self, connection_string: str, container: str) -> None:
        self._service = BlobServiceClient.from_connection_string(connection_string) 
        self._container = container
        self._container_ready = False

    async def _ensure_container(self) -> None:
        if self._container_ready:
            return 
        try:
            await self._service.create_container(self._container)
        except ResourceExistsError:
            pass

        self._container_ready = True

    async def save(self, key: str, data: bytes, content_type: str) -> None:
        await self._ensure_container()
        blob = self._service.get_blob_client(self._container, key)
        await blob.upload_blob(
            data, 
            overwrite=True, 
            content_settings=ContentSettings(content_type=content_type)
        )

    async def delete(self, key: str) -> None:
        try:
            await self._service.get_blob_client(
                self._container,
                key
            ).delete_blob()
        except ResourceNotFoundError:
            pass

    def signed_url(self, key: str, expires_in: timedelta) -> str:
        sas = generate_blob_sas(
            account_name=self._service.account_name,
            container_name=self._container,
            blob_name=key,
            account_key=self._service.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=now() + expires_in,
        )
        return f"{self._service.url.rstrip('/')}/{self._container}/{quote(key)}?{sas}"

    async def close(self) -> None:
        await self._service.close()

class MemoryAudioStore:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    async def save(self, key: str, data: bytes, content_type: str) -> None:
        self.files[key] = data

    async def delete(self, key: str) -> None:
        self.files.pop(key, None)

    def signed_url(self, key: str, expires_in: timedelta) -> str:
        return f"https://storage.test/{key}?expires_in={int(expires_in.total_seconds())}"

    async def close(self) -> None:
        pass
    
