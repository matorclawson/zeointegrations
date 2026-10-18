"""Metadata conformance only; do not import or initialize the media plugin."""

import ast
import copy
import json
import tomllib
import unittest
from pathlib import Path

from tools.manifest import MAX_BYTES, validate, validate_package

PACKAGE = Path(__file__).resolve().parents[1] / "packages" / "ffmpeg"


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((PACKAGE / "manifest.json").read_text())
        self.project = tomllib.loads((PACKAGE / "pyproject.toml").read_text())[
            "project"
        ]

    def check_bad(self, manifest):
        with self.assertRaises(ValueError):
            validate(json.dumps(manifest).encode(), self.project)

    def test_package_metadata_and_source_operations_agree(self):
        manifest = validate_package(PACKAGE)
        tree = ast.parse(
            (PACKAGE / "src/zeo_integrations/ffmpeg/service.py").read_text()
        )
        methods = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }
        self.assertEqual(manifest["secrets"], [])
        self.assertEqual(manifest["entry_points"], ["ffmpeg"])
        self.assertEqual(manifest["minimum_zeo_core"], "0.24.0")
        self.assertTrue(set(manifest["operations"]) <= methods)
        for item in manifest["provenance"]:
            self.assertTrue((PACKAGE / item["destination"]).is_file())

    def test_duplicate_unknown_and_missing_keys_refused(self):
        raw = json.dumps(self.manifest)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate(raw[:-1].encode() + b', "kind": "plugin"}', self.project)
        for change in ({**self.manifest, "execute": "anything"}, {}):
            self.check_bad(change)

    def test_byte_string_and_array_budgets_refused(self):
        with self.assertRaises(ValueError):
            validate(b" " * (MAX_BYTES + 1), self.project)
        for field, value in (("name", "a" * 257), ("operations", ["a"] * 65)):
            self.check_bad({**self.manifest, field: value})

    def test_names_entrypoints_minimum_and_license_crosschecked(self):
        for field, value in (
            ("name", "other"),
            ("entry_points", []),
            ("minimum_zeo_core", "0.23.0"),
            ("minimum_zeo_core", ">=0.24"),
            ("license", "unknown"),
            ("kind", "execute"),
            ("operations", ["probe", "probe"]),
            ("operations", ["invented_route"]),
            ("kind", []),
            ("secrets", ["token-value"]),
            ("secrets", ["FFMPEG_TOKEN"]),
        ):
            self.check_bad({**self.manifest, field: value})
        validate(
            json.dumps({**self.manifest, "name": "ZEO_plugin.ffmpeg"}).encode(),
            self.project,
        )

    def test_provenance_path_and_commit_refusals(self):
        for path in ("/tmp/x", "../x", "a/../x", "a//x", "a/./x", "a\\x", ""):
            changed = copy.deepcopy(self.manifest)
            changed["provenance"][0]["destination"] = path
            self.check_bad(changed)
        for field, value in (("commit", "main"), ("repository", "file:///tmp/x")):
            changed = copy.deepcopy(self.manifest)
            changed["provenance"][0][field] = value
            self.check_bad(changed)

    def test_malformed_nested_types_and_duplicate_provenance_refused(self):
        for value in (None, False, 3, {}, ["not-an-object"]):
            self.check_bad({**self.manifest, "provenance": value})
        changed = copy.deepcopy(self.manifest)
        changed["provenance"].append(changed["provenance"][0])
        self.check_bad(changed)
        with self.assertRaises(ValueError):
            validate(b"\xff", self.project)

    def test_excessive_nesting_and_wrong_provenance_keys_refused(self):
        nested = "leaf"
        for _ in range(10):
            nested = [nested]
        self.check_bad({**self.manifest, "provenance": nested})
        changed = copy.deepcopy(self.manifest)
        changed["provenance"][0]["fetch"] = "never"
        self.check_bad(changed)


if __name__ == "__main__":
    unittest.main()
