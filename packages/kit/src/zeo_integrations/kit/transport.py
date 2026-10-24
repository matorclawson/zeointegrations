# Copyright (c) 2026 Rod Rivera
# SPDX-License-Identifier: MIT
# Adapted from zeroemployeeorg/zeocore@25a9c899c17ac6cdf54f4949e54b0fcc800cce91
# Source: src/zeo_core/integrations/kit/transport.py
# MIT permission notice retained in package LICENSE; provenance in NOTICE.
"""Bounded fixed-origin read-only Kit migration boundary; never retries."""

from __future__ import annotations

import json
import logging
import math
import time
from contextvars import ContextVar
from typing import Any

import httpx
from pydantic import SecretStr

_private_request: ContextVar[bool] = ContextVar("kit_private_request", default=False)


class _PrivateHTTPLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not _private_request.get()


_private_filter = _PrivateHTTPLogs()


def _protect_http_logs() -> None:
    # Filter only this request's standard library HTTP logs. Other callers and
    # threads retain their logging. Host tracing/injected transports remain a
    # separate redaction responsibility.
    for name in (
        "httpx",
        "httpcore.connection",
        "httpcore.http11",
        "httpcore.http2",
        "httpcore.proxy",
        "httpcore.socks",
    ):
        logging.getLogger(name).addFilter(_private_filter)


