from __future__ import annotations

from bipkit._transport import AsyncTransport, SyncTransport
from bipkit.types.models import UsageSummaryResponse, UsageTimeseriesResponse


class UsageResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def summary(self) -> UsageSummaryResponse:
        data = self._transport.request("GET", "/api/v1/usage/summary")
        return UsageSummaryResponse.model_validate(data)

    def timeseries(self, *, days: int | None = None) -> UsageTimeseriesResponse:
        data = self._transport.request(
            "GET",
            "/api/v1/usage/timeseries",
            params={"days": days},
        )
        return UsageTimeseriesResponse.model_validate(data)


class AsyncUsageResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def summary(self) -> UsageSummaryResponse:
        data = await self._transport.request("GET", "/api/v1/usage/summary")
        return UsageSummaryResponse.model_validate(data)

    async def timeseries(self, *, days: int | None = None) -> UsageTimeseriesResponse:
        data = await self._transport.request(
            "GET",
            "/api/v1/usage/timeseries",
            params={"days": days},
        )
        return UsageTimeseriesResponse.model_validate(data)
