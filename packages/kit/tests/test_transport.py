# Copyright (c) 2026 Rod Rivera
# SPDX-License-Identifier: MIT
# Original synthetic controls; no private Broker fixture copying.
import unittest
from unittest.mock import patch

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


class _Chunks(httpx.SyncByteStream):
    def __init__(self, chunks, clock=None):
        self.chunks = chunks
        self.clock = clock
        self.seen = 0
        self.closed = False

    def __iter__(self):
        for chunk in self.chunks:
            self.seen += 1
            if self.clock is not None:
                self.clock[0] += 16
            yield chunk

    def close(self):
        self.closed = True


class StreamBounds(unittest.TestCase):
    boundary = TransportBoundary.boundary

    def test_oversize_stops_stream_and_closes(self):
        stream = _Chunks([b"x" * 1_048_576, b"x", b"must-not-read"])
        boundary = self.boundary(lambda request: httpx.Response(200, stream=stream))
        with self.assertRaises(KitAPIError) as raised:
            boundary.request("GET", "/v4/tags")
        self.assertEqual(raised.exception.code, "RESPONSE")
        self.assertEqual(stream.seen, 2)
        self.assertTrue(stream.closed)

    def test_unbuffered_slow_trickle_exceeds_whole_deadline(self):
        clock = [0.0]
        stream = _Chunks([b'{"tags":', b"[]}", b"must-not-read"], clock)
        boundary = self.boundary(lambda request: httpx.Response(200, stream=stream))
        with patch(
            "zeo_integrations.kit.transport.time.monotonic",
            side_effect=lambda: clock[0],
        ):
            with self.assertRaises(KitAPIError) as raised:
                boundary.request("GET", "/v4/tags")
        self.assertEqual(raised.exception.code, "TRANSPORT")
        self.assertEqual(stream.seen, 2)
        self.assertTrue(stream.closed)

    def test_encoding_and_declared_size_refused_before_body(self):
        for headers in [
            {"Content-Encoding": "gzip"},
            {"Content-Encoding": "br"},
            {"Content-Length": "1048577"},
        ]:
            stream = _Chunks([b"must-not-read"])
            boundary = self.boundary(
                lambda request, headers=headers, stream=stream: httpx.Response(
                    200, headers=headers, stream=stream
                )
            )
            with self.subTest(headers=headers), self.assertRaises(KitAPIError):
                boundary.request("GET", "/v4/tags")
            self.assertEqual(stream.seen, 0)
            self.assertTrue(stream.closed)

    def test_raw_query_bounds_before_http(self):
        def forbidden(request):
            self.fail("invalid query reached HTTP")

        boundary = self.boundary(forbidden)
        cases = [{"per_page": value} for value in [True, 0, 1001, "10", 1.0]]
        cases += [{"after": value} for value in [None, "", "x" * 2049, "x\n", "é"]]
        cases += [{"status": "pending"}, {"status": []}, {"slim": "false"}]
        for params in cases:
            with self.subTest(params=params), self.assertRaises(ValueError):
                boundary.request("GET", "/v4/subscribers", params=params)

    def test_identity_encoding_and_bounded_query_on_wire(self):
        calls = []

        def reply(request):
            calls.append(request)
            return httpx.Response(200, json={})

        self.boundary(reply).request(
            "GET",
            "/v4/subscribers",
            params={
                "per_page": 1000,
                "after": "cursor==",
                "status": "cancelled",
                "slim": False,
            },
        )
        self.assertEqual(calls[0].headers["Accept-Encoding"], "identity")
        self.assertEqual(calls[0].url.params["per_page"], "1000")
        self.assertEqual(calls[0].url.params["after"], "cursor==")

    def test_normalized_errors_drop_original_context(self):
        def transport_fail(request):
            raise httpx.ReadError("synthetic-private-marker", request=request)

        cases = [transport_fail]
        for content in [
            b"\xff",
            b'{"n":NaN}',
            b'{"n":Infinity}',
            b'{"x":' * 2000 + b"0" + b"}" * 2000,
        ]:
            cases.append(
                lambda request, content=content: httpx.Response(
                    200, stream=_Chunks([content])
                )
            )
        for handler in cases:
            with self.subTest(handler=handler):
                with self.assertRaises(KitAPIError) as raised:
                    self.boundary(handler).request("GET", "/v4/tags")
                self.assertIsNone(raised.exception.__context__)
                self.assertIsNone(raised.exception.__cause__)
                self.assertNotIn("synthetic-private-marker", str(raised.exception))

    def test_invalid_credential_or_timeout_before_http_client(self):
        for value in ["", " ", "bad\r\nheader", "é", "x" * 8193]:
            with self.subTest(value=len(value)), self.assertRaises(ValueError):
                KitTransport(SecretStr(value))
        for value in [True, False, float("nan"), float("inf"), -1, 0, 31, "1"]:
            with self.subTest(timeout=value), self.assertRaises(ValueError):
                KitTransport(SecretStr("synthetic-test-only"), timeout=value)

    def test_json_depth_bound_respects_strings_and_escapes(self):
        import json

        content = json.dumps({"text": '[{"\\' * 1000}).encode()
        response = self.boundary(
            lambda request: httpx.Response(200, stream=_Chunks([content]))
        ).request("GET", "/v4/tags")
        self.assertEqual(response["text"], '[{"\\' * 1000)
        for depth in [64, 65]:
            content = b'{"x":' * depth + b"0" + b"}" * depth
            boundary = self.boundary(
                lambda request, content=content: httpx.Response(
                    200, stream=_Chunks([content])
                )
            )
            if depth == 64:
                self.assertIsInstance(boundary.request("GET", "/v4/tags"), dict)
            else:
                with self.assertRaises(KitAPIError):
                    boundary.request("GET", "/v4/tags")
