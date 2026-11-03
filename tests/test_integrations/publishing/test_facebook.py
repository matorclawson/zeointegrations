"""Facebook Page request/receipt boundaries with synthetic transport only."""

from urllib.parse import parse_qs

import httpx
import pytest
from pydantic import ValidationError

from zeo_integrations._http import HttpxTransport, IntegrationError
from zeo_integrations.publishing.facebook import (
    FacebookPagePhoto,
    FacebookPagePost,
    FacebookPagePublisher,
)


def wire(handler):
    return HttpxTransport(
        transport=httpx.MockTransport(handler), origins=(FacebookPagePublisher.origin,)
    )


def page(transport, **extra):
    return FacebookPagePublisher(transport, page_id="123", api_version="v25.0", **extra)


def test_feed_one_admitted_request_retains_unicode_and_all_content():
    seen = []

    def handler(request):
        seen.append(request)
        assert request.method == "POST" and request.url.path == "/v25.0/123/feed"
        assert parse_qs(request.content.decode(), keep_blank_values=True) == {
            "message": ["Hello 🌍"],
            "link": ["https://example.com/story"],
            "published": ["true"],
        }
        assert "authorization" not in request.headers
        return httpx.Response(200, json={"id": "123_456"})

    with wire(handler) as transport:
        client = page(transport, link_origins=("https://example.com",))
        post = FacebookPagePost(message="Hello 🌍", link="https://example.com/story")
        with pytest.raises(IntegrationError, match="ADMISSION"):
            client.publish(post, key="p")
        assert not seen
        assert client.publish(post, key="p", allow_effect=True) == {
            "post_id": "123_456",
            "stage": "created",
        }
    assert len(seen) == 1


def test_photo_keeps_caption_and_alt_text_but_does_not_invent_post_id():
    seen = []

    def handler(request):
        seen.append(request)
        assert request.url.path == "/v25.0/123/photos"
        assert parse_qs(request.content.decode(), keep_blank_values=True) == {
            "url": ["https://assets.example/image.png"],
            "caption": ["caption"],
            "alt_text_custom": ["Accessible 🌍"],
            "published": ["true"],
        }
        return httpx.Response(200, json={"id": "789"})

    with wire(handler) as transport:
        result = page(
            transport, media_origins=("https://assets.example",)
        ).publish_photo(
            FacebookPagePhoto(
                image_url="https://assets.example/image.png",
                caption="caption",
                alt_text="Accessible 🌍",
            ),
            key="p",
            allow_effect=True,
        )
    assert len(seen) == 1 and result == {"photo_id": "789", "stage": "photo_created"}


@pytest.mark.parametrize(
    "message,link",
    [
        ("", None),
        (" \n", None),
        ("x", "https://other.example/a"),
        ("x", "http://example.com/a"),
        ("x", "https://user:password@example.com/a"),
    ],
)
def test_invalid_content_or_link_never_dispatches(message, link):
    seen = []
    with wire(lambda req: seen.append(req)) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport, link_origins=("https://example.com",)).publish(
                FacebookPagePost(message=message, link=link), key="p", allow_effect=True
            )
    assert not seen and not caught.value.outcome_unknown


@pytest.mark.parametrize(
    "url",
    [
        "https://other.example/image",
        "file:///tmp/image",
        "https://assets.example/../private",
        "https://user:password@assets.example/a",
    ],
)
def test_photo_requires_host_allowed_asset_origin_and_safe_url(url):
    seen = []
    with wire(lambda req: seen.append(req)) as transport:
        with pytest.raises(IntegrationError):
            page(transport, media_origins=("https://assets.example",)).publish_photo(
                FacebookPagePhoto(image_url=url), key="p", allow_effect=True
            )
    assert not seen


@pytest.mark.parametrize(
    "changes",
    [
        {"scheduled_publish_time": 1},
        {"published": False},
        {"access_token": "PRIVATE"},
        {"tags": ["1"]},
        {"message": "x" * 10001},
    ],
)
def test_unmodeled_options_or_oversize_content_are_not_silently_dropped(changes):
    with pytest.raises(ValidationError):
        FacebookPagePost(**changes)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"id": 123},
        {"id": "124_456"},
        {"id": "123_456", "errors": [{"detail": "PRIVATE"}]},
        {"id": "123_456", "success": False},
    ],
)
def test_invalid_write_receipt_remains_unknown(body):
    seen = []
    with wire(
        lambda req: seen.append(req) or httpx.Response(200, json=body)
    ) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport).publish(
                FacebookPagePost(message="x"), key="p", allow_effect=True
            )
    assert caught.value.outcome_unknown and len(seen) == 1
    assert "PRIVATE" not in str(caught.value)


@pytest.mark.parametrize("status", [400, 401, 403, 409, 429, 500])
def test_graph_write_errors_do_not_imply_safe_resend(status):
    seen = []
    with wire(
        lambda req: (
            seen.append(req)
            or httpx.Response(
                status, json={"error": {"code": 190, "message": "PRIVATE"}}
            )
        )
    ) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport).publish(
                FacebookPagePost(message="x"), key="p", allow_effect=True
            )
    assert (
        caught.value.outcome_unknown
        and len(seen) == 1
        and "PRIVATE" not in str(caught.value)
    )


