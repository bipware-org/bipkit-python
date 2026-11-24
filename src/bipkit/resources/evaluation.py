from __future__ import annotations

from typing import Any

from bipkit._transport import AsyncTransport, SyncTransport
from bipkit.types.models import CustomerFeedbackRequest, CustomerFeedbackResponse


class FeedbackResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def submit(
        self,
        *,
        request_id: str,
        verified_decision: Any,
        was_accurate: bool,
        operator_notes: str | None = None,
    ) -> CustomerFeedbackResponse:
        payload = CustomerFeedbackRequest(
            request_id=request_id,
            verified_decision=verified_decision,
            was_accurate=was_accurate,
            operator_notes=operator_notes,
        ).model_dump(exclude_none=True)
        data = self._transport.request("POST", "/api/v1/feedback", json_body=payload)
        return CustomerFeedbackResponse.model_validate(data)


class AsyncFeedbackResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def submit(
        self,
        *,
        request_id: str,
        verified_decision: Any,
        was_accurate: bool,
        operator_notes: str | None = None,
    ) -> CustomerFeedbackResponse:
        payload = CustomerFeedbackRequest(
            request_id=request_id,
            verified_decision=verified_decision,
            was_accurate=was_accurate,
            operator_notes=operator_notes,
        ).model_dump(exclude_none=True)
        data = await self._transport.request("POST", "/api/v1/feedback", json_body=payload)
        return CustomerFeedbackResponse.model_validate(data)
