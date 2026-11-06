"""Bounded DB-API execution with injected connections, no credential custody.

Copyright 2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from zeo_integrations._http import IntegrationError


class Query(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    statement: str = Field(min_length=1, max_length=65536)
    parameters: list[JsonValue] = Field(default_factory=list, max_length=1000)
    maximum_rows: int = Field(default=100, ge=1, le=10000)


class Connection(Protocol):
    def cursor(self) -> Any: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class Client:
    """One transaction per call. Caller owns connection close and statement timeout.

    Arbitrary SQL is always an effect: SELECT can invoke mutating functions.
    Connect must admit the statement and durably reconcile its idempotency key.
    The DB role must enforce privileges; this class is not a SQL firewall.
    """

    def __init__(self, connection: Connection, *, max_bytes: int = 1048576):
        if type(max_bytes) is not int or not 1 <= max_bytes <= 16777216:
            raise IntegrationError("POLICY")
        self.connection = connection
        self.max_bytes = max_bytes

    def execute(self, query: Query, *, allow_effect: bool = False):
        if allow_effect is not True:
            raise IntegrationError("EFFECT_ADMISSION_REQUIRED")
        query = Query.model_validate(query.model_dump())
        cursor = self.connection.cursor()
        dispatched = False
        failure = None
        try:
            dispatched = True
            cursor.execute(query.statement, query.parameters)
            columns = [str(d[0]) for d in (cursor.description or ())]
            rows = list(cursor.fetchmany(query.maximum_rows + 1)) if columns else []
            truncated = len(rows) > query.maximum_rows
            result = {
                "columns": columns,
                "rows": rows[: query.maximum_rows],
                "truncated": truncated,
            }
            # Refuse oversized or non-JSON data before committing effects.
            encoded = json.dumps(result, allow_nan=False).encode()
            if len(encoded) > self.max_bytes:
                raise ValueError
            self.connection.commit()
        except Exception:
            failure = True
            try:
                self.connection.rollback()
            except Exception:
                pass
        finally:
            try:
                cursor.close()
            except Exception:
                failure = True
        if failure:
            raise IntegrationError("DATABASE", outcome_unknown=dispatched)
        return result


__all__ = ["Client", "Connection", "Query"]
