"""Provider publishing calls, intended for Connect's claimed execution callbacks.

Copyright 2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
Each method makes at most one network call. Persist each returned provider ID
before advancing a workflow. Credentials, approvals, scheduling, binding checks
and durable claims belong to the host. No automatic retries or polling loops.
"""

from __future__ import annotations

import json
import re
from datetime import UTC
from email.utils import format_datetime, parsedate_to_datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from zeo_integrations._http import IntegrationError, Request, Transport
from zeo_integrations._http.runtime import _bounded, _url


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class TextPost(Input):
    text: str = Field(min_length=1, max_length=3000)


class LinkedInPost(TextPost):
    # Provider-owned URNs from a completed, account-bound upload.
    media_urns: list[str] = Field(default_factory=list, max_length=20)
    media_title: str = Field(default="", max_length=200)


class Carousel(Input):
    children: list[str] = Field(min_length=2, max_length=10)
    caption: str = Field(default="", max_length=2200)


class CarouselItem(Input):
    media_type: Literal["IMAGE", "VIDEO"]
    media_url: str = Field(min_length=1, max_length=4096)
    alt_text: str = Field(default="", max_length=1000)


class InstagramMedia(Input):
    media_type: Literal["IMAGE", "REELS"]
    media_url: str = Field(min_length=1, max_length=4096)
    caption: str = Field(default="", max_length=2200)


class ThreadsMedia(Input):
    media_type: Literal["TEXT", "IMAGE", "VIDEO"]
    text: str = Field(min_length=1, max_length=500)
    media_url: str | None = Field(default=None, max_length=4096)


def _id(value):
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z0-9_-]{1,200}", value) is None
    ):
        raise IntegrationError("PROVIDER_ID")
    return value


class PublishingResponseError(IntegrationError):
    """Bounded provider failure facts; never retain provider messages or bodies."""

    def __init__(
        self,
        *,
        http_status,
        provider_code,
        provider_subcode,
        retry_after,
        definite_refusal,
        effect,
    ):
        super().__init__(
            "PROVIDER_REJECTED" if definite_refusal else "PROVIDER_UNCONFIRMED",
            outcome_unknown=effect and not definite_refusal,
        )
        self.http_status = http_status
        self.provider_code = provider_code
        self.provider_subcode = provider_subcode
        self.retry_after = retry_after
        self.definite_refusal = definite_refusal


def _graph_failure(response, *, effect):
    error = None
    try:
        document = json.loads(response.body)
        _bounded(document, 1048576)
        if isinstance(document, dict) and isinstance(document.get("error"), dict):
            error = document["error"]
    except Exception:
        pass

    def number(name):
        value = error.get(name) if error else None
        return value if type(value) is int and 0 <= value <= 2147483647 else None

    provider_code, subcode = number("code"), number("error_subcode")
    retry_after = next(
        (v for k, v in response.headers.items() if k.lower() == "retry-after"), None
    )
    if not isinstance(retry_after, str) or not 1 <= len(retry_after) <= 200:
        retry_after = None
    elif re.fullmatch(r"[0-9]{1,10}", retry_after):
        retry_after = str(int(retry_after))
    else:
        try:
            date = parsedate_to_datetime(retry_after)
            if date.tzinfo is None:
                raise ValueError("timezone required")
            retry_after = format_datetime(date.astimezone(UTC), usegmt=True)
        except (TypeError, ValueError, OverflowError):
            retry_after = None
    # Require a structured Graph rejection. A server failure, timeout, conflict
    # or malformed answer remains ambiguous for writes, even with an HTTP status.
    definite = (
        provider_code is not None
        and provider_code not in {1, 2}
        and error.get("is_transient") is not True
        and response.status
        in {
            400,
            401,
            403,
            404,
            405,
            410,
            413,
            415,
            422,
            429,
        }
    )
    return PublishingResponseError(
        http_status=response.status,
        provider_code=provider_code,
        provider_subcode=subcode,
        retry_after=retry_after,
        definite_refusal=definite,
        effect=effect,
    )


