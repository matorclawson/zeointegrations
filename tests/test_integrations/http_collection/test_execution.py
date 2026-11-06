"""Execution boundaries with synthetic providers; never call the network."""

from dataclasses import replace
from unittest.mock import Mock

import httpx
import pytest

from zeo_integrations._http import HttpxTransport, IntegrationError, Request
from zeo_integrations.amazon import (
    BrowseNodes,
    Client,
    Items,
    Variations,
    get_asin_from_url,
)
from zeo_integrations.mail.imap import GetMessage, ImapClient, ListMessages


def request(**overrides):
    return replace(
        Request(
            "test",
            "read",
            "GET",
            "https://example.com/items",
            {},
            {},
            None,
            None,
            "key",
            30,
            100,
            False,
        ),
        **overrides,
    )


def transport(handler):
    return HttpxTransport(
        transport=httpx.MockTransport(handler), origins=("https://example.com",)
    )


def test_stream_and_cookies():
    seen = []

    def respond(wire):
        seen.append(wire)
        return httpx.Response(
            200, json={"ok": True}, headers={"set-cookie": "sid=private"}
        )

    with transport(respond) as client:
        assert client.request(request()).body == b'{"ok":true}'
        client.request(request())
    assert len(seen) == 2
    assert all("cookie" not in wire.headers for wire in seen)
    assert all(wire.headers["accept-encoding"] == "identity" for wire in seen)


@pytest.mark.parametrize(
    "status,headers,body,code",
    [
        (302, {"location": "https://elsewhere.com"}, b"", "REDIRECT"),
        (200, {"content-encoding": "br"}, b"", "ENCODING"),
        (200, {}, b"x" * 101, "SIZE_LIMIT"),
    ],
)
def test_response_refusals_are_not_retried(status, headers, body, code):
    seen = []

    def respond(wire):
        seen.append(wire)
        return httpx.Response(status, headers=headers, content=body)

    with transport(respond) as client, pytest.raises(IntegrationError) as caught:
        client.request(request(method="POST", effect=True))
    assert caught.value.code == code
    assert caught.value.outcome_unknown
    assert len(seen) == 1


def test_transport_exception_does_not_retain_request():
    def fail(wire):
        raise httpx.ConnectError("SECRET", request=wire)

    with transport(fail) as client, pytest.raises(IntegrationError) as caught:
        client.request(request())
    assert "SECRET" not in str(caught.value)
    assert caught.value.__context__ is None


@pytest.mark.parametrize(
    "change",
    [
        {"url": "https://elsewhere.com"},
        {"headers": {"Host": "elsewhere.com"}},
        {"headers": {"Authorization": "SECRET"}},
        {"timeout_seconds": float("nan")},
    ],
)
def test_request_refused_before_network(change):
    wire = Mock()
    with transport(wire) as client, pytest.raises(IntegrationError):
        client.request(request(**change))
    wire.assert_not_called()


def test_amazon_lookup_methods_and_local_url():
    api = Mock()
    api.get_items.return_value = [{"asin": "B000000001"}]
    api.get_variations.return_value = {"variations": []}
    api.get_browse_nodes.return_value = []
    client = Client(api)
    assert client.get_items(Items(asins=["B000000001"])) == [{"asin": "B000000001"}]
    assert client.get_variations(Variations(asin="B000000001")) == {"variations": []}
    assert client.get_browse_nodes(BrowseNodes(browse_node_ids=["123"])) == []
    api.get_items.assert_called_once_with(["B000000001"])
    assert get_asin_from_url("https://www.amazon.com/dp/B000000001?q=x") == "B000000001"
    with pytest.raises(IntegrationError):
        get_asin_from_url("https://amazon.com.evil.test/dp/B000000001")


def imap():
    session = Mock()
    session.select.return_value = ("OK", [b"3"])
    session.response.return_value = ("UIDVALIDITY", [b"123"])
    return session


def test_imap_list_uses_uids_and_readonly_selection():
    session = imap()
    session.uid.return_value = ("OK", [b"2 4 6 8"])
    result = ImapClient(session).list_messages(ListMessages(after_uid=3, limit=2))
    assert result["uids"] == [4, 6]
    assert result["next_after_uid"] == 6 and result["has_more"]
    assert result["uidvalidity"] == 123
    session.select.assert_called_once_with('"INBOX"', readonly=True)
    session.uid.assert_called_once_with("SEARCH", None, "UID", "4:*")
    session.close.assert_not_called()


