"""Bounded descriptive manifest checks; no imports, fetches or execution grants."""

import json
import re
import tomllib
from pathlib import Path, PurePosixPath

MAX_BYTES = 16_384
FIELDS = {
    "name",
    "kind",
    "entry_points",
    "secrets",
    "operations",
    "minimum_zeo_core",
    "license",
    "provenance",
}
PROVENANCE = {"repository", "commit", "source", "destination"}


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _bounds(value, depth=0):
    if depth > 8:
        raise ValueError("manifest nesting budget exceeded")
    if isinstance(value, str):
        if len(value) > 256 or any(ord(char) < 32 for char in value):
            raise ValueError("invalid string budget or control character")
    elif isinstance(value, list):
        if len(value) > 64:
            raise ValueError("array budget exceeded")
        for item in value:
            _bounds(item, depth + 1)
    elif isinstance(value, dict):
        for key, item in value.items():
            _bounds(key, depth + 1)
            _bounds(item, depth + 1)
    else:
        raise ValueError("only strings, objects and arrays are supported")


def _path(value):
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or PurePosixPath(value).is_absolute()
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise ValueError("provenance path must be relative POSIX segments")


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?", value
    ):
        raise ValueError("invalid distribution name")
    return re.sub(r"[-_.]+", "-", value).lower()


def validate(data: bytes, project: dict) -> dict:
    """Check pilot metadata, not executable safety or provider admission."""
    if len(data) > MAX_BYTES:
        raise ValueError("manifest byte budget exceeded")
    try:
        manifest = json.loads(data.decode("utf-8"), object_pairs_hook=_object)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("invalid bounded UTF-8 JSON") from exc
    if not isinstance(manifest, dict) or set(manifest) != FIELDS:
        raise ValueError("manifest fields differ from contract")
    _bounds(manifest)
    if _name(manifest["name"]) != _name(project["name"]):
        raise ValueError("distribution name mismatch")
    if not isinstance(manifest["kind"], str) or manifest["kind"] not in {
        "plugin",
        "integration",
    }:
        raise ValueError("invalid kind")
    for field in ("entry_points", "secrets", "operations"):
        items = manifest[field]
        if (
            not isinstance(items, list)
            or any(not isinstance(item, str) or not item for item in items)
            or len(items) != len(set(items))
        ):
            raise ValueError("expected unique nonempty string array")
    names = project.get("entry-points", {}).get("zeo_core.integrations", {})
    if set(manifest["entry_points"]) != set(names):
        raise ValueError("entry-point names differ")
    if any(not re.fullmatch(r"[A-Z][A-Z0-9_]*", name) for name in manifest["secrets"]):
        raise ValueError("secret names only")
    if _name(project["name"]) == "zeo-plugin-ffmpeg" and (
        manifest["kind"] != "plugin"
        or manifest["secrets"]
        or set(manifest["operations"])
        != {"probe", "convert", "transcode_h264", "extract_audio", "thumbnail"}
    ):
        raise ValueError("ffmpeg metadata differs from reviewed local methods")
    if not names and _name(project["name"]) not in {
        "zeo-plugin-notebook",
        "zeo-integration-revolut-enroll",
    }:
        raise ValueError("unreviewed direct-import exception")
    minimum = manifest["minimum_zeo_core"]
    if not isinstance(minimum, str) or not re.fullmatch(
        r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", minimum
    ):
        raise ValueError("minimum must be an exact numeric release")
    # This pilot accepts the reviewed numeric-release form, not arbitrary PEP440.
    dependencies = project.get("dependencies", [])
    if f"zeocore>={minimum}" not in dependencies:
        raise ValueError("minimum differs from pilot dependency floor")
    if manifest["license"] != "MIT" or project.get("license") != "MIT":
        raise ValueError("pilot license mismatch")
    provenance = manifest["provenance"]
    if not isinstance(provenance, list) or not provenance:
        raise ValueError("provenance required")
    destinations = set()
    for item in provenance:
        if not isinstance(item, dict) or set(item) != PROVENANCE:
            raise ValueError("invalid provenance fields")
        if not isinstance(item["repository"], str) or not re.fullmatch(
            r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
            item["repository"],
        ):
            raise ValueError("invalid source repository")
        if not isinstance(item["commit"], str) or not re.fullmatch(
            r"[0-9a-f]{40}", item["commit"]
        ):
            raise ValueError("invalid source commit")
        for field in ("source", "destination"):
            _path(item[field])
        if item["destination"] in destinations:
            raise ValueError("duplicate provenance destination")
        destinations.add(item["destination"])
    return manifest


def validate_package(directory: Path) -> dict:
    with (directory / "manifest.json").open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    project = tomllib.loads((directory / "pyproject.toml").read_text())["project"]
    return validate(data, project)
