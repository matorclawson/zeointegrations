# Copyright (c) 2026 Rod Rivera
# SPDX-License-Identifier: MIT
# Original synthetic controls; no private Broker fixture copying.
import unittest

from pydantic import ValidationError

from zeo_integrations.kit import PageRequest, Subscriber


class ReadModels(unittest.TestCase):
    def test_bounded_closed_page_request(self):
        for values in [
            {"per_page": 0},
            {"per_page": 1001},
            {"per_page": True},
            {"after": ""},
            {"after": "x" * 2049},
            {"send_at": "now"},
        ]:
            with self.subTest(values=values), self.assertRaises(ValidationError):
                PageRequest(**values)
        self.assertEqual(PageRequest(per_page=1000).per_page, 1000)

    def test_identity_and_state_are_not_coerced(self):
        row = {
            "id": 1,
            "state": "cancelled",
            "email_address": "user@example.invalid",
            "first_name": None,
            "fields": {"optional": None},
        }
        self.assertEqual(Subscriber(**row).state, "cancelled")
        for key, value in [
            ("id", True),
            ("id", "1"),
            ("state", "pending"),
            ("fields", {"bad": 1}),
        ]:
            with self.subTest(key=key), self.assertRaises(ValidationError):
                Subscriber(**{**row, key: value})
