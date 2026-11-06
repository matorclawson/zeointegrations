"""Synthetic provider responses exercise the original Connect adapter."""

from unittest.mock import Mock

import httpx
import pytest

from zeo_integrations.loops import LoopsClient
from zeo_integrations.loops.connect import ConnectLoopsClient

CAMPAIGN = {
    "id": "campaign",
    "url": "https://app.loops.so/campaigns/campaign",
    "name": "Issue",
    "status": "Draft",
    "createdAt": "2026-01-01",
    "updatedAt": "2026-01-01",
    "emailMessageId": "message",
    "emailMessageContentRevisionId": "revision",
    "campaignGroupId": None,
    "mailingListId": None,
    "audienceSegmentId": None,
}


def test_create_uses_real_typed_client_and_pacer():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(201, json=CAMPAIGN)

    pacer = Mock()
    typed = LoopsClient("synthetic", transport=httpx.MockTransport(handler))
    adapter = ConnectLoopsClient(typed, wait=pacer)
    try:
        assert adapter.create_campaign("Issue") == {
            "id": "campaign",
            "email_message_id": "message",
            "email_message_content_revision_id": "revision",
            "status": "Draft",
        }
    finally:
        adapter.close()
    pacer.assert_called_once_with()
    assert len(seen) == 1
    assert seen[0].content == b'{"name":"Issue"}'


def test_get_returns_only_connect_projection():
    typed = LoopsClient(
        "synthetic",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=CAMPAIGN)),
    )
    adapter = ConnectLoopsClient(typed, wait=lambda: None)
    try:
        result = adapter.get_campaign("campaign")
        assert set(result) == {
            "id",
            "name",
            "status",
            "email_message_id",
            "mailing_list_id",
            "audience_segment_id",
        }
    finally:
        adapter.close()


def test_activity_filter_does_not_reach_provider():
    typed, wait = Mock(), Mock()
    adapter = ConnectLoopsClient(typed, wait=wait)
    with pytest.raises(ValueError, match="activity"):
        adapter.update_campaign_audience(
            "campaign",
            audience_filter={
                "match": "all",
                "conditions": [
                    {
                        "type": "activity",
                        "action": "opened",
                        "negate": False,
                        "target": "campaign",
                        "id": "other",
                    }
                ],
            },
        )
    wait.assert_not_called()
    typed.update_campaign_audience.assert_not_called()
