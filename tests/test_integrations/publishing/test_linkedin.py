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
        ) == {"post_id": "urn:li:share:123", "stage": "created"}
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


@pytest.mark.parametrize(
    "status,code",
    [
        (400, "MISSING_FIELD"),
        (401, "EMPTY_ACCESS_TOKEN"),
        (403, "ACCESS_DENIED"),
        (422, "UNPROCESSABLE_ENTITY"),
        (429, "TOO_MANY_REQUESTS"),
    ],
)
@pytest.mark.parametrize("operation", ["publish", "initialize"])
def test_linkedin_structured_refusal_metadata_no_retry(status, code, operation):
    from zeo_integrations.publishing import PublishingResponseError

    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            status,
            headers={"Retry-After": "12"},
            json={
                "status": status,
                "code": code,
                "serviceErrorCode": 100,
                "message": "SYNTHETIC_PRIVATE_DETAIL",
            },
        )

    with wire(handler) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        with pytest.raises(PublishingResponseError) as caught:
            if operation == "publish":
                client.publish(TextPost(text="hello"), key="post", allow_effect=True)
            else:
                client.initialize_image_upload(key="init", allow_effect=True)
    error = caught.value
    assert error.definite_refusal and not error.outcome_unknown
    assert (
        error.http_status,
        error.provider_code,
        error.provider_subcode,
        error.retry_after,
    ) == (status, code, 100, "12")
    assert "SYNTHETIC_PRIVATE_DETAIL" not in str(error) + repr(error.__dict__)
    assert len(seen) == 1


@pytest.mark.parametrize(
    "status,body",
    [
        (429, b"not-json"),
        (401, b'{"status":403,"message":"mismatch"}'),
        (400, b'{"status":400,"code":"UNKNOWN_FUTURE_CODE"}'),
        (409, b'{"status":409,"message":"conflict"}'),
        (500, b'{"status":500,"message":"failed"}'),
        (503, b'{"status":503,"code":"SERVICE_UNAVAILABLE"}'),
        (400, b'{"status":400,"message":"temporary","isTransient":true}'),
    ],
)
def test_linkedin_uncertain_failures_remain_unknown(status, body):
    from zeo_integrations.publishing import PublishingResponseError

    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(status, content=body)

    with wire(handler) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        with pytest.raises(PublishingResponseError) as caught:
            client.publish(TextPost(text="hello"), key="post", allow_effect=True)
    assert caught.value.outcome_unknown and not caught.value.definite_refusal
    assert len(seen) == 1


@pytest.mark.parametrize(
    "author,member,allowed",
    [
        ("urn:li:person:abc", "abc", True),
        ("urn:li:person:abc", "other", False),
        ("urn:li:organization:123", "abc", True),
    ],
)
def test_linkedin_member_identity_is_not_an_organization_grant(author, member, allowed):
    def handler(request):
        assert request.method == "GET" and request.url.path == "/v2/me"
        return httpx.Response(200, json={"id": member, "localizedFirstName": "ignored"})

    with wire(handler) as transport:
        client = LinkedInPublisher(transport, author=author, api_version="202610")
        if allowed:
            assert client.member_identity(key="identity") == {
                "member_urn": "urn:li:person:" + member
            }
        else:
            with pytest.raises(IntegrationError, match="ACCOUNT_BINDING"):
                client.member_identity(key="identity")


@pytest.mark.parametrize(
    "status",
    [
        "WAITING_UPLOAD",
        "PROCESSING",
        "PROCESSING_FAILED",
        "AVAILABLE",
        "FUTURE_UNKNOWN",
    ],
)
def test_linkedin_image_status_vocabulary_is_closed(status):
    with wire(
        lambda request: httpx.Response(
            200,
            json={
                "id": "urn:li:image:asset",
                "owner": "urn:li:person:abc",
                "status": status,
            },
        )
    ) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        if status == "FUTURE_UNKNOWN":
            with pytest.raises(IntegrationError, match="INVALID_RECEIPT"):
                client.image_status("urn:li:image:asset", key="status")
        else:
            assert (
                client.image_status("urn:li:image:asset", key="status")[
                    "provider_status"
                ]
                == status
            )


@pytest.mark.parametrize("expires", [1793569999000, None, True, "1793569999000", -1])
def test_linkedin_upload_ticket_expiry_is_bounded(expires):
    with wire(
        lambda request: httpx.Response(
            200,
            json={
                "value": {
                    "image": "urn:li:image:asset",
                    "uploadUrl": "https://www.linkedin.com/dms-uploads/asset",
                    "uploadUrlExpiresAt": expires,
                }
            },
        )
    ) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        if expires is None or type(expires) is int and expires > 0:
            assert (
                client.initialize_image_upload(key="init", allow_effect=True)[
                    "upload_url_expires_at_ms"
                ]
                == expires
            )
        else:
            with pytest.raises(IntegrationError) as caught:
                client.initialize_image_upload(key="init", allow_effect=True)
            assert caught.value.outcome_unknown


@pytest.mark.parametrize("status", [401, 403])
def test_linkedin_legacy_error_shape_is_preserved(status):
    from zeo_integrations.publishing import PublishingResponseError

    with wire(
        lambda request: httpx.Response(
            status,
            json={
                "status": status,
                "message": "SYNTHETIC_REFUSAL",
                "serviceErrorCode": 100,
            },
        )
    ) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        with pytest.raises(PublishingResponseError) as caught:
            client.publish(TextPost(text="hello"), key="post", allow_effect=True)
    assert caught.value.definite_refusal and not caught.value.outcome_unknown
    assert caught.value.provider_code == 100 and caught.value.provider_subcode == 100