def test_lost_response_is_not_retried():
    seen = []

    def handler(request):
        seen.append(request)
        raise httpx.ReadTimeout("PRIVATE", request=request)

    with wire(handler) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport).publish(
                FacebookPagePost(message="x"), key="p", allow_effect=True
            )
    assert (
        caught.value.outcome_unknown
        and len(seen) == 1
        and "PRIVATE" not in str(caught.value)
    )


def test_identity_checks_token_subject_not_page_resource():
    seen = []

    def handler(request):
        seen.append(request)
        assert (
            request.url.path == "/v25.0/me"
            and request.url.params["fields"] == "id,name"
        )
        return httpx.Response(200, json={"id": "123", "name": "Selected Page"})

    with wire(handler) as transport:
        assert page(transport).identity(key="i") == {
            "page_id": "123",
            "name": "Selected Page",
        }
    assert len(seen) == 1


def test_wrong_token_subject_refused():
    with wire(
        lambda req: httpx.Response(200, json={"id": "999", "name": "A user"})
    ) as transport:
        with pytest.raises(IntegrationError, match="PAGE_BINDING"):
            page(transport).identity(key="i")


@pytest.mark.parametrize("story", [None, "123_456", "456"])
def test_photo_read_binds_photo_and_page_and_resolves_optional_story(story):
    def handler(request):
        assert (
            request.url.path == "/v25.0/789"
            and request.url.params["fields"] == "id,from,page_story_id"
        )
        doc = {"id": "789", "from": {"id": "123"}}
        if story is not None:
            doc["page_story_id"] = story
        return httpx.Response(200, json=doc)

    with wire(handler) as transport:
        assert page(transport).read_photo("789", key="r") == {
            "photo_id": "789",
            "post_id": story,
        }


@pytest.mark.parametrize(
    "change",
    [
        {"id": "123_999"},
        {"from": {"id": "999"}},
        {"from": None},
        {"is_published": 1},
        {"permalink_url": "https://facebook.com.evil.example/post"},
        {"permalink_url": "https://user:password@www.facebook.com/post"},
    ],
)
def test_post_read_requires_stored_id_selected_author_and_bounded_safe_metadata(change):
    body = {
        "id": "123_456",
        "from": {"id": "123"},
        "is_published": True,
        "permalink_url": "https://www.facebook.com/posts/456",
        **change,
    }
    with wire(lambda req: httpx.Response(200, json=body)) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport).read_post("123_456", key="r")
    assert not caught.value.outcome_unknown


def test_post_read_reports_provider_fact_without_claiming_external_visibility():
    seen = []

    def handler(request):
        seen.append(request)
        assert request.url.params["fields"] == "id,from,is_published,permalink_url"
        return httpx.Response(
            200, json={"id": "123_456", "from": {"id": "123"}, "is_published": False}
        )

    with wire(handler) as transport:
        assert page(transport).read_post("123_456", key="r") == {
            "post_id": "123_456",
            "page_id": "123",
            "provider_is_published": False,
            "permalink": None,
        }
    assert len(seen) == 1


@pytest.mark.parametrize(
    "name", ["access_token", "client_secret", "password", "authorization"]
)
def test_permalink_does_not_return_provider_echoed_credentials(name):
    body = {
        "id": "123_456",
        "from": {"id": "123"},
        "is_published": True,
        "permalink_url": "https://www.facebook.com/posts/456?" + name + "=PRIVATE",
    }
    with wire(lambda req: httpx.Response(200, json=body)) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport).read_post("123_456", key="r")
    assert "PRIVATE" not in str(caught.value) and not caught.value.outcome_unknown


@pytest.mark.parametrize(
    "version", [None, True, "v00.0", "v0.0", "v25.0/evil", "v25.0?x=1"]
)
def test_host_version_is_closed_before_dispatch(version):
    seen = []
    with wire(lambda req: seen.append(req)) as transport:
        with pytest.raises(IntegrationError, match="API_VERSION"):
            FacebookPagePublisher(transport, page_id="123", api_version=version)
    assert not seen


@pytest.mark.parametrize(
    "body", [{"id": 789}, {"id": "0"}, {"id": "789", "errors": {"detail": "PRIVATE"}}]
)
def test_photo_write_needs_exact_receipt_and_retains_unknown(body):
    seen = []
    with wire(
        lambda req: seen.append(req) or httpx.Response(200, json=body)
    ) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport, media_origins=("https://assets.example",)).publish_photo(
                FacebookPagePhoto(image_url="https://assets.example/a.png"),
                key="p",
                allow_effect=True,
            )
    assert caught.value.outcome_unknown and len(seen) == 1


@pytest.mark.parametrize(
    "change", [{"id": "999"}, {"from": {"id": "999"}}, {"page_story_id": "999_456"}]
)
def test_photo_read_does_not_bind_a_different_photo_page_or_story(change):
    body = {"id": "789", "from": {"id": "123"}, "page_story_id": "123_456", **change}
    with wire(lambda req: httpx.Response(200, json=body)) as transport:
        with pytest.raises(IntegrationError) as caught:
            page(transport).read_photo("789", key="r")
    assert not caught.value.outcome_unknown
