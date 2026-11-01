"""Durable editorial workflow over Core's hosted connection boundary.

Copyright 2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
These are local workflow persistence models, not a replacement Core wire contract.
A trusted host authenticates organization/actor access. Editorial approval is not
Broker authorization. Agenda/Runtime drives tick; this module starts no daemon.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from zeo_core.integrations.hosted.client import (
    HostedConnectionClient,
    HostedExpectedBinding,
    HostedOperationRequest,
    HostedOperationResponse,
)

from zeo_integrations._http.runtime import _bounded


class WorkflowError(ValueError):
    pass


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Asset(_Model):
    asset_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    media_type: str = Field(
        pattern=r"^(image/(jpeg|png|webp|gif)|video/mp4|application/pdf)$"
    )
    size_bytes: int = Field(ge=1, le=2_147_483_648)
    alt_text: str = Field(default="", max_length=4096)


class Step(_Model):
    step_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    operation_id: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,200}$")
    kind: Literal["read", "effect"]
    arguments: dict[str, Any]
    # Poll a read with a fresh observation key, until a field has an allowed value.
    wait_field: str | None = Field(default=None, max_length=100)
    ready_values: list[str] = Field(default_factory=list, max_length=10)
    pending_values: list[str] = Field(default_factory=list, max_length=10)
    poll_seconds: int = Field(default=60, ge=1, le=3600)
    max_polls: int = Field(default=60, ge=1, le=1000)

    @model_validator(mode="after")
    def polling_is_read_only(self):
        if self.wait_field and (self.kind != "read" or not self.ready_values):
            raise ValueError("polling needs a read and explicit ready values")
        if set(self.ready_values) & set(self.pending_values):
            raise ValueError("polling states overlap")
        return self


class Target(_Model):
    target_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")
    platform: str = Field(pattern=r"^[a-z_]{1,30}$")
    connection_id: str = Field(min_length=1, max_length=200)
    expect: HostedExpectedBinding
    caption: str = Field(default="", max_length=10000)
    asset_ids: list[str] = Field(default_factory=list, max_length=20)
    steps: list[Step] = Field(min_length=1, max_length=100)
    completion: Literal["published", "inbox_delivered"] = "published"


class Draft(_Model):
    title: str = Field(min_length=1, max_length=200)
    scheduled_at: AwareDatetime
    assets: list[Asset] = Field(default_factory=list, max_length=100)
    targets: list[Target] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def references(self):
        assets = {a.asset_id for a in self.assets}
        if len(assets) != len(self.assets):
            raise ValueError("duplicate asset")
        if len({t.target_id for t in self.targets}) != len(self.targets):
            raise ValueError("duplicate target")
        for target in self.targets:
            if not set(target.asset_ids) <= assets:
                raise ValueError("unknown target asset")
            seen = set()
            for step in target.steps:
                if step.step_id in seen:
                    raise ValueError("duplicate step")
                _check_arguments(step.arguments, seen, set(target.asset_ids))
                seen.add(step.step_id)
        return self


def _check_arguments(value, previous, assets):
    if isinstance(value, dict):
        if "$step" in value:
            if set(value) != {"$step", "field"} or value["$step"] not in previous:
                raise ValueError("step reference must point backwards")
            if not isinstance(value["field"], str):
                raise ValueError("invalid result field")
        elif "$asset" in value:
            if set(value) != {"$asset"} or value["$asset"] not in assets:
                raise ValueError("invalid media reference")
        else:
            for key, item in value.items():
                normalized = key.lower().replace("_", "").replace("-", "")
                if normalized in {
                    "authorization",
                    "cookie",
                    "apikey",
                    "token",
                    "secret",
                    "credentials",
                    "proxyauthorization",
                    "password",
                    "accesstoken",
                    "refreshtoken",
                    "clientsecret",
                }:
                    raise ValueError("credentials do not belong in a draft")
                _check_arguments(item, previous, assets)
    elif isinstance(value, list):
        for item in value:
            _check_arguments(item, previous, assets)


def _encoded(value):
    _bounded(value, 2_000_000)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _stamp(now):
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise WorkflowError("timezone required")
    return now.timestamp()


class WorkflowStore:
    """One host-owned SQLite journal; all keys and queries are organization scoped.

    Place this file in a private durable host directory. Public HTTP handlers must
    derive organization and actor from authentication, never from arbitrary input.
    """

    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS posts (
              org TEXT, id TEXT, revision INTEGER, document TEXT, digest TEXT,
              approved TEXT, cancelled INTEGER DEFAULT 0, started INTEGER DEFAULT 0,
              due REAL, PRIMARY KEY(org,id));
            CREATE TABLE IF NOT EXISTS targets (
              org TEXT, post TEXT, id TEXT, state TEXT, cursor INTEGER DEFAULT 0,
              polls INTEGER DEFAULT 0, next_at REAL DEFAULT 0, claim TEXT,
              lease REAL, request TEXT, outcome TEXT,
              PRIMARY KEY(org,post,id));
            CREATE TABLE IF NOT EXISTS receipts (
              org TEXT, post TEXT, target TEXT, step TEXT, result TEXT,
              PRIMARY KEY(org,post,target,step));
            CREATE TABLE IF NOT EXISTS events (
              seq INTEGER PRIMARY KEY AUTOINCREMENT, org TEXT, post TEXT,
              actor TEXT, event TEXT, detail TEXT);
            CREATE INDEX IF NOT EXISTS due_posts ON posts(org,due);
            """)

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _event(db, org, post, actor, event, detail=""):
        if not org or not post or not actor:
            raise WorkflowError("organization, post and actor are required")
        db.execute(
            "INSERT INTO events(org,post,actor,event,detail) VALUES (?,?,?,?,?)",
            (org, post, actor, event, detail),
        )

    def save(
        self,
        org: str,
        post: str,
        draft: Draft,
        *,
        actor: str,
        expected_revision: int = 0,
    ):
        draft = Draft.model_validate_json(draft.model_dump_json())
        document = _encoded(draft.model_dump(mode="json"))
        digest = hashlib.sha256(document.encode()).hexdigest()
        with self._db() as db:
            old = db.execute(
                "SELECT * FROM posts WHERE org=? AND id=?", (org, post)
            ).fetchone()
            if old and (old["started"] or old["cancelled"]):
                raise WorkflowError("started or cancelled occurrence is immutable")
            if (old["revision"] if old else 0) != expected_revision:
                raise WorkflowError("revision conflict")
            revision = expected_revision + 1
            db.execute(
                "INSERT OR REPLACE INTO posts VALUES (?,?,?,?,?,NULL,0,0,?)",
                (org, post, revision, document, digest, _stamp(draft.scheduled_at)),
            )
            db.execute("DELETE FROM targets WHERE org=? AND post=?", (org, post))
            for target in draft.targets:
                db.execute(
                    "INSERT INTO targets(org,post,id,state) VALUES (?,?,?,'ready')",
                    (org, post, target.target_id),
                )
            self._event(db, org, post, actor, "draft_saved", str(revision))
        return {"revision": revision, "digest": digest}

    def approve(self, org, post, *, actor, digest):
        with self._db() as db:
            row = db.execute(
                "SELECT * FROM posts WHERE org=? AND id=?", (org, post)
            ).fetchone()
            if not row or row["cancelled"] or row["digest"] != digest:
                raise WorkflowError("preview changed or unavailable")
            db.execute(
                "UPDATE posts SET approved=? WHERE org=? AND id=?", (digest, org, post)
            )
            self._event(db, org, post, actor, "editorial_approved", digest)

    def preview(self, org, post):
        with self._db() as db:
            row = db.execute(
                "SELECT * FROM posts WHERE org=? AND id=?", (org, post)
            ).fetchone()
            if not row:
                raise WorkflowError("post unavailable")
            targets = db.execute(
                "SELECT id,state,cursor,outcome FROM targets WHERE "
                "org=? AND post=? ORDER BY id",
                (org, post),
            ).fetchall()
            return {
                "post_id": post,
                "revision": row["revision"],
                "digest": row["digest"],
                "approved": row["approved"] == row["digest"],
                "cancelled": bool(row["cancelled"]),
                "draft": json.loads(row["document"]),
                "targets": [dict(t) for t in targets],
            }

    def calendar(self, org, *, start: datetime, end: datetime):
        with self._db() as db:
            rows = db.execute(
                "SELECT id FROM posts WHERE org=? AND due>=? AND due<? ORDER BY due,id",
                (org, _stamp(start), _stamp(end)),
            ).fetchall()
        return [self.preview(org, row["id"]) for row in rows]

    def cancel(self, org, post, *, actor):
        with self._db() as db:
            if not db.execute(
                "SELECT id FROM posts WHERE org=? AND id=?", (org, post)
            ).fetchone():
                raise WorkflowError("post unavailable")
            db.execute("UPDATE posts SET cancelled=1 WHERE org=? AND id=?", (org, post))
            db.execute(
                "UPDATE targets SET state='cancelled' WHERE org=? AND "
                "post=? AND state IN "
                "('ready','waiting','approval_required')",
                (org, post),
            )
            self._event(db, org, post, actor, "cancel_requested")

    def recover(self, org, *, now: datetime):
        # An expired worker may already have emitted a write. Never reclaim and
        # redispatch it automatically. A late result can still settle its claim.
        with self._db() as db:
            db.execute(
                "UPDATE targets SET state='unknown' WHERE org=? AND "
                "state='running' AND lease<=?",
                (org, _stamp(now)),
            )

    def resume(self, org, post, target, *, actor):
        """Explicitly replay the identical stored Broker request after a hold.

        Never use this with a raw provider client: Broker owns durable idempotency.
        A failed-safe terminal result needs a new occurrence, not a new key here.
        """
        with self._db() as db:
            row = db.execute(
                "SELECT cancelled FROM posts WHERE org=? AND id=?", (org, post)
            ).fetchone()
            if not row or row["cancelled"]:
                raise WorkflowError("post unavailable")
            changed = db.execute(
                "UPDATE targets SET state='ready',next_at=0 WHERE org=? "
                "AND post=? AND id=? AND state IN "
                "('unknown','approval_required')",
                (org, post, target),
            ).rowcount
            if changed != 1:
                raise WorkflowError("target is not resumable")
            self._event(db, org, post, actor, "broker_replay_requested", target)


