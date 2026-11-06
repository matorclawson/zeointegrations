"""UID-based read-only IMAP over a host-owned authenticated session.

Copyright 2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
The host enforces socket deadlines and literal allocation limits. No login,
expunge, implicit Seen flag, arbitrary search language, or connection ownership.
"""

import base64
import re
import threading

from pydantic import BaseModel, ConfigDict, Field

from zeo_integrations._http import IntegrationError


class Mailbox(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    # ASCII IMAP mailbox wire name (modified UTF-7 for non-ASCII names).
    folder: str = Field(
        default="INBOX", min_length=1, max_length=255, pattern=r"^[\x20-\x7e]+$"
    )


class ListMessages(Mailbox):
    after_uid: int = Field(default=0, ge=0, le=4294967294)
    limit: int = Field(default=50, ge=1, le=200)


class GetMessage(Mailbox):
    uid: int = Field(ge=1, le=4294967295)
    uidvalidity: int = Field(ge=1, le=4294967295)
    max_bytes: int = Field(default=262144, ge=1, le=1048576)


def _quoted(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _ok(reply):
    status, data = reply
    if status != "OK":
        raise IntegrationError("IMAP_REFUSED")
    return data


class ImapClient:
    def __init__(self, imap):
        self.imap = imap
        self._lock = threading.Lock()

    def _select(self, folder):
        _ok(self.imap.select(_quoted(folder), readonly=True))
        kind, values = self.imap.response("UIDVALIDITY")
        if kind != "UIDVALIDITY" or len(values) != 1:
            raise IntegrationError("MAILBOX_IDENTITY")
        value = int(values[0])
        if not 0 < value <= 4294967295:
            raise IntegrationError("MAILBOX_IDENTITY")
        return value

    def _invoke(self, action):
        if not self._lock.acquire(blocking=False):
            raise IntegrationError("BUSY")
        failure = "IMAP_UNAVAILABLE"
        try:
            return action()
        except Exception as exc:
            if isinstance(exc, IntegrationError):
                failure = exc.code
        finally:
            self._lock.release()
        raise IntegrationError(failure)

    def list_messages(self, query: ListMessages):
        query = ListMessages.model_validate(query.model_dump())

        def read():
            validity = self._select(query.folder)
            rows = _ok(self.imap.uid("SEARCH", None, "UID", f"{query.after_uid + 1}:*"))
            if (
                len(rows) != 1
                or not isinstance(rows[0], bytes)
                or len(rows[0]) > 1048576
            ):
                raise IntegrationError("IMAP_RESPONSE")
            ids = [int(x) for x in rows[0].split()]
            if any(not 0 < uid <= 4294967295 for uid in ids):
                raise IntegrationError("IMAP_RESPONSE")
            ids = sorted(set(uid for uid in ids if uid > query.after_uid))
            selected = ids[: query.limit]
            return {
                "folder": query.folder,
                "uidvalidity": validity,
                "uids": selected,
                "has_more": len(ids) > query.limit,
                "next_after_uid": selected[-1] if selected else query.after_uid,
            }

        return self._invoke(read)

    def get_message(self, query: GetMessage):
        query = GetMessage.model_validate(query.model_dump())

        def read():
            if self._select(query.folder) != query.uidvalidity:
                raise IntegrationError("MAILBOX_CHANGED")
            rows = _ok(
                self.imap.uid(
                    "FETCH",
                    str(query.uid),
                    f"(UID RFC822.SIZE BODY.PEEK[]<0.{query.max_bytes + 1}>)",
                )
            )
            literals = [row for row in rows if isinstance(row, tuple)]
            if len(literals) != 1:
                raise IntegrationError("MESSAGE_NOT_FOUND")
            header, body = literals[0]
            uid = re.search(rb"\bUID (\d+)\b", header)
            size = re.search(rb"\bRFC822.SIZE (\d+)\b", header)
            if uid is None or int(uid[1]) != query.uid or size is None:
                raise IntegrationError("MESSAGE_IDENTITY")
            if not isinstance(body, bytes) or len(body) > query.max_bytes:
                raise IntegrationError("SIZE_LIMIT")
            if int(size[1]) != len(body):
                raise IntegrationError("MESSAGE_TRUNCATED")
            return {
                "folder": query.folder,
                "uidvalidity": query.uidvalidity,
                "uid": query.uid,
                "encoding": "base64",
                "media_type": "message/rfc822",
                "data": base64.b64encode(body).decode("ascii"),
            }

        return self._invoke(read)
