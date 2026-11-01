"""Offline media and complete editorial-to-provider boundary checks."""

import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from urllib.parse import parse_qs

import httpx
import pytest
from zeo_core.integrations.hosted.client import (
    HostedConnectionClient,
    HostedExpectedBinding,
    HostedOperationResponse,
)

from zeo_integrations._http import HttpxTransport, IntegrationError
from zeo_integrations.publishing import (
    Carousel,
    CarouselItem,
    InstagramPublisher,
)
from zeo_integrations.publishing.compose import compose_target
from zeo_integrations.publishing.media import MediaLibrary, MediaUploader, sniff
from zeo_integrations.publishing.workflow import (
    Draft,
    WorkflowError,
    WorkflowRunner,
    WorkflowStore,
)

NOW = datetime(2026, 10, 31, tzinfo=UTC)
BINDING = HostedExpectedBinding(external_identity="account", connection_revision="1")


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


def test_carousel_draft_to_provider_with_checkpoints(tmp_path):
    library, asset = staged(tmp_path)
    second = asset.model_copy(update={"asset_id": "second"})
    actions = [
        "create_carousel_item",
        "container_status",
        "create_carousel",
        "publish_container",
    ]
    target = compose_target(
        target_id="instagram",
        platform="instagram",
        connection_id="connection",
        expect=BINDING,
        caption="Our launch",
        assets=[asset, second],
        operations={name: "instagram." + name for name in actions},
    )
    seen = []

    def handler(request):
        seen.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"status_code": "FINISHED"})
        return httpx.Response(200, json={"id": str(len(seen))})

    transport = HttpxTransport(
        transport=httpx.MockTransport(handler), origins=(InstagramPublisher.origin,)
    )
    publisher = InstagramPublisher(
        transport,
        account_id="123",
        api_version="v24.0",
        media_origins=("https://media.example",),
    )

    class Broker:
        def invoke(self, request):
            name = request.operation_id.split(".")[-1]
            arguments = dict(request.arguments)
            if "item" in arguments:
                arguments["item"] = CarouselItem.model_validate(arguments["item"])
            if "carousel" in arguments:
                arguments["carousel"] = Carousel.model_validate(arguments["carousel"])
            arguments["key"] = request.idempotency_key
            if name != "container_status":
                arguments["allow_effect"] = True
            result = getattr(publisher, name)(**arguments)
            return HostedOperationResponse(
                status="confirmed", execution_id="test", result=result
            )

    store = WorkflowStore(tmp_path / "workflow.db")
    draft = Draft(
        title="Launch", scheduled_at=NOW, assets=[asset, second], targets=[target]
    )
    preview = store.save("org", "post", draft, actor="editor")
    runner = WorkflowRunner(
        store,
        HostedConnectionClient(transport=Broker()),
        media_url=library.resolver(lambda a, p: "https://media.example/" + a.sha256),
    )
    assert runner.tick("org", now=NOW) is None
    assert not seen
    store.approve("org", "post", actor="editor", digest=preview["digest"])
    for _ in range(7):
        result = runner.tick("org", now=NOW)
        # Reopen durable store between every operation.
        runner.store = WorkflowStore(tmp_path / "workflow.db")
    assert result["state"] == "published"
    assert runner.tick("org", now=NOW) is None
    assert len(seen) == 7
    parent = parse_qs(seen[4].content.decode())
    assert parent["children"] == ["1,3"]
    assert parse_qs(seen[6].content.decode())["creation_id"] == ["5"]
    transport.close()


def test_compiler_requires_real_operations_and_supported_formats(tmp_path):
    _, asset = staged(tmp_path)
    args = dict(
        target_id="ig",
        platform="instagram",
        connection_id="c",
        expect=BINDING,
        caption="caption",
        assets=[asset],
        operations={},
    )
    with pytest.raises(WorkflowError, match="unavailable"):
        compose_target(**args)
    args["assets"] = [asset.model_copy(update={"media_type": "image/png"})]
    with pytest.raises(WorkflowError, match="convert"):
        compose_target(**args)
