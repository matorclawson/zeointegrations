"""Original Mastodon publishing values. Copyright 2026 Zero Employee Organizations.

SPDX-License-Identifier: MIT
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Protocol

Visibility = Literal["public", "unlisted", "private", "direct"]


class MastodonError(RuntimeError):
    """Sanitized failure; outcome_unknown forbids automatic write replay."""

    def __init__(self, code: str, *, outcome_unknown: bool = False) -> None:
        super().__init__(f"Mastodon request failed: {code}")
        self.code = code
        self.outcome_unknown = outcome_unknown


@dataclass(frozen=True)
class InstanceLimits:
    max_characters: int
    max_media_attachments: int
    characters_reserved_per_url: int
    supported_mime_types: tuple[str, ...]
    image_size_limit: int
    video_size_limit: int
    description_limit: int


class UploadSource(Protocol):
    """Broker-created, size/digest-verified staged object; never seek it.

    Connect verifies the complete object before any POST and owns its lifetime.
    This provider-local structural port neither opens staging URLs nor owns
    custody. read(n) must return at most n bytes, with b"" only at EOF.
    """

    @property
    def size(self) -> int: ...

    @property
    def sha256(self) -> str: ...

    @property
    def mime(self) -> str: ...

    @property
    def filename(self) -> str: ...

    def read(self, n: int) -> bytes: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class MediaUpload:
    source: UploadSource
    description: str

    @property
    def stream(self) -> UploadSource:
        return self.source

    @property
    def size(self) -> int:
        return self.source.size

    @property
    def filename(self) -> str:
        return self.source.filename

    @property
    def mime_type(self) -> str:
        return self.source.mime


@dataclass(frozen=True)
class ReadyMedia:
    id: str
    url: str
    origin: str
    binding: str


@dataclass(frozen=True)
class PublishedStatus:
    id: str
    url: str


@dataclass(frozen=True)
class Response:
    """Adapter supplies final origin and redirect observation, never credentials."""

    status: int
    body: object
    origin: str
    headers: Mapping[str, str]
    redirected: bool = False


class BoundTransport(Protocol):
    """Connect-owned, one-attempt, no-redirect adapter; no credential interface.

    The adapter enforces origin/identity admission, disables ambient proxies,
    bounds responses and injects auth inside custody. It sanitizes exceptions.
    Client request paths/headers cannot override those guarantees.
    """

    @property
    def origin(self) -> str: ...

    @property
    def binding(self) -> str: ...

    def request(
        self,
        method: str,
        path: str,
        *,
        fields: Mapping[str, str | bool | list[str]] | None,
        upload: UploadSource | None,
        headers: Mapping[str, str],
        timeout_seconds: float,
    ) -> Response: ...
