"""Publish only the reviewed aggregate metadata version; never contact a provider."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import urllib.error
import urllib.parse
import urllib.request

PROJECT = "zeo-integrations"
REPOSITORY = "zeroemployeeorg/zeointegrations"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def metadata(path: Path = Path("pyproject.toml")) -> dict:
    project = tomllib.loads(path.read_text())["project"]
    if project.get("name") != PROJECT:
        raise ValueError("Only the zeo-integrations aggregate may be published")
    version = project.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9][A-Za-z0-9.!+_-]*", version):
        raise ValueError("An explicit package metadata version is required")
    return project


def version_exists(version: str, opener=urllib.request.urlopen) -> bool:
    url = f"https://pypi.org/pypi/{PROJECT}/{urllib.parse.quote(version, safe='')}/json"
    try:
        with opener(url, timeout=30) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise
    name = data["info"]["name"].lower().replace("_", "-").replace(".", "-")
    if name != PROJECT or not isinstance(data.get("urls"), list) or not data["urls"]:
        raise ValueError("Unexpected or incomplete PyPI version response; refusing upload")
    return True


def plan() -> None:
    version = metadata()["version"]
    publish = not version_exists(version)
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a") as stream:
            stream.write(f"publish={'true' if publish else 'false'}\n")
    print(json.dumps({"project": PROJECT, "version": version, "publish": publish}))


def artifact_hashes(directory: Path, version: str) -> dict[str, str]:
    expected = {f"zeo_integrations-{version}.tar.gz", f"zeo_integrations-{version}-py3-none-any.whl"}
    if {p.name for p in directory.iterdir()} != expected:
        raise ValueError("Expected exactly the aggregate wheel and sdist")
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.iterdir())}


def build(destination: Path) -> None:
    if git("status", "--porcelain"):
        raise ValueError("Release build requires a clean exact source checkout")
    version = metadata()["version"]
    commit, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    archive = subprocess.check_output(["git", "archive", commit])
    epoch = git("show", "-s", "--format=%ct", commit)
    environment = {**os.environ, "SOURCE_DATE_EPOCH": epoch, "UV_PYTHON_DOWNLOADS": "never"}
    with tempfile.TemporaryDirectory(prefix="zir.") as work:
        outputs = []
        for number in (1, 2):
            source = Path(work) / str(number)
            source.mkdir()
            with tarfile.open(fileobj=io.BytesIO(archive)) as data:
                data.extractall(source, filter="data")
            subprocess.run(
                [sys.executable, "-m", "hatchling", "build", "-t", "sdist", "-t", "wheel"], cwd=source, env=environment, check=True
            )
            outputs.append(source / "dist")
        hashes = artifact_hashes(outputs[0], version)
        if hashes != artifact_hashes(outputs[1], version):
            raise ValueError("The two offline builds differ; refusing publication")
        destination.mkdir(parents=True, exist_ok=False)
        dist = destination / "dist"
        dist.mkdir()
        for name in hashes:
            (dist / name).write_bytes((outputs[0] / name).read_bytes())
        (destination / "SHA256SUMS").write_text("".join(f"{value}  dist/{name}\n" for name, value in hashes.items()))
        receipt = {
            "repository": REPOSITORY, "commit": commit, "tree": tree,
            "project": PROJECT, "version": version, "source_date_epoch": epoch,
            "lock_sha256": hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest(),
            "python": sys.version, "uv": subprocess.check_output(["uv", "--version"], text=True).strip(),
            "repeated_builds_identical": True, "artifacts": hashes,
        }
        (destination / "release-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if git("status", "--porcelain") or git("rev-parse", "HEAD") != commit:
        raise ValueError("Release build changed the source checkout")


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan")
    builder = commands.add_parser("build")
    builder.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "plan":
        plan()
    else:
        build(args.destination)


if __name__ == "__main__":
    main()
