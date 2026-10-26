"""Release refusal/idempotence checks use fake PyPI responses and no network."""

import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error

from tools.release_integrations import artifact_hashes, metadata, version_exists


class ReleaseTests(unittest.TestCase):
    def test_pypi_absent_present_and_uncertain_results(self):
        def absent(*args, **kwargs):
            raise urllib.error.HTTPError("fake", 404, "absent", {}, None)

        def unavailable(*args, **kwargs):
            raise urllib.error.HTTPError("fake", 503, "unavailable", {}, None)

        def present(*args, **kwargs):
            return io.StringIO(json.dumps({"info": {"name": "zeo-integrations"}, "urls": [{"filename": "wheel"}]}))

        self.assertFalse(version_exists("0.1.0", absent))
        self.assertTrue(version_exists("0.1.0", present))
        with self.assertRaises(urllib.error.HTTPError):
            version_exists("0.1.0", unavailable)
        for body in ({"info": {"name": "other"}, "urls": [{}]}, {"info": {"name": "zeo-integrations"}, "urls": []}):
            with self.subTest(body=body), self.assertRaises(ValueError):
                version_exists("0.1.0", lambda *args, body=body, **kwargs: io.StringIO(json.dumps(body)))

    def test_exact_artifact_pair_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "pyproject.toml"
            project.write_text('[project]\nname="zeo-integrations"\nversion="0.1.0"\n')
            self.assertEqual(metadata(project)["version"], "0.1.0")
            project.write_text('[project]\nname="zeo-integration-hubspot"\nversion="0.1.0"\n')
            with self.assertRaises(ValueError):
                metadata(project)
            project.unlink()
            for name in ("zeo_integrations-0.1.0.tar.gz", "zeo_integrations-0.1.0-py3-none-any.whl"):
                (root / name).write_bytes(b"synthetic distribution")
            self.assertEqual(len(artifact_hashes(root, "0.1.0")), 2)
            (root / "unexpected.whl").write_bytes(b"other")
            with self.assertRaises(ValueError):
                artifact_hashes(root, "0.1.0")


if __name__ == "__main__":
    unittest.main()
