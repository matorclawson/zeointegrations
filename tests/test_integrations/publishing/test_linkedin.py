"""Synthetic LinkedIn wire and account-bound receipt tests; no live provider."""

import json

import httpx
import pytest

from zeo_integrations._http import HttpxTransport, IntegrationError
from zeo_integrations.publishing import LinkedInPost, LinkedInPublisher, TextPost


def wire(handler):
    return HttpxTransport(
        transport=httpx.MockTransport(handler), origins=(LinkedInPublisher.origin,)
    )


def test_linkedin_actual_http_header_receipt():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:123"})

    with wire(handler) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        with pytest.raises(IntegrationError, match="ADMISSION"):
            client.publish(TextPost(text="hello"), key="post1")
        assert not seen
        assert client.publish(
            TextPost(text="hello"), key="post1", allow_effect=True
        ) == {"post_id": "urn:li:share:123", "stage": "published"}
    assert len(seen) == 1
    assert seen[0].headers["Linkedin-Version"] == "202610"
    assert seen[0].headers["X-Restli-Protocol-Version"] == "2.0.0"
    assert "authorization" not in seen[0].headers
    assert json.loads(seen[0].content)["author"] == "urn:li:person:abc"


@pytest.mark.parametrize("receipt", [None, "wrong", "urn:li:share:"])
def test_linkedin_invalid_write_receipt_stays_unknown_without_retry(receipt):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(201, headers={"x-restli-id": receipt} if receipt else {})

    with wire(handler) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        with pytest.raises(IntegrationError) as caught:
            client.publish(TextPost(text="hello"), key="post", allow_effect=True)
    assert caught.value.outcome_unknown and len(seen) == 1


@pytest.mark.parametrize("matches", [True, False])
def test_linkedin_image_processing_is_bound_to_selected_owner(matches):
    seen = []

    def handler(request):
        seen.append(request)
        if request.method == "POST":
            assert request.url.params["action"] == "initializeUpload"
            assert (
                json.loads(request.content)["initializeUploadRequest"]["owner"]
                == "urn:li:person:abc"
            )
            return httpx.Response(
                200,
                json={
                    "value": {
                        "image": "urn:li:image:asset",
                        "uploadUrl": "https://www.linkedin.com/dms-uploads/asset",
                    }
                },
            )
        return httpx.Response(
            200,
            json={
                "id": "urn:li:image:asset",
                "owner": "urn:li:person:abc" if matches else "urn:li:person:other",
                "status": "AVAILABLE",
            },
        )

    with wire(handler) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        result = client.initialize_image_upload(key="initialize", allow_effect=True)
        assert result["stage"] == "awaiting_upload"
        if matches:
            assert (
                client.image_status(result["image_urn"], key="status")[
                    "provider_status"
                ]
                == "AVAILABLE"
            )
        else:
            with pytest.raises(IntegrationError, match="MEDIA_IDENTITY"):
                client.image_status(result["image_urn"], key="status")
    assert len(seen) == 2


def test_linkedin_mixed_multi_media_is_refused_without_dispatch():
    seen = []
    with wire(lambda request: seen.append(request)) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        with pytest.raises(IntegrationError, match="MULTI_IMAGE_REQUIRED"):
            client.publish(
                LinkedInPost(
                    text="hello", media_urns=["urn:li:image:a", "urn:li:video:b"]
                ),
                key="post",
                allow_effect=True,
            )
    assert not seen


@pytest.mark.parametrize("matches", [True, False])
def test_linkedin_known_post_read_uses_rest_and_bound_author(matches):
    seen = []

    def handler(request):
        seen.append(request)
        assert request.method == "GET" and request.url.path.startswith("/rest/posts/")
        return httpx.Response(
            200,
            json={
                "id": "urn:li:share:123",
                "author": "urn:li:person:abc" if matches else "urn:li:person:other",
                "lifecycleState": "PUBLISHED",
            },
        )

    with wire(handler) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        if matches:
            assert (
                client.read_post("urn:li:share:123", key="read")["provider_status"]
                == "PUBLISHED"
            )
        else:
            with pytest.raises(IntegrationError, match="POST_BINDING"):
                client.read_post("urn:li:share:123", key="read")
    assert len(seen) == 1
