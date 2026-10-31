"""List-only proof boundary uses injected fakes, never a live account."""

import httpx
import pytest

from zeo_integrations.loops import AuthenticationError, InvalidResponseError, LoopsClient
from zeo_integrations.loops.connect import ConnectLoopsMailingListsReader


LISTS = [
    {"id": "list-one", "name": "Fixture", "description": None, "isPublic": False}
]


def test_lists_only_one_get_and_shared_pacer_projection():
    seen, pacing = [], []

    def handle(request):
        seen.append(request)
        assert pacing == ["waited"]
        return httpx.Response(200, json=LISTS)

    typed = LoopsClient("synthetic", transport=httpx.MockTransport(handle))
    reader = ConnectLoopsMailingListsReader(typed, wait=lambda: pacing.append("waited"))
    try:
        assert reader.list_mailing_lists() == [
            {"id": "list-one", "name": "Fixture", "is_public": False}
        ]
    finally:
        reader.close()
    assert len(seen) == 1
    assert seen[0].method == "GET"
    assert str(seen[0].url) == "https://app.loops.so/api/v1/lists"
    assert seen[0].content == b""
    assert not seen[0].url.query


def test_unexpected_extra_fields_never_enter_projection():
    payload = [{**LISTS[0], "subscriberEmail": "fixture@example.invalid"}]
    typed = LoopsClient(
        "synthetic",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)),
    )
    reader = ConnectLoopsMailingListsReader(typed, wait=lambda: None)
    try:
        result = reader.list_mailing_lists()
    finally:
        reader.close()
    assert result == [{"id": "list-one", "name": "Fixture", "is_public": False}]
    assert "subscriberEmail" not in repr(result)


def test_list_reader_exposes_no_contact_or_write_methods():
    typed = LoopsClient(
        "synthetic", transport=httpx.MockTransport(lambda _: pytest.fail("network"))
    )
    reader = ConnectLoopsMailingListsReader(typed, wait=lambda: None)
    try:
        for name in (
            "find_contact",
            "create_contact",
            "create_campaign",
            "update_email_message",
            "send",
            "schedule",
        ):
            assert not hasattr(reader, name)
    finally:
        reader.close()


@pytest.mark.parametrize(
    "status,error", [(401, AuthenticationError), (200, InvalidResponseError)]
)
def test_failure_is_sanitized_and_never_retried(status, error):
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(status, json={"private": "synthetic-secret"})

    typed = LoopsClient("synthetic", transport=httpx.MockTransport(handle))
    reader = ConnectLoopsMailingListsReader(typed, wait=lambda: None)
    try:
        with pytest.raises(error) as caught:
            reader.list_mailing_lists()
    finally:
        reader.close()
    assert len(seen) == 1
    assert "synthetic-secret" not in str(caught.value)