class _Client:
    provider: str
    origin: str

    def __init__(self, transport: Transport, *, media_origins: tuple[str, ...] = ()):
        self.transport = transport
        if any(_url(origin) != origin for origin in media_origins):
            raise IntegrationError("MEDIA_ORIGIN")
        self.media_origins = frozenset(media_origins)

    def _media(self, value):
        if _url(value) not in self.media_origins:
            raise IntegrationError("MEDIA_ORIGIN")
        return value

    def _call(
        self,
        operation,
        path,
        *,
        key,
        effect,
        admitted=False,
        body=None,
        method="POST",
        query=None,
        headers=None,
        form=False,
    ):
        if effect and admitted is not True:
            raise IntegrationError("EFFECT_ADMISSION_REQUIRED")
        if (
            not isinstance(key, str)
            or re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", key) is None
        ):
            raise IntegrationError("IDEMPOTENCY_KEY")
        _bounded(body, 1048576)
        failure = "PUBLISH_UNCONFIRMED"
        # A dispatched write remains uncertain on any invalid or missing receipt.
        try:
            response = self.transport.request(
                Request(
                    provider=self.provider,
                    operation=operation,
                    method=method,
                    url=self.origin + path,
                    query=query or {},
                    headers=headers or {},
                    json_body=None if form else body,
                    form_body=body if form else None,
                    idempotency_key=key,
                    timeout_seconds=30,
                    max_response_bytes=1048576,
                    effect=effect,
                )
            )
            if _url(response.url) != self.origin or len(response.body) > 1048576:
                raise IntegrationError("PROVIDER_RESPONSE")
            if not 200 <= response.status < 300:
                raise _graph_failure(response, effect=effect)
            document = json.loads(response.body) if response.body else {}
            _bounded(document, 1048576)
            if not isinstance(document, dict):
                raise IntegrationError("PROVIDER_RESPONSE")
            if self.provider == "tiktok":
                error = document.get("error")
                if not isinstance(error, dict) or error.get("code") != "ok":
                    raise IntegrationError("PROVIDER_REJECTED")
            elif "error" in document:
                raise _graph_failure(response, effect=effect)
            return document, {k.lower(): v for k, v in response.headers.items()}
        except PublishingResponseError:
            raise
        except Exception as exc:
            if isinstance(exc, IntegrationError):
                failure = exc.code
        raise IntegrationError(failure, outcome_unknown=effect)

    @staticmethod
    def _receipt(document, field, *, effect):
        value = document.get(field)
        if not isinstance(value, str) or not value or len(value) > 200:
            raise IntegrationError("INVALID_RECEIPT", outcome_unknown=effect)
        return value

    def _identity(self, path, *, key):
        document, _ = self._call(
            "identity",
            path,
            key=key,
            effect=False,
            method="GET",
            query={"fields": "id,username"},
        )
        account = self._receipt(document, "id", effect=False)
        username = self._receipt(document, "username", effect=False)
        if account != self.account_id:
            raise IntegrationError("ACCOUNT_BINDING")
        return {"account_id": account, "username": username}

    def read_post(self, post_id, *, key):
        """Read an already host-bound post ID; this does not identify a lost write."""
        post_id = _id(post_id)
        document, _ = self._call(
            "read_post",
            f"{self.prefix}/{post_id}",
            key=key,
            effect=False,
            method="GET",
            query={"fields": "id,username,permalink,timestamp"},
        )
        if self._receipt(document, "id", effect=False) != post_id:
            raise IntegrationError("POST_BINDING")
        permalink = document.get("permalink")
        if not isinstance(permalink, str) or len(permalink) > 4096:
            raise IntegrationError("INVALID_RECEIPT")
        _url(permalink)
        return {
            "post_id": post_id,
            "username": self._receipt(document, "username", effect=False),
            "permalink": permalink,
            "timestamp": self._receipt(document, "timestamp", effect=False),
        }


