"""Synthetic media lifecycle tests; file bytes and credentials stay with the host."""

import json

import httpx
import pytest
from pydantic import ValidationError

from zeo_integrations._http import HttpxTransport, IntegrationError
from zeo_integrations.publishing.x_media import XMediaClient, XMediaUpload


def wire(handler):
    return HttpxTransport(
        transport=httpx.MockTransport(handler), origins=("https://api.x.com",)
    )


def receipt(**changes):
    return {"id": "123", "media_key": "13_123", "expires_after_secs": 86400, **changes}


def test_initialize_is_one_admitted_json_request_and_not_ready():
    seen = []

    def handler(request):
        seen.append(request)
        assert (
            request.url.path == "/2/media/upload/initialize"
            and request.method == "POST"
        )
        assert json.loads(request.content) == {
            "media_type": "video/mp4",
            "media_category": "tweet_video",
            "total_bytes": 16,
        }
        assert "authorization" not in request.headers
        return httpx.Response(200, json={"data": receipt()})

    with wire(handler) as transport:
        client = XMediaClient(transport, account_id="42")
        upload = XMediaUpload(
            media_type="video/mp4", media_category="tweet_video", total_bytes=16
        )
        with pytest.raises(IntegrationError, match="ADMISSION"):
            client.initialize_upload(upload, key="init")
        assert seen == []
        assert client.initialize_upload(upload, key="init", allow_effect=True) == {
            "media_id": "123",
            "media_key": "13_123",
            "expires_after_secs": 86400,
            "stage": "awaiting_upload",
        }
    assert len(seen) == 1


@pytest.mark.parametrize(
    "fields",
    [
        {"total_bytes": True},
        {"total_bytes": 0},
        {"total_bytes": 17179869185},
        {"shared": True},
        {"additional_owners": ["43"]},
        {"media_type": "bad/type"},
    ],
)
def test_initializer_refuses_invalid_size_or_unmodeled_access_sharing(fields):
    args = {
        "media_type": "image/png",
        "media_category": "tweet_image",
        "total_bytes": 1,
        **fields,
    }
    with pytest.raises(ValidationError):
        XMediaUpload(**args)


def test_mime_category_mismatch_does_not_dispatch():
    seen = []
    with wire(lambda request: seen.append(request)) as transport:
        upload = XMediaUpload(
            media_type="video/mp4", media_category="tweet_image", total_bytes=1
        )
        with pytest.raises(IntegrationError, match="CATEGORY"):
            XMediaClient(transport, account_id="42").initialize_upload(
                upload, key="init", allow_effect=True
            )
    assert not seen


@pytest.mark.parametrize(
    "state,stage",
    [
        ("pending", "processing"),
        ("in_progress", "processing"),
        ("succeeded", "ready"),
        ("failed", "failed"),
    ],
)
def test_status_is_one_bound_read_without_polling(state, stage):
    seen = []

    def handler(request):
        seen.append(request)
        assert request.method == "GET" and request.url.path == "/2/media/upload"
        assert dict(request.url.params) == {"command": "STATUS", "media_id": "123"}
        return httpx.Response(
            200,
            json={
                "data": receipt(
                    processing_info={
                        "state": state,
                        "check_after_secs": 1,
                        "progress_percent": 50,
                        "detail": "PRIVATE",
                    }
                )
            },
        )

    with wire(handler) as transport:
        result = XMediaClient(transport, account_id="42").upload_status(
            "123", key="status"
        )
    assert result["provider_state"] == state and result["stage"] == stage
    assert result["check_after_secs"] == 1 and "PRIVATE" not in repr(result)
    assert len(seen) == 1


def test_missing_state_is_only_ready_after_confirmed_finalize():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"data": receipt()})

    with wire(handler) as transport:
        client = XMediaClient(transport, account_id="42")
        with pytest.raises(IntegrationError, match="ADMISSION"):
            client.finalize_upload("123", key="finalize")
        assert (
            client.finalize_upload("123", key="finalize", allow_effect=True)["stage"]
            == "ready"
        )
        assert (
            client.upload_status("123", key="status")["stage"]
            == "processing_state_absent"
        )
    assert len(seen) == 2 and seen[0].url.path == "/2/media/upload/123/finalize"


