"""Direct X publisher composition and ambiguity tests, synthetic transport only."""

import json

import httpx
import pytest
from pydantic import ValidationError

from zeo_integrations._http import HttpxTransport, IntegrationError
from zeo_integrations.publishing import PublishingResponseError, XPost, XPublisher


def wire(handler):
    return HttpxTransport(
        transport=httpx.MockTransport(handler), origins=(XPublisher.origin,)
    )


def test_publish_is_one_explicitly_admitted_user_context_step():
    seen = []

    def handler(request):
        seen.append(request)
        assert (
            request.method == "POST"
            and str(request.url) == "https://api.x.com/2/tweets"
        )
        assert "authorization" not in request.headers
        assert json.loads(request.content) == {
            "text": "Hello 🌍",
            "media": {"media_ids": ["123", "456"]},
            "reply": {"in_reply_to_tweet_id": "789"},
        }
        return httpx.Response(
            201, json={"data": {"id": "101", "text": "DROP_PRIVATE_TEXT"}}
        )

    with wire(handler) as transport:
        client = XPublisher(transport, account_id="42")
        post = XPost(text="Hello 🌍", media_ids=["123", "456"], reply_to_id="789")
        with pytest.raises(IntegrationError, match="ADMISSION"):
            client.publish(post, key="x-post")
        assert seen == []
        assert client.publish(post, key="x-post", allow_effect=True) == {
            "post_id": "101",
            "stage": "created",
        }
    assert len(seen) == 1


def test_media_only_post_keeps_explicit_empty_text():
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(201, json={"data": {"id": "123"}, "errors": []})

    with wire(handler) as transport:
        XPublisher(transport, account_id="1").publish(
            XPost(media_ids=["2"]), key="a", allow_effect=True
        )
    assert seen == [{"text": "", "media": {"media_ids": ["2"]}}]


@pytest.mark.parametrize(
    "post",
    [
        XPost(),
        XPost(text=" \n"),
        XPost(text="a", media_ids=["x"]),
        XPost(text="a", media_ids=["1", "1"]),
        XPost(text="a", reply_to_id="1/evil"),
    ],
)
def test_invalid_content_is_refused_before_dispatch(post):
    seen = []
    with wire(lambda req: seen.append(req)) as transport:
        with pytest.raises(IntegrationError) as caught:
            XPublisher(transport, account_id="1").publish(
                post, key="a", allow_effect=True
            )
    assert not caught.value.outcome_unknown and not seen


@pytest.mark.parametrize(
    "fields",
    [
        {"text": "a" * 281},
        {"text": 123},
        {"text": "a", "media_ids": ["1"] * 5},
        {"text": "a", "quote_tweet_id": "1"},
    ],
)
def test_closed_input_does_not_drop_or_truncate_fields(fields):
    with pytest.raises(ValidationError):
        XPost(**fields)


@pytest.mark.parametrize(
    "status,body",
    [
        (200, {"data": {"id": "1"}}),
        (202, {"data": {"id": "1"}}),
        (201, {}),
        (201, {"data": []}),
        (201, {"data": {"id": 123}}),
        (201, {"data": {"id": "bad/id"}}),
        (201, {"data": {"id": "1"}, "errors": [{"detail": "PRIVATE"}]}),
        (201, {"data": {"id": "1"}, "errors": None}),
        (201, {"data": {"id": "1"}, "type": "about:blank"}),
    ],
)
def test_bad_write_receipts_remain_unknown_no_retry(status, body):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(status, json=body)

    with wire(handler) as transport:
        with pytest.raises(IntegrationError) as caught:
            XPublisher(transport, account_id="1").publish(
                XPost(text="hello"), key="a", allow_effect=True
            )
    assert caught.value.outcome_unknown and len(seen) == 1
    assert "PRIVATE" not in str(caught.value)


@pytest.mark.parametrize(
    "status,kind",
    [
        (400, "invalid-request"),
        (403, "client-forbidden"),
        (403, "not-authorized-for-resource"),
        (404, "resource-not-found"),
        (429, "usage-capped"),
        (429, "rate-limit-exceeded"),
    ],
)
def test_documented_structured_rejections_keep_only_bounded_facts(status, kind):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            status,
            headers={"Retry-After": "13"},
            json={
                "type": "https://api.x.com/2/problems/" + kind,
                "status": status,
                "detail": "PRIVATE_TEXT",
            },
        )

    with wire(handler) as transport:
        with pytest.raises(PublishingResponseError) as caught:
            XPublisher(transport, account_id="1").publish(
                XPost(text="a"), key="a", allow_effect=True
            )
    error = caught.value
    assert (
        error.definite_refusal
        and not error.outcome_unknown
        and error.retry_after == "13"
    )
    assert error.http_status == status and error.provider_code.endswith("/" + kind)
    assert "PRIVATE_TEXT" not in str(error) + repr(error.__dict__)
    assert len(seen) == 1


