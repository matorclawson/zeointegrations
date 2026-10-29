"""Bounded, credentialless Mastodon publishing client.

Copyright 2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
Original implementation from the primary API documentation; no SDK required.
"""

from __future__ import annotations

import math
import re
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from io import RawIOBase
from urllib.parse import urlsplit

from .models import (
    BoundTransport,
    InstanceLimits,
    MastodonError,
    MediaUpload,
    PublishedStatus,
    ReadyMedia,
    Response,
    Visibility,
)

_ID = re.compile(r"[0-9]+\Z")
_TRANSIENT = {429, 500, 502, 503, 504}


def _origin(value: str) -> str:
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
            or any(c.isspace() or ord(c) < 32 for c in value)
            or "\\" in value
        ):
            raise ValueError
        port = parsed.port
        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
        if ":" in hostname:
            hostname = f"[{hostname}]"
        return "https://" + hostname + (f":{port}" if port not in (None, 443) else "")
    except (ValueError, UnicodeError, AttributeError):
        raise MastodonError("ORIGIN") from None


def _id(value: object) -> str:
    if not isinstance(value, str) or len(value) > 100 or not _ID.fullmatch(value):
        raise MastodonError("RESPONSE")
    return value


def _resource_url(value: object) -> str:
    if not isinstance(value, str):
        raise MastodonError("RESPONSE")
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or any(c.isspace() or ord(c) < 32 for c in value)
            or "\\" in value
        ):
            raise ValueError
        _ = parsed.port
    except ValueError:
        raise MastodonError("RESPONSE") from None
    return value


def _positive(data: Mapping[str, object], name: str) -> int:
    value = data.get(name)
    if type(value) is not int or value <= 0:
        raise MastodonError("CONFIGURATION")
    return value


