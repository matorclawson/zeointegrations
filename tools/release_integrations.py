"""Plan immutable main releases, build on ENG, and check PyPI upload identity."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import tomllib
import urllib.error
import urllib.request

REPOSITORY = "zeroemployeeorg/zeointegrations"
PROJECT = "zeo-integrations"
SHA = re.compile(r"[0-9a-f]{40}")
RELEASE_PATHS = (
    "src/", "pyproject.toml", "uv.lock", "README.md", "LICENSE", "NOTICE",
    "Makefile", "tools/release_integrations.py", ".github/workflows/publish-integrations.yml",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def metadata(commit: str) -> dict:
    if not SHA.fullmatch(commit):
        raise ValueError("Expected a complete immutable commit")
    return tomllib.loads(git("show", f"{commit}:pyproject.toml"))["project"]


def version_for(source_version: str, count: int) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.\d+", source_version)
    if match is None or count < 1:
        raise ValueError("Reviewed version must be major.minor.patch; count must be positive")
    return f"{match[1]}.{match[2]}.{count}"


def release_version(commit: str) -> str:
    return version_for(metadata(commit)["version"], int(git("rev-list", "--first-parent", "--count", commit)))


def pypi_json(version: str | None = None) -> dict | None:
    suffix = f"/{version}" if version else ""
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{PROJECT}{suffix}/json", timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def plan() -> list[dict[str, str]]:
    """Stateless reconciliation: every missing qualifying main commit, oldest first."""
    remote = pypi_json()
    published = (remote or {}).get("releases", {})
    result = []
    for commit in git("rev-list", "--first-parent", "--reverse", "HEAD").splitlines():
        try:
            project = metadata(commit)
        except (subprocess.CalledProcessError, KeyError):
            continue
        if project.get("name") != PROJECT:
            continue
        changed = git("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-m", "--first-parent", commit).splitlines()
        if not any(any(path == prefix or path.startswith(prefix) for prefix in RELEASE_PATHS) for path in changed):
            continue
        version = release_version(commit)
        if published.get(version):
            existing = pypi_json(version)
            expected_source = f"https://github.com/{REPOSITORY}/tree/{commit}"
            urls = (existing or {}).get("info", {}).get("project_urls") or {}
            if urls.get("Source") != expected_source:
                raise ValueError("Published version does not identify its expected source")
            continue
        result.append({"commit": commit, "version": version})
        if len(result) == 32:
            break  # Next hourly reconciliation handles remaining missing versions.
    return result


def stamp_project(text: str, version: str) -> str:
    """Change only reviewed project's version in a disposable build copy."""
    start = text.index("[project]\n") + len("[project]\n")
    end = text.find("\n[", start)
    if end == -1:
        end = len(text)
    section, count = re.subn(r'^version = "[^"]+"$', f'version = "{version}"', text[start:end], count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("Project must have one explicit reviewed version")
    return text[:start] + section + text[end:]


def build(commit: str, destination: Path) -> None:
    if metadata(commit)["name"] != PROJECT or git("rev-parse", "HEAD") != commit:
        raise ValueError("Build requires an exact aggregate checkout")
    if git("status", "--porcelain"):
        raise ValueError("Build source must be clean")
    version = release_version(commit)
    epoch = git("show", "-s", "--format=%ct", commit)
    source_tree = git("rev-parse", f"{commit}^{{tree}}")
    archive = subprocess.check_output(["git", "archive", commit])
    environment = {**os.environ, "SOURCE_DATE_EPOCH": epoch, "UV_PYTHON_DOWNLOADS": "never"}
    with tempfile.TemporaryDirectory(prefix="zeo-release-") as name:
        source = Path(name)
        with tarfile.open(fileobj=io.BytesIO(archive)) as data:
            data.extractall(source, filter="data")
        project = source / "pyproject.toml"
        text = stamp_project(project.read_text(), version)
        if "urls" in metadata(commit):
            raise ValueError("Source URL metadata changed; release helper needs review")
        project.write_text(text + f'\n[project.urls]\nSource = "https://github.com/{REPOSITORY}/tree/{commit}"\n')
        details = {"repository": REPOSITORY, "commit": commit, "tree": source_tree,
                   "version": version, "lock_sha256": hashlib.sha256((source / "uv.lock").read_bytes()).hexdigest()}
        (source / "src/zeo_integrations/_build.json").write_text(json.dumps(details, sort_keys=True) + "\n")
        subprocess.run(["uv", "build", "--offline", "--no-sources"], cwd=source, env=environment, check=True)
        destination.mkdir(parents=True, exist_ok=False)
        expected = {f"zeo_integrations-{version}.tar.gz",
                    f"zeo_integrations-{version}-py3-none-any.whl"}
        if {p.name for p in (source / "dist").iterdir()} != expected:
            raise ValueError("Build produced unexpected distribution artifacts")
        files = []
        for path in sorted((source / "dist").iterdir()):
            data = path.read_bytes()
            (destination / path.name).write_bytes(data)
            files.append({"name": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        details["artifacts"] = files
        log = destination.parent / "qualification.log"
        if not log.is_file() or not log.read_text().endswith("EXIT 0\n"):
            raise ValueError("Successful original qualification receipt required")
        details["qualification_log_sha256"] = hashlib.sha256(log.read_bytes()).hexdigest()
        # Receipt is outside the package upload directory.
        (destination.parent / "release-receipt.json").write_text(json.dumps(details, indent=2) + "\n")
    if git("status", "--porcelain"):
        raise ValueError("Build changed the source checkout")


def existing_matches(receipt: dict, remote: dict | None) -> bool:
    if remote is None:
        return False
    files = {file["filename"]: file for file in remote["urls"]}
    expected = {file["name"]: file for file in receipt["artifacts"]}
    if set(files) != set(expected):
        raise ValueError("PyPI version has unexpected artifact names; stop without upload")
    for name, item in expected.items():
        if files[name]["digests"]["sha256"] != item["sha256"]:
            raise ValueError("Existing PyPI artifact differs from this exact build; stop")
    return True


def check(receipt_path: Path, require_published: bool = False) -> None:
    receipt = json.loads(receipt_path.read_text())
    if receipt["repository"] != REPOSITORY or not SHA.fullmatch(receipt["commit"]):
        raise ValueError("Invalid release receipt source")
    directory = receipt_path.parent / "dist"
    if {p.name for p in directory.iterdir()} != {p["name"] for p in receipt["artifacts"]}:
        raise ValueError("Unexpected files in upload directory")
    for item in receipt["artifacts"]:
        data = (directory / item["name"]).read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("Artifact does not match its build receipt")
    present = existing_matches(receipt, pypi_json(receipt["version"]))
    if require_published and not present:
        raise ValueError("Published index file readback is not yet available")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a") as stream:
            stream.write(f"published={'true' if present else 'false'}\n")
    print(json.dumps({"version": receipt["version"], "already_published_identical": present}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("plan", "build", "check"))
    parser.add_argument("--commit")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--require-published", action="store_true")
    args = parser.parse_args()
    if args.action == "plan":
        print(json.dumps({"include": plan()}))
    elif args.action == "build":
        if args.commit is None or args.destination is None:
            parser.error("build requires --commit and --destination")
        build(args.commit, args.destination)
    else:
        if args.receipt is None:
            parser.error("check requires --receipt")
        check(args.receipt, args.require_published)


if __name__ == "__main__":
    main()
