"""Capture an exact-head ENG qualification receipt outside the source tree."""

import hashlib
import os
from pathlib import Path
import platform
import subprocess
import sys


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    commit, output = sys.argv[1], Path(sys.argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise SystemExit("Refuse to overwrite an original qualification log")
    interpreter = Path(os.environ["UV_PYTHON"]).resolve(strict=True)
    initial_digest = digest(interpreter)
    with output.open("w") as stream:
        head = git("rev-parse", "HEAD")
        dirty = git("status", "--porcelain")
        stream.write(f"HEAD {head}\nDIRTY {len(dirty.splitlines())}\nHOST {platform.node()}\n")
        stream.write(f"PYTHON {interpreter}\nPYTHON_SHA256_BEFORE {initial_digest}\nCOMMAND make setup verify\n")
        stream.flush()
        result = 1
        try:
            if head != commit or dirty:
                raise ValueError("Qualification requires the exact clean source commit")
            if platform.node().lower() != "eng-uk-0006":
                raise ValueError("Qualification must run on the admitted ENG host")
            version = subprocess.check_output([str(interpreter), "--version"], text=True).strip()
            if version != "Python 3.14.3":
                raise ValueError("Configured gate interpreter must be admitted Python3.14.3")
            result = subprocess.run(["make", "setup", "verify"], stdout=stream, stderr=subprocess.STDOUT).returncode
        except Exception as error:
            stream.write(f"GATE_ERROR {error}\n")
            result = 1
        finally:
            after = git("status", "--porcelain")
            after_digest = digest(interpreter)
            if after or after_digest != initial_digest:
                result = 1
            stream.write(f"HEAD_AFTER {git('rev-parse', 'HEAD')}\nDIRTY_AFTER {len(after.splitlines())}\nPYTHON_SHA256_AFTER {after_digest}\nEXIT {result}\n")
    print(f"QUALIFICATION_LOG_SHA256 {digest(output)}")
    raise SystemExit(result)


if __name__ == "__main__":
    main()
