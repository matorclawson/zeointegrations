"""Fixed-origin, one-attempt Loops content client. No send or schedule surface."""

import json
import math
import threading
import time
from collections import deque
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import httpx
from pydantic import TypeAdapter

from .models import (
    Account,
    AudienceFilter,
    AudienceUpdate,
    Campaign,
    Contact,
    ContactSaved,
    ContactUpdate,
    EmailMessage,
    EmailUpdate,
    MailingList,
    Suppression,
    ThemePage,
    UploadedAsset,
    UploadTicket,
)


class LoopsError(RuntimeError):
    """Sanitized error; mutation success is not implied by a failed response."""


class AuthenticationError(LoopsError):
    pass


class NotFoundError(LoopsError):
    pass


class RevisionConflictError(LoopsError):
    pass


class PayloadTooLargeError(LoopsError):
    pass


class RateLimitError(LoopsError):
    def __init__(self, retry_after: float | None = None) -> None:
        super().__init__("Loops rate limit exceeded; no retry attempted")
        self.retry_after = retry_after


class TransportError(LoopsError):
    """One attempt failed; a mutation may have reached the provider."""


class InvalidResponseError(LoopsError):
    pass


def _id(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 256
        or any(not (c.isascii() and (c.isalnum() or c in "_-")) for c in value)
    ):
        raise ValueError("invalid Loops resource identity")
    return quote(value, safe="")


