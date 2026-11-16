"""Synthetic Slack responses through explicit transports; never a socket client."""

import asyncio
import json

import httpx
import pytest
from pydantic import ValidationError

from zeo_integrations._http import HttpxTransport, Response
from zeo_integrations.slack import ConversationListRequest, SlackClient

URL = "https://slack.com/api/conversations.list"


class StubTransport:
    def __init__(self, document=None, *, body=None, status=200, url=URL, error=None):
        self.response = Response(
            status=status,
            body=body if body is not None else json.dumps(document).encode(),
            headers={},
            url=url,
        )
        self.error = error
        self.calls = []

    def request(self, request):
        self.calls.append(request)
        if self.error is not None:
            raise self.error
        return self.response


def test_scoped_single_page_query_and_nullable_projection():
    transport = StubTransport(
        {
            "ok": True,
            "channels": [
                {"id": "C-FIXTURE", "name": "fixture", "topic": {"value": "ignored"}}
            ],
            "response_metadata": {"next_cursor": "opaque+/="},
        }
    )
    result = SlackClient(transport).list_conversations(
        ConversationListRequest(
            limit=10,
            cursor="previous+/=",
            types=["public_channel", "private_channel"],
            exclude_archived=True,
            team_id="T-FIXTURE",
        ),
        key="read:fixture",
    )
    assert result.success
    assert result.content.next_cursor == "opaque+/="
    conversation = result.content.conversations[0]
    assert conversation.id == "C-FIXTURE"
    assert conversation.is_private is None
    assert "topic" not in conversation.model_dump()
    assert len(transport.calls) == 1
    request = transport.calls[0]
    assert request.method == "GET" and request.url == URL
    assert request.provider == "slack" and request.operation == "conversations.list"
    assert request.effect is False
    assert request.headers == {} and request.json_body is None
    assert request.form_body is None and request.raw_body is None
    assert request.query == {
        "limit": "10",
        "cursor": "previous+/=",
        "types": "public_channel,private_channel",
        "exclude_archived": "true",
        "team_id": "T-FIXTURE",
    }
    assert request.timeout_seconds == 30 and request.max_response_bytes == 1024 * 1024


def test_empty_page_with_cursor_is_not_terminal_or_automatically_followed():
    transport = StubTransport(
        {"ok": True, "channels": [], "response_metadata": {"next_cursor": "continue="}}
    )
    result = SlackClient(transport).list_conversations(
        ConversationListRequest(), key="page"
    )
    assert result.success and result.content.conversations == []
    assert result.content.next_cursor == "continue="
    assert len(transport.calls) == 1


@pytest.mark.parametrize("metadata", [{}, {"next_cursor": ""}, {"next_cursor": None}])
def test_documented_terminal_cursor_shapes(metadata):
    transport = StubTransport(
        {"ok": True, "channels": [], "response_metadata": metadata}
    )
    result = SlackClient(transport).list_conversations(
        ConversationListRequest(), key="page"
    )
    assert result.success and result.content.next_cursor is None


@pytest.mark.parametrize(
    "fields",
    [
        {"limit": 0},
        {"limit": 201},
        {"limit": True},
        {"cursor": ""},
        {"cursor": "x" * 4097},
        {"types": []},
        {"types": ["im", "im"]},
        {"types": ["admin"]},
        {"exclude_archived": "true"},
        {"token": "inert-secret"},
    ],
)
def test_closed_request_models_refuse_bad_values(fields):
    with pytest.raises(ValidationError) as caught:
        ConversationListRequest.model_validate(fields)
    assert "inert-secret" not in str(caught.value)


def test_mutation_cannot_bypass_request_validation():
    transport = StubTransport({"ok": True, "channels": []})
    request = ConversationListRequest()
    request.types.clear()
    result = SlackClient(transport).list_conversations(request, key="page")
    assert not result.success and transport.calls == []


@pytest.mark.parametrize("key", ["", "inert\nkey", 1, "x" * 201])
def test_invalid_invocation_key_never_dispatches(key):
    transport = StubTransport({"ok": True, "channels": []})
    result = SlackClient(transport).list_conversations(
        ConversationListRequest(), key=key
    )
    assert not result.success and transport.calls == []


