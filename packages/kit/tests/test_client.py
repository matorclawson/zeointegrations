# Copyright (c) 2026 Rod Rivera
# SPDX-License-Identifier: MIT
# Original synthetic controls; no private Broker fixture copying.
import unittest

import httpx
from pydantic import SecretStr

from zeo_integrations.kit import KitAPIError, KitClient, KitTransport, PageRequest


def envelope(key, rows, *, more=False, previous=False, cursor="next"):
    return {
        key: rows,
        "pagination": {
            "has_next_page": more,
            "has_previous_page": previous,
            "end_cursor": cursor,
        },
    }


class ClientReads(unittest.TestCase):
    def client(self, data):
        self.requests = []

        def reply(request):
            self.requests.append(request)
            return httpx.Response(200, json=data)

        boundary = KitTransport(
            SecretStr("synthetic-test-only"), transport=httpx.MockTransport(reply)
        )
        client = KitClient(transport=boundary)
        self.addCleanup(client.close)
        return client

    def test_all_subscriber_states_and_fields_survive(self):
        states = ["active", "inactive", "bounced", "complained", "cancelled"]
        dates = [
            "2024-02-29T00:00:00Z",
            "2026-10-24T12:34:56.123456789+05:30",
            "2023-01-27T11:43:55-07:00",
            "2026-10-24T00:00:00.000+00:00",
            "2024-02-29T23:59:59Z",
        ]
        rows = [
            {
                "id": i + 1,
                "state": state,
                "created_at": dates[i],
                "email_address": "user@example.invalid",
                "first_name": None,
                "fields": {"team": "demo", "optional": None},
            }
            for i, state in enumerate(states)
        ]
        result = self.client(envelope("subscribers", rows)).list_subscribers()
        self.assertEqual([row["state"] for row in result.results], states)
        self.assertEqual([row["created_at"] for row in result.results], dates)
        self.assertEqual(result.results[-1]["fields"], rows[-1]["fields"])
        self.assertTrue(result.complete)
        self.assertEqual(self.requests[0].url.params["status"], "all")
        self.assertEqual(self.requests[0].url.params["slim"], "false")

    def test_four_exact_get_reads(self):
        cases = [
            ("tags", "list_tags", {"id": 1, "name": "migration"}),
            (
                "forms",
                "list_forms",
                {
                    "id": 1,
                    "name": "audit",
                    "type": "embed",
                    "archived": True,
                    "embed_js": "never return",
                    "embed_url": "https://example.invalid/form",
                },
            ),
            (
                "custom_fields",
                "list_custom_fields",
                {"id": 1, "name": "ck_field", "key": "team", "label": "Team"},
            ),
        ]
        for key, method, row in cases:
            with self.subTest(key=key):
                result = getattr(self.client(envelope(key, [row])), method)()
                self.assertEqual(self.requests[0].method, "GET")
                self.assertEqual(self.requests[0].url.path, "/v4/" + key)
                self.assertNotIn("embed_js", result.results[0])
                self.assertNotIn("embed_url", result.results[0])
                self.assertEqual(len(self.requests), 1)
                if key == "forms":
                    self.assertEqual(self.requests[0].url.params["status"], "all")

    def test_cursor_and_completeness(self):
        client = self.client(envelope("tags", [], more=True))
        result = client.list_tags(PageRequest(per_page=2))
        self.assertEqual(result.next_after, "next")
        self.assertFalse(result.complete)
        client = self.client(envelope("tags", [], previous=True))
        result = client.list_tags(PageRequest(after="last"))
        self.assertFalse(result.complete)
        self.assertEqual(self.requests[0].url.params["after"], "last")
        self.assertIsNone(result.next_after)

    def test_invalid_pages_fail_closed(self):
        cases = [
            {},
            {"tags": [], "pagination": {}},
            envelope("tags", [{"id": True, "name": "invalid"}]),
            envelope("tags", [{"id": 1, "name": "one"}] * 2),
            envelope("tags", [], more=True, cursor=""),
            envelope("tags", [], more=True, cursor="same"),
            envelope("tags", "not-a-list"),
        ]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(KitAPIError) as raised:
                self.client(data).list_tags(PageRequest(after="same"))
            self.assertEqual(raised.exception.code, "RESPONSE")

    def test_missing_or_invalid_subscriber_state_refused(self):
        row = {
            "id": 1,
            "email_address": "user@example.invalid",
            "first_name": None,
            "created_at": "2024-02-29T00:00:00Z",
            "fields": {},
        }
        for state in [None, "unknown", True]:
            with self.subTest(state=state), self.assertRaises(KitAPIError):
                self.client(
                    envelope("subscribers", [{**row, "state": state}])
                ).list_subscribers()

    def test_filters_fail_before_request(self):
        client = self.client(envelope("forms", []))
        with self.assertRaises(ValueError):
            client.list_forms(status="pending")
        with self.assertRaises(ValueError):
            client.list_subscribers(status="pending")
        self.assertEqual(self.requests, [])

    def test_provider_model_error_does_not_retain_validation_context(self):
        row = {"id": "synthetic-private-marker", "name": "audit"}
        with self.assertRaises(KitAPIError) as raised:
            self.client(envelope("tags", [row])).list_tags()
        self.assertIsNone(raised.exception.__context__)
        self.assertIsNone(raised.exception.__cause__)
        self.assertNotIn("synthetic-private-marker", str(raised.exception))

    def test_present_invalid_provider_date_refuses_the_page_safely(self):
        row = {
            "id": 1,
            "state": "active",
            "email_address": "user@example.invalid",
            "first_name": None,
            "fields": {},
        }
        cases = [
            {**row, "created_at": value}
            for value in [
                1700000000,
                "synthetic-private-marker",
                "2023-02-29T00:00:00Z",
                "2024-02-29T00:00:00",
            ]
        ]
        for candidate in cases:
            with self.subTest(candidate=candidate):
                with self.assertRaises(KitAPIError) as raised:
                    self.client(envelope("subscribers", [candidate])).list_subscribers()
                self.assertEqual(raised.exception.code, "RESPONSE")
                self.assertIsNone(raised.exception.__context__)
                self.assertIsNone(raised.exception.__cause__)
                self.assertNotIn("synthetic-private-marker", str(raised.exception))
                self.assertEqual(len(self.requests), 1)

    def test_missing_and_null_provider_dates_preserve_compatible_pages(self):
        rows = []
        for state in ["active", "inactive", "bounced", "complained", "cancelled"]:
            for supplied in [False, True]:
                row = {
                    "id": len(rows) + 1,
                    "state": state,
                    "email_address": "user@example.invalid",
                    "first_name": None,
                    "fields": {},
                }
                if supplied:
                    row["created_at"] = None
                rows.append(row)
        page = self.client(envelope("subscribers", rows)).list_subscribers()
        self.assertEqual(len(page.results), 10)
        self.assertEqual([r["state"] for r in page.results], [r["state"] for r in rows])
        self.assertTrue(all(r["created_at"] is None for r in page.results))
        self.assertEqual([r["id"] for r in page.results], [r["id"] for r in rows])
        self.assertTrue(page.complete)
        self.assertIsNone(page.next_after)
        self.assertEqual(len(self.requests), 1)

    def test_terminal_page_can_finish_cursor_chain_with_complete_false(self):
        requests = []

        def reply(request):
            requests.append(request)
            after = request.url.params.get("after")
            if after is None:
                return httpx.Response(
                    200,
                    json=envelope(
                        "subscribers",
                        [
                            {
                                "id": 1,
                                "state": "active",
                                "created_at": "2024-02-29T00:00:00Z",
                                "email_address": "user@example.invalid",
                                "first_name": None,
                                "fields": {},
                            }
                        ],
                        more=True,
                        cursor="page-two",
                    ),
                )
            self.assertEqual(after, "page-two")
            return httpx.Response(
                200,
                json=envelope(
                    "subscribers",
                    [
                        {
                            "id": 2,
                            "state": "cancelled",
                            "created_at": "2023-01-27T11:43:55-07:00",
                            "email_address": "other@example.invalid",
                            "first_name": None,
                            "fields": {},
                        }
                    ],
                    previous=True,
                ),
            )

        boundary = KitTransport(
            SecretStr("synthetic-test-only"), transport=httpx.MockTransport(reply)
        )
        client = KitClient(transport=boundary)
        self.addCleanup(client.close)
        first = client.list_subscribers(PageRequest(per_page=1))
        last = client.list_subscribers(PageRequest(per_page=1, after=first.next_after))
        self.assertFalse(first.complete)
        self.assertFalse(last.complete)
        self.assertIsNone(last.next_after)
        self.assertEqual(
            [first.results[0]["state"], last.results[0]["state"]],
            ["active", "cancelled"],
        )
        self.assertEqual(len(requests), 2)
