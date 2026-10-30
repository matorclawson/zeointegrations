"""Credentialless, one-call receive/ACK adapter for agreed Connect operations.

Copyright 2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
Original implementation; no Telegram SDK or direct provider transport.
"""

from __future__ import annotations

import json
import math
import time
from collections.abc import Callable
from typing import cast

from pydantic import JsonValue, ValidationError
from zeo_core.integrations.hosted.client import (
    HostedConnectionClient,
    HostedOperationRequest,
    HostedOperationResponse,
)

from .models import (
    DurablePrefixVerifier,
    TelegramAcknowledgement,
    TelegramBatch,
    TelegramCondition,
    TelegramError,
    TelegramRetention,
    TelegramUpdate,
)

_CONDITION_CODES = {
    TelegramCondition.RECEIVE_CONFLICT: "REQUEST_REFUSED",
    TelegramCondition.LEASE_LOST: "REQUEST_REFUSED",
    TelegramCondition.CURSOR_INVALID: "REQUEST_REFUSED",
    TelegramCondition.TRANSIENT_REPLAY: "REQUEST_REFUSED",
    TelegramCondition.RATE_LIMITED: "RATE_LIMITED",
    TelegramCondition.CONNECTION_NOT_USABLE: "CONNECTION_REPAIR_REQUIRED",
}


def _text(value: object, maximum: int) -> str:
    if not isinstance(value, str) or not value:
        raise TelegramError("INVALID_SHAPE")
    try:
        invalid = len(value.encode("utf-8")) > maximum
    except UnicodeError:
        raise TelegramError("INVALID_SHAPE") from None
    if invalid or any(ord(char) < 32 for char in value):
        raise TelegramError("INVALID_SHAPE")
    return value


