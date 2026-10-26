"""Qualify the installed aggregate at its declared Python 3.12 floor."""

import hashlib
import os
import shutil
import subprocess
from pathlib import Path


def main():
    configured = os.environ.get("FLOOR_PYTHON") or shutil.which("python3.12")
    if not configured:
        raise SystemExit("Set FLOOR_PYTHON to an existing admitted Python 3.12 binary")
    binary = Path(configured).resolve(strict=True)
    before = hashlib.sha256(binary.read_bytes()).hexdigest()
    version = subprocess.check_output([str(binary), "--version"], text=True).strip()
    if not version.startswith("Python 3.12."):
        raise SystemExit(f"Python floor requires 3.12, got {version}")
    root = Path(__file__).resolve().parents[1]
    environment = {
        **os.environ,
        "UV_PYTHON": str(binary),
        "UV_PYTHON_DOWNLOADS": "never",
        "UV_PROJECT_ENVIRONMENT": str(root / ".venv" / "python312"),
    }
    environment.pop("VIRTUAL_ENV", None)
    environment.pop("PYTHONPATH", None)
    print(f"FLOOR_PYTHON {binary}\nFLOOR_VERSION {version}", flush=True)
    print(f"FLOOR_SHA256_BEFORE {before}", flush=True)
    commands = [
        ["uv", "sync", "--frozen", "--all-extras"],
        [
            "uv",
            "run",
            "--frozen",
            "--no-sync",
            "python",
            "-m",
            "compileall",
            "-q",
            "src/zeo_integrations",
        ],
        [
            "uv",
            "run",
            "--frozen",
            "--no-sync",
            "python",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        ],
        [
            "uv",
            "run",
            "--frozen",
            "--no-sync",
            "python",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests_installed",
            "-v",
        ],
        [
            "uv",
            "run",
            "--frozen",
            "--no-sync",
            "python",
            "tools/verify_provider_tests.py",
        ],
    ]
    result = 1
    try:
        for command in commands:
            subprocess.run(command, cwd=root, env=environment, check=True)
        result = 0
    finally:
        after = hashlib.sha256(binary.read_bytes()).hexdigest()
        if after != before:
            result = 1
        print(f"FLOOR_SHA256_AFTER {after}\nFLOOR_EXIT {result}", flush=True)
    if result:
        raise SystemExit(result)


if __name__ == "__main__":
    main()
