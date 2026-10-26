"""HubSpot provider client; credential discovery and lifecycle remain in Core."""

from .client import HubSpotClient
from .models import (
    Audience,
    CampaignProperties,
    EmailAddress,
    EmailContent,
    EmailDraft,
    EmailSequence,
    MarketingPage,
    MarketingRecord,
    PageRequest,
    PublishRequest,
    SequenceStep,
    SubscriptionChange,
    send_spec_digest,
)
from .transport import HubSpotAPIError, HubSpotTransport

__all__ = [
    "Audience",
    "CampaignProperties",
    "EmailAddress",
    "EmailContent",
    "EmailDraft",
    "EmailSequence",
    "HubSpotAPIError",
    "HubSpotClient",
    "HubSpotTransport",
    "MarketingPage",
    "MarketingRecord",
    "PageRequest",
    "PublishRequest",
    "SequenceStep",
    "SubscriptionChange",
    "send_spec_digest",
]
