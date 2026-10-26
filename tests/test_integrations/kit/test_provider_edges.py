"""Counterexamples for nullable provider metadata and read/approval separation."""

from __future__ import annotations

from typing import Any

import httpx

from zeo_integrations.kit import record_digest

from .conftest import ClientFixture, queue_snapshot, snapshot


def test_hour_sequence_with_null_preview_can_activate(
    setup_client: ClientFixture, sequence: dict[str, Any], email: dict[str, Any]
) -> None:
    client, calls, responses = setup_client
    email.update(preview_text=None, delay_unit="hours", delay_value=2)
    queue_snapshot(responses, sequence, email)
    responses.append(httpx.Response(200, json={"sequence": sequence}))
    client.set_sequence_active(
        23,
        active=True,
        expected_digest=record_digest(snapshot(sequence, email)),
        confirm=True,
        render_evidence_ref="render",
        audience_policy_ref="policy",
    )
    assert calls[-1].method == "PUT"
