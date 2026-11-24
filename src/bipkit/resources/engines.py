from __future__ import annotations

from bipkit._transport import AsyncTransport, SyncTransport
from bipkit.types.models import EngineStatusModel


class EnginesResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(self) -> list[EngineStatusModel]:
        data = self._transport.request("GET", "/api/v1/engines")
        return [EngineStatusModel.model_validate(item) for item in data]


class AsyncEnginesResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(self) -> list[EngineStatusModel]:
        data = await self._transport.request("GET", "/api/v1/engines")
        return [EngineStatusModel.model_validate(item) for item in data]
