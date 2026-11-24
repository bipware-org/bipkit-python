from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from bipkit._transport import AsyncTransport, SyncTransport
from bipkit.types.models import (
    APIKeyInfo,
    CreateAPIKeyRequest,
    CreateAPIKeyResponse,
    RotateAPIKeyRequest,
    RotateAPIKeyResponse,
)


class APIKeysResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(self) -> list[APIKeyInfo]:
        data = self._transport.request("GET", "/api/v1/api-keys")
        return [APIKeyInfo.model_validate(item) for item in data]

    def create(
        self,
        *,
        name: str,
        environment: str = "live",
        scopes: Sequence[str] | None = None,
    ) -> CreateAPIKeyResponse:
        req = CreateAPIKeyRequest(
            name=name,
            environment=environment,
            scopes=list(scopes) if scopes is not None else ["evaluate:run"],
        )
        data = self._transport.request("POST", "/api/v1/api-keys", json_body=req.model_dump())
        return CreateAPIKeyResponse.model_validate(data)

    def rotate(
        self,
        key_id: str,
        *,
        grace_period_minutes: int = 0,
    ) -> RotateAPIKeyResponse:
        req = RotateAPIKeyRequest(grace_period_minutes=grace_period_minutes)
        data = self._transport.request(
            "POST",
            f"/api/v1/api-keys/{key_id}/rotate",
            json_body=req.model_dump(),
        )
        return RotateAPIKeyResponse.model_validate(data)

    def revoke(self, key_id: str) -> Any:
        return self._transport.request("DELETE", f"/api/v1/api-keys/{key_id}")


class AsyncAPIKeysResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(self) -> list[APIKeyInfo]:
        data = await self._transport.request("GET", "/api/v1/api-keys")
        return [APIKeyInfo.model_validate(item) for item in data]

    async def create(
        self,
        *,
        name: str,
        environment: str = "live",
        scopes: Sequence[str] | None = None,
    ) -> CreateAPIKeyResponse:
        req = CreateAPIKeyRequest(
            name=name,
            environment=environment,
            scopes=list(scopes) if scopes is not None else ["evaluate:run"],
        )
        data = await self._transport.request("POST", "/api/v1/api-keys", json_body=req.model_dump())
        return CreateAPIKeyResponse.model_validate(data)

    async def rotate(
        self,
        key_id: str,
        *,
        grace_period_minutes: int = 0,
    ) -> RotateAPIKeyResponse:
        req = RotateAPIKeyRequest(grace_period_minutes=grace_period_minutes)
        data = await self._transport.request(
            "POST",
            f"/api/v1/api-keys/{key_id}/rotate",
            json_body=req.model_dump(),
        )
        return RotateAPIKeyResponse.model_validate(data)

    async def revoke(self, key_id: str) -> Any:
        return await self._transport.request("DELETE", f"/api/v1/api-keys/{key_id}")