def _integer(value: object, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise TelegramError("INVALID_SHAPE")
    return value


def _object(value: object, keys: set[str]) -> dict[str, JsonValue]:
    if not isinstance(value, dict) or set(value) != keys:
        raise TelegramError("INVALID_SHAPE")
    return cast(dict[str, JsonValue], value)


class TelegramClient:
    """Receive slice only; does not send messages, poll in a loop or own a DB.

    The injected hosted transport must enforce its configured call deadline
    and response-byte ceiling. Local checks before/after invoke cannot cancel
    a blocking transport. No timeout is invented in the pinned Core request.
    """

    def __init__(
        self,
        client: HostedConnectionClient,
        *,
        connection_id: str,
        consumers: tuple[str, ...],
        verifier: DurablePrefixVerifier,
        max_response_bytes: int = 1_048_576,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._connection_id = _text(connection_id, 200)
        if not consumers or type(consumers) is not tuple:
            raise TelegramError("CONSUMER_CONFIGURATION")
        self._consumers = tuple(_text(consumer, 200) for consumer in consumers)
        if len(set(self._consumers)) != len(self._consumers):
            raise TelegramError("CONSUMER_CONFIGURATION")
        self._max_bytes = _integer(max_response_bytes, 1)
        self._client = client
        self._verifier = verifier
        self._clock = clock
        self._bot_id: int | None = None
        self._last_batch: TelegramBatch | None = None
        self._pending_ack: tuple[TelegramBatch, str] | None = None

    def _invoke(
        self,
        operation: str,
        arguments: dict[str, JsonValue],
        key: str,
        deadline: float,
        *,
        effect: bool,
    ) -> HostedOperationResponse:
        _text(key, 200)
        if (
            isinstance(deadline, bool)
            or not isinstance(deadline, (float, int))
            or not math.isfinite(deadline)
            or not math.isfinite(self._clock())
            or self._clock() >= deadline
        ):
            raise TelegramError("DEADLINE")
        request = HostedOperationRequest(
            connection_id=self._connection_id,
            operation_id=operation,
            arguments=arguments,
            idempotency_key=key,
        )
        # No expect: it is absent from the Broker's pinned Core 0.12.0.
        try:
            response = self._client.invoke(request)
            if not isinstance(response, HostedOperationResponse):
                raise ValueError
            response = HostedOperationResponse.model_validate(response.model_dump())
            encoded = json.dumps(
                response.model_dump(mode="json"), allow_nan=False
            ).encode("utf-8")
            if len(encoded) > self._max_bytes:
                raise ValueError
        except Exception:
            raise TelegramError("UNAVAILABLE", outcome_unknown=effect) from None
        if not math.isfinite(self._clock()) or self._clock() >= deadline:
            raise TelegramError("DEADLINE", outcome_unknown=effect)
        receipt = response.receipt or {}
        replayed = receipt.get("replayed", False)
        if type(replayed) is not bool:
            raise TelegramError("INVALID_RECEIPT", outcome_unknown=effect)
        condition = None
        retry_after = None
        if "condition" not in receipt:
            raise TelegramError("INVALID_RECEIPT", outcome_unknown=effect)
        if receipt["condition"] is not None:
            try:
                condition = TelegramCondition(receipt["condition"])
            except (ValueError, TypeError):
                raise TelegramError("UNKNOWN_CONDITION", outcome_unknown=effect) from None
            error = response.normalized_error
            if error is None or error.code.value != _CONDITION_CODES[condition]:
                raise TelegramError("INVALID_RECEIPT", outcome_unknown=effect)
            if condition is TelegramCondition.TRANSIENT_REPLAY and not replayed:
                raise TelegramError("INVALID_RECEIPT", outcome_unknown=effect)
            if condition is TelegramCondition.RATE_LIMITED:
                retry_after = _integer(receipt.get("retry_after_seconds"))
        if response.status.value != "confirmed":
            raise TelegramError(
                response.status.value.upper(),
                outcome_unknown=response.status.value == "ambiguous",
                condition=condition,
                retry_after_seconds=retry_after,
            )
        if condition is not None:
            raise TelegramError("INVALID_RECEIPT", outcome_unknown=effect)
        if replayed and not effect:
            raise TelegramError("REPLAY_WITHOUT_BATCH")
        if response.artifact is not None or not isinstance(response.result, dict):
            raise TelegramError("INVALID_RESULT", outcome_unknown=effect)
        return response

    def read_updates(
        self, *, idempotency_key: str, deadline: float, maximum: int = 100
    ) -> TelegramBatch:
        if type(maximum) is not int or not 1 <= maximum <= 100:
            raise TelegramError("READ_LIMIT")
        response = self._invoke(
            "telegram.updates.read",
            {"max": maximum},
            idempotency_key,
            deadline,
            effect=False,
        )
        result = _object(
            response.result,
            {
                "bot_id", "fence", "batch_cursor", "updates",
                "retention", "lost_to_retention",
            },
        )
        bot_id = _integer(result["bot_id"], 1)
        if self._bot_id is not None and bot_id != self._bot_id:
            raise TelegramError("BOT_CHANGED")
        fence = _integer(result["fence"])
        cursor = result["batch_cursor"]
        if cursor is not None:
            cursor = _text(cursor, 4096)
        rows = result["updates"]
        if not isinstance(rows, list) or len(rows) > maximum:
            raise TelegramError("INVALID_BATCH")
        updates = []
        previous = -1
        for row in rows:
            if not isinstance(row, dict):
                raise TelegramError("INVALID_UPDATE")
            kinds = set(row) - {"update_id"}
            if len(kinds) != 1 or not kinds <= {"message", "callback_query"}:
                raise TelegramError("UNSUPPORTED_UPDATE")
            kind = next(iter(kinds))
            update_id = _integer(row.get("update_id"))
            if update_id <= previous or not isinstance(row[kind], dict):
                raise TelegramError("INVALID_UPDATE")
            previous = update_id
            updates.append(
                TelegramUpdate(
                    update_id, kind, json.dumps(row[kind], ensure_ascii=True)
                )
            )
        if updates and cursor is None:
            raise TelegramError("MISSING_CURSOR")
        retention = _object(
            result["retention"], {"state", "oldest_unacknowledged_age_seconds"}
        )
        state = retention["state"]
        if state not in ("ok", "warn", "critical", "expired"):
            raise TelegramError("INVALID_RETENTION")
        age = retention["oldest_unacknowledged_age_seconds"]
        if age is not None:
            age = _integer(age)
        lost = result["lost_to_retention"]
        if type(lost) is not bool:
            raise TelegramError("INVALID_RETENTION")
        batch = TelegramBatch(
            bot_id, fence, cursor, tuple(updates),
            TelegramRetention(str(state), age, lost),
        )
        self._bot_id = bot_id
        self._last_batch = batch
        return batch

    def acknowledge(
        self, batch: TelegramBatch, *, idempotency_key: str, deadline: float
    ) -> TelegramAcknowledgement:
        pending = self._pending_ack
        if pending is not None:
            if batch is not pending[0] or idempotency_key != pending[1]:
                raise TelegramError("RECONCILE_ORIGINAL")
        elif batch is not self._last_batch:
            raise TelegramError("UNISSUED_BATCH")
        if not batch.updates or batch.batch_cursor is None:
            raise TelegramError("EMPTY_PREFIX")
        try:
            durable = self._verifier.is_durably_handled(
                batch=batch,
                consumers=self._consumers,
            )
        except Exception:
            raise TelegramError("DURABILITY_UNKNOWN") from None
        if durable is not True:
            raise TelegramError("PREFIX_NOT_DURABLE")
        try:
            response = self._invoke(
                "telegram.updates.acknowledge",
                {"batch_cursor": batch.batch_cursor},
                idempotency_key,
                deadline,
                effect=True,
            )
            result = _object(response.result, {"acknowledged", "confirmed_cursor"})
            if result["acknowledged"] is not True:
                raise TelegramError("INVALID_ACK", outcome_unknown=True)
            cursor = _text(result["confirmed_cursor"], 4096)
        except TelegramError as error:
            if error.code in {
                "INVALID_SHAPE", "INVALID_ACK", "INVALID_RECEIPT",
                "UNKNOWN_CONDITION", "INVALID_RESULT",
            }:
                error.outcome_unknown = True
            if error.outcome_unknown:
                self._pending_ack = (batch, idempotency_key)
            raise
        except (ValidationError, ValueError, TypeError):
            self._pending_ack = (batch, idempotency_key)
            raise TelegramError("INVALID_ACK", outcome_unknown=True) from None
        self._pending_ack = None
        self._last_batch = None
        return TelegramAcknowledgement(cursor, response.replayed)
