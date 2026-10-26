"""Run travelling provider tests when the migration has introduced them."""

import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    directory = Path("tests/test_integrations")
    if not any(directory.rglob("test_*.py")):
        print("No provider tests migrated into the aggregate yet")
        return
    environment = {
        **os.environ,
        "HYPOTHESIS_STORAGE_DIRECTORY": str(Path(".venv/hypothesis").resolve()),
    }
    subprocess.run(
        [sys.executable, "-m", "pytest", str(directory), "-q",
         "-o", "cache_dir=.venv/pytest_cache"],
        env=environment,
        check=True,
    )


if __name__ == "__main__":
    main()