class InstagramPublisher(_Client):
    provider, origin = "instagram", "https://graph.facebook.com"

    def __init__(
        self, transport, *, account_id: str, api_version: str, media_origins=()
    ):
        super().__init__(transport, media_origins=media_origins)
        self.account_id = _id(account_id)
        if re.fullmatch(r"v[0-9]{1,2}\.0", api_version) is None:
            raise IntegrationError("API_VERSION")
        self.prefix = "/" + api_version

    def identity(self, *, key):
        """Check credential access to the host-selected professional account."""
        return self._identity(f"{self.prefix}/{self.account_id}", key=key)

    def create_container(self, media: InstagramMedia, *, key, allow_effect=False):
        media = InstagramMedia.model_validate(media.model_dump())
        body = {"caption": media.caption}
        if media.media_type == "IMAGE":
            body["image_url"] = self._media(media.media_url)
        else:
            body.update(media_type="REELS", video_url=self._media(media.media_url))
        doc, _ = self._call(
            "create_container",
            f"{self.prefix}/{self.account_id}/media",
            key=key,
            effect=True,
            admitted=allow_effect,
            body=body,
            form=True,
        )
        return {
            "container_id": self._receipt(doc, "id", effect=True),
            "stage": "processing",
        }

    def container_status(self, container_id, *, key):
        doc, _ = self._call(
            "container_status",
            f"{self.prefix}/{_id(container_id)}",
            key=key,
            effect=False,
            method="GET",
            query={"fields": "status_code"},
        )
        status = self._receipt(doc, "status_code", effect=False)
        if status not in {"IN_PROGRESS", "FINISHED", "ERROR", "EXPIRED", "PUBLISHED"}:
            raise IntegrationError("INVALID_RECEIPT")
        return {"container_id": container_id, "provider_status": status}

    def create_carousel_item(self, item: CarouselItem, *, key, allow_effect=False):
        item = CarouselItem.model_validate(item.model_dump())
        body = {"is_carousel_item": "true"}
        body["image_url" if item.media_type == "IMAGE" else "video_url"] = self._media(
            item.media_url
        )
        if self.provider == "threads" or item.media_type == "VIDEO":
            body["media_type"] = item.media_type
        if item.alt_text and item.media_type == "IMAGE":
            body["alt_text"] = item.alt_text
        doc, _ = self._call(
            "create_carousel_item",
            f"{self.prefix}/{self.account_id}/media",
            key=key,
            effect=True,
            admitted=allow_effect,
            body=body,
            form=True,
        )
        return {
            "container_id": self._receipt(doc, "id", effect=True),
            "stage": "processing",
        }

    def create_carousel(self, carousel: Carousel, *, key, allow_effect=False):
        carousel = Carousel.model_validate(carousel.model_dump())
        if self.provider == "threads" and len(carousel.caption) > 500:
            raise IntegrationError("TEXT_LIMIT")
        children = [_id(child) for child in carousel.children]
        if len(set(children)) != len(children):
            raise IntegrationError("DUPLICATE_MEDIA")
        doc, _ = self._call(
            "create_carousel",
            f"{self.prefix}/{self.account_id}/media",
            key=key,
            effect=True,
            admitted=allow_effect,
            form=True,
            body={
                "media_type": "CAROUSEL",
                "children": ",".join(children),
                "caption": carousel.caption,
            },
        )
        return {
            "container_id": self._receipt(doc, "id", effect=True),
            "stage": "processing",
        }

    def publish_container(self, container_id, *, key, allow_effect=False):
        doc, _ = self._call(
            "publish_container",
            f"{self.prefix}/{self.account_id}/media_publish",
            key=key,
            effect=True,
            admitted=allow_effect,
            body={"creation_id": _id(container_id)},
            form=True,
        )
        return {"post_id": self._receipt(doc, "id", effect=True), "stage": "published"}


