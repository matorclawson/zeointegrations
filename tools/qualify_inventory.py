"""Product-only semantic qualification for the trusted S1a development fixture.

No job admission, timeouts, process control, resource policy or execution receipt.
Pomar runs this command after make verify and captures its ordinary test output.
"""

import importlib.util
import json
import sys
import unittest
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from unittest import mock


@dataclass(frozen=True)
class Mutation:
    name: str
    before: str
    after: str


MEMBERSHIP = "if any(item not in admitted_set for item in installed):"
MUTATIONS = (
    Mutation("duplicate-json-key", "if key in result:", "if False:"),
    Mutation("duplicate-installed", "if len(set(names)) != len(names):", "if False:"),
    Mutation("installed-name-set", "if set(names) != set(required):", "if False:"),
    Mutation(
        "version-membership",
        MEMBERSHIP,
        "if any((i[0], i[2], i[3]) not in "
        "{(a[0], a[2], a[3]) for a in admitted_set} for i in installed):",
    ),
    Mutation(
        "artifact-membership",
        MEMBERSHIP,
        "if any((i[0], i[1], i[3]) not in "
        "{(a[0], a[1], a[3]) for a in admitted_set} for i in installed):",
    ),
    Mutation(
        "dependency-membership",
        MEMBERSHIP,
        "if any((i[0], i[1], i[2]) not in "
        "{(a[0], a[1], a[2]) for a in admitted_set} for i in installed):",
    ),
    Mutation(
        "rollback-rejection",
        MEMBERSHIP,
        'if any(item not in admitted_set or item[1] == "1" for item in installed):',
    ),
    Mutation(
        "expected-authority",
        'return Comparison(True, "admitted-fixture-set", expected)',
        'return Comparison(expected == "accept", "admitted-fixture-set", expected)',
    ),
    Mutation("digest-characters", "[0-9a-f]{64}", "[0-9a-fA-Fg]{64}"),
    Mutation("byte-bound", "len(payload) > MAX_BYTES", "False"),
    Mutation("array-bound", "len(value) > MAX_ITEMS", "len(value) > MAX_ITEMS + 1"),
    Mutation(
        "string-codepoints",
        "not 1 <= len(value) <= 256",
        'not 1 <= len(value.encode("utf-8", errors="surrogatepass")) <= 256',
    ),
)


@contextmanager
def candidate_module(source):
    """Compile only caller-owned development source, never an external payload."""
    name = "tools._s1a_qualification_candidate"
    previous = sys.modules.get(name)
    candidate = ModuleType(name)
    sys.modules[name] = candidate
    try:
        exec(
            compile(source, "<trusted-s1a-fixture-candidate>", "exec"),
            candidate.__dict__,
        )
        yield candidate
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous


def evaluate(source, test_case, test_module, stream):
    """Errors and skipped coverage are invalid, never assertion kills."""
    try:
        with candidate_module(source) as candidate:
            with mock.patch.multiple(
                test_module,
                compare_fixture=candidate.compare_fixture,
                FixtureRefusal=candidate.FixtureRefusal,
            ):
                suite = unittest.TestLoader().loadTestsFromTestCase(test_case)
                result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    except Exception as error:
        return {"outcome": "invalid", "error_type": type(error).__name__}
    counts = {
        "tests": result.testsRun,
        "assertion_failures": len(result.failures),
        "errors": len(result.errors),
    }
    if (
        not result.testsRun
        or result.errors
        or result.skipped
        or result.expectedFailures
        or result.unexpectedSuccesses
    ):
        return {"outcome": "invalid", **counts}
    return {
        "outcome": "assertion-failure" if result.failures else "passed",
        **counts,
    }


def qualify_source(source, test_case, test_module, stream, mutations=MUTATIONS):
    """Return fixture assertion results, without runner or provenance authority."""
    baseline = evaluate(source, test_case, test_module, stream)
    rows = []
    if baseline["outcome"] == "passed":
        for mutation in mutations:
            print(f"MUTATION {mutation.name}", file=stream)
            if source.count(mutation.before) != 1:
                rows.append({"name": mutation.name, "outcome": "not-applied"})
                continue
            observation = evaluate(
                source.replace(mutation.before, mutation.after, 1),
                test_case,
                test_module,
                stream,
            )
            outcome = {
                "assertion-failure": "killed",
                "passed": "survived",
                "invalid": "invalid",
            }[observation["outcome"]]
            rows.append(
                {"name": mutation.name, "outcome": outcome, "assertions": observation}
            )
    split = {
        outcome: sum(row["outcome"] == outcome for row in rows)
        for outcome in ("killed", "survived", "accepted", "not-applied", "invalid")
    }
    return {"baseline": baseline, "mutations": rows, "split": split}


def main():
    if len(sys.argv) != 1:
        raise SystemExit("this fixed product command takes no source or execution args")
    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        "s1a_fixture_assertions", root / "tests/test_inventory_fixture.py"
    )
    assertions = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(assertions)
    report = qualify_source(
        (root / "tools/inventory_fixture.py").read_text(),
        assertions.InventoryFixtureTests,
        assertions,
        sys.stderr,
    )
    print(json.dumps(report, indent=2))
    return (
        0
        if report["baseline"]["outcome"] == "passed"
        and report["split"]["killed"] == len(MUTATIONS)
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
