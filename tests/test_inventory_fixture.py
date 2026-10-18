"""Prepared S1a behavioral tests; qualification status is recorded in the SOW."""

import copy
import json
import unittest

from tools.inventory_fixture import FixtureRefusal, compare_fixture


def artifact(version="2", digest="a", dependency="b", name="demo"):
    return {
        "distribution": name,
        "version": version,
        "artifact_sha256": digest * 64,
        "dependency_lock_sha256": dependency * 64,
    }


def fixture():
    return {
        "fixture_version": 1,
        "case_id": "public-synthetic-scaffold",
        "revision_label": "fixture-local-only",
        "required_names": ["demo"],
        "admitted_artifacts": [artifact(), artifact("1", "c", "d")],
        "installed_artifacts": [artifact()],
        "expected": "accept",
    }


def compare(value):
    return compare_fixture(json.dumps(value).encode("utf-8"))


class InventoryFixtureTests(unittest.TestCase):
    def test_forward_and_rollback_use_full_admitted_tuple(self):
        for installed in (artifact(), artifact("1", "c", "d")):
            with self.subTest(installed=installed):
                value = fixture()
                value["installed_artifacts"] = [installed]
                result = compare(value)
                self.assertTrue(result.accepted)
                self.assertTrue(result.matches_expected)

    def test_expected_is_assertion_not_authority(self):
        value = fixture()
        value["expected"] = "refuse"
        result = compare(value)
        self.assertTrue(result.accepted)
        self.assertFalse(result.matches_expected)

    def test_duplicate_missing_extra_and_unapproved_refuse(self):
        cases = [
            [artifact(), artifact()],
            [],
            [artifact(), artifact(name="extra")],
            [artifact(version="unadmitted")],
            [artifact(digest="e")],
            [artifact(dependency="e")],
            [artifact("1", "c", "b")],
            [artifact(name="Demo")],
        ]
        for installed in cases:
            with self.subTest(installed=installed):
                value = fixture()
                value["installed_artifacts"] = installed
                value["expected"] = "refuse"
                result = compare(value)
                self.assertFalse(result.accepted)
                self.assertTrue(result.matches_expected)

    def test_closed_fields_and_types(self):
        mutations = [
            ("fixture_version", True),
            ("fixture_version", 1.0),
            ("fixture_version", 2),
            ("case_id", ""),
            ("revision_label", "x" * 257),
            ("expected", "approved"),
            ("expected", []),
            ("required_names", "demo"),
            ("required_names", ["demo", "demo"]),
            ("required_names", ["x"] * 65),
            ("installed_artifacts", {}),
            ("admitted_artifacts", [None]),
        ]
        for key, replacement in mutations:
            with self.subTest(key=key, replacement=replacement):
                value = fixture()
                value[key] = replacement
                with self.assertRaises(FixtureRefusal):
                    compare(value)
        for extra in ("url", "path", "import", "auth", "secret"):
            for nested in (False, True):
                with self.subTest(extra=extra, nested=nested):
                    value = fixture()
                    target = value["admitted_artifacts"][0] if nested else value
                    target[extra] = "not-a-permission"
                    with self.assertRaises(FixtureRefusal):
                        compare(value)

    def test_invalid_digests_and_missing_fields(self):
        for digest in ("A" * 64, "a" * 63, "g" * 64):
            value = fixture()
            value["installed_artifacts"][0]["artifact_sha256"] = digest
            with self.assertRaises(FixtureRefusal):
                compare(value)
        baseline = fixture()
        for key in baseline:
            value = copy.deepcopy(baseline)
            del value[key]
            with self.subTest(key=key), self.assertRaises(FixtureRefusal):
                compare(value)

    def test_raw_json_duplicate_keys_size_unicode_and_constants(self):
        for payload in (
            b'{"case_id":"x","case_id":"y"}',
            b'{"nested":{"x":1,"x":2}}',
            b'{"x":NaN}',
            b"\xff",
            b"{} trailing",
            b"[]",
            b" " * 16_385,
            b"[" * 2_000 + b"]" * 2_000,
        ):
            with self.subTest(payload=payload[:60]):
                with self.assertRaises(FixtureRefusal):
                    compare_fixture(payload)
        value = fixture()
        value["case_id"] = "\ud800"
        with self.assertRaises(FixtureRefusal):
            compare(value)

    def test_empty_and_maximum_array_bounds_and_utf8_byte_limit(self):
        value = fixture()
        for key in ("required_names", "admitted_artifacts", "installed_artifacts"):
            value[key] = []
        self.assertTrue(compare(value).accepted)
        value["required_names"] = [str(index) for index in range(64)]
        self.assertFalse(compare(value).accepted)
        value = fixture()
        encoded = json.dumps(value).encode()
        at_limit = encoded + b" " * (16_384 - len(encoded))
        self.assertTrue(compare_fixture(at_limit).accepted)
        with self.assertRaises(FixtureRefusal):
            compare_fixture(encoded + b" " * (16_385 - len(encoded)))

    def test_duplicate_keys_in_otherwise_accepted_fixture_refuse(self):
        encoded = json.dumps(fixture()).encode()
        duplicates = (
            encoded.replace(
                b'"fixture_version": 1',
                b'"fixture_version": 1, "fixture_version": 1',
                1,
            ),
            encoded.replace(
                b'"version": "2"', b'"version": "2", "version": "2"', 1
            ),
        )
        for payload in duplicates:
            with self.subTest(payload=payload[:80]):
                with self.assertRaises(FixtureRefusal):
                    compare_fixture(payload)

    def test_each_artifact_array_at_64_and_65_items(self):
        for key in ("admitted_artifacts", "installed_artifacts"):
            with self.subTest(key=key):
                value = fixture()
                value["required_names"] = []
                value["admitted_artifacts"] = []
                value["installed_artifacts"] = []
                value[key] = [artifact(name=str(index)) for index in range(64)]
                # Admission alternatives alone grant nothing. Installed extras
                # are a comparison refusal, not a malformed-array refusal.
                result = compare(value)
                self.assertEqual(result.accepted, key == "admitted_artifacts")
                value[key].append(artifact(name="65th"))
                with self.assertRaises(FixtureRefusal):
                    compare(value)

    def test_unicode_codepoint_and_encoded_byte_limits_are_distinct(self):
        value = fixture()
        value["case_id"] = "é" * 256
        encoded = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.assertTrue(compare_fixture(encoded).accepted)
        padded = encoded + b" " * (16_384 - len(encoded))
        self.assertTrue(compare_fixture(padded).accepted)
        with self.assertRaises(FixtureRefusal):
            compare_fixture(padded + b" ")
        value["case_id"] += "é"
        with self.assertRaises(FixtureRefusal):
            compare(value)


if __name__ == "__main__":
    unittest.main()
