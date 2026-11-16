"""One bounded Slack conversations.list read through a host-owned transport."""

import json
import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field
from zeo_core.integrations.core.results import IntegrationResult

from zeo_integrations._http import Request, Transport
from zeo_integrations.slack.models import (
    Conversation,
    ConversationListRequest,
    ConversationPage,
    Cursor,
)

_URL = "https://slack.com/api/conversations.list"
_CAP = 1024 * 1024
_SAFE_ERRORS = frozenset(
    {"invalid_auth", "not_authed", "token_revoked", "missing_scope", "invalid_cursor"}
)


class _Metadata(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore", hide_input_in_errors=True)
    next_cursor: Cursor | None = None


class _Page(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore", hide_input_in_errors=True)
    ok: Literal[True]
    channels: list[Conversation] = Field(max_length=200)
    response_metadata: _Metadata | None = None
    error: None = None


def _unique_keys(items):
    document = {}
    for key, value in items:
        if key in document:
            raise ValueError("Duplicate JSON key")
        document[key] = value
    return document


def _invalid_number(_value):
    raise ValueError("Invalid JSON number")


class SlackClient:
    """No default socket or credentials; construct inside an admitted host callback.

    The transport owns OAuth headers, scope/egress admission and deadlines. It
    must not follow redirects or retry. The client never discovers credentials,
    paginates automatically, sends messages, or renders provider UI content.
    """

    def __init__(self, transport: Transport):
        if transport is None:
            raise ValueError("An explicit Slack transport is required")
        self._transport = transport

    def list_conversations(
        self, request: ConversationListRequest, *, key: str
    ) -> IntegrationResult[ConversationPage]:
        """Return one page; empty/short pages can still have a next cursor."""
        if not isinstance(request, ConversationListRequest) or (
            not isinstance(key, str)
            or re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", key) is None
        ):
            return IntegrationResult.error_result("slack_invalid_request")
        try:
            request = ConversationListRequest.model_validate(request.model_dump())
        except Exception:
            return IntegrationResult.error_result("slack_invalid_request")
        query = {
            "limit": str(request.limit),
            "types": ",".join(request.types),
            "exclude_archived": "true" if request.exclude_archived else "false",
        }
        if request.cursor is not None:
            query["cursor"] = request.cursor
        if request.team_id is not None:
            query["team_id"] = request.team_id
        try:
            response = self._transport.request(
                Request(
                    provider="slack",
                    operation="conversations.list",
                    method="GET",
                    url=_URL,
                    query=query,
                    headers={},
                    json_body=None,
                    form_body=None,
                    idempotency_key=key,
                    timeout_seconds=30,
                    max_response_bytes=_CAP,
                    effect=False,
                )
            )
        except Exception:
            return IntegrationResult.error_result("slack_request_failed")
        try:
            destination = urlsplit(response.url)
            if (
                destination.scheme != "https"
                or destination.hostname != "slack.com"
                or destination.port not in {None, 443}
                or destination.username is not None
                or destination.password is not None
                or destination.path != "/api/conversations.list"
                or destination.fragment
                or any(c.isspace() for c in response.url)
            ):
                return IntegrationResult.error_result("slack_invalid_response")
            if type(response.status) is not int:
                return IntegrationResult.error_result("slack_invalid_response")
            if response.status == 429:
                return IntegrationResult.error_result("slack_rate_limited")
            if response.status != 200:
                return IntegrationResult.error_result("slack_http_error")
            if type(response.body) is not bytes or len(response.body) > _CAP:
                return IntegrationResult.error_result("slack_invalid_response")
            document = json.loads(
                response.body.decode("utf-8"),
                object_pairs_hook=_unique_keys,
                parse_constant=_invalid_number,
            )
            if not isinstance(document, dict) or type(document.get("ok")) is not bool:
                return IntegrationResult.error_result("slack_invalid_response")
            if document["ok"] is False:
                code = document.get("error")
                safe = code if isinstance(code, str) and code in _SAFE_ERRORS else None
                return IntegrationResult.error_result(
                    "slack_" + safe if safe else "slack_rejected"
                )
            page = _Page.model_validate(document)
            if len(page.channels) > request.limit:
                return IntegrationResult.error_result("slack_invalid_response")
            cursor = (
                page.response_metadata.next_cursor if page.response_metadata else None
            )
            return IntegrationResult.success_result(
                content=ConversationPage(
                    conversations=page.channels, next_cursor=cursor or None
                ),
                message="Retrieved conversation page",
            )
        except Exception:
            return IntegrationResult.error_result("slack_invalid_response")
