"""Elder review: never bind one workflow's revision to another workflow's removal."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import SecretStr

from zeo_integrations.hubspot import (
    HubSpotClient,
    HubSpotTransport,
)


def test_correct_workflow_identity_allows_removal_despite_graph_drift() -> None:
    calls: list[httpx.Request] = []
    data: dict[str, Any] = {
        "id": "123",
        "type": "CONTACT_FLOW",
        "objectTypeId": "0-1",
        "flowType": "WORKFLOW",
        "revisionId": "7",
        "actions": [{"unknown": True}],
        "enrollmentCriteria": {"type": "EVENT_BASED"},
    }
    responses = [
        httpx.Response(200, json=data),
        httpx.Response(200, json={"results": [{"flowId": 123, "workflowId": 456}]}),
        httpx.Response(204),
    ]

    def provider(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return responses.pop(0)

    client = HubSpotClient(
        transport=HubSpotTransport(
            SecretStr("test"), transport=httpx.MockTransport(provider)
        )
    )
    try:
        assert (
            client.enroll(
                "123", "reader@example.com", revision_id="7", remove=True
            ).data
            == {}
        )
        assert [r.method for r in calls] == ["GET", "POST", "DELETE"]
        assert calls[-1].url.path.startswith("/automation/v2/workflows/456/")
    finally:
        client.close()
