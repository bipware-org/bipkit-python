from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Mapping
from typing import Any

import httpx

from bipkit._version import __version__
from bipkit.errors import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ValidationError,
)

DEFAULT_BASE_URL = "https://api.bipkit.io"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
RETRYABLE_STATUS_CODES = frozenset({429, 502, 503, 504})


def _parse_retry_after(headers: httpx.Headers) -> float | None:
    raw = headers.get("retry-after")
    if not raw:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        return None


def _compute_backoff(attempt: int, retry_after: float | None) -> float:
    if retry_after is not None:
        return min(retry_after, 60.0)
    base = 0.25 * (2**attempt)
    jitter = random.uniform(0.0, 0.15)
    return min(base + jitter, 15.0)


def _extract_error_message(response: httpx.Response) -> tuple[str, Any]:
    try:
        body: Any = response.json()
    except ValueError:
        text = response.text.strip()
        return text or f"HTTP {response.status_code}", text

    if isinstance(body, dict):
        detail = body.get("detail") or body.get("message") or body.get("error")
        if isinstance(detail, str):
            return detail, body
        if detail is not None:
            return str(detail), body
    return f"HTTP {response.status_code}", body


def _raise_for_status(response: httpx.Response) -> None:
    if 200 <= response.status_code < 300:
        return

    message, body = _extract_error_message(response)
    request_id = response.headers.get("x-request-id")
    status = response.status_code

    if status == 401:
        raise AuthenticationError(message, status_code=status, request_id=request_id, body=body)
    if status == 403:
        raise PermissionError(message, status_code=status, request_id=request_id, body=body)
    if status == 404:
        raise NotFoundError(message, status_code=status, request_id=request_id, body=body)
    if status == 422:
        raise ValidationError(message, status_code=status, request_id=request_id, body=body)
    if status == 429:
        raise RateLimitError(
            message,
            status_code=status,
            request_id=request_id,
            body=body,
            retry_after=_parse_retry_after(response.headers),
        )
    if status >= 500:
        raise InternalServerError(message, status_code=status, request_id=request_id, body=body)
    raise APIStatusError(message, status_code=status, request_id=request_id, body=body)


def _build_headers(
    api_key: str | None,
    extra_headers: Mapping[str, str] | None = None,
    *,
    require_auth: bool = True,
) -> dict[str, str]:
    headers: dict[str, str] = {
        "Accept": "application/json",
        "User-Agent": f"bipkit-python/{__version__}",
    }
    if extra_headers:
        headers.update(extra_headers)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif require_auth:
        raise AuthenticationError(
            "Missing Bipkit API key. Pass api_key=... or set the BIPKIT_API_KEY environment variable.",
            status_code=401,
        )
    return headers


class SyncTransport:
    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        timeout: float,
        max_retries: int,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_retries = max(0, max_retries)
        self._default_headers = dict(default_headers or {})
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(base_url=self._base_url, timeout=timeout)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        require_auth: bool = True,
    ) -> Any:
        headers = _build_headers(self._api_key, self._default_headers, require_auth=require_auth)
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.request(
                    method=method,
                    url=f"{self._base_url}{path}",
                    params=clean_params or None,
                    json=json_body,
                    headers=headers,
                )
            except httpx.TimeoutException as exc:
                last_exc = APITimeoutError(f"Request timed out: {exc}")
                if attempt < self._max_retries:
                    time.sleep(_compute_backoff(attempt, None))
                    continue
                raise last_exc from exc
            except httpx.HTTPError as exc:
                last_exc = APIConnectionError(f"Connection error: {exc}")
                if attempt < self._max_retries:
                    time.sleep(_compute_backoff(attempt, None))
                    continue
                raise last_exc from exc

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < self._max_retries:
                time.sleep(_compute_backoff(attempt, _parse_retry_after(response.headers)))
                continue

            _raise_for_status(response)
            if not response.content:
                return None
            return response.json()

        if last_exc is not None:
            raise last_exc
        raise APIConnectionError("Request failed after retries")


class AsyncTransport:
    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        timeout: float,
        max_retries: int,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_retries = max(0, max_retries)
        self._default_headers = dict(default_headers or {})
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(base_url=self._base_url, timeout=timeout)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        require_auth: bool = True,
    ) -> Any:
        headers = _build_headers(self._api_key, self._default_headers, require_auth=require_auth)
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=f"{self._base_url}{path}",
                    params=clean_params or None,
                    json=json_body,
                    headers=headers,
                )
            except httpx.TimeoutException as exc:
                last_exc = APITimeoutError(f"Request timed out: {exc}")
                if attempt < self._max_retries:
                    await asyncio.sleep(_compute_backoff(attempt, None))
                    continue
                raise last_exc from exc
            except httpx.HTTPError as exc:
                last_exc = APIConnectionError(f"Connection error: {exc}")
                if attempt < self._max_retries:
                    await asyncio.sleep(_compute_backoff(attempt, None))
                    continue
                raise last_exc from exc

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < self._max_retries:
                await asyncio.sleep(_compute_backoff(attempt, _parse_retry_after(response.headers)))
                continue

            _raise_for_status(response)
            if not response.content:
                return None
            return response.json()

        if last_exc is not None:
            raise last_exc
        raise APIConnectionError("Request failed after retries")
