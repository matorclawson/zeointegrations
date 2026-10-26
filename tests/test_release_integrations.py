"""Release metadata and uncertain-outcome checks, with no PyPI calls."""

import unittest

from tools.release_integrations import existing_matches, stamp_project, version_for


class ReleaseMetadataTests(unittest.TestCase):
    def test_version_is_deterministic_and_uses_reviewed_minor(self):
        self.assertEqual(version_for("0.1.0", 25), "0.1.25")
        self.assertEqual(version_for("0.2.0", 26), "0.2.26")
        for value, count in (("latest", 1), ("0.1.0", 0)):
            with self.assertRaises(ValueError):
                version_for(value, count)

    def test_stamp_changes_only_project_version(self):
        original = '[project]\nname = "zeo-integrations"\nversion = "0.1.0"\n\n[other]\nversion = "keep"\n'
        expected = original.replace('version = "0.1.0"', 'version = "0.1.29"')
        self.assertEqual(stamp_project(original, "0.1.29"), expected)
        with self.assertRaises(ValueError):
            stamp_project('[project]\nname = "missing"\n', "0.1.2")

    def test_existing_version_must_have_exact_artifacts_and_hashes(self):
        receipt = {"artifacts": [{"name": "wheel.whl", "sha256": "approved"}]}
        good = {"urls": [{"filename": "wheel.whl", "digests": {"sha256": "approved"}}]}
        self.assertFalse(existing_matches(receipt, None))
        self.assertTrue(existing_matches(receipt, good))
        for bad in (
            {"urls": []},
            {"urls": [{"filename": "wheel.whl", "digests": {"sha256": "different"}}]},
        ):
            with self.assertRaises(ValueError):
                existing_matches(receipt, bad)


if __name__ == "__main__":
    unittest.main()