@pytest.mark.parametrize(
    "change",
    [
        {"id": "124"},
        {"media_key": "13_124"},
        {"expires_after_secs": True},
        {"processing_info": None},
        {"processing_info": {"state": []}},
        {"processing_info": {"state": "mystery"}},
        {"processing_info": {"state": "succeeded", "progress_percent": 101}},
    ],
)
def test_bad_finalize_receipts_keep_write_unknown(change):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"data": receipt(**change)})

    with wire(handler) as transport:
        with pytest.raises(IntegrationError) as caught:
            XMediaClient(transport, account_id="42").finalize_upload(
                "123", key="f", allow_effect=True
            )
    assert caught.value.outcome_unknown and len(seen) == 1


def test_zero_ttl_never_becomes_ready():
    with wire(
        lambda req: httpx.Response(
            200,
            json={
                "data": receipt(
                    expires_after_secs=0, processing_info={"state": "succeeded"}
                )
            },
        )
    ) as transport:
        assert (
            XMediaClient(transport, account_id="42").upload_status("123", key="s")[
                "stage"
            ]
            == "expired"
        )


def test_known_no_post_problem_is_not_no_media_mutation_proof():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            400,
            json={
                "type": "https://api.x.com/2/problems/invalid-request",
                "status": 400,
                "detail": "PRIVATE",
            },
        )

    with wire(handler) as transport:
        with pytest.raises(IntegrationError) as caught:
            XMediaClient(transport, account_id="42").finalize_upload(
                "123", key="f", allow_effect=True
            )
    assert caught.value.outcome_unknown and "PRIVATE" not in str(caught.value)
    assert len(seen) == 1


def test_append_sends_exact_binary_multipart_once():
    import hashlib

    seen = []
    chunk = b"\x00\xff\r\nTEST"

    def handler(request):
        seen.append(request)
        assert request.url.path == "/2/media/upload/123/append"
        boundary = request.headers["content-type"].split("boundary=")[1]
        assert request.content.count(b'name="segment_index"') == 1
        assert b"\r\n\r\n7\r\n" in request.content
        assert b'name="media"; filename="chunk.bin"' in request.content
        assert chunk + ("\r\n--" + boundary + "--\r\n").encode() in request.content
        return httpx.Response(200, json={"data": {"expires_at": 12345}})

    with wire(handler) as transport:
        client = XMediaClient(transport, account_id="42")
        with pytest.raises(IntegrationError, match="ADMISSION"):
            client.append_chunk("123", 7, chunk, key="a")
        assert not seen
        result = client.append_chunk("123", 7, chunk, key="a", allow_effect=True)
    assert len(seen) == 1 and result == {
        "media_id": "123",
        "segment_index": 7,
        "chunk_sha256": hashlib.sha256(chunk).hexdigest(),
        "expires_at": 12345,
        "stage": "chunk_accepted",
    }


@pytest.mark.parametrize(
    "index,chunk",
    [
        (True, b"x"),
        (-1, b"x"),
        (10000, b"x"),
        (0, b""),
        (0, b"x" * 524289),
        (0, bytearray(b"x")),
        (0, "data"),
    ],
)
def test_invalid_append_never_dispatches(index, chunk):
    seen = []
    with wire(lambda request: seen.append(request)) as transport:
        with pytest.raises(IntegrationError):
            XMediaClient(transport, account_id="42").append_chunk(
                "123", index, chunk, key="a", allow_effect=True
            )
    assert not seen


def test_old_transport_cannot_silently_drop_binary():
    class Old:
        def request(self, request):
            pytest.fail("unsupported binary must refuse before dispatch")

    with pytest.raises(IntegrationError, match="RAW_BODY_UNSUPPORTED") as caught:
        XMediaClient(Old(), account_id="42").append_chunk(
            "123", 0, b"x", key="a", allow_effect=True
        )
    assert not caught.value.outcome_unknown


@pytest.mark.parametrize("mode", ["lost", "bad_receipt", "partial", "wrong_status"])
def test_append_uncertainty_is_never_retried(mode):
    seen = []

    def handler(request):
        seen.append(request)
        if mode == "lost":
            raise httpx.ReadTimeout("PRIVATE", request=request)
        doc = {"data": {"expires_at": True if mode == "bad_receipt" else 12345}}
        if mode == "partial":
            doc["errors"] = [{"detail": "PRIVATE"}]
        return httpx.Response(201 if mode == "wrong_status" else 200, json=doc)

    with wire(handler) as transport:
        with pytest.raises(IntegrationError) as caught:
            XMediaClient(transport, account_id="42").append_chunk(
                "123", 0, b"x", key="a", allow_effect=True
            )
    assert caught.value.outcome_unknown and len(seen) == 1
    assert "PRIVATE" not in str(caught.value)
