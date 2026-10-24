# Copyright (c) 2026 Rod Rivera
# SPDX-License-Identifier: MIT
# Original synthetic controls; no private Broker fixture copying.
import unittest

import httpx
from pydantic import SecretStr

from zeo_integrations.kit import KitAPIError, KitTransport


class TransportBoundary(unittest.TestCase):
    def boundary(self, handler):
        result = KitTransport(
            SecretStr("synthetic-test-only"), transport=httpx.MockTransport(handler)
        )
        self.addCleanup(result.close)
        return result

    def test_no_write_or_unallocated_read_reaches_http(self):
        def forbidden(request):
            self.fail("refused route reached HTTP")

        boundary = self.boundary(forbidden)
        for method in ["POST", "PUT", "DELETE", "PATCH", "HEAD", "get"]:
            with self.subTest(method=method), self.assertRaises(ValueError):
                boundary.request(method, "/v4/subscribers")
        for path in [
            "/v4/broadcasts",
            "/v4/sequences",
            "/v4/account",
            "/v3/subscribers",
            "/v4/subscribers/1",
            "/v4/forms?x=1",
            "https://example.invalid/v4/forms",
            "/v4/%2e%2e/forms",
        ]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                boundary.request("GET", path)
        with self.assertRaises(ValueError):
            boundary.request("GET", "/v4/forms", body={})

    def test_unknown_query_cannot_override_read_method(self):
        def forbidden(request):
            self.fail("query escape reached HTTP")

        boundary = self.boundary(forbidden)
        for key in ["_method", "method", "send_at", "subscriber_id", "callback"]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                boundary.request("GET", "/v4/forms", params={key: "POST"})

    def test_safe_errors_without_retries(self):
        for status, code in [
            (401, "AUTHENTICATION"),
            (403, "ACCESS"),
            (429, "RATE_LIMIT"),
            (500, "HTTP"),
        ]:
            calls = []

            def reply(request, calls=calls, status=status):
                calls.append(request)
                return httpx.Response(
                    status,
                    json={"secret": "never-retain"},
                    headers={"Retry-After": "12"},
                )

            boundary = self.boundary(reply)
            with self.subTest(status=status), self.assertRaises(KitAPIError) as raised:
                boundary.request("GET", "/v4/forms")
            self.assertEqual(raised.exception.code, code)
            self.assertEqual(len(calls), 1)
            self.assertNotIn("never-retain", str(raised.exception))
            self.assertFalse(raised.exception.outcome_unknown)
            self.assertEqual(raised.exception.retry_after_seconds, 12)

    def test_redirect_is_not_followed(self):
        calls = []

        def reply(request):
            calls.append(request)
            self.assertEqual(request.url.host, "api.kit.com")
            return httpx.Response(302, headers={"Location": "https://example.invalid"})

        with self.assertRaises(KitAPIError):
            self.boundary(reply).request("GET", "/v4/forms")
        self.assertEqual(len(calls), 1)

    def test_malformed_json_and_http_failure(self):
        for response in [
            httpx.Response(200, content=b"bad-json"),
            httpx.Response(200, json=[]),
        ]:
            with self.assertRaises(KitAPIError) as raised:
                self.boundary(lambda request, response=response: response).request(
                    "GET", "/v4/tags"
                )
            self.assertEqual(raised.exception.code, "RESPONSE")

        def fail(request):
            raise httpx.ConnectError("private diagnostics", request=request)

        with self.assertRaises(KitAPIError) as raised:
            self.boundary(fail).request("GET", "/v4/tags")
        self.assertEqual(raised.exception.code, "TRANSPORT")
        self.assertNotIn("private diagnostics", str(raised.exception))
