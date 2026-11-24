from __future__ import annotations

from typing import Any

from bipkit._transport import AsyncTransport, SyncTransport
from bipkit.types.models import (
    BatchRecordOutcomeRequest,
    DplBundle,
    ExportBundleRequest,
    RecordOutcomeRequest,
)


class ProvenanceResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def manifest(self) -> dict[str, Any]:
        return dict(self._transport.request("GET", "/api/v1/provenance/manifest", require_auth=False))

    def calibration(self) -> dict[str, Any]:
        return dict(
            self._transport.request("GET", "/api/v1/provenance/calibration", require_auth=False)
        )

    def keys(self) -> dict[str, Any]:
        return dict(self._transport.request("GET", "/api/v1/provenance/keys", require_auth=False))

    def record_outcome(
        self,
        *,
        request_id: str,
        observed_effect: Any,
        output_name: str | None = None,
    ) -> dict[str, Any]:
        req = RecordOutcomeRequest(
            request_id=request_id,
            output_name=output_name,
            observed_effect=observed_effect,
        )
        return dict(
            self._transport.request(
                "POST",
                "/api/v1/provenance/outcomes",
                json_body=req.model_dump(exclude_none=True),
            )
        )

    def record_outcomes_batch(
        self,
        items: list[RecordOutcomeRequest | dict[str, Any]],
    ) -> dict[str, Any]:
        normalized = [
            item if isinstance(item, RecordOutcomeRequest) else RecordOutcomeRequest.model_validate(item)
            for item in items
        ]
        req = BatchRecordOutcomeRequest(items=normalized)
        return dict(
            self._transport.request(
                "POST",
                "/api/v1/provenance/outcomes/batch",
                json_body=req.model_dump(exclude_none=True),
            )
        )

    def chain(self, *, from_seq: int | None = None, limit: int | None = None) -> dict[str, Any]:
        return dict(
            self._transport.request(
                "GET",
                "/api/v1/provenance/chain",
                params={"from_seq": from_seq, "limit": limit},
            )
        )

    def metrics(self) -> dict[str, Any]:
        return dict(self._transport.request("GET", "/api/v1/provenance/metrics"))

    def records(
        self,
        *,
        status: str | None = None,
        primitive_type: str | None = None,
        execution_stage: str | None = None,
        request_id: str | None = None,
        from_seq: int | None = None,
        to_seq: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order: str | None = None,
    ) -> dict[str, Any]:
        return dict(
            self._transport.request(
                "GET",
                "/api/v1/provenance/records",
                params={
                    "status": status,
                    "primitive_type": primitive_type,
                    "execution_stage": execution_stage,
                    "request_id": request_id,
                    "from_seq": from_seq,
                    "to_seq": to_seq,
                    "limit": limit,
                    "offset": offset,
                    "order": order,
                },
            )
        )

    def get_record(self, entry_id: str) -> dict[str, Any]:
        return dict(self._transport.request("GET", f"/api/v1/provenance/records/{entry_id}"))

    def get_request(self, request_id: str) -> dict[str, Any]:
        return dict(self._transport.request("GET", f"/api/v1/provenance/requests/{request_id}"))

    def export(
        self,
        *,
        request_id: str,
        output_name: str | None = None,
        presented_state: str | None = None,
    ) -> dict[str, Any]:
        req = ExportBundleRequest(
            request_id=request_id,
            output_name=output_name,
            presented_state=presented_state,
        )
        return dict(
            self._transport.request(
                "POST",
                "/api/v1/provenance/export",
                json_body=req.model_dump(exclude_none=True),
            )
        )

    def verify(self, bundle: DplBundle | dict[str, Any]) -> dict[str, Any]:
        payload = (
            bundle.model_dump(exclude_none=True) if isinstance(bundle, DplBundle) else dict(bundle)
        )
        return dict(
            self._transport.request("POST", "/api/v1/provenance/verify", json_body=payload)
        )


class AsyncProvenanceResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def manifest(self) -> dict[str, Any]:
        return dict(
            await self._transport.request("GET", "/api/v1/provenance/manifest", require_auth=False)
        )

    async def calibration(self) -> dict[str, Any]:
        return dict(
            await self._transport.request(
                "GET", "/api/v1/provenance/calibration", require_auth=False
            )
        )

    async def keys(self) -> dict[str, Any]:
        return dict(
            await self._transport.request("GET", "/api/v1/provenance/keys", require_auth=False)
        )

    async def record_outcome(
        self,
        *,
        request_id: str,
        observed_effect: Any,
        output_name: str | None = None,
    ) -> dict[str, Any]:
        req = RecordOutcomeRequest(
            request_id=request_id,
            output_name=output_name,
            observed_effect=observed_effect,
        )
        return dict(
            await self._transport.request(
                "POST",
                "/api/v1/provenance/outcomes",
                json_body=req.model_dump(exclude_none=True),
            )
        )

    async def record_outcomes_batch(
        self,
        items: list[RecordOutcomeRequest | dict[str, Any]],
    ) -> dict[str, Any]:
        normalized = [
            item if isinstance(item, RecordOutcomeRequest) else RecordOutcomeRequest.model_validate(item)
            for item in items
        ]
        req = BatchRecordOutcomeRequest(items=normalized)
        return dict(
            await self._transport.request(
                "POST",
                "/api/v1/provenance/outcomes/batch",
                json_body=req.model_dump(exclude_none=True),
            )
        )

    async def chain(
        self, *, from_seq: int | None = None, limit: int | None = None
    ) -> dict[str, Any]:
        return dict(
            await self._transport.request(
                "GET",
                "/api/v1/provenance/chain",
                params={"from_seq": from_seq, "limit": limit},
            )
        )

    async def metrics(self) -> dict[str, Any]:
        return dict(await self._transport.request("GET", "/api/v1/provenance/metrics"))

    async def records(
        self,
        *,
        status: str | None = None,
        primitive_type: str | None = None,
        execution_stage: str | None = None,
        request_id: str | None = None,
        from_seq: int | None = None,
        to_seq: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order: str | None = None,
    ) -> dict[str, Any]:
        return dict(
            await self._transport.request(
                "GET",
                "/api/v1/provenance/records",
                params={
                    "status": status,
                    "primitive_type": primitive_type,
                    "execution_stage": execution_stage,
                    "request_id": request_id,
                    "from_seq": from_seq,
                    "to_seq": to_seq,
                    "limit": limit,
                    "offset": offset,
                    "order": order,
                },
            )
        )

    async def get_record(self, entry_id: str) -> dict[str, Any]:
        return dict(await self._transport.request("GET", f"/api/v1/provenance/records/{entry_id}"))

    async def get_request(self, request_id: str) -> dict[str, Any]:
        return dict(
            await self._transport.request("GET", f"/api/v1/provenance/requests/{request_id}")
        )

    async def export(
        self,
        *,
        request_id: str,
        output_name: str | None = None,
        presented_state: str | None = None,
    ) -> dict[str, Any]:
        req = ExportBundleRequest(
            request_id=request_id,
            output_name=output_name,
            presented_state=presented_state,
        )
        return dict(
            await self._transport.request(
                "POST",
                "/api/v1/provenance/export",
                json_body=req.model_dump(exclude_none=True),
            )
        )

    async def verify(self, bundle: DplBundle | dict[str, Any]) -> dict[str, Any]:
        payload = (
            bundle.model_dump(exclude_none=True) if isinstance(bundle, DplBundle) else dict(bundle)
        )
        return dict(
            await self._transport.request("POST", "/api/v1/provenance/verify", json_body=payload)
        )