def _retry_after(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        if value.isascii() and value.isdigit():
            return min(float(value), 86400.0)
        stamp = parsedate_to_datetime(value)
        if stamp.tzinfo is None:
            return None
        return min(max(0.0, (stamp - datetime.now(UTC)).total_seconds()), 86400.0)
    except ValueError, TypeError, OverflowError:
        return None


class LoopsClient:
    def __init__(
        self,
        api_key: str,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
    ) -> None:
        if (
            not isinstance(api_key, str)
            or not api_key
            or len(api_key) > 8192
            or any(ord(c) < 33 or ord(c) > 126 for c in api_key)
        ):
            raise ValueError("invalid injected Loops API key")
        if (
            type(timeout) not in (int, float)
            or not math.isfinite(timeout)
            or not 0 < timeout <= 60
        ):
            raise ValueError("timeout must be finite and within 60 seconds")
        self._http = httpx.Client(
            base_url="https://app.loops.so/api/",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )
        self._attempts: deque[float] = deque()
        self._lock = threading.Lock()

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _reserve_attempt(self) -> None:
        # Conservative per-client bound. Broker must aggregate across keys for
        # a team; this cannot infer that different keys belong to the same team.
        with self._lock:
            now = time.monotonic()
            while self._attempts and now - self._attempts[0] >= 60:
                self._attempts.popleft()
            if len(self._attempts) >= 60:
                raise RateLimitError(max(0.0, 60 - (now - self._attempts[0])))
            self._attempts.append(now)

    def _request[T](
        self, method: str, path: str, result_type: type[T], *, body=None, params=None
    ) -> T:
        if body is not None:
            try:
                encoded = json.dumps(body, allow_nan=False).encode("utf-8")
            except ValueError, TypeError:
                raise ValueError("invalid Loops request data") from None
            if len(encoded) > 2_000_000:
                raise ValueError("Loops request exceeds byte bound")
        self._reserve_attempt()
        try:
            with self._http.stream(
                method, f"v1/{path}", json=body, params=params
            ) as response:
                status = response.status_code
                error = {
                    401: AuthenticationError,
                    403: AuthenticationError,
                    404: NotFoundError,
                    409: RevisionConflictError,
                    413: PayloadTooLargeError,
                }.get(status)
                if error is not None:
                    raise error(f"Loops request refused ({status})")
                if status == 429:
                    raise RateLimitError(
                        _retry_after(response.headers.get("Retry-After"))
                    )
                if not 200 <= status < 300:
                    # Includes redirects: never forward the credential elsewhere.
                    raise LoopsError(f"Loops request refused ({status})")
                content = bytearray()
                for chunk in response.iter_bytes(chunk_size=65536):
                    if len(content) + len(chunk) > 8_000_000:
                        raise InvalidResponseError("Loops response exceeds byte bound")
                    content.extend(chunk)
            data = json.loads(content)
            if (
                isinstance(data, dict)
                and "success" in data
                and data["success"] is not True
            ):
                raise InvalidResponseError("Loops response did not confirm success")
            return TypeAdapter(result_type).validate_python(data, strict=True)
        except httpx.HTTPError:
            raise TransportError(
                "Loops transport failed; outcome may be unknown"
            ) from None
        except ValueError:
            raise InvalidResponseError("Loops returned invalid response data") from None

    def test_api_key(self) -> Account:
        return self._request("GET", "api-key", Account)

    def create_campaign(self, name: str) -> Campaign:
        if not isinstance(name, str) or not name.strip() or len(name) > 1024:
            raise ValueError("campaign name is required and bounded")
        result = self._request("POST", "campaigns", Campaign, body={"name": name})
        if result.status != "Draft":
            raise InvalidResponseError("new campaign is not a draft")
        return result

    def get_campaign(self, campaign_id: str) -> Campaign:
        result = self._request("GET", f"campaigns/{_id(campaign_id)}", Campaign)
        if result.id != campaign_id:
            raise InvalidResponseError("campaign identity mismatch")
        return result

    def get_email_message(self, email_message_id: str) -> EmailMessage:
        result = self._request(
            "GET", f"email-messages/{_id(email_message_id)}", EmailMessage
        )
        if result.id != email_message_id:
            raise InvalidResponseError("email message identity mismatch")
        return result

    def update_email_message(
        self,
        email_message_id: str,
        expected_revision_id: str,
        subject: str,
        preview_text: str,
        from_name: str,
        from_email: str,
        lmx: str,
    ) -> EmailMessage:
        update = EmailUpdate(
            expected_revision_id=expected_revision_id,
            subject=subject,
            preview_text=preview_text,
            from_name=from_name,
            from_email=from_email,
            lmx=lmx,
        )
        result = self._request(
            "POST",
            f"email-messages/{_id(email_message_id)}",
            EmailMessage,
            body=update.model_dump(by_alias=True),
        )
        if result.id != email_message_id:
            raise InvalidResponseError("email message identity mismatch")
        return result

    def update_campaign_audience(
        self,
        campaign_id: str,
        *,
        mailing_list_id: str | None = None,
        audience_segment_id: str | None = None,
        audience_filter: AudienceFilter | None = None,
    ) -> Campaign:
        update = AudienceUpdate(
            mailing_list_id=mailing_list_id,
            audience_segment_id=audience_segment_id,
            audience_filter=audience_filter,
        )
        result = self._request(
            "POST",
            f"campaigns/{_id(campaign_id)}",
            Campaign,
            body={
                key: value
                for key, value in update.model_dump(by_alias=True).items()
                if value is not None
            },
        )
        if result.id != campaign_id:
            raise InvalidResponseError("campaign identity mismatch")
        return result

    def list_themes(self, *, cursor: str | None = None) -> ThemePage:
        return self._request(
            "GET", "themes", ThemePage, params={"cursor": cursor} if cursor else None
        )

    def list_mailing_lists(self) -> list[MailingList]:
        return self._request("GET", "lists", list[MailingList])

    def create_upload(self, content_type: str, content_length: int) -> UploadTicket:
        if content_type not in {"image/jpeg", "image/png", "image/gif", "image/webp"}:
            raise ValueError("unsupported upload content type")
        if type(content_length) is not int or not 0 < content_length <= 4_000_000:
            raise ValueError("upload size must be within 4000000 bytes")
        # Returns the ticket only. Never send an API credential to its signed URL.
        return self._request(
            "POST",
            "uploads",
            UploadTicket,
            body={
                "contentType": content_type,
                "contentLength": content_length,
            },
        )

    def complete_upload(self, email_asset_id: str) -> UploadedAsset:
        result = self._request(
            "POST", f"uploads/{_id(email_asset_id)}/complete", UploadedAsset
        )
        if result.email_asset_id != email_asset_id:
            raise InvalidResponseError("upload identity mismatch")
        return result

    def _save_contact(self, operation: str, contact: ContactUpdate) -> ContactSaved:
        if not isinstance(contact, ContactUpdate):
            raise TypeError("contact must be a ContactUpdate")
        body = contact.model_dump(
            by_alias=True, exclude_none=True, exclude={"properties"}
        )
        body.update(contact.properties)
        return self._request(
            "POST" if operation == "create" else "PUT",
            f"contacts/{operation}",
            ContactSaved,
            body=body,
        )

    def create_contact(self, contact: ContactUpdate) -> ContactSaved:
        return self._save_contact("create", contact)

    def update_contact(self, contact: ContactUpdate) -> ContactSaved:
        """Provider upsert; caller owns consent and any subscribed=True decision."""
        return self._save_contact("update", contact)

    def find_contact(self, email: str) -> list[Contact]:
        identity = ContactUpdate(email=email)
        result = self._request(
            "GET", "contacts/find", list[Contact], params={"email": identity.email}
        )
        if any(contact.email != email for contact in result):
            raise InvalidResponseError("contact identity mismatch")
        return result

    def unsubscribe_contact(self, email: str) -> ContactSaved:
        return self.update_contact(ContactUpdate(email=email, subscribed=False))

    def check_suppression(self, email: str) -> Suppression:
        identity = ContactUpdate(email=email)
        result = self._request(
            "GET", "contacts/suppression", Suppression, params={"email": identity.email}
        )
        if result.contact.email != email:
            raise InvalidResponseError("contact identity mismatch")
        return result
