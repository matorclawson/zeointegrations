"""Typed read-only Slack API slice; auth and execution remain host-owned."""

from zeo_integrations.slack.client import SlackClient
from zeo_integrations.slack.models import (
    Conversation,
    ConversationListRequest,
    ConversationPage,
)

__all__ = ["SlackClient", "Conversation", "ConversationListRequest", "ConversationPage"]