def test_imap_changed_mailbox_does_not_fetch():
    session = imap()
    with pytest.raises(IntegrationError, match="MAILBOX_CHANGED"):
        ImapClient(session).get_message(GetMessage(uid=4, uidvalidity=122))
    session.uid.assert_not_called()


@pytest.mark.parametrize(
    "header,body,code",
    [
        (b"1 (UID 5 RFC822.SIZE 3)", b"abc", "MESSAGE_IDENTITY"),
        (b"1 (UID 4 RFC822.SIZE 4)", b"abc", "MESSAGE_TRUNCATED"),
        (b"1 (UID 4 RFC822.SIZE 4)", b"abcd", "SIZE_LIMIT"),
    ],
)
def test_imap_does_not_return_wrong_or_partial_message(header, body, code):
    session = imap()
    session.uid.return_value = ("OK", [(header, body), b")"])
    with pytest.raises(IntegrationError, match=code):
        ImapClient(session).get_message(GetMessage(uid=4, uidvalidity=123, max_bytes=3))


def test_imap_peek_preserves_unread():
    session = imap()
    session.uid.return_value = ("OK", [(b"1 (UID 4 RFC822.SIZE 3)", b"abc"), b")"])
    result = ImapClient(session).get_message(
        GetMessage(uid=4, uidvalidity=123, max_bytes=3)
    )
    assert result["data"] == "YWJj"
    session.uid.assert_called_once_with(
        "FETCH", "4", "(UID RFC822.SIZE BODY.PEEK[]<0.4>)"
    )


def test_whatsapp_read_binding_and_limits():
    from zeo_integrations.whatsapp.reads import Chats, ReadClient

    bridge = Mock()
    bridge.list_chats.return_value = {"chats": []}
    assert ReadClient(bridge, user_id="account-a").get_chats(Chats()) == {"chats": []}
    bridge.list_chats.assert_called_once_with(
        "account-a",
        query=None,
        limit=20,
        page=0,
        include_last_message=False,
        sort_by="last_active",
    )
    bridge.list_chats.return_value = {"oversize": "x" * 1048576}
    with pytest.raises(IntegrationError, match="BRIDGE_READ_FAILED"):
        ReadClient(bridge, user_id="account-a").get_chats(Chats())


def test_e2b_execution_omits_active_displays_and_requires_admission():
    from types import SimpleNamespace

    from zeo_integrations.e2b import Code, CodeClient

    sandbox = Mock()
    client = CodeClient(sandbox)
    with pytest.raises(IntegrationError, match="EFFECT_ADMISSION_REQUIRED"):
        client.run_code(Code(code="1+1"))
    sandbox.run_code.assert_not_called()
    sandbox.run_code.return_value = SimpleNamespace(
        logs=SimpleNamespace(stdout=[], stderr=[]),
        error=None,
        results=[SimpleNamespace(text="2", html="<script>bad()</script>")],
    )
    assert client.run_code(Code(code="1+1"), allow_effect=True) == {
        "stdout": [],
        "stderr": [],
        "execution_failed": False,
        "text_results": ["2"],
    }
    sandbox.run_code.assert_called_once_with("1+1", language="python", timeout=30)


def test_real_provider_facade_round_trip_and_effect_admission():
    from zeo_integrations.slack import Client as Slack

    seen = []

    def respond(wire):
        seen.append(wire)
        return httpx.Response(200, json={"ok": True, "ts": "123.456"})

    with HttpxTransport(
        transport=httpx.MockTransport(respond), origins=("https://slack.com",)
    ) as wire:
        client = Slack(wire)
        arguments = {"parameters": {"channel": "C1", "text": "hello"}}
        with pytest.raises(IntegrationError):
            client.invoke("post_message", arguments, idempotency_key="one")
        assert not seen
        result = client.invoke(
            "post_message", arguments, idempotency_key="one", allow_effect=True
        )
        assert result == {"ok": True, "ts": "123.456"}
    assert len(seen) == 1
    assert seen[0].url.path == "/api/chat.postMessage"
    assert seen[0].content == b'{"channel":"C1","text":"hello"}'
