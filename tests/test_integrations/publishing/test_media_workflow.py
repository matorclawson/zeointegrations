"""Offline media and complete editorial-to-provider boundary checks."""

import hashlib
import shutil
import subprocess

import httpx
import pytest

from zeo_integrations._http import IntegrationError
from zeo_integrations.publishing.media import MediaLibrary, MediaUploader, sniff
from zeo_integrations.publishing.workflow import WorkflowError


def staged(tmp_path):
    source = tmp_path / "source.jpg"
    source.write_bytes(b"\xff\xd8\xff" + b"fixture" * 10)
    library = MediaLibrary(tmp_path / "media")
    return library, library.stage(source, asset_id="image", alt_text="An image")


def test_stage_digest_tampering_and_bounds(tmp_path):
    library, asset = staged(tmp_path)
    path = library.verify(asset)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == asset.sha256
    assert library.stage(path, asset_id="other").sha256 == asset.sha256
    with pytest.raises(WorkflowError, match="size bound"):
        library.stage(path, asset_id="large", max_bytes=3)
    path.chmod(0o600)
    path.write_bytes(b"\xff\xd8\xfftampered")
    with pytest.raises(WorkflowError, match="changed"):
        library.verify(asset)
    assert (tmp_path / "source.jpg").exists()
    assert not list(library.root.glob(".stage-*"))


@pytest.mark.parametrize("data", [b"<svg/>", b"<html/>", b"", b"GIFinvalid"])
def test_reject_non_media(data):
    with pytest.raises(WorkflowError):
        sniff(data)


def test_upload_exact_bytes_admission_origin_and_no_retry(tmp_path):
    library, asset = staged(tmp_path)
    seen = []

    def handler(request):
        seen.append(request)
        assert request.read() == library.verify(asset).read_bytes()
        assert request.headers["Content-Type"] == "image/jpeg"
        return httpx.Response(201)

    uploader = MediaUploader(
        httpx.MockTransport(handler), allowed_origins=["https://www.linkedin.com"]
    )
    url = "https://www.linkedin.com/dms-uploads/test"
    with pytest.raises(IntegrationError, match="ADMISSION"):
        uploader.upload(library, asset, url=url)
    with pytest.raises(IntegrationError, match="ORIGIN"):
        uploader.upload(
            library, asset, url="https://other.example/x", allow_effect=True
        )
    assert not seen
    receipt = uploader.upload(library, asset, url=url, allow_effect=True)
    assert receipt["uploaded"] is True and "stage" not in receipt
    assert len(seen) == 1
    uploader.close()


def test_upload_redirect_is_unknown_never_followed(tmp_path):
    library, asset = staged(tmp_path)
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(302, headers={"Location": "https://evil.example"})

    uploader = MediaUploader(
        httpx.MockTransport(handler), allowed_origins=["https://up.example"]
    )
    with pytest.raises(IntegrationError) as exc:
        uploader.upload(
            library, asset, url="https://up.example/file", allow_effect=True
        )
    assert exc.value.outcome_unknown
    assert len(seen) == 1
    uploader.close()


def test_explicit_image_conversion_preserves_original(tmp_path):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("optional ffmpeg/ffprobe")
    source = tmp_path / "image.png"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=64x32",
            "-frames:v",
            "1",
            "-threads",
            "1",
            str(source),
        ],
        check=True,
        timeout=30,
    )
    library = MediaLibrary(tmp_path / "media")
    original = library.stage(source, asset_id="original")
    converted = library.convert(original, asset_id="instagram", profile="square_jpeg")
    assert original.sha256 != converted.sha256
    assert converted.media_type == "image/jpeg"
    assert library.inspect(converted)["width"] == 1080
    assert library.inspect(converted)["height"] == 1080
    assert library.verify(original).read_bytes() == source.read_bytes()
    assert not list(library.root.glob(".convert-*"))
