"""Immutable X thread values and pure step planning; no approval or I/O.

Copyright2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
"""

import hashlib
import json
from dataclasses import dataclass

from zeo_integrations._http import IntegrationError

from . import XPost, _x_id, _x_outbound_id

PREVIEW_MAX_BYTES = 6000
THREAD_MAX_POSTS = 25


def _canonical(value):
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (UnicodeError, TypeError, ValueError):
        raise IntegrationError("THREAD_VALUE") from None


@dataclass(frozen=True, slots=True)
class XThreadPost:
    text: str
    media_ids: tuple[str, ...] = ()
    reply_to_prior_index: int | None = None

    def __post_init__(self):
        if type(self.text) is not str or len(self.text) > 280:
            raise IntegrationError("THREAD_VALUE")
        if type(self.media_ids) is not tuple or len(self.media_ids) > 4:
            raise IntegrationError("THREAD_VALUE")
        if not self.text.strip() and not self.media_ids:
            raise IntegrationError("POST_CONTENT")
        for value in self.media_ids:
            _x_outbound_id(value)
        if len(set(self.media_ids)) != len(self.media_ids):
            raise IntegrationError("DUPLICATE_MEDIA")
        _canonical(self.text)
        i = self.reply_to_prior_index
        if i is not None and (type(i) is not int or not 0 <= i < THREAD_MAX_POSTS):
            raise IntegrationError("THREAD_REPLY_LINK")


@dataclass(frozen=True, slots=True)
class XThreadStep:
    index: int
    request_digest: str
    returned_id: str | None = None

    def __post_init__(self):
        if type(self.index) is not int or not 0 <= self.index < THREAD_MAX_POSTS:
            raise IntegrationError("THREAD_STATE")
        if (
            type(self.request_digest) is not str
            or len(self.request_digest) != 64
            or any(c not in "0123456789abcdef" for c in self.request_digest)
        ):
            raise IntegrationError("THREAD_STATE")
        if self.returned_id is not None and self.returned_id != "UNKNOWN":
            _x_id(self.returned_id)


@dataclass(frozen=True, slots=True)
class XThread:
    account_id: str
    posts: tuple[XThreadPost, ...]

    def __post_init__(self):
        _x_id(self.account_id)
        if (
            type(self.posts) is not tuple
            or not 1 <= len(self.posts) <= THREAD_MAX_POSTS
        ):
            raise IntegrationError("THREAD_VALUE")
        for i, post in enumerate(self.posts):
            if type(post) is not XThreadPost:
                raise IntegrationError("THREAD_VALUE")
            link = post.reply_to_prior_index
            if link != (i - 1 if i else None):
                raise IntegrationError("THREAD_REPLY_LINK")
        if len(self.rendering().encode("utf-8")) > PREVIEW_MAX_BYTES:
            raise IntegrationError("THREAD_PREVIEW_LIMIT")

    def rendering(self):
        """Complete canonical preview; callers must display it whole, never cut."""
        return _canonical(
            {
                "account_id": self.account_id,
                "posts": [
                    {
                        "text": p.text,
                        "media_ids": list(p.media_ids),
                        "reply_to_prior_index": p.reply_to_prior_index,
                    }
                    for p in self.posts
                ],
                "provider": "x",
                "version": 1,
            }
        ).decode("utf-8")

    @property
    def digest(self):
        """Content binding, not an approval token or provider deduplication key."""
        return hashlib.sha256(self.rendering().encode("utf-8")).hexdigest()

    def _request(self, index, states):
        item = self.posts[index]
        reply = None
        if item.reply_to_prior_index is not None:
            reply = _x_outbound_id(states[item.reply_to_prior_index].returned_id)
        post = XPost(text=item.text, media_ids=list(item.media_ids), reply_to_id=reply)
        body = {"text": post.text}
        if post.media_ids:
            body["media"] = {"media_ids": post.media_ids}
        if reply is not None:
            body["reply"] = {"in_reply_to_tweet_id": reply}
        document = {
            "thread_digest": self.digest,
            "index": index,
            "account_id": self.account_id,
            "provider": "x",
            "method": "POST",
            "path": "/2/tweets",
            "body": body,
        }
        return post, hashlib.sha256(_canonical(document)).hexdigest()

    def next_index(self, states: tuple[XThreadStep, ...]):
        """Only trusted persisted records may be supplied. UNKNOWN never advances."""
        if type(states) is not tuple or len(states) > len(self.posts):
            raise IntegrationError("THREAD_STATE")
        for i, state in enumerate(states):
            if type(state) is not XThreadStep or state.index != i:
                raise IntegrationError("THREAD_STATE")
        for i, state in enumerate(states):
            _, expected = self._request(i, states)
            if state.request_digest != expected:
                raise IntegrationError("THREAD_REQUEST_BINDING")
            if state.returned_id is None or state.returned_id == "UNKNOWN":
                return None
        if len(states) == len(self.posts):
            return None
        index = len(states)
        link = self.posts[index].reply_to_prior_index
        if link is not None and len(states[link].returned_id) > 19:
            return None  # Receipt is preserved, but the outbound schema cannot use it.
        return index

    def next_step(self, states: tuple[XThreadStep, ...]):
        """Return a post plus an unconfirmed step to persist BEFORE dispatch."""
        index = self.next_index(states)
        if index is None:
            return None
        post, digest = self._request(index, states)
        return post, XThreadStep(index=index, request_digest=digest)