@pytest.mark.parametrize(
    "document",
    [
        {"ok": "true", "channels": []},
        {"ok": 1, "channels": []},
        {"ok": True},
        {"ok": True, "channels": [{"name": "missing-id"}]},
        {"ok": True, "channels": [{"id": 1}]},
        {"ok": True, "channels": [{"id": "C", "is_private": "false"}]},
        {"ok": True, "channels": [], "response_metadata": {"next_cursor": 1}},
        {"ok": True, "channels": [], "error": "inert-secret"},
        {"ok": True, "channels": [{"id": "A"}, {"id": "B"}]},
    ],
)
def test_malformed_or_over_limit_reply_is_not_success(document, caplog):
    transport = StubTransport(document)
    result = SlackClient(transport).list_conversations(
        ConversationListRequest(limit=1), key="page"
    )
    assert not result.success and len(transport.calls) == 1
    assert "inert-secret" not in str(result.error) + caplog.text


@pytest.mark.parametrize(
    "body",
    [
        b'{"ok":false,"ok":true,"channels":[]}',
        b'{"ok":true,"channels":[],"unknown":NaN}',
        b"not-json inert-secret",
        b"\xff",
        b"x" * (1024 * 1024 + 1),
    ],
)
def test_invalid_duplicate_or_oversized_json_is_refused(body):
    transport = StubTransport(body=body)
    result = SlackClient(transport).list_conversations(
        ConversationListRequest(), key="page"
    )
    assert not result.success and "inert-secret" not in str(result.error)


@pytest.mark.parametrize(
    "destination",
    [
        "https://elsewhere.invalid/api/conversations.list",
        "http://slack.com/api/conversations.list",
        "https://inert-secret@slack.com/api/conversations.list",
        "https://slack.com/api/users.list",
        URL + "#fragment",
    ],
)
def test_wrong_response_destination_is_refused(destination):
    transport = StubTransport({"ok": True, "channels": []}, url=destination)
    result = SlackClient(transport).list_conversations(
        ConversationListRequest(), key="page"
    )
    assert not result.success and "inert-secret" not in str(result.error)


@pytest.mark.parametrize(
    ("status", "document", "error"),
    [
        (429, {}, "slack_rate_limited"),
        (503, {"error": "inert-secret"}, "slack_http_error"),
        (200, {"ok": False, "error": "missing_scope"}, "slack_missing_scope"),
        (200, {"ok": False, "error": "invalid_cursor"}, "slack_invalid_cursor"),
        (200, {"ok": False, "error": "inert-secret"}, "slack_rejected"),
    ],
)
def test_http200_is_not_api_success_and_failures_are_not_retried(
    status, document, error
):
    transport = StubTransport(document, status=status)
    result = SlackClient(transport).list_conversations(
        ConversationListRequest(), key="page"
    )
    assert not result.success and result.error == error
    assert len(transport.calls) == 1


def test_transport_failure_is_sanitized_and_single_attempt(caplog):
    transport = StubTransport(error=RuntimeError("inert-secret"))
    result = SlackClient(transport).list_conversations(
        ConversationListRequest(), key="page"
    )
    assert not result.success and result.error == "slack_request_failed"
    assert "inert-secret" not in caplog.text
    assert len(transport.calls) == 1


def test_explicit_httpx_transport_has_no_default_socket_or_token_in_query():
    seen = []

    def handler(request):
        request.headers["Authorization"] = "Bearer inert-host-owned"
        seen.append(request)
        return httpx.Response(200, json={"ok": True, "channels": []})

    with HttpxTransport(
        transport=httpx.MockTransport(handler), origins=("https://slack.com",)
    ) as transport:
        result = SlackClient(transport).list_conversations(
            ConversationListRequest(cursor="opaque+/="), key="page"
        )
    assert result.success and len(seen) == 1
    assert seen[0].headers["Authorization"] == "Bearer inert-host-owned"
    assert seen[0].url.params["cursor"] == "opaque+/="
    assert "token" not in seen[0].url.params


def test_none_transport_is_not_a_default_network_route():
    with pytest.raises(ValueError, match="explicit"):
        SlackClient(None)


def test_caller_cancellation_propagates_without_retry():
    transport = StubTransport(error=asyncio.CancelledError())
    with pytest.raises(asyncio.CancelledError):
        SlackClient(transport).list_conversations(ConversationListRequest(), key="page")
    assert len(transport.calls) == 1