class ThreadsPublisher(_Client):
    provider, origin = "threads", "https://graph.threads.net"

    def __init__(
        self, transport, *, account_id: str, api_version: str, media_origins=()
    ):
        super().__init__(transport, media_origins=media_origins)
        self.account_id = _id(account_id)
        if re.fullmatch(r"v[0-9]{1,2}\.0", api_version) is None:
            raise IntegrationError("API_VERSION")
        self.prefix = "/" + api_version

    def identity(self, *, key):
        """Confirm the authenticated Threads user matches the pinned subject."""
        return self._identity(f"{self.prefix}/me", key=key)

    def create_container(self, post: ThreadsMedia, *, key, allow_effect=False):
        post = ThreadsMedia.model_validate(post.model_dump())
        body = {"text": post.text, "media_type": post.media_type}
        if post.media_type != "TEXT":
            if post.media_url is None:
                raise IntegrationError("MEDIA_REQUIRED")
            body["image_url" if post.media_type == "IMAGE" else "video_url"] = (
                self._media(post.media_url)
            )
        elif post.media_url is not None:
            raise IntegrationError("UNEXPECTED_MEDIA")
        doc, _ = self._call(
            "create_container",
            f"{self.prefix}/{self.account_id}/threads",
            key=key,
            effect=True,
            admitted=allow_effect,
            body=body,
            form=True,
        )
        return {
            "container_id": self._receipt(doc, "id", effect=True),
            "stage": "processing",
        }

    def create_carousel_item(self, item: CarouselItem, *, key, allow_effect=False):
        item = CarouselItem.model_validate(item.model_dump())
        body = {"is_carousel_item": "true"}
        body["image_url" if item.media_type == "IMAGE" else "video_url"] = self._media(
            item.media_url
        )
        if self.provider == "threads" or item.media_type == "VIDEO":
            body["media_type"] = item.media_type
        if item.alt_text and item.media_type == "IMAGE":
            body["alt_text"] = item.alt_text
        doc, _ = self._call(
            "create_carousel_item",
            f"{self.prefix}/{self.account_id}/threads",
            key=key,
            effect=True,
            admitted=allow_effect,
            body=body,
            form=True,
        )
        return {
            "container_id": self._receipt(doc, "id", effect=True),
            "stage": "processing",
        }

    def create_carousel(self, carousel: Carousel, *, key, allow_effect=False):
        carousel = Carousel.model_validate(carousel.model_dump())
        if self.provider == "threads" and len(carousel.caption) > 500:
            raise IntegrationError("TEXT_LIMIT")
        children = [_id(child) for child in carousel.children]
        if len(set(children)) != len(children):
            raise IntegrationError("DUPLICATE_MEDIA")
        doc, _ = self._call(
            "create_carousel",
            f"{self.prefix}/{self.account_id}/threads",
            key=key,
            effect=True,
            admitted=allow_effect,
            form=True,
            body={
                "media_type": "CAROUSEL",
                "children": ",".join(children),
                "text": carousel.caption,
            },
        )
        return {
            "container_id": self._receipt(doc, "id", effect=True),
            "stage": "processing",
        }

    def container_status(self, container_id, *, key):
        doc, _ = self._call(
            "container_status",
            f"{self.prefix}/{_id(container_id)}",
            key=key,
            effect=False,
            method="GET",
            query={"fields": "status"},
        )
        status = self._receipt(doc, "status", effect=False)
        if status not in {"IN_PROGRESS", "FINISHED", "ERROR", "EXPIRED", "PUBLISHED"}:
            raise IntegrationError("INVALID_RECEIPT")
        return {"container_id": container_id, "provider_status": status}

    def publish_container(self, container_id, *, key, allow_effect=False):
        doc, _ = self._call(
            "publish_container",
            f"{self.prefix}/{self.account_id}/threads_publish",
            key=key,
            effect=True,
            admitted=allow_effect,
            body={"creation_id": _id(container_id)},
            form=True,
        )
        return {"post_id": self._receipt(doc, "id", effect=True), "stage": "published"}


