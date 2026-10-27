"""Release decisions use synthetic PyPI state and never perform network uploads."""

import copy
import io
import json
import os
import subprocess
import tempfile
import unittest
import urllib.error
from pathlib import Path

from tools.release_integrations import (
    artifact_hashes,
    fetch_version,
    metadata,
    published_matches,
    release_version,
    stamp_archive_version,
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
    def test_mainline_versions_increase_and_retries_keep_commit_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            root.mkdir()

            def command(*args, **kwargs):
                return subprocess.check_output(
                    ["git", "-C", str(root), *args], text=True, **kwargs
                ).strip()

            command("init", "--initial-branch=main")
            command("config", "user.name", "Synthetic release test")
            command("config", "user.email", "release-test@example.invalid")
            command("commit", "--allow-empty", "-m", "sow: zeointegrations-SOW-02")
            first = command("rev-parse", "HEAD")
            project = {"version": "0.1.0"}
            self.assertEqual(release_version(project, root), "0.1.0.post1")
            command("checkout", "-b", "feature")
            for _ in range(2):
                command("commit", "--allow-empty", "-m", "sow: zeointegrations-SOW-02")
            command("checkout", "main")
            # A reversed commit clock must not reverse the release order.
            command(
                "commit",
                "--allow-empty",
                "-m",
                "sow: zeointegrations-SOW-02",
                env={
                    **os.environ,
                    "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
                    "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
                },
            )
            self.assertEqual(release_version(project, root), "0.1.0.post2")
            command("merge", "--no-ff", "feature", "-m", "sow: zeointegrations-SOW-02")
            merged = command("rev-parse", "HEAD")
            self.assertEqual(release_version(project, root), "0.1.0.post3")
            self.assertEqual(release_version(project, root), "0.1.0.post3")
            shallow = Path(directory) / "shallow"
            subprocess.run(
                ["git", "clone", "--depth=1", root.as_uri(), str(shallow)], check=True
            )
            with self.assertRaises(ValueError):
                release_version(project, shallow)
            command("checkout", "--detach", first)
            self.assertEqual(release_version(project, root), "0.1.0.post1")
            command("checkout", "--detach", merged)
            self.assertEqual(release_version(project, root), "0.1.0.post3")

    def test_archive_stamping_preserves_source_and_other_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = (
                '[build-system]\nrequires=["hatchling==1.27.0"]\n\n'
                '[project]\nname="zeo-integrations"\nversion="0.1.0"\n'
                'description="unchanged"\n\n[tool.example]\nversion="untouched"\n'
            )
            checkout = root / "pyproject.toml"
            checkout.write_text(original)
            results = []
            for number in (1, 2):
                archive = root / str(number)
                archive.mkdir()
                (archive / "pyproject.toml").write_text(original)
                stamp_archive_version(archive, "0.1.0.post42")
                results.append((archive / "pyproject.toml").read_bytes())
                self.assertEqual(
                    metadata(archive / "pyproject.toml")["version"], "0.1.0.post42"
                )
            self.assertEqual(results[0], results[1])
            self.assertIn(b'version="untouched"', results[0])
            self.assertEqual(checkout.read_text(), original)

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
