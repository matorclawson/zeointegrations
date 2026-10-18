"""S1a fixture-only comparison; never loads packages or grants execution authority.

Coordination: zeoconnect-tools handoff e08c51f2e1c6211ea4914dabcf383020063354df.
This is not a production inventory, manifest, loader, or approval protocol.
"""

import json
import re
from dataclasses import dataclass

MAX_BYTES = 16_384
MAX_ITEMS = 64
ROOT_KEYS = frozenset(
    {
        "fixture_version",
        "case_id",
        "revision_label",
        "required_names",
        "admitted_artifacts",
        "installed_artifacts",
        "expected",
    }
)
ARTIFACT_KEYS = frozenset(
    {"distribution", "version", "artifact_sha256", "dependency_lock_sha256"}
)
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class FixtureRefusal(ValueError):
    """Malformed fixture, without echoing untrusted payloads."""


@dataclass(frozen=True)
class Comparison:
    """Fixture observation only; expected does not influence the verdict."""

    accepted: bool
    reason: str
    expected: str

    @property
    def matches_expected(self) -> bool:
        return self.expected == ("accept" if self.accepted else "refuse")


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise FixtureRefusal("duplicate-key")
        result[key] = value
    return result


def _constant(_value: str) -> object:
    raise FixtureRefusal("non-json-constant")


def _text(value: object) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 256:
        raise FixtureRefusal("invalid-string")
    # Escaped lone surrogates are accepted by json.loads but are not UTF-8 text.
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise FixtureRefusal("invalid-string") from None
    return value


def _array(value: object) -> list:
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        raise FixtureRefusal("invalid-array")
    return value


def _artifacts(value: object) -> list[tuple[str, str, str, str]]:
    artifacts = []
    for item in _array(value):
        if not isinstance(item, dict) or item.keys() != ARTIFACT_KEYS:
            raise FixtureRefusal("invalid-artifact-fields")
        name = _text(item["distribution"])
        version = _text(item["version"])
        artifact = _text(item["artifact_sha256"])
        dependency = _text(item["dependency_lock_sha256"])
        if not DIGEST.fullmatch(artifact) or not DIGEST.fullmatch(dependency):
            raise FixtureRefusal("invalid-digest")
        artifacts.append((name, version, artifact, dependency))
    return artifacts


def compare_fixture(payload: bytes) -> Comparison:
    """Compare one bounded JSON fixture; malformed input raises FixtureRefusal.

    Names are exact, case-sensitive fixture labels, without packaging normalization.
    A refused comparison is a valid fixture observation. Malformed fixtures have no
    assertion result. Neither expected nor revision_label grants any authority.
    """
    if not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        raise FixtureRefusal("invalid-payload-size-or-type")
    try:
        root = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_object,
            parse_constant=_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        raise FixtureRefusal("invalid-json") from None
    if not isinstance(root, dict) or root.keys() != ROOT_KEYS:
        raise FixtureRefusal("invalid-root-fields")
    if type(root["fixture_version"]) is not int or root["fixture_version"] != 1:
        raise FixtureRefusal("invalid-fixture-version")
    _text(root["case_id"])
    _text(root["revision_label"])
    expected = root["expected"]
    if not isinstance(expected, str) or expected not in {"accept", "refuse"}:
        raise FixtureRefusal("invalid-expected")
    required = [_text(name) for name in _array(root["required_names"])]
    if len(set(required)) != len(required):
        raise FixtureRefusal("duplicate-required-name")
    admitted = _artifacts(root["admitted_artifacts"])
    installed = _artifacts(root["installed_artifacts"])
    names = [item[0] for item in installed]
    if len(set(names)) != len(names):
        return Comparison(False, "duplicate-installed-name", expected)
    if set(names) != set(required):
        return Comparison(False, "installed-name-set-mismatch", expected)
    admitted_set = set(admitted)
    if any(item not in admitted_set for item in installed):
        return Comparison(False, "unapproved-artifact-tuple", expected)
    return Comparison(True, "admitted-fixture-set", expected)
