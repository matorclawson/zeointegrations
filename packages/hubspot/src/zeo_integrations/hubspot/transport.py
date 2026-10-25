# MIT License
#
# Copyright (c) 2026 Rod Rivera
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Fixed-origin HubSpot HTTP boundary with no implicit mutation retries."""

from __future__ import annotations

import json
import logging
import math
import time
from contextvars import ContextVar
from typing import Any
from urllib.parse import unquote

import httpx
from pydantic import SecretStr

_private_request: ContextVar[bool] = ContextVar(
    "hubspot_private_request", default=False
)


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


class HubSpotAPIError(RuntimeError):
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


class HubSpotTransport:
    """A caller may inject an HTTP transport, never a provider base URL."""

    def __init__(
        self,
        access_token: SecretStr,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        if not isinstance(access_token, SecretStr):
            raise ValueError("HubSpot access token must be injected as SecretStr")
        token = access_token.get_secret_value()
        if (
            not token
            or len(token) > 8192
            or any(not 33 <= ord(c) <= 126 for c in token)
        ):
            raise ValueError("HubSpot access token is not header-safe")
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or not 0 < timeout <= 120
        ):
            raise ValueError("HubSpot timeout must be between zero and 120 seconds")
        _protect_http_logs()
        self._token = access_token
        self._whole_timeout = timeout
        self._http = httpx.Client(
            transport=transport,
            timeout=timeout,
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
        read_only: bool = False,
    ) -> dict[str, Any]:
        allowed = (
            "/marketing/emails/2026-03",
            "/marketing/campaigns/2026-03",
            "/communication-preferences/2026-03",
            "/automation/v4/flows",
            "/automation/v4/workflow-id-mappings/batch/read",
            "/automation/v2/workflows/",
        )
        if (
            not any(
                path == prefix or path.startswith(prefix.rstrip("/") + "/")
                for prefix in allowed
            )
            or any(part in {".", ".."} for part in unquote(path).split("/"))
            or "\\" in unquote(path)
            or any(ord(character) < 32 for character in unquote(path))
            or method not in {"GET", "POST", "PATCH", "PUT", "DELETE"}
            or "?" in path
            or "#" in path
        ):
            raise ValueError("HubSpot route is outside the marketing integration")
        mutation = method != "GET" and not read_only
        started = time.monotonic()
        private_token = _private_request.set(True)
        failure: tuple[str, str, int | None, bool, int | None] | None = None
        raw = bytearray()
        no_content = False
        try:
            with self._http.stream(
                method,
                "https://api.hubapi.com" + path,
                headers={
                    "Authorization": "Bearer " + self._token.get_secret_value(),
                    "Accept": "application/json",
                    "Accept-Encoding": "identity",
                },
                json=body,
                params=params,
            ) as response:
                status = response.status_code
                if not 200 <= status < 300:
                    code, message = {
                        401: (
                            "AUTHENTICATION",
                            (
                                "HubSpot token is invalid or expired; "
                                "reauthorize before retrying"
                            ),
                        ),
                        403: (
                            "ACCESS",
                            (
                                "HubSpot access denied; check app scopes "
                                "and Marketing Hub subscription tier"
                            ),
                        ),
                        404: ("NOT_FOUND", "HubSpot marketing resource was not found"),
                        429: (
                            "RATE_LIMIT",
                            (
                                "HubSpot rate limit reached; "
                                "no automatic retry was attempted"
                            ),
                        ),
                    }.get(status, ("HTTP", "HubSpot rejected the marketing request"))
                    retry = response.headers.get("Retry-After", "")
                    retry_seconds = (
                        min(int(retry), 86400)
                        if retry.isascii() and retry.isdigit() and len(retry) < 9
                        else None
                    )
                    failure = (
                        code,
                        message,
                        status,
                        mutation and status >= 500,
                        retry_seconds,
                    )
                elif time.monotonic() - started > self._whole_timeout:
                    failure = (
                        "TRANSPORT",
                        (
                            "HubSpot request exceeded its whole deadline; "
                            "reconcile before retry"
                        ),
                        None,
                        mutation,
                        None,
                    )
                elif status == 204:
                    no_content = True
                elif response.headers.get(
                    "Content-Encoding", "identity"
                ).lower() not in {"", "identity"}:
                    failure = (
                        "RESPONSE",
                        "HubSpot returned an encoded response",
                        None,
                        mutation,
                        None,
                    )
                else:
                    length = response.headers.get("Content-Length")
                    if length is not None and (
                        not length.isascii()
                        or not length.isdigit()
                        or len(length) > 10
                        or int(length) > 1048576
                    ):
                        failure = (
                            "RESPONSE",
                            ("HubSpot response exceeds the bounded body contract"),
                            None,
                            mutation,
                            None,
                        )
                    else:
                        for chunk in response.iter_bytes():
                            if time.monotonic() - started > self._whole_timeout:
                                failure = (
                                    "TRANSPORT",
                                    (
                                        "HubSpot request exceeded its whole deadline; "
                                        "reconcile before retry"
                                    ),
                                    None,
                                    mutation,
                                    None,
                                )
                                break
                            if len(raw) + len(chunk) > 1048576:
                                failure = (
                                    "RESPONSE",
                                    (
                                        "HubSpot response exceeds "
                                        "the bounded body contract"
                                    ),
                                    None,
                                    mutation,
                                    None,
                                )
                                break
                            raw.extend(chunk)
        except httpx.HTTPError:
            failure = (
                "TRANSPORT",
                (
                    "HubSpot request failed; reconcile provider "
                    "state before repeating a mutation"
                ),
                None,
                mutation,
                None,
            )
        finally:
            _private_request.reset(private_token)
        # EOF and response cleanup can consume the remaining budget without
        # yielding another chunk. Preserve any earlier provider failure.
        if failure is None and time.monotonic() - started > self._whole_timeout:
            failure = (
                "TRANSPORT",
                "HubSpot request exceeded its whole deadline; reconcile before retry",
                None,
                mutation,
                None,
            )
        # Raise only after handlers finish: normalized errors must not retain an
        # HTTP request, provider body or injected credential as __context__.
        if failure is not None:
            code, message, status, unknown, retry_seconds = failure
            raise HubSpotAPIError(
                code,
                message,
                status_code=status,
                outcome_unknown=unknown,
                retry_after_seconds=retry_seconds,
            )
        if no_content:
            return {}
        invalid = False
        try:
            data = json.loads(raw)
        except (ValueError, RecursionError):
            invalid = True
        if invalid:
            raise HubSpotAPIError(
                "RESPONSE",
                "HubSpot returned an invalid JSON response",
                outcome_unknown=mutation,
            )
        if not isinstance(data, dict):
            raise HubSpotAPIError(
                "RESPONSE",
                "HubSpot returned an unexpected response shape",
                outcome_unknown=mutation,
            )
        return data
