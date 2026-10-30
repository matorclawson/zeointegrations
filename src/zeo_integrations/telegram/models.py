"""Client-owned Telegram receive data, outside Core's unchanged hosted types.

Copyright 2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
Original implementation; contract provenance is recorded in NOTICE.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from pydantic import JsonValue


class TelegramCondition(StrEnum):
    RECEIVE_CONFLICT = "receive_conflict"
    LEASE_LOST = "lease_lost"
    CURSOR_INVALID = "cursor_invalid"
    RATE_LIMITED = "rate_limited"
    CONNECTION_NOT_USABLE = "connection_not_usable"
    RESULT_NOT_RETAINED = "result_not_retained"


class TelegramError(RuntimeError):
    """Sanitized disposition; never retains transport exceptions or raw content."""

    def __init__(
        self,
        code: str,
        *,
        outcome_unknown: bool = False,
        condition: TelegramCondition | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.outcome_unknown = outcome_unknown
        self.condition = condition
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True)
class TelegramUpdate:
    update_id: int
    kind: str
    _payload_json: str = field(repr=False)

    def payload(self) -> JsonValue:
        """Return a fresh copy: mutation cannot change the issued batch."""
        return json.loads(self._payload_json)


@dataclass(frozen=True)
class TelegramRetention:
    state: str
    oldest_unacknowledged_age_seconds: int | None
    lost_to_retention: bool


@dataclass(frozen=True)
class TelegramBatch:
    bot_id: int
    fence: int
    batch_cursor: str | None = field(repr=False)
    updates: tuple[TelegramUpdate, ...] = field(repr=False)
    retention: TelegramRetention

    @property
    def update_ids(self) -> tuple[int, ...]:
        return tuple(update.update_id for update in self.updates)


@dataclass(frozen=True)
class TelegramAcknowledgement:
    confirmed_cursor: str = field(repr=False)
    replayed: bool


class DurablePrefixVerifier(Protocol):
    """Trusted consumer-store adapter, not data received from Telegram.

    True attests ALL configured consumers durably handled this ordered batch
    prefix, including earlier deliveries. Storage failure/unknown must not
    return True. The implementation owns stable (bot_id, update_id) dedup,
    changed-payload conflicts, consumer routing and receiver authentication.
    The immutable batch includes the current payload for conflict checking;
    seeing a previously stored ID alone is not a durable disposition of it.
    """

    def is_durably_handled(
        self,
        *,
        batch: TelegramBatch,
        consumers: tuple[str, ...],
    ) -> bool: ...
