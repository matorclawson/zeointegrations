"""Explicit, data-only status projections using Core's canonical UI contract.

Provider payloads are never automatically rendered or promoted to action authority.
"""

from __future__ import annotations

import json


def status_card(
    *,
    provider: str,
    operation: str,
    invocation: str,
    result_id: str,
    produced_at: str,
    summary: str,
    state: str = "unknown",
) -> dict:
    from zeo_core.contracts.ui.wire import validate_bytes

    value = {
        "schema": "zeo.ui-result/v1",
        "result_id": result_id,
        "in_reply_to": {"operation": operation, "invocation": invocation},
        "produced_at": produced_at,
        "complete": True,
        "plain_text": summary,
        "components": [
            {
                "id": "integration.status",
                "kind": "card",
                "title": provider,
                "accessibility_label": provider,
                "fallback_text": summary,
                "props": {
                    "summary": summary,
                    "facts": [],
                    "status": {"state": state, "text": state},
                    "evidence": [{"kind": "operation", "ref": invocation}],
                    "action_refs": [],
                },
            }
        ],
    }
    validate_bytes(json.dumps(value, ensure_ascii=False).encode())
    return value
