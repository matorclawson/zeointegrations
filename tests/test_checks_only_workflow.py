"""Prevent automatic publication from returning to the artifact-check workflow."""

import re
import unittest
from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github/workflows/publish-integrations.yml"
)


class ChecksOnlyWorkflowTests(unittest.TestCase):
    def test_only_the_artifact_check_job_remains(self):
        text = WORKFLOW.read_text()
        jobs = text.split("\njobs:\n", 1)[1]
        self.assertEqual(re.findall(r"^  ([a-zA-Z0-9_-]+):\s*$", jobs, re.M), ["build"])

    def test_no_publisher_environment_or_identity_permission(self):
        text = WORKFLOW.read_text()
        self.assertNotRegex(text, r"(?m)^\s+environment:")
        self.assertNotRegex(text, r"(?m)^\s+id-token:")
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("persist-credentials: false", text)

    def test_no_registry_upload_or_release_command(self):
        text = WORKFLOW.read_text()
        for forbidden in (
            "pypa/gh-action-pypi-publish@",
            "twine upload",
            "gh release",
            "tools/release_integrations.py plan",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_frozen_build_and_import_checks_are_retained(self):
        text = WORKFLOW.read_text()
        for required in (
            "uv sync --frozen --only-group release",
            "Build twice offline and compare exact bytes",
            "tools/release_integrations.py build",
            "Import smoke from the installed built wheel",
            "actions/upload-artifact@",
            "if-no-files-found: error",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
