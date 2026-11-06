"""Original adapter from typed Loops results to Connect's newsletter projections.

Copyright 2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
Connect supplies the client from custody and its shared per-connection pacer.
Registration, approval validators and durable execution remain in Connect.
"""

from collections.abc import Callable

from .client import LoopsClient
from .models import AudienceFilter
from .transport import InvalidResponseError


class ConnectLoopsClient:
    """One injected client; dictionary results expected by Connect's dispatchers.

    This replaces the provider-call object, not Connect's approval validators or
    operation registry. The host must keep its narrower request constraints and
    supply a pacer shared by contacts and newsletter calls for the connection.
    """

    def __init__(self, client: LoopsClient, *, wait: Callable[[], None]):
        self.client, self.wait = client, wait

    def close(self):
        self.client.close()

    def _call(self, method, *args, **kwargs):
        self.wait()
        return method(*args, **kwargs)

    @staticmethod
    def _campaign(result):
        return result.model_dump(
            include={
                "id",
                "name",
                "status",
                "email_message_id",
                "mailing_list_id",
                "audience_segment_id",
            }
        )

    @staticmethod
    def _message(result):
        document = result.model_dump(
            include={
                "id",
                "campaign_id",
                "subject",
                "preview_text",
                "from_name",
                "from_email",
                "content_revision_id",
                "lmx",
            }
        )
        document["warning_count"] = len(result.warnings)
        return document

    def create_campaign(self, name):
        result = self._call(self.client.create_campaign, name)
        if not result.email_message_id or not result.email_message_content_revision_id:
            raise InvalidResponseError("new draft lacks message identity")
        return result.model_dump(
            include={
                "id",
                "email_message_id",
                "email_message_content_revision_id",
                "status",
            }
        )

    def get_campaign(self, campaign_id):
        return self._campaign(self._call(self.client.get_campaign, campaign_id))

    def update_campaign_audience(
        self,
        campaign_id,
        *,
        mailing_list_id=None,
        audience_segment_id=None,
        audience_filter=None,
    ):
        parsed = None
        if audience_filter is not None:
            parsed = AudienceFilter.model_validate(audience_filter)
            # Connect's approval contract does not admit activity conditions.
            if any(condition.type == "activity" for condition in parsed.conditions):
                raise ValueError("activity conditions are unavailable in this facade")
        return self._campaign(
            self._call(
                self.client.update_campaign_audience,
                campaign_id,
                mailing_list_id=mailing_list_id,
                audience_segment_id=audience_segment_id,
                audience_filter=parsed,
            )
        )

    def get_email_message(self, email_message_id):
        return self._message(
            self._call(self.client.get_email_message, email_message_id)
        )

    def update_email_message(
        self,
        email_message_id,
        *,
        expected_revision_id,
        subject,
        preview_text,
        from_name,
        from_email,
        lmx,
    ):
        return self._message(
            self._call(
                self.client.update_email_message,
                email_message_id,
                expected_revision_id=expected_revision_id,
                subject=subject,
                preview_text=preview_text,
                from_name=from_name,
                from_email=from_email,
                lmx=lmx,
            )
        )

    def list_themes(self):
        page = self._call(self.client.list_themes)
        return [
            item.model_dump(include={"id", "name", "is_default"}) for item in page.data
        ]

    def list_mailing_lists(self):
        return [
            item.model_dump(include={"id", "name", "is_public"})
            for item in self._call(self.client.list_mailing_lists)
        ]

    def create_upload(self, content_type, content_length):
        return self._call(
            self.client.create_upload, content_type, content_length
        ).model_dump()

    def complete_upload(self, email_asset_id):
        return self._call(self.client.complete_upload, email_asset_id).model_dump()
