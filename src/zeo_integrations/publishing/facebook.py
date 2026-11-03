"""Explicit Facebook Page calls; host owns Page credentials and admission.

Copyright 2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
Original implementation; protocol references in docs/facebook-provenance.json.
"""

import re
from urllib.parse import parse_qsl, urlsplit

from pydantic import Field

from zeo_integrations._http import IntegrationError
from zeo_integrations._http.runtime import _url

from . import Input, PublishingResponseError, _Client


class FacebookPagePost(Input):
    # Conservative local caps, not provider eligibility or weighted limits.
    message: str = Field(default="", max_length=10000)
    link: str | None = Field(default=None, min_length=1, max_length=4096)


class FacebookPagePhoto(Input):
    image_url: str = Field(min_length=1, max_length=4096)
    caption: str = Field(default="", max_length=10000)
    alt_text: str = Field(default="", max_length=1000)


def _object_id(value, *, effect=False):
    if type(value) is not str or re.fullmatch(r"[1-9][0-9]{0,39}", value) is None:
        raise IntegrationError("FACEBOOK_ID", outcome_unknown=effect)
    return value


class FacebookPagePublisher(_Client):
    """One explicit request per step; no token flow, file read or retry."""

    provider, origin = "facebook", "https://graph.facebook.com"

    def __init__(
        self, transport, *, page_id, api_version, media_origins=(), link_origins=()
    ):
        super().__init__(transport, media_origins=media_origins)
        self.page_id = _object_id(page_id)
        if (
            type(api_version) is not str
            or re.fullmatch(r"v[1-9][0-9]?\.0", api_version) is None
        ):
            raise IntegrationError("API_VERSION")
        self.prefix = "/" + api_version
        if any(_url(origin) != origin for origin in link_origins):
            raise IntegrationError("LINK_ORIGIN")
        self.link_origins = frozenset(link_origins)

    def _failure(self, response, *, effect):
        error = super()._failure(response, effect=effect)
        # This initial Page client has no endpoint-specific no-mutation proof.
        # A Graph rejection must not automatically permit a second publish.
        return PublishingResponseError(
            http_status=error.http_status,
            provider_code=error.provider_code,
            provider_subcode=error.provider_subcode,
            retry_after=error.retry_after,
            definite_refusal=error.definite_refusal and not effect,
            effect=effect,
        )

    @staticmethod
    def _document(document, *, effect):
        if ("errors" in document and document["errors"] != []) or document.get(
            "success"
        ) is False:
            raise IntegrationError("FACEBOOK_RECEIPT", outcome_unknown=effect)
        return document

    def _post_id(self, value, *, effect=False):
        if type(value) is not str:
            raise IntegrationError("FACEBOOK_ID", outcome_unknown=effect)
        parts = value.split("_")
        if len(parts) == 1:
            return _object_id(value, effect=effect)
        if len(parts) != 2:
            raise IntegrationError("FACEBOOK_ID", outcome_unknown=effect)
        for part in parts:
            _object_id(part, effect=effect)
        if parts[0] != self.page_id:
            raise IntegrationError("PAGE_BINDING", outcome_unknown=effect)
        return value

    def _author(self, document):
        author = document.get("from")
        if not isinstance(author, dict) or _object_id(author.get("id")) != self.page_id:
            raise IntegrationError("PAGE_BINDING")

    def identity(self, *, key):
        """Verify the injected token's subject is the selected Page, not a user."""
        doc, _ = self._call(
            "identity",
            self.prefix + "/me",
            key=key,
            effect=False,
            method="GET",
            query={"fields": "id,name"},
            expected_status=200,
        )
        self._document(doc, effect=False)
        if _object_id(doc.get("id")) != self.page_id:
            raise IntegrationError("PAGE_BINDING")
        name = doc.get("name")
        if name is not None and (type(name) is not str or not 1 <= len(name) <= 500):
            raise IntegrationError("FACEBOOK_RECEIPT")
        return {"page_id": self.page_id, "name": name}

    def publish(self, post: FacebookPagePost, *, key, allow_effect=False):
        post = FacebookPagePost.model_validate(post.model_dump())
        if not post.message.strip() and post.link is None:
            raise IntegrationError("POST_CONTENT")
        body = {"message": post.message, "published": "true"}
        if post.link is not None:
            if _url(post.link) not in self.link_origins:
                raise IntegrationError("LINK_ORIGIN")
            body["link"] = post.link
        doc, _ = self._call(
            "publish",
            f"{self.prefix}/{self.page_id}/feed",
            key=key,
            effect=True,
            admitted=allow_effect,
            body=body,
            form=True,
            expected_status=200,
        )
        self._document(doc, effect=True)
        return {
            "post_id": self._post_id(doc.get("id"), effect=True),
            "stage": "created",
        }

    def publish_photo(self, photo: FacebookPagePhoto, *, key, allow_effect=False):
        photo = FacebookPagePhoto.model_validate(photo.model_dump())
        body = {
            "url": self._media(photo.image_url),
            "caption": photo.caption,
            "published": "true",
        }
        if photo.alt_text:
            body["alt_text_custom"] = photo.alt_text
        doc, _ = self._call(
            "publish_photo",
            f"{self.prefix}/{self.page_id}/photos",
            key=key,
            effect=True,
            admitted=allow_effect,
            body=body,
            form=True,
            expected_status=200,
        )
        self._document(doc, effect=True)
        return {
            "photo_id": _object_id(doc.get("id"), effect=True),
            "stage": "photo_created",
        }

    def read_photo(self, photo_id, *, key):
        """Resolve a host-bound photo's Page story, without guessing from its ID."""
        photo_id = _object_id(photo_id)
        doc, _ = self._call(
            "read_photo",
            f"{self.prefix}/{photo_id}",
            key=key,
            effect=False,
            method="GET",
            query={"fields": "id,from,page_story_id"},
            expected_status=200,
        )
        self._document(doc, effect=False)
        if _object_id(doc.get("id")) != photo_id:
            raise IntegrationError("PHOTO_BINDING")
        self._author(doc)
        story = doc.get("page_story_id")
        return {
            "photo_id": photo_id,
            "post_id": self._post_id(story) if story is not None else None,
        }

    def read_post(self, post_id, *, key):
        """Read only a stored, host-bound ID; not reconciliation for a lost write."""
        post_id = self._post_id(post_id)
        doc, _ = self._call(
            "read_post",
            f"{self.prefix}/{post_id}",
            key=key,
            effect=False,
            method="GET",
            query={"fields": "id,from,is_published,permalink_url"},
            expected_status=200,
        )
        self._document(doc, effect=False)
        if self._post_id(doc.get("id")) != post_id:
            raise IntegrationError("POST_BINDING")
        self._author(doc)
        published = doc.get("is_published")
        if type(published) is not bool:
            raise IntegrationError("FACEBOOK_RECEIPT")
        link = doc.get("permalink_url")
        if link is not None:
            if type(link) is not str or not 1 <= len(link) <= 4096:
                raise IntegrationError("FACEBOOK_RECEIPT")
            _url(link)
            if any(
                any(
                    word in name.lower()
                    for word in ("token", "secret", "password", "authorization")
                )
                for name, _ in parse_qsl(urlsplit(link).query)
            ):
                raise IntegrationError("FACEBOOK_RECEIPT")
            if urlsplit(link).hostname not in {
                "facebook.com",
                "www.facebook.com",
                "m.facebook.com",
            }:
                raise IntegrationError("POST_BINDING")
        return {
            "post_id": post_id,
            "page_id": self.page_id,
            "provider_is_published": published,
            "permalink": link,
        }
