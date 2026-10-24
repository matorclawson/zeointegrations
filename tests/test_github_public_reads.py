"""Synthetic provider doubles for a public repository; no recorded API response."""

import importlib.util
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "packages/github/src/zeo_integrations/github/public_reads.py"
)
SPEC = importlib.util.spec_from_file_location("github_public_reads", SOURCE)
reads = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reads
SPEC.loader.exec_module(reads)


class FakeBroker:
    def __init__(self, responses):
        self.responses = list(responses)
        self.paths = []

    def get(self, path):
        self.paths.append(path)
        return self.responses.pop(0)


def repository(**overrides):
    # python/cpython is a public identity; all response content below is invented.
    data = {
        "full_name": "python/cpython",
        "html_url": "https://github.com/python/cpython",
        "private": False,
        "description": "Synthetic public repository fixture",
        "unselected_field": "must not be returned",
    }
    return reads.Response(200, data | overrides)


def issue(**overrides):
    data = {
        "number": 123,
        "html_url": "https://github.com/python/cpython/issues/123",
        "state": "open",
        "title": "Synthetic issue; not a claim about real issue 123",
        "body": "Fixture body",
    }
    return reads.Response(200, data | overrides)


class PublicReadsTests(unittest.TestCase):
    def test_repository_projects_only_closed_result_fields(self):
        broker = FakeBroker([repository()])
        result = reads.get_repository(broker, "python", "cpython")
        self.assertEqual(broker.paths, ["/repos/python/cpython"])
        self.assertEqual(set(asdict(result)), {"full_name", "url", "description"})

    def test_invalid_identity_never_calls_transport(self):
        for name in ("../private", "..", "", "a?token=x", "a/b", "é", "a" * 101):
            with self.subTest(name=name):
                broker = FakeBroker([])
                with self.assertRaises(reads.Refused):
                    reads.get_repository(broker, name, "cpython")
                self.assertEqual(broker.paths, [])

    def test_public_provenance_is_required(self):
        for changes in (
            {"private": True},
            {"private": 0},
            {"private": None},
            {"full_name": "other/repository"},
            {"html_url": "https://elsewhere.invalid/python/cpython"},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(reads.Refused):
                    reads.get_issue(
                        FakeBroker([repository(**changes)]), "python", "cpython", 123
                    )

    def test_issue_preflights_public_repository_and_limits_body(self):
        broker = FakeBroker([repository(), issue(body="x" * 5000)])
        result = reads.get_issue(broker, "python", "cpython", 123)
        self.assertEqual(
            broker.paths,
            ["/repos/python/cpython", "/repos/python/cpython/issues/123"],
        )
        self.assertEqual(result.body_summary, "x" * 4096)
        self.assertEqual(result.repository, "python/cpython")

    def test_invalid_issue_number_never_calls_transport(self):
        for number in (True, 0, -1, "123", 2**63):
            with self.subTest(number=number):
                broker = FakeBroker([])
                with self.assertRaises(reads.Refused):
                    reads.get_issue(broker, "python", "cpython", number)
                self.assertEqual(broker.paths, [])

    def test_issue_identity_state_and_shape_are_checked(self):
        for changes in (
            {"number": True},
            {"number": 124},
            {"html_url": "https://github.com/other/repo/issues/123"},
            {"state": "unknown"},
            {"pull_request": {}},
            {"title": []},
            {"body": {}},
            {"body": "x" * 262145},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(reads.Refused):
                    reads.get_issue(
                        FakeBroker([repository(), issue(**changes)]),
                        "python",
                        "cpython",
                        123,
                    )

    def test_provider_error_details_are_not_exposed(self):
        for response in (
            reads.Response(403, {"detail": "do not expose"}),
            reads.Response(200, []),
        ):
            with self.subTest(response=response):
                with self.assertRaises(reads.Refused) as error:
                    reads.get_repository(FakeBroker([response]), "python", "cpython")
                self.assertNotIn("do not expose", str(error.exception))
