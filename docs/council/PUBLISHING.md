# ZEO social publishing product

Operator scope: 31 October 2026. Build our own Buffer/Postiz-style publishing
service across Zeointegrations, Core and Connect. Instagram, TikTok, X, YouTube,
LinkedIn, Bluesky, Threads and Telegram channels are required; Substack Notes is
desired. This supersedes the earlier X manual-only implementation hold. TikTok
Inbox remains a distinct supported delivery mode; Direct Post is a separate mode.

The earlier 101/111 source-row count is not a publishing completion metric.

## Implementation now

| Platform | Existing or added code | Remaining publishing scope |
|---|---|---|
| Instagram | New official Facebook Graph client: image/Reel and carousel containers, status, publish; account and API version bound at construction | Stories, resumable media, Connect registration and account acceptance |
| TikTok | New official client: URL-pull inbox upload, creator info, direct video initialization, status | Creator-info/consent UI enforcement in host, verified media source, app access/audit, file upload/photo paths, Connect registration |
| X | New official text/pre-uploaded-media post client | Media upload, threads/reply workflows, Connect grants, account acceptance |
| YouTube | Existing resumable/hosted publication workflow | Qualify current Connect route, media route and channel binding; public release approval |
| LinkedIn | Official Posts API text/media publisher, image-upload initialization/status; constructor binds author and API version | Video/document upload, compiler media orchestration, Connect registration and account acceptance |
| Bluesky | Existing create-record publisher | Managed custody path and full media/thread workflow qualification |
| Threads | Official text/image/video/carousel container, status and publish calls | Connect registration and account acceptance |
| Telegram channels | Existing hosted text sender | Channel binding qualification, photo/video/albums and hosted provider route |
| Substack Notes | Not implemented | Unofficial Notes adapter, Connect-owned cookie custody, one-request-per-second distributed emission fence and reconciliation |

New provider clients live in `zeo_integrations.publishing`, separately from the
RapidAPI-backed discovery/read clients. They are not activated Broker operations.
All require injected transport. No environment lookup or credentials are accepted.
Each method dispatches at most one request; there is no automatic write retry or
combined create-and-publish call. Host records must retain container/publish IDs
between steps and across restarts.

The library's `allow_effect` argument is an explicit local guard, not a grant or
proof of user approval. Connect must authenticate the caller, bind the connection,
validate the precise content and media, claim the operation durably, and inject
credentials before any provider call. The host must ensure a container belongs
to this connection and approved occurrence before publishing it. Runtime supplies
stable occurrence identities; application-level idempotency keys are not magically
honoured by social providers.

Instagram uses the documented Facebook Login / linked professional account route.
Threads has its own origin and credentials. API versions are host configuration,
never guessed at import time. LinkedIn also accepts validated media URNs; upload completion and ownership remain host obligations. X text
has a conservative 280-code-point limit, not the provider's full weighted-text
algorithm or long-post feature. Its media IDs must already have been uploaded and
verified for that connection. Media-source origins are configured by the host;
TikTok additionally requires verified ownership of the URL domain/prefix.

TikTok's direct-post caller must first obtain fresh creator information, show
allowed privacy settings and account identity, and obtain explicit user consent.
There is deliberately no default privacy choice in the request model. The current
request surface covers basic non-branded video posts. Provider access and audit
are still required for production. Initialization yields `processing`, inbox
notification yields `inbox_delivered`, and only the provider's completed status
is reported as `published`. These states do not imply public visibility.

## Product responsibilities

- **Zeointegrations:** provider validation, upload/create/publish/status calls,
  bounded results and failure classification. Keep public MIT code independent
  of proprietary Connect server internals and Postiz implementation code.
- **Zeocore:** shared post/media/target/result contracts and ephemeral UI schemas.
  One editorial item can have separate platform variants and target results.
- **Zeoconnect:** account linking, credential custody, refresh, scopes, exact
  approval or standing authority, durable claims, execution and reconciliation.
- **Runtime/Agenda:** due occurrences, durable scheduling, cancellation and wakeup.
  Do not introduce another polling scheduler inside the provider collection.
- **Creator/App:** composer, calendar, previews, day approval, queue visibility,
  failures, reconciliation controls and eventual analytics.

The user journey is one content item with platform-specific variants, media and
account targets; preview and approve the exact batch; schedule; follow independent
per-target outcomes. Editing approved text, media or targets invalidates that
approval. A failed LinkedIn target must not cause successful Instagram or Telegram
targets to be republished. A timed-out write stays unknown until reconciled; no
fresh-key retry may turn uncertainty into duplicate content.

This packet now includes a durable local content/workflow store, exact approvals,
per-target execution, a CLI and Core status-card output, plus media staging, explicit
conversion and streaming upload. See [WORKFLOW.md](WORKFLOW.md) for usage, supported
formats and recovery semantics. A deployed web composer, cross-service scheduler
and complete media coverage remain to be wired. The package/Connect Core version conflict remains documented in
CONNECT.md. No account has been linked, charged or published to during this work.

## Sources checked

Postiz is a scheduling/analytics product with NextJS, NestJS, Prisma/PostgreSQL and
Temporal, under AGPL-3.0. It is a product/architecture reference only; no source was
copied into this MIT collection.

- https://github.com/gitroomhq/postiz-app
- https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api
- https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api
- https://developers.tiktok.com/docs/en/content-posting-api-reference-upload-video
- https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post
- https://developers.tiktok.com/docs/en/content-posting-api-reference-get-video-status
- https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-01
- https://github.com/xdevplatform/docs/blob/main/x-api/posts/manage-tweets/introduction.mdx

Verification uses synthetic HTTP responses, including LinkedIn's header-only post
receipt, refusal before dispatch, missing receipts, media-source rejection, and
TikTok inbox/publication distinctions. It does not prove real-account acceptance.