def _mapping(value: object, code: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise MastodonError(code)
    return value


def _duration(value: float) -> float:
    if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
        raise MastodonError("POLICY")
    return value


class _UploadReader(RawIOBase):
    """Bounded chunks, never a whole-media buffer; does not own caller stream."""

    def __init__(self, upload: MediaUpload, check_deadline: Callable[[], float]):
        self._source = upload.stream
        self._remaining = upload.size
        self._check_deadline = check_deadline

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        if self.closed:
            raise MastodonError("UPLOAD_READ")
        self._check_deadline()
        amount = min(65536, self._remaining, size if size >= 0 else 65536)
        if amount == 0:
            return b""
        data = self._source.read(amount)
        if not isinstance(data, bytes) or not 0 < len(data) <= amount:
            raise MastodonError("UPLOAD_READ")
        self._remaining -= len(data)
        if self._remaining == 0 and self._source.read(1):
            raise MastodonError("UPLOAD_SIZE")
        self._check_deadline()
        return data


class MastodonClient:
    """No default transport. A Connect adapter must be injected explicitly.

    Deadlines and byte/attempt ceilings are caller policy, not provider quotas.
    A client instance is synchronous; its transport owns shared admission.
    """

    def __init__(
        self,
        transport: BoundTransport,
        *,
        origin: str,
        max_upload_bytes: int,
        timeout_seconds: float = 30.0,
        request_timeout_seconds: float = 10.0,
        poll_interval_seconds: float = 1.0,
        max_read_attempts: int = 30,
        monotonic: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.origin = _origin(origin)
        if _origin(transport.origin) != self.origin or not transport.binding:
            raise MastodonError("BINDING")
        if type(max_upload_bytes) is not int or max_upload_bytes <= 0:
            raise MastodonError("POLICY")
        if type(max_read_attempts) is not int or max_read_attempts <= 0:
            raise MastodonError("POLICY")
        self._transport = transport
        self._binding = transport.binding
        self._max_upload_bytes = max_upload_bytes
        self._timeout = _duration(timeout_seconds)
        self._request_timeout = _duration(request_timeout_seconds)
        self._poll_interval = _duration(poll_interval_seconds)
        self._max_reads = max_read_attempts
        self._now, self._wall, self._sleep = monotonic, wall_clock, sleep
        self._limits: InstanceLimits | None = None
        self._not_before = 0.0

    def _binding_check(self) -> None:
        if (
            _origin(self._transport.origin) != self.origin
            or self._transport.binding != self._binding
        ):
            raise MastodonError("BINDING")

    def _remaining(self, deadline: float) -> float:
        remaining = deadline - self._now()
        if remaining <= 0:
            raise MastodonError("DEADLINE")
        return remaining

    def _wait(self, delay: float, deadline: float) -> None:
        if delay >= self._remaining(deadline):
            raise MastodonError("DEADLINE")
        if delay > 0:
            self._sleep(delay)
        self._remaining(deadline)

    def _rate_delay(self, headers: Mapping[str, str]) -> float:
        selected = {k.lower(): v for k, v in headers.items()}
        delays = [0.0]
        retry = selected.get("retry-after")
        reset = selected.get("x-ratelimit-reset")
        for value, numeric in (
            (retry, True),
            (reset if selected.get("x-ratelimit-remaining") == "0" else None, False),
        ):
            if value is None:
                continue
            try:
                try:
                    delay = float(value) if numeric else float("nan")
                except ValueError:
                    delay = float("nan")
                if not math.isfinite(delay):
                    try:
                        stamp = parsedate_to_datetime(value)
                    except ValueError:
                        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    if stamp.tzinfo is None:
                        stamp = stamp.replace(tzinfo=UTC)
                    delay = stamp.timestamp() - self._wall()
                if math.isfinite(delay):
                    delays.append(max(0.0, delay))
            except (ValueError, TypeError, OverflowError):
                raise MastodonError("RATE_HEADERS") from None
        return max(delays)

    def _request(
        self,
        method: str,
        path: str,
        deadline: float,
        *,
        fields: Mapping[str, str | bool | list[str]] | None = None,
        upload: MediaUpload | None = None,
        key: str | None = None,
    ) -> Response:
        self._binding_check()
        self._wait(max(0.0, self._not_before - self._now()), deadline)
        timeout = min(self._request_timeout, self._remaining(deadline))
        try:
            response = self._transport.request(
                method,
                path,
                fields=fields,
                upload=upload,
                headers={"Idempotency-Key": key} if key is not None else {},
                timeout_seconds=timeout,
            )
        except Exception:
            raise MastodonError("TRANSPORT", outcome_unknown=method == "POST") from None
        if not isinstance(response, Response):
            raise MastodonError("RESPONSE", outcome_unknown=method == "POST")
        try:
            self._binding_check()
            if response.redirected or _origin(response.origin) != self.origin:
                raise MastodonError("ORIGIN")
            if type(response.status) is not int:
                raise MastodonError("RESPONSE")
            delay = self._rate_delay(response.headers)
            self._not_before = max(self._not_before, self._now() + delay)
            self._remaining(deadline)
        except MastodonError as error:
            raise MastodonError(error.code, outcome_unknown=method == "POST") from None
        except Exception:
            raise MastodonError("RESPONSE", outcome_unknown=method == "POST") from None
        if response.status in (401, 403):
            raise MastodonError("AUTH")
        if 300 <= response.status < 400:
            raise MastodonError("REDIRECT", outcome_unknown=method == "POST")
        return response

    def _get(self, path: str, deadline: float, *, media: bool = False) -> Response:
        for attempt in range(self._max_reads):
            response = self._request("GET", path, deadline)
            if response.status == 200 or (media and response.status == 206):
                return response
            if response.status not in _TRANSIENT:
                raise MastodonError("PROCESSING" if media else "REJECTED")
            if attempt + 1 < self._max_reads:
                self._wait(self._poll_interval, deadline)
        raise MastodonError("READ_ATTEMPTS")

    def _discover(self, deadline: float) -> InstanceLimits:
        response = self._get("/api/v2/instance", deadline)
        data = _mapping(response.body, "CONFIGURATION")
        config = _mapping(data.get("configuration"), "CONFIGURATION")
        statuses = _mapping(config.get("statuses"), "CONFIGURATION")
        media = _mapping(config.get("media_attachments"), "CONFIGURATION")
        mimes = media.get("supported_mime_types")
        if (
            not isinstance(mimes, list)
            or not mimes
            or any(not isinstance(m, str) or not m for m in mimes)
        ):
            raise MastodonError("CONFIGURATION")
        self._limits = InstanceLimits(
            _positive(statuses, "max_characters"),
            _positive(statuses, "max_media_attachments"),
            _positive(statuses, "characters_reserved_per_url"),
            tuple(mimes),
            _positive(media, "image_size_limit"),
            _positive(media, "video_size_limit"),
            _positive(media, "description_limit"),
        )
        return self._limits

    def discover_limits(self) -> InstanceLimits:
        """Explicit discovery refreshes the per-binding cache."""
        return self._discover(self._now() + self._timeout)

    def _ready(self, response: Response, expected_id: str | None = None) -> ReadyMedia:
        data = _mapping(response.body, "RESPONSE")
        identity = _id(data.get("id"))
        if expected_id is not None and identity != expected_id:
            raise MastodonError("RESPONSE")
        if data.get("type") not in ("image", "video", "gifv", "audio"):
            raise MastodonError("PROCESSING")
        return ReadyMedia(
            identity, _resource_url(data.get("url")), self.origin, self._binding
        )

    def _poll(self, identity: str, deadline: float) -> ReadyMedia:
        for attempt in range(self._max_reads):
            response = self._request("GET", f"/api/v1/media/{identity}", deadline)
            if response.status == 200:
                return self._ready(response, identity)
            if response.status == 206:
                data = _mapping(response.body, "RESPONSE")
                if _id(data.get("id")) != identity:
                    raise MastodonError("RESPONSE")
            elif response.status not in _TRANSIENT:
                raise MastodonError("PROCESSING")
            if attempt + 1 < self._max_reads:
                self._wait(self._poll_interval, deadline)
        raise MastodonError("PROCESSING_ATTEMPTS")

    def upload_media(self, upload: MediaUpload) -> ReadyMedia:
        """Check size before POST, then stream bounded chunks without replay."""
        deadline = self._now() + self._timeout
        limits = self._limits or self._discover(deadline)
        if upload.mime_type not in limits.supported_mime_types:
            raise MastodonError("MIME")
        # GIF/audio mapping to image/video caps is not established by the API
        # configuration descriptions. Refuse instead of guessing a global cap.
        if upload.mime_type.startswith("image/") and upload.mime_type != "image/gif":
            provider_cap = limits.image_size_limit
        elif upload.mime_type.startswith("video/"):
            provider_cap = limits.video_size_limit
        else:
            raise MastodonError("UNSUPPORTED_MEDIA")
        if (
            type(upload.size) is not int
            or not 0 < upload.size <= min(provider_cap, self._max_upload_bytes)
            or not upload.filename
            or any(c in upload.filename for c in ("\r", "\n", "\x00", "/", "\\", '"'))
            or len(upload.description) > limits.description_limit
        ):
            raise MastodonError("UPLOAD")
        # Verify seekable input length without buffering. Connect must supply a
        # stable, digest-verified staged object; arbitrary non-seekable caller
        # streams are refused until its UploadSource bridge is agreed.
        try:
            if not upload.stream.seekable():
                raise MastodonError("UPLOAD_SOURCE")
            start = upload.stream.tell()
            end = upload.stream.seek(0, 2)
            upload.stream.seek(start)
            if end - start != upload.size:
                raise MastodonError("UPLOAD_SIZE")
        except MastodonError:
            raise
        except Exception:
            raise MastodonError("UPLOAD_SOURCE") from None
        staged = _UploadReader(upload, lambda: self._remaining(deadline))
        try:
            response = self._request(
                "POST",
                "/api/v2/media",
                deadline,
                upload=MediaUpload(
                    staged,
                    upload.size,
                    upload.filename,
                    upload.mime_type,
                    upload.description,
                ),
                fields={"description": upload.description},
            )
        finally:
            staged.close()
        if response.status not in (200, 202):
            self._post_error(response)
        try:
            if response.status == 200:
                return self._ready(response)
            identity = _id(_mapping(response.body, "RESPONSE").get("id"))
        except MastodonError:
            raise MastodonError("RESPONSE", outcome_unknown=True) from None
        return self._poll(identity, deadline)

    @staticmethod
    def _post_error(response: Response) -> None:
        raise MastodonError(
            "RATE_LIMIT" if response.status == 429 else "REJECTED",
            outcome_unknown=response.status >= 500 or response.status < 400,
        )

    def publish_status(
        self,
        *,
        text: str,
        visibility: Visibility,
        idempotency_key: str,
        media: Sequence[ReadyMedia] = (),
        spoiler_text: str = "",
        sensitive: bool = False,
        language: str | None = None,
    ) -> PublishedStatus:
        deadline = self._now() + self._timeout
        limits = self._limits or self._discover(deadline)
        if (
            visibility not in ("public", "unlisted", "private", "direct")
            or not idempotency_key
            or len(idempotency_key) > 256
            or any(ord(c) < 33 or ord(c) > 126 for c in idempotency_key)
            or not isinstance(text, str)
            or not isinstance(spoiler_text, str)
            or type(sensitive) is not bool
            or (not text.strip() and not media)
            or len(media) > limits.max_media_attachments
            or (language is not None and not re.fullmatch(r"[a-z]{2}", language))
        ):
            raise MastodonError("STATUS")
        # Conservative upper bound, not exact Mastodon grapheme/link counting:
        # retain every code point and add the URL reservation for each possible
        # dotted/scheme link. This deliberately refuses some valid borderline text.
        combined = text + spoiler_text
        possible_links = sum(combined.count(c) for c in (".", "。", "．", "｡", "://"))
        bound = len(combined) + possible_links * limits.characters_reserved_per_url
        if bound > limits.max_characters:
            raise MastodonError("STATUS_SIZE")
        ids = []
        for item in media:
            if item.origin != self.origin or item.binding != self._binding:
                raise MastodonError("BINDING")
            identity = _id(item.id)
            if identity in ids:
                raise MastodonError("STATUS")
            # Recheck even a caller-constructed ReadyMedia; a dataclass is no
            # capability proof, and no unverified external media ID is published.
            self._poll(identity, deadline)
            ids.append(identity)
        fields: dict[str, str | bool | list[str]] = {
            "status": text,
            "visibility": visibility,
            "spoiler_text": spoiler_text,
            "sensitive": sensitive,
        }
        if ids:
            fields["media_ids[]"] = ids
        if language is not None:
            fields["language"] = language
        response = self._request(
            "POST", "/api/v1/statuses", deadline, fields=fields, key=idempotency_key
        )
        if response.status != 200:
            self._post_error(response)
        try:
            data = _mapping(response.body, "RESPONSE")
            return PublishedStatus(_id(data.get("id")), _resource_url(data.get("url")))
        except MastodonError:
            raise MastodonError("RESPONSE", outcome_unknown=True) from None
