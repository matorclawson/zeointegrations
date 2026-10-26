"""Credentials, effects, canonical tool wiring, bounded reads and error privacy."""

from __future__ import annotations

import logging

import httpx
import pytest
from pydantic import SecretStr

from zeo_integrations.kit import (
    KitAPIError,
    KitTransport,
)

from .conftest import CANARY


@pytest.mark.parametrize(
    "method,status,unknown",
    [
        ("GET", 500, False),
        ("POST", 503, True),
        ("POST", 401, False),
        ("POST", 403, False),
        ("POST", 404, False),
        ("POST", 429, False),
        ("POST", 302, False),
    ],
)
def test_http_failures_are_safe_and_never_retried(
    method: str, status: int, unknown: bool
) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            status,
            text=CANARY,
            headers={"Retry-After": "60", "Location": "https://evil.invalid/" + CANARY},
        )

    transport = KitTransport(SecretStr(CANARY), transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(KitAPIError) as error:
            transport.request(method, "/v4/broadcasts")
        assert error.value.outcome_unknown is unknown
        assert error.value.retry_after_seconds == 60
        assert CANARY not in str(error.value)
        assert len(calls) == 1
    finally:
        transport.close()


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(201, text="bad-json"),
        httpx.Response(201, json=[]),
        httpx.ReadTimeout("secret-timeout"),
    ],
)
def test_ambiguous_mutation_outcome_is_not_replayed(
    response: httpx.Response | Exception,
) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if isinstance(response, Exception):
            raise response
        return response

    transport = KitTransport(SecretStr(CANARY), transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(KitAPIError) as error:
            transport.request("POST", "/v4/broadcasts", body={})
        assert error.value.outcome_unknown and len(calls) == 1
        assert "secret" not in str(error.value)
    finally:
        transport.close()


@pytest.mark.parametrize(
    "path,method",
    [
        ("https://evil.invalid/v4/account", "GET"),
        ("/v4/purchases", "POST"),
        ("/v4/broadcasts/../subscribers", "GET"),
        ("/v4/broadcasts/%2e%2e/subscribers", "GET"),
        ("/v4/account?key=secret", "GET"),
        ("/v4/sequences/1/subscribers/2", "DELETE"),
        ("/v4/subscribers/2", "PUT"),
    ],
)
def test_route_boundary_excludes_undocumented_or_nonmarketing_operations(
    path: str, method: str
) -> None:
    transport = KitTransport(
        SecretStr(CANARY),
        transport=httpx.MockTransport(
            lambda r: pytest.fail("Unexpected network request")
        ),
    )
    try:
        with pytest.raises(ValueError):
            transport.request(method, path)
    finally:
        transport.close()


def test_authentication_headers_and_log_privacy(
    caplog: pytest.LogCaptureFixture,
) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        logging.getLogger("httpcore.http11").debug(CANARY)
        return httpx.Response(200, json={})

    caplog.set_level(logging.DEBUG)
    transport = KitTransport(
        access_token=SecretStr(CANARY), transport=httpx.MockTransport(handler)
    )
    try:
        transport.request("GET", "/v4/account")
        assert calls[0].headers["Authorization"] == "Bearer " + CANARY
        assert "X-Kit-Api-Key" not in calls[0].headers
        assert CANARY not in caplog.text
        logging.getLogger("httpx").info("other-call-visible")
        assert "other-call-visible" in caplog.text
    finally:
        transport.close()
    for kwargs in [
        {},
        {"api_key": SecretStr(" ")},
        {"api_key": SecretStr(CANARY), "access_token": SecretStr(CANARY)},
        {"api_key": SecretStr(CANARY), "timeout": 0},
    ]:
        with pytest.raises(ValueError):
            KitTransport(**kwargs)  # type: ignore[arg-type]
