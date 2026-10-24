# Copyright (c) 2026 Rod Rivera
# SPDX-License-Identifier: MIT
# Adapted from zeroemployeeorg/zeocore@25a9c899c17ac6cdf54f4949e54b0fcc800cce91
# Source: src/zeo_core/integrations/kit/models.py
# MIT permission notice retained in package LICENSE; provenance in NOTICE.
"""Read-only migration requests and selected data-only provider fields."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Id = Annotated[int, Field(gt=0, strict=True)]
SubscriberState = Literal["active", "inactive", "bounced", "complained", "cancelled"]
SubscriberStatus = Literal[
    "active", "inactive", "bounced", "complained", "cancelled", "all"
]
FormStatus = Literal["active", "archived", "trashed", "all"]


class PageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    per_page: int = Field(default=50, ge=1, le=1000)
    after: str | None = Field(default=None, min_length=1, max_length=2048)


class ReadRecord(BaseModel):
    # Return selected typed data, never form embed scripts or arbitrary markup.
    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)
    id: Id


class Subscriber(ReadRecord):
    state: SubscriberState
    email_address: str
    first_name: str | None
    fields: dict[str, str | None]


class Tag(ReadRecord):
    name: str


class Form(ReadRecord):
    name: str
    type: Literal["embed", "hosted"]
    archived: bool


class CustomField(ReadRecord):
    name: str
    key: str
    label: str


class Page(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    results: list[dict[str, Any]]
    next_after: str | None
    complete: bool