class WorkflowRunner:
    def __init__(
        self,
        store: WorkflowStore,
        client: HostedConnectionClient,
        *,
        media_url=None,
        read_operation_ids: frozenset[str] = frozenset(),
    ):
        self.store, self.client, self.media_url = store, client, media_url
        # Host catalogue authority is independent of untrusted draft labels.
        self.read_operation_ids = frozenset(read_operation_ids)

    def _resolve(self, value, receipts, assets):
        if isinstance(value, dict):
            if "$step" in value:
                return receipts[value["$step"]][value["field"]]
            if "$asset" in value:
                if self.media_url is None:
                    raise WorkflowError("media resolver unavailable")
                # Resolver verifies stored bytes/digest and returns a host-approved
                # immutable media URL; credentials never enter this callback.
                return self.media_url(assets[value["$asset"]])
            return {k: self._resolve(v, receipts, assets) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve(v, receipts, assets) for v in value]
        return value

    def tick(self, org, *, now: datetime):
        """Advance one due target by one Broker operation. No background loop."""
        stamp = _stamp(now)
        with self.store._db() as db:
            row = db.execute(
                """SELECT t.*,p.document,p.digest FROM targets t JOIN posts p
                ON p.org=t.org AND p.id=t.post WHERE t.org=? AND p.cancelled=0
                AND p.approved=p.digest AND p.due<=? AND t.next_at<=?
                AND t.state IN ('ready','waiting')
                ORDER BY p.due,t.post,t.id LIMIT 1""",
                (org, stamp, stamp),
            ).fetchone()
            if row is None:
                return None
            draft = Draft.model_validate_json(row["document"])
            target = next(t for t in draft.targets if t.target_id == row["id"])
            step = target.steps[row["cursor"]]
            claim = uuid.uuid4().hex
            # Claim before resolving media or invoking anything external.
            db.execute(
                "UPDATE targets SET state='running',claim=?,lease=? "
                "WHERE org=? AND post=? AND id=?",
                (claim, stamp + 120, org, row["post"], row["id"]),
            )
            db.execute(
                "UPDATE posts SET started=1 WHERE org=? AND id=?", (org, row["post"])
            )
            saved = db.execute(
                "SELECT step,result FROM receipts WHERE org=? AND post=? AND target=?",
                (org, row["post"], row["id"]),
            ).fetchall()
        request = row["request"]
        response = None
        invoked = False
        try:
            if step.kind == "read" and step.operation_id not in self.read_operation_ids:
                raise WorkflowError("operation is not an admitted read")
            if request is None:
                arguments = self._resolve(
                    step.arguments,
                    {r["step"]: json.loads(r["result"]) for r in saved},
                    {a.asset_id: a for a in draft.assets},
                )
                key_parts = [
                    org,
                    row["post"],
                    row["digest"],
                    target.target_id,
                    step.step_id,
                    row["polls"] if step.kind == "read" else 0,
                ]
                key = hashlib.sha256(_encoded(key_parts).encode()).hexdigest()
                request = HostedOperationRequest(
                    connection_id=target.connection_id,
                    operation_id=step.operation_id,
                    arguments=arguments,
                    idempotency_key=key,
                    expect=target.expect,
                ).model_dump_json(exclude_none=True)
                with self.store._db() as db:
                    cancelled = db.execute(
                        "SELECT cancelled FROM posts WHERE org=? AND id=?",
                        (org, row["post"]),
                    ).fetchone()[0]
                    if cancelled:
                        db.execute(
                            "UPDATE targets SET state='cancelled' WHERE "
                            "org=? AND post=? AND id=? AND claim=?",
                            (org, row["post"], row["id"], claim),
                        )
                        return {"target_id": row["id"], "state": "cancelled"}
                    db.execute(
                        "UPDATE targets SET request=? WHERE org=? AND "
                        "post=? AND id=? AND claim=?",
                        (request, org, row["post"], row["id"], claim),
                    )
            with self.store._db() as db:
                fence = db.execute(
                    "SELECT t.claim,t.state,p.cancelled FROM targets t JOIN posts p "
                    "ON p.org=t.org AND p.id=t.post "
                    "WHERE t.org=? AND t.post=? AND t.id=?",
                    (org, row["post"], row["id"]),
                ).fetchone()
                if fence["claim"] != claim:
                    return {"target_id": row["id"], "state": fence["state"]}
                if fence["cancelled"]:
                    db.execute(
                        "UPDATE targets SET state='cancelled' "
                        "WHERE org=? AND post=? AND id=? AND claim=?",
                        (org, row["post"], row["id"], claim),
                    )
                    return {"target_id": row["id"], "state": "cancelled"}
            invoked = True
            response = self.client.invoke(
                HostedOperationRequest.model_validate_json(request)
            )
            response = HostedOperationResponse.model_validate(response.model_dump())
        except Exception:
            response = None
        with self.store._db() as db:
            current = db.execute(
                "SELECT * FROM targets WHERE org=? AND post=? AND id=?",
                (org, row["post"], row["id"]),
            ).fetchone()
            if current["claim"] != claim:
                # An old worker must not overwrite a newer replay's outcome.
                return {"target_id": row["id"], "state": current["state"]}
            state, result, cursor, polls, next_at = (
                "unknown" if invoked else "failed",
                None,
                row["cursor"],
                row["polls"],
                0,
            )
            if response is not None:
                status = response.status.value
                if status == "approval_required":
                    state = "approval_required"
                elif status in {"refused", "failed_safe"}:
                    state = "failed"
                elif status == "confirmed" and isinstance(response.result, dict):
                    result = response.result
                    if (
                        step.wait_field
                        and result.get(step.wait_field) not in step.ready_values
                    ):
                        polls += 1
                        state = (
                            "waiting"
                            if result.get(step.wait_field) in step.pending_values
                            and polls < step.max_polls
                            else "failed"
                        )
                        next_at = stamp + step.poll_seconds
                        request = None  # a later observation needs a fresh read key
                    elif (
                        cursor + 1 == len(target.steps)
                        and result.get("stage") != target.completion
                    ):
                        # A successful HTTP/Broker call is not proof of publication.
                        state = "unknown" if step.kind == "effect" else "failed"
                    else:
                        db.execute(
                            "INSERT OR REPLACE INTO receipts VALUES (?,?,?,?,?)",
                            (
                                org,
                                row["post"],
                                row["id"],
                                step.step_id,
                                _encoded(result),
                            ),
                        )
                        cursor += 1
                        polls, request = 0, None
                        state = (
                            target.completion
                            if cursor == len(target.steps)
                            else "ready"
                        )
            outcome = (
                None if response is None else _encoded(response.model_dump(mode="json"))
            )
            db.execute(
                "UPDATE targets SET "
                "state=?,cursor=?,polls=?,next_at=?,request=?,outcome=? "
                "WHERE org=? AND post=? AND id=? AND claim=?",
                (
                    state,
                    cursor,
                    polls,
                    next_at,
                    request,
                    outcome,
                    org,
                    row["post"],
                    row["id"],
                    claim,
                ),
            )
            self.store._event(
                db,
                org,
                row["post"],
                "workflow",
                "target_advanced",
                f"{row['id']}:{state}",
            )
        return {"target_id": row["id"], "state": state}


