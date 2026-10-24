# Copyright (c) 2026 Rod Rivera
# SPDX-License-Identifier: MIT
# Original synthetic controls; no private Broker fixture copying.
"""Static ownership and scope controls; no legacy write compatibility contract."""

import ast
import pathlib
import unittest


class PackageScope(unittest.TestCase):
    def test_only_read_client_surface(self):
        from zeo_integrations.kit import KitClient

        methods = {name for name in vars(KitClient) if not name.startswith("_")}
        self.assertEqual(
            methods,
            {
                "close",
                "list_subscribers",
                "list_tags",
                "list_forms",
                "list_custom_fields",
            },
        )

    def test_no_core_back_edge_or_environment_discovery(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        for path in [
            *root.joinpath("src").rglob("*.py"),
            *root.joinpath("tests").rglob("*.py"),
        ]:
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    names = []
                self.assertFalse(
                    any(name.split(".")[0] == "zeo_core" for name in names), str(path)
                )
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, {"environ", "getenv"}, str(path))

    def test_no_registry_or_write_models(self):
        import tomllib

        from zeo_integrations.kit import models

        root = pathlib.Path(__file__).resolve().parents[1]
        config = tomllib.loads(root.joinpath("pyproject.toml").read_text())
        self.assertNotIn("entry-points", config["project"])
        self.assertFalse(
            any(
                name in vars(models)
                for name in [
                    "BroadcastDraft",
                    "SendBroadcast",
                    "SequenceDraft",
                    "SequenceEmailDraft",
                    "SubscriberCreate",
                ]
            )
        )
