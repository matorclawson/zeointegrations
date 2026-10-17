"""Use inert archive bytes and mocked transport; never install or execute real uv."""

import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import acquire_uv


def archive_bytes(*, link=False, duplicate=False):
    result = io.BytesIO()
    with tarfile.open(fileobj=result, mode="w:gz") as archive:
        for name in ("uv", "uvx"):
            info = tarfile.TarInfo(f"uv-{acquire_uv.PLATFORM}/{name}")
            data = f"inert fixture for {name}\n".encode()
            if link and name == "uv":
                info.type = tarfile.SYMTYPE
                info.linkname = "/unrelated/path"
                archive.addfile(info)
            else:
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
                if duplicate and name == "uv":
                    archive.addfile(info, io.BytesIO(data))
        extra = tarfile.TarInfo("../unwanted")
        extra.size = 1
        archive.addfile(extra, io.BytesIO(b"x"))
    return result.getvalue()


class AcquireUvTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.system = mock.patch.object(
            acquire_uv.platform, "system", return_value="Linux"
        )
        self.machine = mock.patch.object(
            acquire_uv.platform, "machine", return_value="x86_64"
        )
        self.system.start()
        self.machine.start()
        self.addCleanup(self.system.stop)
        self.addCleanup(self.machine.stop)
        self.directory = Path(self.temp.name) / "fresh-tool"
        self.context = {
            "source_head": "a" * 40,
            "checkout_head": "b" * 40,
            "run_id": "123",
            "run_attempt": "1",
        }

    def acquire_fixture(self, data, **bounds):
        limits = {
            "MAX_ARCHIVE_BYTES": acquire_uv.MAX_ARCHIVE_BYTES,
            "MAX_EXECUTABLE_BYTES": acquire_uv.MAX_EXECUTABLE_BYTES,
            **bounds,
        }
        with (
            mock.patch.object(
                acquire_uv, "ARCHIVE_SHA256", hashlib.sha256(data).hexdigest()
            ),
            mock.patch.object(
                acquire_uv.urllib.request, "urlopen", return_value=io.BytesIO(data)
            ),
            mock.patch.multiple(acquire_uv, **limits),
        ):
            return acquire_uv.acquire(self.directory, self.context)

    def test_verified_archive_writes_only_expected_files_and_bound_receipt(self):
        data = archive_bytes()
        receipt = self.acquire_fixture(data)
        self.assertEqual(
            {p.name for p in self.directory.iterdir()}, {"uv", "uvx", "receipt.json"}
        )
        self.assertFalse((Path(self.temp.name) / "unwanted").exists())
        self.assertEqual(receipt["context"], self.context)
        self.assertEqual(receipt["archive"]["sha256"], hashlib.sha256(data).hexdigest())
        for name in ("uv", "uvx"):
            expected = f"inert fixture for {name}\n".encode()
            self.assertEqual((self.directory / name).read_bytes(), expected)
            self.assertEqual(
                receipt["executables"][name]["sha256"],
                hashlib.sha256(expected).hexdigest(),
            )
        self.assertEqual(
            json.loads((self.directory / "receipt.json").read_text()), receipt
        )

    def test_checksum_mismatch_creates_no_directory(self):
        with (
            mock.patch.object(
                acquire_uv.urllib.request,
                "urlopen",
                return_value=io.BytesIO(archive_bytes()),
            ),
            self.assertRaisesRegex(ValueError, "checksum mismatch"),
        ):
            acquire_uv.acquire(self.directory, self.context)
        self.assertFalse(self.directory.exists())

    def test_existing_directory_never_reused_or_cleared(self):
        self.directory.mkdir()
        marker = self.directory / "keep"
        marker.write_bytes(b"existing")
        with (
            mock.patch.object(acquire_uv.urllib.request, "urlopen") as download,
            self.assertRaises(FileExistsError),
        ):
            acquire_uv.acquire(self.directory, self.context)
        download.assert_not_called()
        self.assertEqual(marker.read_bytes(), b"existing")

    def test_invalid_context_is_refused_before_transport(self):
        self.context["source_head"] = "not-a-commit"
        with (
            mock.patch.object(acquire_uv.urllib.request, "urlopen") as download,
            self.assertRaises(ValueError),
        ):
            acquire_uv.acquire(self.directory, self.context)
        download.assert_not_called()

    def test_link_in_expected_executable_is_refused_before_writing(self):
        with self.assertRaisesRegex(ValueError, "a link"):
            self.acquire_fixture(archive_bytes(link=True))
        self.assertFalse(self.directory.exists())

    def test_unsupported_platform_is_refused_before_transport(self):
        with (
            mock.patch.object(acquire_uv.platform, "system", return_value="Darwin"),
            mock.patch.object(acquire_uv.urllib.request, "urlopen") as download,
            self.assertRaisesRegex(ValueError, "pinned linux/amd64"),
        ):
            acquire_uv.acquire(self.directory, self.context)
        download.assert_not_called()

    def test_duplicate_expected_executable_is_refused_before_writing(self):
        with self.assertRaisesRegex(ValueError, "duplicated"):
            self.acquire_fixture(archive_bytes(duplicate=True))
        self.assertFalse(self.directory.exists())

    def test_oversized_executable_is_refused_before_writing(self):
        with self.assertRaisesRegex(ValueError, "executable exceeds"):
            self.acquire_fixture(archive_bytes(), MAX_EXECUTABLE_BYTES=2)
        self.assertFalse(self.directory.exists())

    def test_transport_read_is_bounded_and_oversize_is_refused(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"abc"
        with (
            mock.patch.object(acquire_uv, "MAX_ARCHIVE_BYTES", 2),
            mock.patch.object(
                acquire_uv.urllib.request, "urlopen", return_value=response
            ),
            self.assertRaisesRegex(ValueError, "archive exceeds"),
        ):
            acquire_uv.acquire(self.directory, self.context)
        response.__enter__.return_value.read.assert_called_once_with(3)
        self.assertFalse(self.directory.exists())


if __name__ == "__main__":
    unittest.main()