def workflow_card(store, org, post, *, result_id, invocation, produced_at):
    """Read-only ephemeral Core card; approval authority is never embedded here."""
    from zeo_integrations.ui import status_card

    preview = store.preview(org, post)
    states = ", ".join(f"{t['id']}: {t['state']}" for t in preview["targets"])
    summary = f"{preview['draft']['title']} — revision {preview['revision']}. {states}"
    return status_card(
        provider="Publishing",
        operation="publishing.preview",
        invocation=invocation,
        result_id=result_id,
        produced_at=produced_at,
        summary=summary,
        state="unknown",
    )


def main():
    """Local operator workflow CLI; this is not an unauthenticated web API."""
    import argparse

    parser = argparse.ArgumentParser(description="Durable editorial workflow")
    parser.add_argument("--database", required=True)
    parser.add_argument("--organization", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    save = commands.add_parser("save")
    save.add_argument("post")
    save.add_argument("draft_file")
    save.add_argument("--revision", type=int, default=0)
    for name in ("preview", "approve", "cancel"):
        sub = commands.add_parser(name)
        sub.add_argument("post")
        if name == "approve":
            sub.add_argument("--digest", required=True)
    parser.add_argument("--actor", default="local-operator")
    args = parser.parse_args()
    store = WorkflowStore(args.database)
    try:
        if args.command == "save":
            with Path(args.draft_file).open("rb") as stream:
                raw = stream.read(2_000_001)
            if len(raw) > 2_000_000:
                raise WorkflowError("draft size")
            result = store.save(
                args.organization,
                args.post,
                Draft.model_validate_json(raw),
                actor=args.actor,
                expected_revision=args.revision,
            )
        elif args.command == "preview":
            result = store.preview(args.organization, args.post)
        elif args.command == "approve":
            store.approve(
                args.organization, args.post, actor=args.actor, digest=args.digest
            )
            result = {"editorial_approved": True}
        else:
            store.cancel(args.organization, args.post, actor=args.actor)
            result = {"cancel_requested": True}
        print(_encoded(result))
    except Exception:
        parser.exit(
            2, "workflow request failed; check revision, preview and arguments\n"
        )


if __name__ == "__main__":
    main()
