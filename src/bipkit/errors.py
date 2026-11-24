from __future__ import annotations

from typing import Any


class BipkitError(Exception):
    """Base exception for all Bipkit SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.body = body


class APIConnectionError(BipkitError):
    """Raised when a network or connection error occurs communicating with Bipkit."""


class APITimeoutError(APIConnectionError):
    """Raised when a request to Bipkit exceeds the configured timeout."""


class APIStatusError(BipkitError):
    """Raised when the Bipkit API returns a non-2xx HTTP status code."""


class AuthenticationError(APIStatusError):
    """Raised on HTTP 401 Unauthorized (missing or invalid API key)."""


class PermissionError(APIStatusError):
    """Raised on HTTP 403 Forbidden (insufficient API key scope or suspended access)."""


class NotFoundError(APIStatusError):
    """Raised on HTTP 404 Not Found."""


class ValidationError(APIStatusError):
    """Raised on HTTP 422 Unprocessable Entity (request schema validation error)."""


class RateLimitError(APIStatusError):
    """Raised on HTTP 429 Too Many Requests (rate limit or monthly quota exceeded)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = 429,
        request_id: str | None = None,
        body: Any = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, request_id=request_id, body=body)
        self.retry_after = retry_after


class InternalServerError(APIStatusError):
    """Raised on HTTP 5xx server errors."""
