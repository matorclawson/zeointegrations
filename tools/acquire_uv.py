"""Acquire one checksum-pinned CI tool into a new private directory; never run it."""

import argparse
import hashlib
import io
import json
import platform
import re
import tarfile
import urllib.request
from pathlib import Path

VERSION = "0.12.2"
PLATFORM = "x86_64-unknown-linux-gnu"
ARCHIVE_URL = (
    f"https://github.com/astral-sh/uv/releases/download/{VERSION}/uv-{PLATFORM}.tar.gz"
)
ARCHIVE_SHA256 = "d66e96b5f1ca3b99806eee283a8125d33a0bd669e6e6d9bc4ab7ffda63c41bf4"
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_EXECUTABLE_BYTES = 128 * 1024 * 1024
EXECUTABLES = ("uv", "uvx")


def acquire(directory: Path, context: dict[str, str]) -> dict:
    """Refuse cache reuse; verify the whole archive before reading its members."""
    if directory.exists() or directory.is_symlink():
        raise FileExistsError("destination must be new; existing paths are not cleared")
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "AMD64"):
        raise ValueError("acquisition requires the pinned linux/amd64 CI platform")
    for key in ("source_head", "checkout_head"):
        if not re.fullmatch(r"[0-9a-f]{40}", context[key]):
            raise ValueError("source and checkout identities must be full commit ids")
    for key in ("run_id", "run_attempt"):
        if not re.fullmatch(r"[0-9]+", context[key]):
            raise ValueError("run identity must contain ASCII digits only")

    with urllib.request.urlopen(ARCHIVE_URL, timeout=30) as response:
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES:
        raise ValueError("archive exceeds the acquisition bound")
    digest = hashlib.sha256(data).hexdigest()
    if digest != ARCHIVE_SHA256:
        raise ValueError("archive checksum mismatch; no tool is installed")

    binaries = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        for name in EXECUTABLES:
            expected = f"uv-{PLATFORM}/{name}"
            matches = [member for member in members if member.name == expected]
            if len(matches) != 1 or not matches[0].isfile():
                raise ValueError("expected executable is missing, duplicated or a link")
            member = matches[0]
            if not 0 < member.size <= MAX_EXECUTABLE_BYTES:
                raise ValueError("executable exceeds the acquisition bound")
            stream = archive.extractfile(member)
            assert stream is not None
            payload = stream.read(MAX_EXECUTABLE_BYTES + 1)
            if len(payload) != member.size:
                raise ValueError("executable size does not match the verified archive")
            binaries[name] = payload

    # Only the two fixed filenames are written: no general tar extraction, cache
    # lookup, shared-cache removal, environment loading, or tool execution.
    directory.mkdir(mode=0o700)
    receipt = {
        "tool": "uv",
        "version": VERSION,
        "platform": PLATFORM,
        "method": "fresh checksum-verified archive; no runner tool-cache lookup",
        "archive": {"url": ARCHIVE_URL, "sha256": digest, "bytes": len(data)},
        "context": context,
        "executables": {},
    }
    for name, payload in binaries.items():
        target = directory / name
        with target.open("xb") as output:
            output.write(payload)
        target.chmod(0o700)
        installed_digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if installed_digest != hashlib.sha256(payload).hexdigest():
            raise ValueError("written executable differs from the verified archive")
        receipt["executables"][name] = {
            "bytes": len(payload),
            "sha256": installed_digest,
        }
    (directory / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--checkout-head", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-attempt", required=True)
    args = parser.parse_args()
    context = {
        key: getattr(args, key)
        for key in ("source_head", "checkout_head", "run_id", "run_attempt")
    }
    try:
        receipt = acquire(args.directory, context)
    except (OSError, ValueError, tarfile.TarError) as error:
        # No server response or ambient environment is echoed into public logs.
        parser.exit(
            1, f"uv acquisition refused ({type(error).__name__}); inspect inputs\n"
        )
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
