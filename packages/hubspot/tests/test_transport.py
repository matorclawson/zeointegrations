"""Synthetic boundary checks; no provider credentials or network."""

import logging
import math
import unittest
from unittest.mock import patch

import httpx
from pydantic import SecretStr

from zeo_integrations.hubspot.transport import HubSpotAPIError, HubSpotTransport


class Stream(httpx.SyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks
        self.closed = False

    def __iter__(self):
        yield from self.chunks

    def close(self):
        self.closed = True


class TransportBoundary(unittest.TestCase):
    def boundary(self, callback, **kwargs):
        result = HubSpotTransport(
            SecretStr("synthetic-token"),
            transport=httpx.MockTransport(callback),
            **kwargs,
        )
        self.addCleanup(result.close)
        return result

    def test_fixed_origin_auth_and_private_logs(self):
        calls = []
        records = []

        class Sink(logging.Handler):
            def emit(self, record):
                records.append(record.getMessage())

        logger = logging.getLogger("httpx")
        handler = Sink()
        logger.addHandler(handler)
        self.addCleanup(logger.removeHandler, handler)

        def callback(request):
            calls.append(request)
            logger.warning("synthetic-sensitive-body")
            return httpx.Response(200, json={"results": []})

        client = self.boundary(callback)
        client.request("GET", "/marketing/emails/2026-03")
        self.assertEqual(
            str(calls[0].url), "https://api.hubapi.com/marketing/emails/2026-03"
        )
        self.assertEqual(calls[0].headers["Authorization"], "Bearer synthetic-token")
        self.assertEqual(calls[0].headers["Accept-Encoding"], "identity")
        self.assertNotIn("synthetic-token", str(calls[0].url))
        self.assertEqual(records, [])
        logger.warning("unrelated-visible")
        self.assertEqual(records, ["unrelated-visible"])

    def test_rejected_routes_never_reach_transport(self):
        calls = []
        client = self.boundary(lambda r: calls.append(r))
        for path in [
            "https://elsewhere.invalid",
            "/crm/v3/objects",
            "/marketing/emails/2026-03/../x",
            "/marketing/emails/2026-03?token=x",
            "/marketing/emails/2026-03/%0a",
        ]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                client.request("GET", path)
        self.assertEqual(calls, [])

    def test_redirect_and_auth_failure_are_not_retried(self):
        for status in [302, 401, 403, 429, 503]:
            calls = []
            client = self.boundary(
                lambda r, calls=calls, status=status: (
                    calls.append(r),
                    httpx.Response(
                        status,
                        headers={
                            "Location": "https://elsewhere.invalid",
                            "Retry-After": "9999999",
                        },
                    ),
                )[1]
            )
            with (
                self.subTest(status=status),
                self.assertRaises(HubSpotAPIError) as raised,
            ):
                client.request("POST", "/marketing/emails/2026-03", body={})
            self.assertEqual(len(calls), 1)
            self.assertEqual(raised.exception.outcome_unknown, status >= 500)
            self.assertEqual(raised.exception.retry_after_seconds, 86400)

    def test_read_only_post_preserves_ambiguity_classification(self):
        def fail(request):
            raise httpx.ReadTimeout("synthetic-sensitive-body", request=request)

        client = self.boundary(fail)
        for read_only in [False, True]:
            with (
                self.subTest(read_only=read_only),
                self.assertRaises(HubSpotAPIError) as raised,
            ):
                client.request(
                    "POST",
                    "/automation/v4/workflow-id-mappings/batch/read",
                    body={},
                    read_only=read_only,
                )
            self.assertEqual(raised.exception.outcome_unknown, not read_only)
            self.assertIsNone(raised.exception.__context__)
            self.assertIsNone(raised.exception.__cause__)
            self.assertNotIn("synthetic-sensitive-body", str(raised.exception))
            self.assertNotIn("synthetic-token", str(raised.exception))

    def test_encoding_and_declared_size_refused_without_body(self):
        for headers in [
            {"Content-Encoding": "gzip"},
            {"Content-Length": "1048577"},
            {"Content-Length": "invalid"},
        ]:
            stream = Stream([b"never-read"])
            client = self.boundary(
                lambda r, headers=headers, stream=stream: httpx.Response(200, headers=headers, stream=stream)
            )
            with self.subTest(headers=headers), self.assertRaises(HubSpotAPIError):
                client.request("GET", "/marketing/emails/2026-03")
            self.assertTrue(stream.closed)

    def test_actual_size_limit_closes_stream_and_marks_mutation_unknown(self):
        stream = Stream([b"x" * 524288, b"x" * 524289])
        client = self.boundary(lambda r: httpx.Response(200, stream=stream))
        with self.assertRaises(HubSpotAPIError) as raised:
            client.request("PATCH", "/marketing/emails/2026-03/1", body={})
        self.assertTrue(stream.closed)
        self.assertTrue(raised.exception.outcome_unknown)

    def test_whole_deadline_counts_unbuffered_chunks(self):
        stream = Stream([b'{"ok":', b"true}"])
        client = self.boundary(lambda r: httpx.Response(200, stream=stream), timeout=30)
        with patch(
            "zeo_integrations.hubspot.transport.time.monotonic",
            side_effect=[0, 1, 2, 31],
        ):
            with self.assertRaises(HubSpotAPIError) as raised:
                client.request("GET", "/marketing/emails/2026-03")
        self.assertEqual(raised.exception.code, "TRANSPORT")
        self.assertTrue(stream.closed)

    def test_invalid_json_and_shape_drop_exception_context(self):
        for content in [b"synthetic-sensitive-body", b"[]"]:
            client = self.boundary(lambda r, content=content: httpx.Response(200, content=content))
            with (
                self.subTest(content=content),
                self.assertRaises(HubSpotAPIError) as raised,
            ):
                client.request("GET", "/marketing/emails/2026-03")
            self.assertIsNone(raised.exception.__context__)
            self.assertNotIn("synthetic-sensitive-body", str(raised.exception))

    def test_invalid_timeout_and_credential_before_http_initialization(self):
        for timeout in [True, 0, 121, math.nan, math.inf]:
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                HubSpotTransport(SecretStr("synthetic-token"), timeout=timeout)
        for token in ["", "unsafe\nheader", "x" * 8193]:
            with self.subTest(token_length=len(token)), self.assertRaises(ValueError):
                HubSpotTransport(SecretStr(token))

    def test_empty_response_and_normal_json(self):
        for status, content, expected in [
            (204, b"", {}),
            (200, b'{"ok":true}', {"ok": True}),
        ]:
            client = self.boundary(lambda r, status=status, content=content: httpx.Response(status, content=content))
            self.assertEqual(
                client.request("GET", "/marketing/emails/2026-03"), expected
            )
