"""Check inventory facts that would otherwise misstate migration scope."""

import unittest

from tools.inventory import imports, parse, router_directories, summarize


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


if __name__ == "__main__":
    unittest.main()
