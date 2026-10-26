"""Release decisions use synthetic PyPI state and never perform network uploads."""

import copy
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

from tools.release_integrations import (
    artifact_hashes,
    fetch_version,
    metadata,
    published_matches,
)

WHEEL = "zeo_integrations-0.1.0-py3-none-any.whl"
SDIST = "zeo_integrations-0.1.0.tar.gz"


def receipt(wheel="a", source="b"):
    return {"version": "0.1.0", "artifacts": {WHEEL: wheel * 64, SDIST: source * 64}}


def remote_for(build):
    return {
        "info": {"name": "zeo-integrations", "version": build["version"]},
        "urls": [
            {"filename": name, "digests": {"sha256": digest}}
            for name, digest in build["artifacts"].items()
        ],
    }


class ReleaseTests(unittest.TestCase):
    def test_pypi_absence_and_service_failure_are_distinct(self):
        def absent(*args, **kwargs):
            raise urllib.error.HTTPError("fake", 404, "absent", {}, None)

        def unavailable(*args, **kwargs):
            raise urllib.error.HTTPError("fake", 503, "unavailable", {}, None)

        def present(*args, **kwargs):
            return io.StringIO(json.dumps(remote_for(receipt())))

        self.assertIsNone(fetch_version("0.1.0", absent))
        self.assertEqual(fetch_version("0.1.0", present), remote_for(receipt()))
        with self.assertRaises(urllib.error.HTTPError):
            fetch_version("0.1.0", unavailable)

    def test_only_complete_matching_release_can_skip_publication(self):
        build = receipt()
        complete = remote_for(build)
        self.assertFalse(published_matches(build, None))
        self.assertTrue(published_matches(build, complete))
        wheel_only = copy.deepcopy(complete)
        wheel_only["urls"] = [complete["urls"][0]]
        source_only = copy.deepcopy(complete)
        source_only["urls"] = [complete["urls"][1]]
        unrelated = copy.deepcopy(complete)
        unrelated["urls"][0]["filename"] = "other.whl"
        wrong_version = copy.deepcopy(complete)
        wrong_version["info"]["version"] = "0.2.0"
        conflict = copy.deepcopy(complete)
        conflict["urls"][0]["digests"]["sha256"] = "c" * 64
        wrong_project = copy.deepcopy(complete)
        wrong_project["info"]["name"] = "other-project"
        for bad in (
            wheel_only,
            source_only,
            unrelated,
            wrong_version,
            conflict,
            wrong_project,
        ):
            with self.subTest(remote=bad), self.assertRaises(ValueError):
                published_matches(build, bad)

    def test_serialized_same_version_decisions_never_mix_builds(self):
        first, second = receipt(), receipt("c", "d")
        store, uploads = None, []
        # The workflow concurrency group keeps each decision/upload interval whole.
        if not published_matches(first, store):
            uploads.append(first)
            store = remote_for(first)
        with self.assertRaises(ValueError):
            published_matches(second, store)
        self.assertTrue(published_matches(first, store))
        self.assertEqual(uploads, [first])
        self.assertEqual(store, remote_for(first))
        # An interrupted first upload refuses instead of filling it with build two.
        store["urls"] = store["urls"][:1]
        for build in (first, second):
            with self.assertRaises(ValueError):
                published_matches(build, store)
        self.assertEqual(uploads, [first])

    def test_exact_artifact_pair_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "pyproject.toml"
            project.write_text('[project]\nname="zeo-integrations"\nversion="0.1.0"\n')
            self.assertEqual(metadata(project)["version"], "0.1.0")
            project.write_text(
                '[project]\nname="zeo-integration-hubspot"\nversion="0.1.0"\n'
            )
            with self.assertRaises(ValueError):
                metadata(project)
            project.unlink()
            for name in (WHEEL, SDIST):
                (root / name).write_bytes(b"synthetic distribution")
            self.assertEqual(len(artifact_hashes(root, "0.1.0")), 2)
            (root / "unexpected.whl").write_bytes(b"other")
            with self.assertRaises(ValueError):
                artifact_hashes(root, "0.1.0")


if __name__ == "__main__":
    unittest.main()
