"""Behavioral checks for product assertion classification, not runner controls."""

import io
import unittest
from types import ModuleType

from tools.qualify_inventory import Mutation, qualify_source


class QualificationTests(unittest.TestCase):
    def probe(self, source, mutations):
        assertions = ModuleType("fixture_qualification_probe")

        def original(_payload):
            return True

        assertions.compare_fixture = original
        assertions.FixtureRefusal = ValueError

        class RequiresAcceptance(unittest.TestCase):
            def test_valid_fixture_accepts(self):
                self.assertTrue(assertions.compare_fixture(b"fixture"))

        report = qualify_source(
            source, RequiresAcceptance, assertions, io.StringIO(), mutations
        )
        self.assertIs(assertions.compare_fixture, original)
        self.assertIs(assertions.FixtureRefusal, ValueError)
        return report

    def source(self, verdict="True"):
        return (
            "class FixtureRefusal(ValueError): pass\n"
            f"def compare_fixture(payload): return {verdict}\n"
        )

    def test_failed_baseline_stops_mutation_assertions(self):
        report = self.probe(
            self.source("False"), (Mutation("unused", "False", "True"),)
        )
        self.assertEqual(report["baseline"]["outcome"], "assertion-failure")
        self.assertEqual(report["mutations"], [])

    def test_assertion_failure_kills_but_runtime_error_is_invalid(self):
        report = self.probe(
            self.source(),
            (
                Mutation("behavior", "True", "False"),
                Mutation("runtime-error", "True", "1 / 0"),
            ),
        )
        self.assertEqual(report["split"]["killed"], 1)
        self.assertEqual(report["split"]["invalid"], 1)

    def test_import_or_compile_failure_is_not_a_kill(self):
        report = self.probe(self.source(), (Mutation("bad-syntax", "True", "("),))
        self.assertEqual(report["split"]["killed"], 0)
        self.assertEqual(report["split"]["invalid"], 1)
        self.assertEqual(
            report["mutations"][0]["assertions"]["error_type"], "SyntaxError"
        )

    def test_missing_anchor_is_not_applied(self):
        report = self.probe(self.source(), (Mutation("absent", "missing", "False"),))
        self.assertEqual(report["split"]["not-applied"], 1)
        self.assertEqual(report["split"]["killed"], 0)

    def test_unchanged_behavior_is_reported_as_survived(self):
        report = self.probe(self.source(), (Mutation("equivalent", "True", "bool(1)"),))
        self.assertEqual(report["split"]["survived"], 1)
        self.assertEqual(report["split"]["killed"], 0)


if __name__ == "__main__":
    unittest.main()