class LinkedInPublisher(_Client):
    provider, origin = "linkedin", "https://api.linkedin.com"

    def __init__(self, transport, *, author: str, api_version: str):
        super().__init__(transport)
        if re.fullmatch(r"urn:li:(person|organization):[A-Za-z0-9_-]+", author) is None:
            raise IntegrationError("ACCOUNT_BINDING")
        if re.fullmatch(r"20[0-9]{2}(0[1-9]|1[0-2])", api_version) is None:
            raise IntegrationError("API_VERSION")
        self.author, self.api_version = author, api_version

    def initialize_image_upload(self, *, key, allow_effect=False):
        doc, _ = self._call(
            "initialize_image_upload",
            "/rest/images",
            key=key,
            effect=True,
            admitted=allow_effect,
            query={"action": "initializeUpload"},
            headers={
                "Linkedin-Version": self.api_version,
                "X-Restli-Protocol-Version": "2.0.0",
            },
            body={"initializeUploadRequest": {"owner": self.author}},
        )
        value = doc.get("value")
        if not isinstance(value, dict):
            raise IntegrationError("INVALID_RECEIPT", outcome_unknown=True)
        image = self._receipt(value, "image", effect=True)
        url = value.get("uploadUrl")
        if (
            re.fullmatch(r"urn:li:image:[A-Za-z0-9_-]+", image) is None
            or not isinstance(url, str)
            or len(url) > 4096
        ):
            raise IntegrationError("INVALID_RECEIPT", outcome_unknown=True)
        invalid = False
        try:
            invalid = _url(url) != "https://www.linkedin.com"
        except Exception:
            invalid = True
        if invalid:
            raise IntegrationError("UPLOAD_ORIGIN", outcome_unknown=True)
        return {"image_urn": image, "upload_url": url, "stage": "awaiting_upload"}

    def image_status(self, image_urn, *, key):
        from urllib.parse import quote

        if re.fullmatch(r"urn:li:image:[A-Za-z0-9_-]+", image_urn) is None:
            raise IntegrationError("MEDIA_ID")
        doc, _ = self._call(
            "image_status",
            "/rest/images/" + quote(image_urn, safe=""),
            key=key,
            effect=False,
            method="GET",
            headers={
                "Linkedin-Version": self.api_version,
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )
        if doc.get("id") != image_urn or doc.get("owner") != self.author:
            raise IntegrationError("MEDIA_IDENTITY")
        return {
            "image_urn": image_urn,
            "provider_status": self._receipt(doc, "status", effect=False),
        }

    def read_post(self, post_id, *, key):
        """Read an already bound post; this cannot discover a lost publish ID."""
        from urllib.parse import quote

        if re.fullmatch(r"urn:li:(share|ugcPost):[0-9]+", post_id) is None:
            raise IntegrationError("MEDIA_ID")
        doc, _ = self._call(
            "read_post",
            "/rest/posts/" + quote(post_id, safe=""),
            key=key,
            effect=False,
            method="GET",
            query={"viewContext": "AUTHOR"},
            headers={
                "Linkedin-Version": self.api_version,
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )
        if doc.get("id") != post_id or doc.get("author") != self.author:
            raise IntegrationError("POST_BINDING")
        return {
            "post_id": post_id,
            "author": self.author,
            "provider_status": self._receipt(doc, "lifecycleState", effect=False),
        }

    def publish(
        self, post: TextPost | LinkedInPost, *, key: str, allow_effect: bool = False
    ):
        post = LinkedInPost.model_validate(post.model_dump())
        content = None
        if post.media_urns:
            for urn in post.media_urns:
                if (
                    re.fullmatch(r"urn:li:(image|video|document):[A-Za-z0-9_-]+", urn)
                    is None
                ):
                    raise IntegrationError("MEDIA_ID")
            if len(post.media_urns) > 1:
                if not all(urn.startswith("urn:li:image:") for urn in post.media_urns):
                    raise IntegrationError("MULTI_IMAGE_REQUIRED")
                content = {
                    "multiImage": {"images": [{"id": urn} for urn in post.media_urns]}
                }
            else:
                content = {
                    "media": {"id": post.media_urns[0], "title": post.media_title}
                }
        _, headers = self._call(
            "publish",
            "/rest/posts",
            key=key,
            effect=True,
            admitted=allow_effect,
            headers={
                "Linkedin-Version": self.api_version,
                "X-Restli-Protocol-Version": "2.0.0",
            },
            body={
                "author": self.author,
                "commentary": post.text,
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
                **({"content": content} if content else {}),
            },
        )
        post_id = self._receipt(headers, "x-restli-id", effect=True)
        if re.fullmatch(r"urn:li:(share|ugcPost):[0-9]+", post_id) is None:
            raise IntegrationError("INVALID_RECEIPT", outcome_unknown=True)
        return {"post_id": post_id, "stage": "published"}
