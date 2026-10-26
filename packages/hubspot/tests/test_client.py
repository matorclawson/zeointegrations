"""Guarded provider workflows with a synthetic in-memory boundary."""

import copy
import unittest
from datetime import UTC, datetime, timedelta

from zeo_integrations.hubspot.client import EMAILS, HubSpotClient, _id
from zeo_integrations.hubspot.models import (
    Audience,
    EmailSequence,
    PageRequest,
    PublishRequest,
    SequenceStep,
    send_spec_digest,
)
from zeo_integrations.hubspot.transport import HubSpotAPIError


class FakeBoundary:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        if not self.responses:
            raise AssertionError("unexpected provider call")
        return copy.deepcopy(self.responses.pop(0))

    def close(self):
        pass


class Client(unittest.TestCase):
    def client(self, *responses):
        boundary = FakeBoundary(responses)
        return HubSpotClient(transport=boundary), boundary

    def email(self):
        return {
            "id": "1",
            "name": "reviewed",
            "subject": "subject",
            "updatedAt": "v1",
            "isPublished": False,
            "isTransactional": False,
            "type": "BATCH_EMAIL",
            "state": "DRAFT",
            "subscriptionDetails": {"subscriptionId": "2"},
            "to": Audience(contact_ids=("3",)).to_api(),
            "sendOnPublish": False,
        }

    def publish(self, data, **extra):
        return PublishRequest(
            email_id="1",
            expected_updated_at="v1",
            expected_send_spec_sha256=send_spec_digest(data),
            render_evidence_ref="inert-render",
            subscription_id="2",
            audience=Audience(contact_ids=("3",)),
            **extra,
        )

    def test_old_private_helper_and_constant(self):
        self.assertEqual(EMAILS, "/marketing/emails/2026-03")
        self.assertEqual(_id("valid_1"), "valid_1")
        with self.assertRaises(ValueError):
            _id("../unsafe")

    def test_publish_requires_explicit_confirmation_before_any_request(self):
        data = self.email()
        client, boundary = self.client()
        with self.assertRaises(ValueError):
            client.publish_email(self.publish(data))
        self.assertEqual(boundary.calls, [])

    def test_reviewed_publish_preserves_check_patch_recheck_publish_order(self):
        data = self.email()
        client, boundary = self.client(
            data, {}, {**data, "sendOnPublish": True}, {"id": "1"}
        )
        self.assertEqual(
            client.publish_email(self.publish(data, confirm=True)).data, {"id": "1"}
        )
        self.assertEqual(
            [(m, p) for m, p, _ in boundary.calls],
            [
                ("GET", f"{EMAILS}/1"),
                ("PATCH", f"{EMAILS}/1"),
                ("GET", f"{EMAILS}/1"),
                ("POST", f"{EMAILS}/1/publish"),
            ],
        )

    def test_changed_revision_audience_or_digest_never_mutates(self):
        data = self.email()
        for changed in [
            {**data, "updatedAt": "v2"},
            {**data, "to": Audience(contact_ids=("other",)).to_api()},
            {**data, "subject": "changed"},
        ]:
            client, boundary = self.client(changed)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                client.publish_email(self.publish(data, confirm=True))
            self.assertEqual([c[0] for c in boundary.calls], ["GET"])

    def test_race_after_configuration_never_publishes(self):
        data = self.email()
        client, boundary = self.client(
            data, {}, {**data, "subject": "raced", "sendOnPublish": True}
        )
        with self.assertRaises(ValueError):
            client.publish_email(self.publish(data, confirm=True))
        self.assertEqual([c[0] for c in boundary.calls], ["GET", "PATCH", "GET"])

    def test_invalid_final_schedule_drops_provider_context_and_never_publishes(self):
        data = self.email()
        send_at = datetime.now(UTC) + timedelta(days=1)
        marker = "synthetic-private-provider-schedule"
        client, boundary = self.client(data, {}, {**data, "publishDate": marker})
        request = PublishRequest(
            email_id="1",
            expected_updated_at="v1",
            expected_send_spec_sha256=send_spec_digest(data, send_at=send_at),
            render_evidence_ref="inert-render",
            subscription_id="2",
            audience=Audience(contact_ids=("3",)),
            send_at=send_at,
            confirm=True,
        )
        with self.assertRaises(ValueError) as raised:
            client.publish_email(request)
        self.assertEqual(str(raised.exception), "Provider schedule is invalid")
        self.assertIsNone(raised.exception.__context__)
        self.assertIsNone(raised.exception.__cause__)
        self.assertNotIn(marker, str(raised.exception))
        self.assertEqual([c[0] for c in boundary.calls], ["GET", "PATCH", "GET"])

    def test_invalid_page_and_immediate_cursor_repeat_refused(self):
        for response in [
            {"results": [{}], "paging": {"next": {"after": "repeat"}}},
            {"results": [], "paging": {"next": {}}},
        ]:
            client, _ = self.client(response)
            if response["paging"]["next"]:
                with self.assertRaises(HubSpotAPIError):
                    client.list_emails(PageRequest(after="repeat"))
            else:
                self.assertEqual(client.list_emails().results, [])

    def test_enable_and_enroll_require_confirmation_before_provider_calls(self):
        client, boundary = self.client()
        sequence = EmailSequence(name="linear", steps=(SequenceStep(email_id="1"),))
        with self.assertRaises(ValueError):
            client.update_sequence("1", sequence, revision_id="v1", enabled=True)
        with self.assertRaises(ValueError):
            client.enroll("1", "reader@example.invalid", revision_id="v1")
        self.assertEqual(boundary.calls, [])
