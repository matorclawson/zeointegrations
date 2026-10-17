"""Detect report drift without requiring source checkouts or provider imports."""

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(name):
    lines = (ROOT / "docs/inventory" / name).read_text().splitlines()
    # Both reports put their inventory in the first table. Later tables are prose.
    table = []
    started = False
    for line in lines:
        if line.startswith("|---"):
            started = True
        elif started:
            if not line.startswith("|"):
                break
            table.append([cell.strip() for cell in line.strip("|").split("|")])
    return table


class InventoryArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads((ROOT / "docs/inventory/snapshot.json").read_text())

    def test_veyrax_table_matches_all_snapshot_rows(self):
        actual = rows("veyrax.md")
        expected = [
            [
                r["directory"],
                ", ".join(r["router_tags"]) or "—",
                r["observed_auth"],
                ", ".join(r["third_party_import_roots"]) or "—",
                str(r["python_lines_including_tests"]),
                r["zeocore_overlap"],
            ]
            for r in self.snapshot["veyrax_directories"]
        ]
        self.assertEqual(actual, expected)

    def test_zeocore_table_names_paths_dependencies_and_sizes_match_snapshot(self):
        actual = [[r[0], r[1], r[3], r[4]] for r in rows("zeocore.md")]
        expected = [
            [
                r["name"],
                r["directory"],
                ", ".join(r["third_party_import_roots"]),
                str(r["python_lines_including_tests"]),
            ]
            for r in self.snapshot["zeocore_entry_points"]
        ]
        self.assertEqual(actual, expected)

    def test_preserved_mit_notice_matches_reviewed_source_digest(self):
        # Independently received source LICENSE at VeyraX commit 1cdddde9.
        digest = hashlib.sha256(
            (ROOT / "docs/licenses/VeyraX-MIT.txt").read_bytes()
        ).hexdigest()
        self.assertEqual(
            digest, "22dfe6dffcc25e456ae8489631245a6f443733579105cf3160dbb35302a1e0fb"
        )


if __name__ == "__main__":
    unittest.main()
