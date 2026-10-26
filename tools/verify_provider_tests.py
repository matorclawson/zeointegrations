"""Run travelling provider tests when the migration has introduced them."""

from pathlib import Path
import subprocess
import sys


def main() -> None:
    directory = Path("tests/test_integrations")
    if not any(directory.rglob("test_*.py")):
        print("No provider tests migrated into the aggregate yet")
        return
    subprocess.run(
        [sys.executable, "-m", "pytest", str(directory), "-q"], check=True
    )


if __name__ == "__main__":
    main()
