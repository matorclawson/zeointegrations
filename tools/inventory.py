"""Read committed Python sources as data; never import or execute provider code."""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import subprocess
import sys
import tarfile
import tomllib
import warnings
from pathlib import Path


def git(repo: Path, *args: str) -> bytes:
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=env,
        check=True,
        capture_output=True,
    ).stdout


def snapshot(repo: Path, paths: list[str]) -> tuple[str, dict[str, bytes]]:
    commit = git(repo, "rev-parse", "HEAD").decode().strip()
    archive = git(repo, "archive", commit, *paths)
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        files = {}
        for member in source.getmembers():
            if member.isfile():
                stream = source.extractfile(member)
                assert stream is not None
                files[member.name] = stream.read()
    return commit, files


def parse(data: bytes) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return ast.parse(data)


def imports(tree: ast.Module) -> set[str]:
    result = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            result.add(node.module.split(".")[0])
    return result - sys.stdlib_module_names


def router_directories(tree: ast.Module) -> dict[str, str]:
    aliases = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if len(parts) >= 3 and parts[0] == "integrations":
                for alias in node.names:
                    aliases[alias.asname or alias.name] = parts[1]
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "INTEGRATION_ROUTERS"
            for target in node.targets
        ):
            if not isinstance(node.value, ast.Dict):
                raise ValueError("INTEGRATION_ROUTERS is not a literal dictionary")
            return {
                ast.literal_eval(key): aliases[value.id]
                for key, value in zip(node.value.keys, node.value.values, strict=True)
                if isinstance(value, ast.Name)
            }
    raise ValueError("INTEGRATION_ROUTERS not found")


def summarize(files: dict[str, bytes], prefix: str, first_party: set[str]) -> dict:
    selected = {name: data for name, data in files.items() if name.startswith(prefix)}
    runtime, tests, errors = set(), set(), []
    lines = test_lines = 0
    for name, data in selected.items():
        if not name.endswith(".py"):
            continue
        is_test = Path(name).name == "tests.py" or any(
            part == "tests" or part.startswith("test_") for part in Path(name).parts
        )
        count = len(data.splitlines())
        lines += count
        test_lines += count if is_test else 0
        try:
            roots = imports(parse(data)) - first_party
        except SyntaxError:
            errors.append(name)
            continue
        (tests if is_test else runtime).update(roots)
    return {
        "files": len(selected),
        "bytes": sum(len(data) for data in selected.values()),
        "python_lines_including_tests": lines,
        "python_test_lines": test_lines,
        "third_party_import_roots": sorted(runtime),
        "additional_test_import_roots": sorted(tests - runtime),
        "parse_errors": sorted(errors),
    }


OVERLAP = {
    "github": "github",
    "gmail": "google.mail",
    "google_calendar": "google.calendar",
    "google_docs": "google.docs",
    "google_drive": "google.drive",
    "google_sheets": "google.sheets",
    "notion": "notion",
    "supabase": "supabase (different API: SQL, not SDK)",
    "youtube": "google/youtube (unregistered)",
}

AUTH_OVERRIDES = {
    "common": "shared auth/custody support; not a provider",
    "veyrax": "VeyraX internal workflow support; not a provider port",
    "veyrax_auth": "VeyraX credential store (Supabase/encryption); not a provider port",
    "gmail": "OAuth (imported but unregistered in router registry/catalog)",
    "docusign": "OAuth (unregistered; route uses TokenService)",
    "hilvl": "API key (unregistered; validate_provider_api_key)",
    "veyrax-mcp": "bearer plus server Upstash token (unregistered)",
    "apollo": "server RapidAPI key (catalog says none)",
    "binance_p2p": "server RapidAPI key (catalog says none)",
    "bybit_p2p": "server RapidAPI key (catalog says none)",
    "okx_p2p": "server RapidAPI key (catalog says none)",
    "ipinfo": "server API token (catalog says none)",
    "skyscanner": "server RapidAPI key (catalog says none)",
    "yelp": "server RapidAPI key (catalog says none)",
    "zillow": "server RapidAPI key (catalog says none)",
    "supabase": "database credentials; delegates to postgresql",
    "neondb": "database credentials; delegates to postgresql",
}


def build(veyrax: Path, zeocore: Path) -> dict:
    vcommit, vfiles = snapshot(veyrax, ["aci_server"])
    zcommit, zfiles = snapshot(zeocore, ["pyproject.toml", "src/zeo_core/integrations"])
    catalog = json.loads(vfiles["aci_server/db/scripts/catalog.json"])
    routers = router_directories(parse(vfiles["aci_server/main.py"]))
    if set(catalog) != set(routers):
        raise ValueError("catalog and registered routers differ; review mapping")
    vroot = "aci_server/integrations/"
    dirs = sorted(
        {
            name.removeprefix(vroot).split("/")[0]
            for name in vfiles
            if name.startswith(vroot)
        }
    )
    first_party = {
        "aci_server",
        "integrations",
        "db",
        "utils",
        "config",
        "llm",
        "celery_app",
        "flow",
        "memory",
        "agent",
        "service",
        "tools",
        "main",
        "models",
        "auth",
        "acitrace",
        "mcp_deployment",
        "healthcheck",
    }
    providers = []
    for name in dirs:
        tags = sorted(tag for tag, directory in routers.items() if directory == name)
        auth = sorted({catalog[tag]["auth_method"] for tag in tags})
        providers.append(
            {
                "directory": name,
                "router_tags": tags,
                "catalog_auth": auth,
                "observed_auth": AUTH_OVERRIDES.get(name, ", ".join(auth)),
                "zeocore_overlap": OVERLAP.get(name, "none"),
                **summarize(vfiles, f"{vroot}{name}/", first_party),
            }
        )
    project = tomllib.loads(zfiles["pyproject.toml"].decode())["project"]
    entries = []
    for name, target in project["entry-points"]["zeo_core.integrations"].items():
        module = target.split(":")[0]
        directory = module.removeprefix("zeo_core.integrations.").replace(".", "/")
        entries.append(
            {
                "name": name,
                "target": target,
                "directory": directory,
                **summarize(
                    zfiles, f"src/zeo_core/integrations/{directory}/", {"zeo_core"}
                ),
            }
        )
    return {
        "sources": {"veyrax": vcommit, "zeocore": zcommit},
        "method": "committed snapshots, AST only, no imports or provider calls",
        "veyrax_requirements": vfiles["aci_server/requirements.txt"]
        .decode()
        .splitlines(),
        "veyrax_registered_router_count": len(routers),
        "veyrax_directories": providers,
        "zeocore_entry_points": entries,
        "zeocore_extras": project["optional-dependencies"],
        "zeocore_google_family": summarize(
            zfiles, "src/zeo_core/integrations/google/", {"zeo_core"}
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--veyrax", required=True, type=Path)
    parser.add_argument("--zeocore", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    # Refuse to write the report into either source repository.
    output = args.output.resolve()
    for repo in (args.veyrax, args.zeocore):
        if output.is_relative_to(repo.resolve()):
            parser.error("output must be outside the inventoried repositories")
    result = build(args.veyrax, args.zeocore)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
