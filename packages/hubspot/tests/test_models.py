"""Provider-model compatibility and refusal controls; synthetic inputs only."""

import unittest
from datetime import UTC, datetime, timedelta

from pydantic import ValidationError

from zeo_integrations.hubspot.models import (
    Audience, EmailContent, EmailDraft, PublishRequest, SubscriptionChange,
    send_spec_digest,
)


class Models(unittest.TestCase):
    def draft(self, **extra):
        return EmailDraft(name="draft", subject="subject", content=EmailContent(), from_name="sender", from_email="sender@example.invalid", **extra)

    def test_draft_and_reply_to_wire_compatibility(self):
        plain = self.draft().to_api()
        self.assertEqual(plain["from"], {"fromName": "sender", "replyTo": "sender@example.invalid"})
        self.assertFalse(plain["sendOnPublish"])
        self.assertEqual(plain["state"], "DRAFT")
        self.assertEqual(self.draft(reply_to="reply@example.invalid").to_api()["from"]["customReplyTo"], "reply@example.invalid")
        self.assertEqual(self.draft().to_api(), plain)

    def test_closed_fields_and_invalid_addresses(self):
        with self.assertRaises(ValidationError):
            self.draft(unknown="ignored?")
        with self.assertRaises(ValidationError):
            self.draft(reply_to="bad\n@example.invalid")

    def test_audience_conflicts_and_empty_publish_refused(self):
        for kwargs in [{"contact_ids": ("1", "1")}, {"contact_ids": ("1",), "exclude_contact_ids": ("1",)}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValidationError):
                Audience(**kwargs)
        with self.assertRaises(ValidationError):
            PublishRequest(email_id="1", expected_updated_at="v1", expected_send_spec_sha256="a" * 64, render_evidence_ref="render", subscription_id="2")

    def test_dynamic_audience_requires_policy(self):
        with self.assertRaises(ValidationError):
            PublishRequest(email_id="1", expected_updated_at="v1", expected_send_spec_sha256="a" * 64, render_evidence_ref="render", subscription_id="2", audience=Audience(list_ids=("3",)), audience_mode="dynamic_segments")

    def test_consent_cannot_be_created_by_subscription_request(self):
        with self.assertRaises(ValidationError):
            SubscriptionChange(email="reader@example.invalid", subscription_id=1, status="SUBSCRIBED")
        stop = SubscriptionChange(email="reader@example.invalid", subscription_id=1, status="UNSUBSCRIBED")
        self.assertEqual(stop.to_api()["statusState"], "UNSUBSCRIBED")

    def test_digest_binds_reviewed_content_and_schedule(self):
        base = {"name": "one", "updatedAt": "v1", "sendOnPublish": False}
        digest = send_spec_digest(base)
        self.assertEqual(digest, send_spec_digest({**base, "updatedAt": "v2", "sendOnPublish": True}))
        self.assertNotEqual(digest, send_spec_digest({**base, "name": "two"}))
        self.assertNotEqual(digest, send_spec_digest(base, send_at=datetime.now(UTC) + timedelta(hours=1)))
