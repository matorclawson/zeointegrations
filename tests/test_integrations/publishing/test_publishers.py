"""Original synthetic wire tests. No account credentials or live publication."""

import httpx
import pytest

from zeo_integrations._http import HttpxTransport, IntegrationError
from zeo_integrations.publishing import (
    InstagramMedia,
    InstagramPublisher,
    PublishingResponseError,
    ThreadsMedia,
    ThreadsPublisher,
)


def wire(origin, handler):
    return HttpxTransport(transport=httpx.MockTransport(handler), origins=(origin,))


@pytest.mark.parametrize("kind", ["instagram", "threads"])
def test_container_is_not_publication(kind):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"id": "123"})

    cls = InstagramPublisher if kind == "instagram" else ThreadsPublisher
    with wire(cls.origin, handler) as transport:
        extra = {"api_version": "v23.0" if kind == "instagram" else "v1.0"}
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


@pytest.mark.parametrize("status", [400, 401, 403, 429])
def test_definite_graph_rejection_retains_only_bounded_facts(status):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            status,
            headers={"Retry-After": "12"},
            json={
                "error": {
                    "code": 190,
                    "error_subcode": 463,
                    "message": "SYNTHETIC_PRIVATE_MESSAGE",
                }
            },
        )

    with wire(InstagramPublisher.origin, handler) as transport:
        client = InstagramPublisher(
            transport, account_id="account", api_version="v23.0"
        )
        with pytest.raises(PublishingResponseError) as caught:
            client.publish_container("container", key="publish", allow_effect=True)
    error = caught.value
    assert error.definite_refusal and not error.outcome_unknown
    assert (error.http_status, error.provider_code, error.provider_subcode) == (
        status,
        190,
        463,
    )
    assert error.retry_after == "12"
    assert "SYNTHETIC_PRIVATE_MESSAGE" not in str(error) + repr(error.__dict__)
    assert len(seen) == 1


@pytest.mark.parametrize(
    "status,body",
    [
        (503, b'{"error":{"code":2}}'),
        (409, b'{"error":{"code":100}}'),
        (429, b"not-json"),
        (200, b'{"error":{"code":190}}'),
    ],
)
def test_ambiguous_answers_stay_unknown_without_retry(status, body):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            status, content=body, headers={"Retry-After": "not-a-date"}
        )

    with wire(ThreadsPublisher.origin, handler) as transport:
        client = ThreadsPublisher(transport, account_id="account", api_version="v1.0")
        with pytest.raises(PublishingResponseError) as caught:
            client.publish_container("container", key="publish", allow_effect=True)
    assert caught.value.outcome_unknown and not caught.value.definite_refusal
    assert caught.value.http_status == status and caught.value.retry_after is None
    assert len(seen) == 1


@pytest.mark.parametrize("kind", ["instagram", "threads"])
@pytest.mark.parametrize("matches", [True, False])
def test_identity_binds_credential_read_to_selected_subject(kind, matches):
    cls = InstagramPublisher if kind == "instagram" else ThreadsPublisher
    seen = []

    def handler(request):
        seen.append(request)
        assert request.method == "GET"
        assert request.url.params["fields"] == "id,username"
        assert "authorization" not in request.headers
        return httpx.Response(
            200, json={"id": "account" if matches else "other", "username": "demo"}
        )

    with wire(cls.origin, handler) as transport:
        client = cls(
            transport,
            account_id="account",
            api_version="v23.0" if kind == "instagram" else "v1.0",
        )
        if matches:
            assert client.identity(key="identity") == {
                "account_id": "account",
                "username": "demo",
            }
        else:
            with pytest.raises(IntegrationError, match="ACCOUNT_BINDING"):
                client.identity(key="identity")
    assert seen[0].url.path.endswith("/account" if kind == "instagram" else "/me")
    assert len(seen) == 1


def test_threads_version_is_explicit_and_rejects_path_injection():
    with wire(
        ThreadsPublisher.origin, lambda request: httpx.Response(200)
    ) as transport:
        with pytest.raises(IntegrationError, match="API_VERSION"):
            ThreadsPublisher(transport, account_id="account", api_version="v1.0/other")


@pytest.mark.parametrize("kind", ["instagram", "threads"])
def test_known_post_read_is_not_an_automatic_publish_confirmation(kind):
    cls = InstagramPublisher if kind == "instagram" else ThreadsPublisher
    seen = []

    def handler(request):
        seen.append(request)
        assert request.method == "GET"
        return httpx.Response(
            200,
            json={
                "id": "post",
                "username": "demo",
                "permalink": "https://social.example/post",
                "timestamp": "2026-11-01T18:00:00Z",
            },
        )

    with wire(cls.origin, handler) as transport:
        client = cls(
            transport,
            account_id="account",
            api_version="v23.0" if kind == "instagram" else "v1.0",
        )
        result = client.read_post("post", key="read")
    assert result["post_id"] == "post" and "stage" not in result
    assert len(seen) == 1
