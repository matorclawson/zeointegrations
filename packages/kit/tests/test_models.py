# Copyright (c) 2026 Rod Rivera
# SPDX-License-Identifier: MIT
# Original synthetic controls; no private Broker fixture copying.
import json
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
            "created_at": "2024-02-29T12:34:56Z",
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

    def test_provider_creation_timestamp_is_preserved_in_json(self):
        for value in [
            "2024-02-29T00:00:00Z",
            "2024-01-01T24:00:00Z",
            "2026-10-24T12:34:56.123456789+05:30",
            "2023-01-27T11:43:55-07:00",
            "2026-10-24T00:00:00.000000+00:00",
            "2026-10-24T00:00:00." + "1" * 38 + "+01:00",
        ]:
            with self.subTest(value=value):
                row = self.subscriber_row(created_at=value)
                model = Subscriber(**row)
                self.assertEqual(model.created_at, value)
                self.assertEqual(model.model_dump(mode="json")["created_at"], value)
                self.assertEqual(
                    json.loads(model.model_dump_json())["created_at"], value
                )

    @staticmethod
    def subscriber_row(**overrides):
        return {
            "id": 1,
            "state": "active",
            "created_at": "2024-02-29T12:34:56Z",
            "email_address": "user@example.invalid",
            "first_name": None,
            "fields": {},
            **overrides,
        }

    def test_invalid_provider_dates_fail_without_coercion(self):
        invalid = [
            None,
            True,
            1700000000,
            1.5,
            "",
            "2024-02-29",
            "2024-02-29T12:34:56",
            "2024-02-29 12:34:56Z",
            "2024-02-29T12:34Z",
            "2023-02-29T12:34:56Z",
            "2024-02-30T12:34:56Z",
            "0000-01-01T00:00:00Z",
            "2024-13-01T00:00:00Z",
            "2024-01-01T25:00:00Z",
            "2024-01-01T24:00:01Z",
            "2024-01-01T00:60:00Z",
            "2024-01-01T00:00:60Z",
            "2024-01-01T00:00:00+24:00",
            "2024-01-01T00:00:00+00:60",
            "2024-01-01T00:00:00+05",
            "2024-01-01T00:00:00+0530",
            " 2024-01-01T00:00:00Z",
            "2024-01-01T00:00:00Z\n",
            "2024-01-01T00:00:00." + "1" * 39 + "+01:00",
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                Subscriber(**self.subscriber_row(created_at=value))
        row = self.subscriber_row()
        del row["created_at"]
        with self.assertRaises(ValidationError):
            Subscriber(**row)
