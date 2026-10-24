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
        rows = [
            {
                "id": i + 1,
                "state": state,
                "email_address": "user@example.invalid",
                "first_name": None,
                "fields": {"team": "demo", "optional": None},
            }
            for i, state in enumerate(states)
        ]
        result = self.client(envelope("subscribers", rows)).list_subscribers()
        self.assertEqual([row["state"] for row in result.results], states)
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
