"""Original synthetic wire tests. No account credentials or live publication."""

import json

import httpx
import pytest

from zeo_integrations._http import HttpxTransport, IntegrationError
from zeo_integrations.publishing import (
    InstagramMedia,
    InstagramPublisher,
    LinkedInPublisher,
    TextPost,
    ThreadsMedia,
    ThreadsPublisher,
    TikTokPublisher,
    Video,
    XPost,
    XPublisher,
)


def wire(origin, handler):
    return HttpxTransport(transport=httpx.MockTransport(handler), origins=(origin,))


def test_linkedin_actual_http_header_receipt():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:123"})

    with wire(LinkedInPublisher.origin, handler) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202601"
        )
        assert client.publish(
            TextPost(text="hello"), key="post1", allow_effect=True
        ) == {"post_id": "urn:li:share:123", "stage": "published"}
    assert len(seen) == 1
    assert seen[0].headers["Linkedin-Version"] == "202601"
    assert json.loads(seen[0].content)["author"] == "urn:li:person:abc"


def test_x_no_implicit_write_or_retry():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"data": {"id": "123"}})

    with wire(XPublisher.origin, handler) as transport:
        client = XPublisher(transport)
        with pytest.raises(IntegrationError, match="ADMISSION"):
            client.publish(XPost(text="hello"), key="post1")
        assert not seen
        assert (
            client.publish(XPost(text="hello"), key="post1", allow_effect=True)[
                "post_id"
            ]
            == "123"
        )
    assert len(seen) == 1
    assert seen[0].url.path == "/2/tweets"


@pytest.mark.parametrize("kind", ["instagram", "threads"])
def test_container_is_not_publication(kind):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"id": "123"})

    cls = InstagramPublisher if kind == "instagram" else ThreadsPublisher
    with wire(cls.origin, handler) as transport:
        extra = {"api_version": "v23.0"} if kind == "instagram" else {}
        client = cls(
            transport,
            account_id="account",
            media_origins=("https://media.example",),
            **extra,
        )
        post = (
            InstagramMedia(media_type="IMAGE", media_url="https://media.example/a.jpg")
            if kind == "instagram"
            else ThreadsMedia(media_type="TEXT", text="hello")
        )
        assert (
            client.create_container(post, key="prepare", allow_effect=True)["stage"]
            == "processing"
        )
        assert len(seen) == 1
        assert (
            client.publish_container("123", key="publish", allow_effect=True)["stage"]
            == "published"
        )
    assert len(seen) == 2
    assert seen[1].content == b"creation_id=123"


@pytest.mark.parametrize(
    "status,stage",
    [
        ("PROCESSING_DOWNLOAD", "processing"),
        ("SEND_TO_USER_INBOX", "inbox_delivered"),
        ("PUBLISH_COMPLETE", "published"),
        ("FAILED", "failed"),
    ],
)
def test_tiktok_separates_inbox_from_publication(status, stage):
    def handler(_):
        return httpx.Response(
            200, json={"error": {"code": "ok"}, "data": {"status": status}}
        )

    with wire(TikTokPublisher.origin, handler) as transport:
        assert (
            TikTokPublisher(transport).status("v_pub~123.456", key="inspect")["stage"]
            == stage
        )


def test_tiktok_upload_only_initializes():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            200, json={"error": {"code": "ok"}, "data": {"publish_id": "abc"}}
        )

    with wire(TikTokPublisher.origin, handler) as transport:
        client = TikTokPublisher(transport, media_origins=("https://media.example",))
        result = client.upload_to_inbox(
            Video(video_url="https://media.example/a.mp4"),
            key="upload",
            allow_effect=True,
        )
        assert result == {"publish_id": "abc", "stage": "processing"}
    assert seen[0].url.path == "/v2/post/publish/inbox/video/init/"
    assert len(seen) == 1


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500),
        httpx.Response(200, json={}),
        httpx.Response(200, json={"error": {"code": "no"}}),
    ],
)
def test_invalid_receipt_preserves_unknown_effect(response):
    seen = []

    def handler(request):
        seen.append(request)
        return response

    with wire(XPublisher.origin, handler) as transport:
        with pytest.raises(IntegrationError) as caught:
            XPublisher(transport).publish(
                XPost(text="hello"), key="publish", allow_effect=True
            )
    assert caught.value.outcome_unknown
    assert len(seen) == 1


def test_untrusted_media_refused_before_call():
    with wire(
        TikTokPublisher.origin, lambda _: pytest.fail("network called")
    ) as transport:
        client = TikTokPublisher(transport, media_origins=("https://media.example",))
        with pytest.raises(IntegrationError, match="MEDIA_ORIGIN"):
            client.upload_to_inbox(
                Video(video_url="https://untrusted.example/a.mp4"),
                key="upload",
                allow_effect=True,
            )
