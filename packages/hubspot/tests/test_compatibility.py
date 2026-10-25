"""Installed distribution, source identity and inert import compatibility."""

import importlib
import importlib.metadata
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile


class Compatibility(unittest.TestCase):
    def test_installed_modules_are_current_source_bytes(self):
        root = Path(__file__).resolve().parents[1]
        dist = importlib.metadata.distribution("zeo-integration-hubspot")
        self.assertEqual(dist.metadata["Requires-Python"], ">=3.12")
        self.assertFalse(dist.entry_points)
        for name in ["__init__", "client", "models", "transport", "workflow"]:
            module = importlib.import_module(f"zeo_integrations.hubspot{'.' + name if name != '__init__' else ''}")
            installed = Path(module.__file__).resolve()
            source = root / "src" / "zeo_integrations" / "hubspot" / f"{name}.py"
            self.assertNotEqual(installed, source)
            self.assertEqual(installed.read_bytes(), source.read_bytes())
        requirements = dist.requires or []
        self.assertFalse(any("zeo-core" in value.lower() or "zeo_core" in value.lower() for value in requirements))

    def test_fresh_import_has_no_credential_discovery_network_or_core(self):
        code = '''
import os, sys
from unittest.mock import patch
with patch("httpx.Client", side_effect=AssertionError("import initialized HTTP")):
    with patch.dict(os.environ, {}, clear=True):
        import zeo_integrations.hubspot as h
        from zeo_integrations.hubspot.models import EmailDraft
        assert h.EmailDraft is EmailDraft
        assert not hasattr(h, "create_integration")
        assert not hasattr(h, "HubSpotIntegration")
        assert not any(n == "zeo_core" or n.startswith("zeo_core.") for n in sys.modules)
'''
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=15, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_implicit_namespace_and_provider_only_files(self):
        namespace = importlib.import_module("zeo_integrations")
        self.assertIsNone(namespace.__file__)
        dist = importlib.metadata.distribution("zeo-integration-hubspot")
        paths = [str(p) for p in dist.files or []]
        self.assertFalse(any(p == "zeo_integrations/__init__.py" for p in paths))
        self.assertFalse(any("service.py" in p or "zeo_core/" in p for p in paths))
        self.assertTrue(any(p.endswith("hubspot/NOTICE") for p in paths))
        self.assertTrue(any(p.endswith("licenses/LICENSE") for p in paths))

    def test_existing_built_wheels_preserve_notices_when_available(self):
        root = Path(__file__).resolve().parents[1]
        # Wheel building follows tests in make verify; source provenance and
        # installed NOTICE are checked even on the first clean run.
        dist = importlib.metadata.distribution("zeo-integration-hubspot")
        notice = Path(dist.locate_file("zeo_integrations/hubspot/NOTICE"))
        self.assertEqual(notice.read_bytes(), (root / "NOTICE").read_bytes())
        for wheel in (root / "dist").glob("*.whl"):
            with zipfile.ZipFile(wheel) as archive:
                self.assertEqual(archive.read("zeo_integrations/hubspot/NOTICE"), (root / "NOTICE").read_bytes())