class KitAPIError(RuntimeError):
    """Safe diagnostic: never retain provider bodies, request URLs or credentials."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int | None = None,
        outcome_unknown: bool = False,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.outcome_unknown = outcome_unknown
        self.retry_after_seconds = retry_after_seconds


_MAX_RESPONSE_BYTES = 1_048_576
_WHOLE_SECONDS = 30.0


def _check_deadline(deadline: float) -> None:
    if time.monotonic() >= deadline:
        raise KitAPIError("TRANSPORT", "Kit response deadline exceeded")


def _invalid_constant(value: str) -> None:
    raise ValueError("Non-finite JSON number")


def _check_json_depth(content: bytearray) -> None:
    depth = 0
    quoted = False
    escaped = False
    for byte in content:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > 64:
                raise KitAPIError("RESPONSE", "Kit JSON nesting exceeds bound")
        elif byte in (93, 125):
            depth -= 1


class KitTransport:
    """One bounded attempt with injected credentials and no provider base URL."""

    def __init__(
        self,
        api_key: SecretStr | None = None,
        *,
        access_token: SecretStr | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
    ) -> None:
        if (api_key is None) == (access_token is None):
            raise ValueError("Supply exactly one Kit API key or OAuth access token")
        credential = api_key if api_key is not None else access_token
        if not isinstance(credential, SecretStr):
            raise ValueError("Kit credential must be an injected SecretStr")
        token = credential.get_secret_value()
        if (
            type(token) is not str
            or not token
            or len(token) > 8192
            or any(ord(c) < 33 or ord(c) > 126 for c in token)
        ):
            raise ValueError("Kit credential must be nonempty and header-safe")
        if (
            type(timeout) not in (int, float)
            or not 0 < timeout <= 30
            or not math.isfinite(timeout)
        ):
            raise ValueError("Kit phase timeout must be finite and within 30 seconds")
        _protect_http_logs()
        self._token = credential
        self._auth_header = "X-Kit-Api-Key" if api_key is not None else "Authorization"
        self._auth_prefix = "" if api_key is not None else "Bearer "
        self._http = httpx.Client(
            transport=transport,
            timeout=httpx.Timeout(timeout),
            trust_env=False,
            follow_redirects=False,
        )

    def close(self) -> None:
        self._http.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        params: dict[str, str | int | bool] | None = None,
    ) -> dict[str, Any]:
        if (
            method != "GET"
            or type(path) is not str
            or path
            not in {"/v4/subscribers", "/v4/tags", "/v4/forms", "/v4/custom_fields"}
            or body is not None
        ):
            raise ValueError("Kit route is outside the read-only migration surface")
        query = self._query(path, params)
        deadline = time.monotonic() + _WHOLE_SECONDS
        failure = None
        content = bytearray()
        private_token = _private_request.set(True)
        try:
            with self._http.stream(
                "GET",
                "https://api.kit.com" + path,
                headers={
                    self._auth_header: self._auth_prefix
                    + self._token.get_secret_value(),
                    "Accept": "application/json",
                    "Accept-Encoding": "identity",
                },
                params=query,
            ) as response:
                _check_deadline(deadline)
                if not 200 <= response.status_code < 300:
                    self._refuse_status(response)
                if (
                    response.headers.get("Content-Encoding", "identity").lower()
                    != "identity"
                ):
                    raise KitAPIError("RESPONSE", "Encoded Kit response refused")
                length = response.headers.get("Content-Length", "")
                if (
                    length.isascii()
                    and length.isdigit()
                    and (len(length) > 8 or int(length) > _MAX_RESPONSE_BYTES)
                ):
                    raise KitAPIError("RESPONSE", "Kit response exceeds byte bound")
                # No chunk_size: a buffer must not hide a slow trickle from the clock.
                # Encoding is refused above, so these are identity response bytes.
                for chunk in response.iter_bytes():
                    _check_deadline(deadline)
                    if len(content) + len(chunk) > _MAX_RESPONSE_BYTES:
                        raise KitAPIError("RESPONSE", "Kit response exceeds byte bound")
                    content.extend(chunk)
            _check_deadline(deadline)
            _check_json_depth(content)
            data = json.loads(content, parse_constant=_invalid_constant)
            _check_deadline(deadline)
            if not isinstance(data, dict):
                raise KitAPIError(
                    "RESPONSE", "Kit returned an unexpected response shape"
                )
        except httpx.HTTPError:
            failure = KitAPIError("TRANSPORT", "Kit read transport failed; no retry")
        except ValueError, RecursionError:
            failure = KitAPIError("RESPONSE", "Kit returned invalid JSON data")
        finally:
            _private_request.reset(private_token)
        # Outside handlers: __context__ must not retain requests or provider PII.
        if failure is not None:
            raise failure
        return data

    @staticmethod
    def _query(
        path: str, params: dict[str, str | int | bool] | None
    ) -> dict[str, str | int | bool]:
        if params is not None and type(params) is not dict:
            raise ValueError("Kit query must be a bounded dictionary")
        query = dict(params or {})
        allowed = {"per_page", "after"}
        if path == "/v4/subscribers":
            allowed |= {"status", "slim"}
        elif path == "/v4/forms":
            allowed |= {"status"}
        if set(query) - allowed:
            raise ValueError("Kit query is outside the read-only migration surface")
        per_page = query.get("per_page", 50)
        if type(per_page) is not int or not 1 <= per_page <= 1000:
            raise ValueError("Kit per_page must be an integer between 1 and 1000")
        query["per_page"] = per_page
        if "after" in query:
            after = query["after"]
            if (
                type(after) is not str
                or not 1 <= len(after) <= 2048
                or any(ord(c) < 33 or ord(c) > 126 for c in after)
            ):
                raise ValueError("Kit cursor must be bounded printable ASCII")
        if path in {"/v4/subscribers", "/v4/forms"}:
            statuses = (
                {"active", "archived", "trashed", "all"}
                if path == "/v4/forms"
                else {"active", "inactive", "bounced", "complained", "cancelled", "all"}
            )
            status = query.get("status", "all")
            if type(status) is not str or status not in statuses:
                raise ValueError("Kit status is outside the read-only contract")
            query["status"] = status
        if path == "/v4/subscribers":
            if "slim" in query and type(query["slim"]) is not bool:
                raise ValueError("Kit slim must be boolean")
            query.setdefault("slim", False)
        return query

    @staticmethod
    def _refuse_status(response: httpx.Response) -> None:
        status = response.status_code
        code, message = {
            401: (
                "AUTHENTICATION",
                "Kit token is invalid or expired; stop and reauthorize",
            ),
            403: ("ACCESS", "Kit access denied"),
            404: ("NOT_FOUND", "Kit migration resource was not found"),
            429: ("RATE_LIMIT", "Kit rate limit reached; no retry"),
        }.get(status, ("HTTP", "Kit rejected the read request"))
        retry = response.headers.get("Retry-After", "")
        raise KitAPIError(
            code,
            message,
            status_code=status,
            retry_after_seconds=int(retry)
            if retry.isascii() and retry.isdigit() and len(retry) < 9
            else None,
        )
