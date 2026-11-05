"""Synthetic Page video protocol and claim boundaries; no provider traffic."""

from urllib.parse import parse_qs

import httpx
import pytest
from pydantic import ValidationError

from zeo_integrations._http import HttpxTransport, IntegrationError
from zeo_integrations.publishing import PublishingResponseError
from zeo_integrations.publishing.facebook import (
    FacebookPagePublisher,
    FacebookPageVideo,
)

GRAPH = "https://graph.facebook.com"
VIDEO = "https://graph-video.facebook.com"
ASSET = "https://assets.example"


def wire(handler, *, origins=(GRAPH, VIDEO)):
    return HttpxTransport(transport=httpx.MockTransport(handler), origins=origins)


def page(transport):
    return FacebookPagePublisher(
        transport, page_id="123", api_version="v25.0", media_origins=(ASSET,)
    )


def video():
    return FacebookPageVideo(
        video_url=ASSET + "/immutable.mp4",
        title="Title 🌍",
        description="Full description",
    )


def test_one_video_form_at_fixed_video_origin_without_ambient_auth():
    seen = []

    def handler(request):
        seen.append(request)
        assert request.method == "POST"
        assert str(request.url) == VIDEO + "/v25.0/123/videos"
        assert "authorization" not in request.headers
        assert parse_qs(request.content.decode()) == {
            "file_url": [ASSET + "/immutable.mp4"],
            "title": ["Title 🌍"],
            "description": ["Full description"],
            "published": ["true"],
        }
        return httpx.Response(200, json={"id": "789"})

    with wire(handler) as transport:
        assert page(transport).publish_video(
            video(), key="video1", allow_effect=True
        ) == {"video_id": "789", "stage": "submitted"}
    assert len(seen) == 1


@pytest.mark.parametrize("admitted", [False, None, "true", 1])
def test_submission_requires_explicit_effect_admission(admitted):
    seen = []
    with wire(lambda r: seen.append(r)) as transport:
        with pytest.raises(IntegrationError, match="ADMISSION") as caught:
            page(transport).publish_video(video(), key="v", allow_effect=admitted)
    assert not seen and not caught.value.outcome_unknown


@pytest.mark.parametrize(
    "url",
    [
        "https://other.example/a",
        "file:///private",
        "https://assets.example/../a",
        "https://user:pass@assets.example/a",
    ],
)
def test_video_asset_refusal_happens_before_dispatch(url):
    seen = []
    with wire(lambda r: seen.append(r)) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport).publish_video(
                FacebookPageVideo(video_url=url), key="v", allow_effect=True
            )
    assert not seen and not caught.value.outcome_unknown


@pytest.mark.parametrize(
    "extra",
    [
        {"source": "local.mp4"},
        {"scheduled_publish_time": 1},
        {"access_token": "PRIVATE"},
        {"published": False},
        {"title": "x" * 256},
        {"description": "x" * 10001},
        {"title": 12},
    ],
)
def test_closed_local_video_schema_never_drops_options(extra):
    with pytest.raises(ValidationError):
        FacebookPageVideo(video_url=ASSET + "/v", **extra)


def test_origin_not_admitted_does_not_fallback_to_graph():
    seen = []
    with wire(lambda r: seen.append(r), origins=(GRAPH,)) as transport:
        with pytest.raises(IntegrationError):
            page(transport).publish_video(video(), key="v", allow_effect=True)
    assert not seen


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"id": 789},
        {"id": "0"},
        {"id": "123_789"},
        {"id": "789", "error": None},
        {"id": "789", "errors": ["PRIVATE"]},
        {"id": "789", "success": False},
    ],
)
def test_invalid_video_receipt_remains_unknown_without_resend(body):
    seen = []
    with wire(lambda r: seen.append(r) or httpx.Response(200, json=body)) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport).publish_video(video(), key="v", allow_effect=True)
    assert len(seen) == 1 and caught.value.outcome_unknown
    assert "PRIVATE" not in str(caught.value)


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500])
def test_graph_video_failure_metadata_does_not_authorize_resend(status):
    seen = []
    with wire(
        lambda r: (
            seen.append(r)
            or httpx.Response(
                status,
                json={
                    "error": {"code": 190, "error_subcode": 463, "message": "PRIVATE"}
                },
                headers={"Retry-After": "10"},
            )
        )
    ) as transport:
        with pytest.raises(PublishingResponseError) as caught:
            page(transport).publish_video(video(), key="v", allow_effect=True)
    err = caught.value
    assert len(seen) == 1 and err.outcome_unknown and not err.definite_refusal
    assert (
        err.http_status,
        err.provider_code,
        err.provider_subcode,
        err.retry_after,
    ) == (status, 190, 463, "10")
    assert "PRIVATE" not in str(err)


def test_lost_video_answer_is_one_unknown_write():
    seen = []

    def handler(request):
        seen.append(request)
        raise httpx.ReadTimeout("PRIVATE")

    with wire(handler) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport).publish_video(video(), key="v", allow_effect=True)
    assert len(seen) == 1 and caught.value.outcome_unknown
    assert "PRIVATE" not in str(caught.value)


@pytest.mark.parametrize(
    "state,published",
    [("processing", None), ("ready", False), ("ready", True), ("error", False)],
)
def test_read_video_checks_object_author_and_only_projects_closed_facts(
    state, published
):
    seen = []

    def handler(request):
        seen.append(request)
        assert request.method == "GET" and request.url.host == "graph.facebook.com"
        assert request.url.path == "/v25.0/789"
        assert dict(request.url.params) == {"fields": "id,from,status,published"}
        doc = {
            "id": "789",
            "from": {"id": "123"},
            "status": {"video_status": state, "detail": "PRIVATE"},
            "source": "PRIVATE",
        }
        if published is not None:
            doc["published"] = published
        return httpx.Response(200, json=doc)

    with wire(handler) as transport:
        result = page(transport).read_video("789", key="read1")
    assert result == {
        "video_id": "789",
        "page_id": "123",
        "video_status": state,
        "provider_published": published,
    }
    assert len(seen) == 1 and "PRIVATE" not in str(result)


@pytest.mark.parametrize(
    "change",
    [
        {"id": "790"},
        {"id": 789},
        {"from": {"id": "124"}},
        {"from": None},
        {"status": None},
        {"status": {}},
        {"status": {"video_status": []}},
        {"status": {"video_status": "UNKNOWN_PRIVATE"}},
        {"published": "true"},
        {"published": 1},
        {"error": {"message": "PRIVATE"}},
        {"success": False},
    ],
)
def test_invalid_video_status_fails_without_polling_or_mutation(change):
    seen = []
    doc = {
        "id": "789",
        "from": {"id": "123"},
        "status": {"video_status": "ready"},
        "published": True,
    }
    doc.update(change)
    with wire(lambda r: seen.append(r) or httpx.Response(200, json=doc)) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport).read_video("789", key="read1")
    assert len(seen) == 1 and not caught.value.outcome_unknown
    assert "PRIVATE" not in str(caught.value)


@pytest.mark.parametrize("video_id", [789, "", "0", "123_789", "../789", "1" * 41])
def test_video_read_requires_exact_host_bound_numeric_id_before_dispatch(video_id):
    seen = []
    with wire(lambda r: seen.append(r)) as transport:
        with pytest.raises(IntegrationError):
            page(transport).read_video(video_id, key="read1")
    assert not seen
