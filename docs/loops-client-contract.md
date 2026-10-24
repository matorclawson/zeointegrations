# Loops client receiving contract

sow: zeointegrations-SOW-02

Proposed to zeoconnect in `ans_8f792790e550fcb7`, answering its six consumption
questions. Broker confirmation, fixture contribution and actual dependency/gate
closure remain outstanding; this document is not a qualified package release.

Source: official <https://app.loops.so/openapi.json>, received version **1.22.6**,
SHA256 `518500f5f94aeba4c242d8474ce050b0607dd356f4875dc0279a6120df18a811`.
The frozen received document is in the extraction evidence packet. No live account
response or credential is used as a fixture.

## Distribution and transport

- Distribution `zeo-integration-loops`, directory `packages/loops`, implicit
  namespace import `from zeo_integrations.loops import LoopsClient`.
- Constructor: `LoopsClient(api_key: str, *, transport: httpx.BaseTransport | None
  = None, timeout: float = 10.0)`. Reuse Broker's existing approved httpx pin;
  neither a new SDK nor a new dependency version is assumed approved.
- Fixed origin `https://app.loops.so/api`, `/v1` routes, redirects disabled and
  bounded timeouts. No network at import, local credential discovery, key logging
  or persistence. No automatic mutation retries; ambiguous transport failures
  must not be silently retried or reported as successful mutations.
- Consumers use a full immutable Git commit and `subdirectory=packages/loops`
  in their direct dependency and lockfile. Offline build/install requires the
  exact source/build artifacts; a Git pin alone does not prove that closure.
  No PyPI, editable install, floating branch or available commit is claimed yet.

## Bounded surface

| Capability | Proposed typed methods / constraints |
| --- | --- |
| Account | `test_api_key()` returns typed success/team context. |
| Drafts | `create_campaign(name)`, `get_campaign(id)`, `get_email_message(id)`. |
| Content | `update_email_message(id, expected_revision_id, subject, preview_text, from_name, from_email, lmx)`; exact revision binding, no arbitrary extra fields. |
| Audience | `update_campaign_audience(id, mailing_list_id / audience_segment_id / audience_filter)`; typed schema, reject `scheduling`, no generic update payload. |
| Supporting reads | `list_themes()`, `list_mailing_lists()`, preserving specified pagination/completeness rather than inventing all-pages success. |
| Assets | Typed upload creation/completion; actual upload destination/authorization handling must follow the spec and cannot leak the API key to another origin. |
| Contacts | Separate `LoopsContactsClient`: typed create/update-upsert/find and suppression check; absent from draft `LoopsClient`. Atomic update-only unsubscribe is unavailable in OpenAPI 1.22.6 and is withheld by Architect ans_0fc17ba75cdb8222. No automatic consent repair or uncertain-write retries. |
| Webhooks | Signature verification against the official signing contract; no guessed signature encoding or custody store. |

Typed errors distinguish authentication/authorization (401/403), missing resource
(404), revision conflict (409), payload size (413), rate limit (429 with validated
Retry-After), transport failure and invalid provider response. Provider bodies,
request headers and API keys must not leak through error messages or logs.

There is **no send, schedule, preview-email or workflow method**, and no public
arbitrary-request escape hatch. Both OpenAPI campaign creation and update schemas
contain `scheduling`; expose narrow hand-selected builders, not the full generated
schema. Negative tests must prove rejection before any transport request.
The spec's `fromEmail` is the sender local-part, not an arbitrary full address.
`expectedRevisionId` refers to the fetched content revision, not a local timestamp.

## Receiving and acceptance

Use spec-derived synthetic fixtures shared with Broker, with exact hash and
provenance. Test expected paths/bodies, typed results, malformed responses,
revision errors, redirect refusal, credential/log redaction, rate limits and the
absence of forbidden methods/payloads. Network-free provider doubles do not prove
live account entitlement. Package build, installed import/discovery and full
exact-head gate remain separate acceptance steps in an actually permitted venue.

Target first account/draft/content/audience source by 10:00 UTC and a qualified
pin by 11:00 UTC on October 24, conditional on actual inputs and venue. Architect
`ans_e2264e94650214a6` explicitly clears implementation coverage under SOW-02.
If no qualified pin exists then, Broker may use its scoped temporary same-interface
fallback rather than miss delivery; one behavior contract and eventual removal
of the fallback are required. No fallback implementation is claimed approved here.

Council correction checkpoint (2026-10-24, ans_cd6f12755dad4313):

- 409 is neutral `ConflictError`, not proof of a changed revision.
- Upload tickets accept only HTTPS, no userinfo/port/fragment, exact
  loops-assets.s3.amazonaws.com and `/uploads/{checked emailAssetId}`.
  Final assets accept only assets.loops.so and images.vialoops.com.
- A 30-second monotonic deadline is checked at headers, every unbuffered chunk,
  and decoding. Per-phase timeout bounds an in-flight blocking read; this is
  not a hard process wall deadline. Responses over 1 MiB or with content encoding
  other than identity fail with unknown outcome. The request wire bytes are
  encoded once and limited to 400,000 bytes, preserving 60,000-byte escaped LMX.
- The contact client is a distinct review surface. No fake update-only wrapper
  uses the provider upsert. The proposed unsubscribe omission is a substantive
  scope decision, not claimed accepted or delivered.
- Broker must check Draft status before writes, enforce an aggregate team rate
  limit, use test_api_key for enrollment, and independently qualify its typed-model
  and ThemePage adapter diff. Package availability alone is not adoption.
