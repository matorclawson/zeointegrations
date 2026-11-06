# Durable publishing workflow and media

This is an implemented local backend for a Buffer-style product: content storage,
platform variants, exact editorial approval, scheduling eligibility, independent
target execution, durable receipts, cancellation and review of uncertain writes.
It is not a deployed web composer or an activated Connect service.

## User journey

1. Stage local media in `MediaLibrary`. The immutable asset descriptor includes
   SHA256, detected type, size and alt text. Inspect it with optional ffprobe.
2. Explicitly convert an incompatible image/video if desired. `square_jpeg`
   produces a padded 1080-square JPEG. `portrait_mp4` produces padded 1080x1920
   H.264/AAC MP4 at 30fps with faststart. No implicit crop or duration cut occurs.
   Conversion preserves the original and creates a new asset/digest to review.
3. Build each platform variant using `compose_target` and actual operation IDs
   from the host's admitted Connect catalogue. Supply the connected identity and
   connection revision using Core's `HostedExpectedBinding`.
4. Save a `Draft` through `WorkflowStore.save`, preview it and approve the returned
   digest. The digest covers text, assets, target bindings, operation arguments,
   sequence and schedule. An edit requires the current revision and invalidates
   approval. Started items cannot be silently edited.
5. Runtime/Agenda invokes `WorkflowRunner.tick` when work is due. Each invocation
   advances one target by one operation. SQLite transactions claim it before any
   external operation. The runner uses the real Core `HostedConnectionClient`.
6. Inspect `preview` or organization-scoped `calendar` for target states and
   receipts. `workflow_card` builds a data-only Core status card for ephemeral UI.
   Cancellation prevents new work; it cannot undo an already emitted provider call.

A minimal host flow (the host supplies the authenticated `organization`, `actor`,
Core client, operation catalogue, media URL service and connection binding):

```python
from zeo_integrations.publishing.compose import compose_target
from zeo_integrations.publishing.media import MediaLibrary
from zeo_integrations.publishing.workflow import Draft, WorkflowRunner, WorkflowStore

media = MediaLibrary(media_directory)
asset = media.stage(local_jpeg, asset_id="hero", alt_text="Product launch")
media.inspect(asset)
target = compose_target(
    target_id="instagram", platform="instagram", connection_id=connection_id,
    expect=expected_binding, caption="Our launch", assets=[asset],
    operations=admitted_instagram_operations,
)
store = WorkflowStore(database_path)
draft = Draft(title="Launch", scheduled_at=scheduled_at, assets=[asset], targets=[target])
preview = store.save(organization, "launch", draft, actor=actor)
# Display preview; approve only after the user approves this exact digest.
store.approve(organization, "launch", actor=actor, digest=preview["digest"])
runner = WorkflowRunner(store, hosted_client, media_url=media.resolver(immutable_url_for))
runner.tick(organization, now=now)
```

The local operator CLI can save, preview, approve and cancel JSON drafts:

```sh
python -m zeo_integrations.publishing.workflow --database publishing.db \
  --organization example save launch draft.json
python -m zeo_integrations.publishing.workflow --database publishing.db \
  --organization example preview launch
```

`approve launch --digest HASH` and `cancel launch` use the same database and
organization options. This CLI is a trusted local operator tool, not a web API.
The example is not authentication middleware and grants no provider authority.

## Recovery and authority

Confirmed receipts and the current cursor survive restarts. A failure on one
platform never resets another platform's successful result. Read polling creates
fresh observation keys, with bounded count and spacing. An upload/container
acknowledgment cannot finish a target: the final confirmed receipt must identify
`published` or the explicitly selected TikTok `inbox_delivered` completion.

A timeout, lost lease, malformed response or unknown write stays `unknown`.
`recover` identifies expired claims. An authenticated operator may use `resume`
after investigation to replay the exact stored Core request with the same key;
Connect must own durable deduplication/reconciliation. This is not a fresh-key
provider retry. Broker approval-required responses also need explicit resumption.
Failed-safe/refused operations remain failed; create a newly reviewed item when
appropriate. Lease expiry alone never dispatches another write. Late workers
cannot overwrite a newer claim. No scheduler daemon is started by this library.

Editorial approval is separate from Connect authorization. The trusted host must
validate organization/actor access, issue grants, enforce account/asset/container
ownership, bind provider IDs to the approved occurrence, inject credentials and
reconcile ambiguous writes. It must serve the exact verified digest at the media
URL throughout provider ingestion. A URL's syntax/origin alone does not prove
immutable bytes. The host must also enforce provider-specific geometry, duration,
codec, account and consent requirements before approval. ffprobe supplies facts;
it is not a universal provider acceptance certificate.

SQLite and staged assets require durable private storage and backups. Use one
shared database per deployment, not isolated worker copies. For a multi-host
service, port transactional claims and records to the service's durable database
before deployment. Local persistence models are implementation details; Core owns
shared cross-service contracts. Untrusted media processing needs host resource
isolation; subprocess time/output bounds do not replace a container sandbox.

## Implemented media paths

| Path | Implemented | Boundary still to wire |
|---|---|---|
| Shared staging | JPEG, PNG, WebP, GIF, selected MP4 brands and PDF signatures; streaming digest/size; tamper checks | Host storage retention, upload UI and immutable serving |
| Explicit conversion | Still JPEG/PNG/WebP to square JPEG; MP4 to portrait H.264/AAC MP4 | Host ffmpeg installation, resource isolation and preview |
| Shared binary upload | One admitted streaming PUT to an explicitly allowed origin; bounded response; no redirect/retry | Connect claim binding URL, digest, account and provider upload ID |
| Instagram | JPEG/Reel composition; image/video carousel items, parent container, status polling, final publish | Host media preflight, registered operations and account acceptance |
| Threads | Text/image/video composition; image/video carousels, status polling, final publish | Host media preflight, registered operations and account acceptance |
| TikTok | MP4 URL-pull inbox or direct-post composition with explicit privacy and status polling | Fresh creator info, consent UI, app access, verified domain and registration |
| LinkedIn | Text composition; image initialization/status; single image/video/document URN and multi-image post payloads | Compiler upload-step adapter; video/document upload protocols; account acceptance |
| X | Text composition; low-level post accepts already uploaded media IDs | Upload protocols and media-step compiler |
| YouTube, Bluesky, Telegram | Existing specialized clients/workflows remain available | Common compiler adapters, receipt normalization and expanded media coverage |
| Substack Notes | No adapter | Session custody and a qualified implementation |

Staging a GIF or PDF does not imply every provider can publish it. Unsupported
compiler combinations fail before approval. Instagram image compilation currently
accepts JPEG only; PNG/WebP require explicit conversion. Conversion does not
promise that every output satisfies every provider's changing requirements.

## Verification

Offline tests cover stale approvals, edits, due times, competing claims,
cancellation during media resolution, independent target failure, polling keys,
timeout/restart replay, wrong completion receipts, tampering, upload admission,
redirect refusal, actual ffmpeg image conversion, LinkedIn media wire payloads and
an end-to-end carousel through Core's hosted boundary and synthetic HTTP transport.
The carousel test reopens durable storage between operations and proves no dispatch
before approval. No live account credentials, content publication or activated
Broker registrations were used. See VERIFICATION.md for the full package gate.
