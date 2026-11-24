from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Self

import httpx

from bipkit._transport import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    AsyncTransport,
    SyncTransport,
)
from bipkit.resources.api_keys import APIKeysResource, AsyncAPIKeysResource
from bipkit.resources.engines import AsyncEnginesResource, EnginesResource
from bipkit.resources.evaluation import AsyncFeedbackResource, FeedbackResource
from bipkit.resources.provenance import AsyncProvenanceResource, ProvenanceResource
from bipkit.resources.usage import AsyncUsageResource, UsageResource
from bipkit.types.models import (
    CandidateModel,
    DecisionRequest,
    DecisionResponse,
    EvaluateRequest,
    EvaluateResponse,
)


def _normalize_choices(choices: Sequence[CandidateModel | Mapping[str, Any] | str]) -> list[Any]:
    out: list[Any] = []
    for c in choices:
        if isinstance(c, CandidateModel):
            out.append(c.model_dump(exclude_none=True))
        elif isinstance(c, Mapping):
            out.append(dict(c))
        else:
            out.append(str(c))
    return out


class Bipkit:
    """Synchronous client for the Bipkit System One Decision Engine API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        resolved_key = api_key if api_key is not None else os.getenv("BIPKIT_API_KEY")
        resolved_url = base_url or os.getenv("BIPKIT_BASE_URL", DEFAULT_BASE_URL)
        self._transport = SyncTransport(
            api_key=resolved_key,
            base_url=resolved_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            http_client=http_client,
        )
        self.feedback = FeedbackResource(self._transport)
        self.engines = EnginesResource(self._transport)
        self.api_keys = APIKeysResource(self._transport)
        self.usage = UsageResource(self._transport)
        self.provenance = ProvenanceResource(self._transport)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def evaluate(
        self,
        *,
        state: str,
        evaluations: dict[str, Any],
        engine: str = "bip-instant",
        temperature: float | None = None,
    ) -> EvaluateResponse:
        req = EvaluateRequest(
            state=state,
            evaluations=evaluations,
            engine=engine,
            temperature=temperature,
        )
        data = self._transport.request(
            "POST",
            "/api/v1/evaluate",
            json_body=req.model_dump(exclude_none=True),
        )
        return EvaluateResponse.model_validate(data)

    def decide(
        self,
        *,
        state: str,
        choices: Sequence[CandidateModel | Mapping[str, Any] | str],
        engine: str = "bip-instant",
        top_k: int | None = None,
        temperature: float | None = None,
    ) -> DecisionResponse:
        req = DecisionRequest(
            state=state,
            choices=_normalize_choices(choices),
            engine=engine,
            top_k=top_k,
            temperature=temperature,
        )
        data = self._transport.request(
            "POST",
            "/api/v1/decide",
            json_body=req.model_dump(exclude_none=True),
        )
        return DecisionResponse.model_validate(data)

    def health(self) -> dict[str, Any]:
        return dict(self._transport.request("GET", "/api/v1/health", require_auth=False))


class AsyncBipkit:
    """Asynchronous client for the Bipkit System One Decision Engine API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        resolved_key = api_key if api_key is not None else os.getenv("BIPKIT_API_KEY")
        resolved_url = base_url or os.getenv("BIPKIT_BASE_URL", DEFAULT_BASE_URL)
        self._transport = AsyncTransport(
            api_key=resolved_key,
            base_url=resolved_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            http_client=http_client,
        )
        self.feedback = AsyncFeedbackResource(self._transport)
        self.engines = AsyncEnginesResource(self._transport)
        self.api_keys = AsyncAPIKeysResource(self._transport)
        self.usage = AsyncUsageResource(self._transport)
        self.provenance = AsyncProvenanceResource(self._transport)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def evaluate(
        self,
        *,
        state: str,
        evaluations: dict[str, Any],
        engine: str = "bip-instant",
        temperature: float | None = None,
    ) -> EvaluateResponse:
        req = EvaluateRequest(
            state=state,
            evaluations=evaluations,
            engine=engine,
            temperature=temperature,
        )
        data = await self._transport.request(
            "POST",
            "/api/v1/evaluate",
            json_body=req.model_dump(exclude_none=True),
        )
        return EvaluateResponse.model_validate(data)

    async def decide(
        self,
        *,
        state: str,
        choices: Sequence[CandidateModel | Mapping[str, Any] | str],
        engine: str = "bip-instant",
        top_k: int | None = None,
        temperature: float | None = None,
    ) -> DecisionResponse:
        req = DecisionRequest(
            state=state,
            choices=_normalize_choices(choices),
            engine=engine,
            top_k=top_k,
            temperature=temperature,
        )
        data = await self._transport.request(
            "POST",
            "/api/v1/decide",
            json_body=req.model_dump(exclude_none=True),
        )
        return DecisionResponse.model_validate(data)

    async def health(self) -> dict[str, Any]:
        return dict(await self._transport.request("GET", "/api/v1/health", require_auth=False))