@pytest.mark.parametrize(
    "status,body",
    [
        (503, {"type": "https://api.x.com/2/problems/invalid-request"}),
        (409, {}),
        (401, {"type": "about:blank", "status": 401}),
        (429, {"type": "https://evil.invalid/2/problems/rate-limit-exceeded"}),
        (400, {"type": "https://api.x.com/2/problems/invalid-request", "status": 503}),
        (
            400,
            {
                "type": "https://api.x.com/2/problems/invalid-request",
                "data": {"id": "1"},
            },
        ),
    ],
)
def test_ambiguous_failures_remain_unknown_without_retries(status, body):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(status, json=body)

    with wire(handler) as transport:
        with pytest.raises(PublishingResponseError) as caught:
            XPublisher(transport, account_id="1").publish(
                XPost(text="a"), key="a", allow_effect=True
            )
    assert not caught.value.definite_refusal and caught.value.outcome_unknown
    assert len(seen) == 1 and "evil.invalid" not in repr(caught.value.__dict__)


@pytest.mark.parametrize(
    "response,ok",
    [
        ({"data": {"id": "42", "username": "fixture"}}, True),
        ({"data": {"id": "43", "username": "fixture"}}, False),
        ({"data": {"id": "42", "username": "bad name"}}, False),
        ({"data": {"id": "42", "username": "fixture"}, "errors": [1]}, False),
    ],
)
def test_identity_uses_authenticated_subject_not_supplied_username(response, ok):
    seen = []

    def handler(request):
        seen.append(request)
        assert (
            request.method == "GET"
            and str(request.url) == "https://api.x.com/2/users/me"
        )
        return httpx.Response(200, json=response)

    with wire(handler) as transport:
        client = XPublisher(transport, account_id="42")
        if ok:
            assert client.identity(key="me") == {
                "account_id": "42",
                "username": "fixture",
            }
        else:
            with pytest.raises(IntegrationError) as caught:
                client.identity(key="me")
            assert not caught.value.outcome_unknown
    assert len(seen) == 1


@pytest.mark.parametrize(
    "post_id,author_id,ok",
    [("123", "42", True), ("124", "42", False), ("123", "43", False)],
)
def test_read_is_bound_to_known_post_and_selected_author(post_id, author_id, ok):
    seen = []

    def handler(request):
        seen.append(request)
        assert request.method == "GET" and request.url.path == "/2/tweets/123"
        assert dict(request.url.params) == {"tweet.fields": "author_id"}
        return httpx.Response(
            200,
            json={
                "data": {"id": post_id, "author_id": author_id, "text": "PRIVATE_TEXT"}
            },
        )

    with wire(handler) as transport:
        client = XPublisher(transport, account_id="42")
        if ok:
            assert client.read_post("123", key="read") == {
                "post_id": "123",
                "account_id": "42",
                "stage": "observed",
            }
        else:
            with pytest.raises(IntegrationError, match="BINDING"):
                client.read_post("123", key="read")
    assert len(seen) == 1


@pytest.mark.parametrize("account", [123, "", "x", "123/evil", "1" * 20])
def test_invalid_selected_identity_is_refused(account):
    with wire(lambda req: pytest.fail("unexpected dispatch")) as transport:
        with pytest.raises(IntegrationError):
            XPublisher(transport, account_id=account)


def test_transport_failure_after_dispatch_is_unknown_no_retry():
    seen = []

    def handler(request):
        seen.append(request)
        raise httpx.ReadTimeout("PRIVATE_TRACE")

    with wire(handler) as transport:
        with pytest.raises(IntegrationError) as caught:
            XPublisher(transport, account_id="1").publish(
                XPost(text="a"), key="a", allow_effect=True
            )
    assert caught.value.outcome_unknown and "PRIVATE_TRACE" not in str(caught.value)
    assert len(seen) == 1