@pytest.mark.parametrize(
    "extra",
    [
        {"code": False},
        {"code": "bad-code"},
        {"serviceErrorCode": "100"},
        {"isTransient": 1},
    ],
)
def test_linkedin_malformed_error_markers_are_not_safe_refusals(extra):
    from zeo_integrations.publishing import PublishingResponseError

    with wire(
        lambda request: httpx.Response(
            403, json={"status": 403, "message": "SYNTHETIC_REFUSAL", **extra}
        )
    ) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        with pytest.raises(PublishingResponseError) as caught:
            client.publish(TextPost(text="hello"), key="post", allow_effect=True)
    assert caught.value.outcome_unknown and not caught.value.definite_refusal


@pytest.mark.parametrize("character", list("|{}@[]()<>#\\*_~"))
def test_linkedin_each_reserved_character_is_literal_on_wire(character):
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:123"})

    with wire(handler) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        client.publish(
            TextPost(text="before" + character + "after"), key="post", allow_effect=True
        )
    assert seen[0]["commentary"] == "before\\" + character + "after"
    assert (
        seen[0]["visibility"] == "PUBLIC"
        and seen[0]["distribution"]["feedDistribution"] == "MAIN_FEED"
    )
    assert (
        seen[0]["lifecycleState"] == "PUBLISHED"
        and seen[0]["isReshareDisabledByAuthor"] is False
    )


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Launch (beta) now", r"Launch \(beta\) now"),
        (
            "hi @[Acme](urn:li:organization:9)",
            r"hi \@\[Acme\]\(urn:li:organization:9\)",
        ),
        (r"back\slash #tag {hashtag|#|x}", r"back\\slash \#tag \{hashtag\|\#\|x\}"),
    ],
)
def test_linkedin_plain_text_never_requests_mentions_or_templates(text, expected):
    with wire(
        lambda request: (
            httpx.Response(201, headers={"x-restli-id": "urn:li:share:123"})
            if json.loads(request.content)["commentary"] == expected
            else pytest.fail("wrong literal wire text")
        )
    ) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        client.publish(TextPost(text=text), key="post", allow_effect=True)


@pytest.mark.parametrize(
    "text,allowed",
    [
        ("a" * 3000, True),
        ("(" * 1500, True),
        ("(" * 1501, False),
        ("😀" * 1500, True),
        ("😀" * 1501, False),
    ],
)
def test_linkedin_local_encoded_limit_never_truncates_or_dispatches_overflow(
    text, allowed
):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:123"})

    with wire(handler) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        if allowed:
            client.publish(TextPost(text=text), key="post", allow_effect=True)
            assert len(seen) == 1
        else:
            with pytest.raises(IntegrationError, match="ENCODED_TEXT_LIMIT"):
                client.publish(TextPost(text=text), key="post", allow_effect=True)
            assert not seen


@pytest.mark.parametrize(
    "media,title,error",
    [
        (["urn:li:document:a"], "", "DOCUMENT_TITLE_REQUIRED"),
        (["urn:li:document:a"], " ", "MEDIA_TITLE"),
        ([], "ignored", "MEDIA_TITLE"),
        (["urn:li:image:a", "urn:li:image:b"], "ignored", "MEDIA_TITLE"),
        (["urn:li:image:a", "urn:li:image:a"], "", "DUPLICATE_MEDIA"),
    ],
)
def test_linkedin_invalid_or_dropped_media_fields_refused_before_dispatch(
    media, title, error
):
    seen = []
    with wire(lambda request: seen.append(request)) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        with pytest.raises(IntegrationError, match=error):
            client.publish(
                LinkedInPost(text="hello", media_urns=media, media_title=title),
                key="post",
                allow_effect=True,
            )
    assert not seen


@pytest.mark.parametrize(
    "media,title",
    [
        ("urn:li:image:a", ""),
        ("urn:li:video:a", ""),
        ("urn:li:document:a", "Document.pdf"),
    ],
)
def test_linkedin_optional_title_omitted_and_document_title_retained(media, title):
    seen = []

    def handler(request):
        seen.append(json.loads(request.content)["content"]["media"])
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:123"})

    with wire(handler) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        client.publish(
            LinkedInPost(text="hello", media_urns=[media], media_title=title),
            key="post",
            allow_effect=True,
        )
    assert seen == [{"id": media, **({"title": title} if title else {})}]


@pytest.mark.parametrize(
    "url",
    [
        "http://www.linkedin.com/x",
        "https://www.linkedin.com:443/x",
        "https://www.linkedin.com:8443/x",
        "https://user@www.linkedin.com/x",
        "https://www.linkedin.com.attacker.invalid/x",
        "https://WWW.LINKEDIN.COM/x",
        "https://attacker.invalid/x",
        "https://www.linkedin.com\\x",
        "https://www.linkedin.com/x#fragment",
        "//www.linkedin.com/x",
        "https://api.linkedin.com/x",
    ],
)
def test_linkedin_upload_origin_guard_is_required(url):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            200, json={"value": {"image": "urn:li:image:a", "uploadUrl": url}}
        )

    with wire(handler) as transport:
        client = LinkedInPublisher(
            transport, author="urn:li:person:abc", api_version="202610"
        )
        with pytest.raises(IntegrationError, match="UPLOAD_ORIGIN") as caught:
            client.initialize_image_upload(key="init", allow_effect=True)
    assert caught.value.outcome_unknown and len(seen) == 1
