"""Installed Core direction and aggregate metadata constraints (no live providers)."""

import importlib.metadata
import os
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path


class PackageBoundaryTests(unittest.TestCase):
    def test_one_distribution_and_core_dependency(self):
        data = tomllib.loads(Path("pyproject.toml").read_text())
        self.assertEqual(data["project"]["name"], "zeo-integrations")
        self.assertEqual(data["project"]["requires-python"], ">=3.12")
        self.assertIn("zeocore>=0.43.0,<1", data["project"]["dependencies"])
        self.assertNotIn("entry-points", data["project"])

    def test_installed_distribution_has_no_duplicate_provider_registration(self):
        distribution = importlib.metadata.distribution("zeo-integrations")
        self.assertEqual(distribution.metadata["Name"], "zeo-integrations")
        self.assertFalse(distribution.entry_points)

    def test_sdk_dependencies_are_extras(self):
        data = tomllib.loads(Path("pyproject.toml").read_text())["project"]
        sdks = ("supabase", "notion-client", "google-api-python-client", "openai")
        for sdk in sdks:
            self.assertFalse(any(d.startswith(sdk) for d in data["dependencies"]))
        self.assertIn("google", data["optional-dependencies"])

    def test_m1_core_import_never_loads_the_aggregate(self):
        script = """
import importlib.abc
import sys
class RefuseAggregate(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'zeo_integrations' or fullname.startswith(
            'zeo_integrations.'
        ):
            raise AssertionError('Core imported aggregate at import time: ' + fullname)
sys.meta_path.insert(0, RefuseAggregate())
import zeo_core
import zeo_core.integrations
assert not any(
    n == 'zeo_integrations' or n.startswith('zeo_integrations.')
    for n in sys.modules
)
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
