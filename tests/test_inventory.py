"""Check inventory facts that would otherwise misstate migration scope."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.inventory import build, imports, main, parse, router_directories, summarize


class InventoryTests(unittest.TestCase):
    def test_router_alias_determines_directory_not_catalog_spelling(self):
        tree = parse(b"""
from integrations.gmail.route import router as gmail_router
INTEGRATION_ROUTERS = {"google-mail": gmail_router}
""")
        self.assertEqual(router_directories(tree), {"google-mail": "gmail"})

    def test_missing_router_registry_is_an_error(self):
        with self.assertRaises(ValueError):
            router_directories(parse(b"pass"))

    def test_static_import_scan_never_executes_source(self):
        tree = parse(b"""
raise RuntimeError("must never run")
import os
import httpx as transport
from google.oauth2 import credentials
from .service import Service
""")
        self.assertEqual(imports(tree), {"httpx", "google"})

    def test_size_and_dependencies_separate_tests_and_prefix_siblings(self):
        result = summarize(
            {
                "providers/mail/client.py": b"import requests\nimport local\n",
                "providers/mail/tests.py": b"import pytest\nimport requests\n",
                "providers/mail/component.json": b"{}",
                "providers/mail_other/client.py": b"import unrelated\n",
            },
            "providers/mail/",
            {"local"},
        )
        self.assertEqual(result["files"], 3)
        self.assertEqual(result["python_lines_including_tests"], 4)
        self.assertEqual(result["python_test_lines"], 2)
        self.assertEqual(result["third_party_import_roots"], ["requests"])
        self.assertEqual(result["additional_test_import_roots"], ["pytest"])

    def test_invalid_source_is_reported_instead_of_disappearing(self):
        result = summarize({"provider/broken.py": b"def (\n"}, "provider/", set())
        self.assertEqual(result["parse_errors"], ["provider/broken.py"])

    def fixture_sources(self, catalog):
        return [
            (
                "a" * 40,
                {
                    "aci_server/main.py": b"""
from integrations.gmail.route import router as mail_router
INTEGRATION_ROUTERS = {"mail": mail_router}
""",
                    "aci_server/db/scripts/catalog.json": json.dumps(catalog).encode(),
                    "aci_server/requirements.txt": b"requests==1\n",
                    "aci_server/integrations/gmail/client.py": b"import requests\n",
                },
            ),
            (
                "b" * 40,
                {
                    "pyproject.toml": b"""
[project.entry-points."zeo_core.integrations"]
"google.mail" = "zeo_core.integrations.google.mail:create_integration"
[project.optional-dependencies]
google = ["google-api-python-client"]
""",
                    "src/zeo_core/integrations/google/mail/client.py": (
                        b"import googleapiclient\n"
                    ),
                },
            ),
        ]

    def test_build_joins_registry_auth_overlap_and_entry_point_source(self):
        with mock.patch(
            "tools.inventory.snapshot",
            side_effect=self.fixture_sources({"mail": {"auth_method": "oauth"}}),
        ):
            result = build(Path("veyrax"), Path("zeocore"))
        (row,) = result["veyrax_directories"]
        self.assertEqual(row["router_tags"], ["mail"])
        self.assertEqual(row["catalog_auth"], ["oauth"])
        self.assertEqual(row["zeocore_overlap"], "google.mail")
        self.assertEqual(row["third_party_import_roots"], ["requests"])
        (entry,) = result["zeocore_entry_points"]
        self.assertEqual(entry["name"], "google.mail")
        self.assertEqual(entry["python_lines_including_tests"], 1)
        self.assertEqual(result["sources"], {"veyrax": "a" * 40, "zeocore": "b" * 40})

    def test_build_refuses_catalog_router_mismatch(self):
        with (
            mock.patch(
                "tools.inventory.snapshot",
                side_effect=self.fixture_sources(
                    {"different": {"auth_method": "oauth"}}
                ),
            ),
            self.assertRaisesRegex(ValueError, "catalog and registered routers differ"),
        ):
            build(Path("veyrax"), Path("zeocore"))

    def test_source_output_refused_before_any_inventory_read(self):
        with tempfile.TemporaryDirectory() as temp:
            for source in ("veyrax", "zeocore"):
                output = Path(temp) / source / "inventory.json"
                args = [
                    "inventory",
                    "--veyrax",
                    str(Path(temp) / "veyrax"),
                    "--zeocore",
                    str(Path(temp) / "zeocore"),
                    "--output",
                    str(output),
                ]
                with (
                    self.subTest(source=source),
                    mock.patch("sys.argv", args),
                    mock.patch("tools.inventory.build") as read_sources,
                    contextlib.redirect_stderr(io.StringIO()),
                    self.assertRaises(SystemExit) as error,
                ):
                    main()
                self.assertEqual(error.exception.code, 2)
                read_sources.assert_not_called()
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
