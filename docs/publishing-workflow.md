# Publishing workflow and media

This library stores drafts, exact-content approvals, independent target results and
media digests. Runtime supplies due occurrences; the runner advances one operation
through the existing Core hosted connection client. It starts no scheduling daemon.
Editorial approval does not grant Broker execution authority.

Use WorkflowStore.save, preview and approve before WorkflowRunner.tick. An edit
invalidates approval. A timeout stays unknown; recovery never retries a write
automatically. Explicit resume reuses the saved request and key and requires
Broker durable idempotency. Cancellation cannot retract an emitted request.

MediaLibrary stages local files, checks immutable digests, and supports explicit
image/video conversion with optional ffmpeg and ffprobe. MediaUploader performs
one admitted streaming upload using injected HTTP transport and an allowed origin.
The host must bind upload URL, account, asset digest and operation claim.

WorkflowStore uses a single host-owned SQLite journal for local persistence, not
a replacement for a deployed service database. Host authentication, private durable
storage, immutable media serving, provider registration and account acceptance are
required before service use. This change installs no service, registry, credentials,
UI or live publishing route. Per-platform publishers follow in separate changes.

Copied source is MIT, copyright Zero Employee Organizations 2026;
[publishing provenance](publishing-workflow-provenance.json) records source hashes.
