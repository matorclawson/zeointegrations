# Instagram and Threads publishing clients

InstagramPublisher uses a linked professional account through Facebook Login,
with explicit account_id, api_version and allowed media origins. ThreadsPublisher
uses its own account and provider origin. Both require injected transport; neither
reads credentials or creates a network transport.

Create media/carousel containers, retain their identifiers, query status, then
explicitly publish the approved container. Container creation is processing, not
publication. Each call performs at most one request, without write retries. The
host binds containers, account, immutable media and operation occurrence, enforces
exact-post approval, and injects credentials inside a durable execution claim.
allow_effect is a local guard, not an authorization grant.

Travelling tests use synthetic HTTP transport and exercise a carousel through
Core hosted operations and durable workflow checkpoints. No live account is used.
This library slice registers no Broker operation and installs no service. Stories
and resumable uploads remain required follow-up features; real-account acceptance
and Meta app access/review remain separate.

## Receiving contract

Both constructors require an explicit `api_version` such as `v23.0` or `v1.0`;
these are examples, not a claim that an application's version is enabled. The
host chooses and pins its supported version. `identity(key=...)` is a single GET
returning only account ID and username, and rejects a different account. Instagram
checks credential access to the selected professional account; this does not prove
that a Page token belongs exclusively to that account. Threads reads `/me` and
compares its ID to the host's selected account. The host must perform enrolment
inside credential custody and bind that result to its connection subject.

`PublishingResponseError` exposes bounded HTTP status, numeric Graph code/subcode,
and a sanitized Retry-After value; it retains no provider message, body or token.
A structured Graph rejection on an explicit client-error status is definite
refusal. Server errors, conflicts, malformed replies and transport loss remain
unknown for effects. Neither classification causes a retry. Retry-After is advice
for host scheduling, never permission to repeat a write. The host persists the
original operation key, returned container IDs and uncertain outcomes.

`read_post(post_id, key=...)` reads metadata for an already host-bound post ID.
It is not discovery of a lost publish result and returns no workflow stage.
Container status is an observation, not proof that an unknown write is safe to
repeat. This slice makes no numeric container-expiry or automatic reconciliation
guarantee: those vendor facts were not established by the accessible primary
sources. Keep an unresolved publish held until independently bound evidence or a
human disposition resolves it. Never infer success by matching text alone.

## Authentication and media boundary

The [official Instagram collection](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api)
describes the Facebook Login route selected here: professional Instagram account
linked to a Facebook Page, with scoped access. Its collection includes permissions
for features beyond publishing; the host must select actual identity/publishing
permissions and obtain the required app access. A Page access token can be derived
through the authorized Page selection. The transport injects authorization only
inside ZEOconnect; this library neither obtains, stores nor refreshes tokens.

The [official Threads collection](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)
describes a separate Threads app and OAuth user authorization. Its long-lived token
example expires after 60 days and supplies a refresh endpoint. These are provider
lifetimes, not a library renewal service. The host handles refresh, revocation and
actual granted permissions (`threads_basic` / `threads_content_publish` for this
identity/publishing subset). Expired or rejected credentials require host handling.
No refresh token or access token belongs in request arguments, returned metadata,
fixtures or logs. Exact app-review/verification state is deployment input, unknown
here; no app approval is implied by offline tests.

Media URLs are fetched by Meta. Allowed HTTPS origins are host-configured; the
host must preserve immutable content, availability, TLS and provider reachability
for the whole processing interval. Local model limits are input bounds, not a
complete vendor media validator. The host must verify current type, size, duration,
aspect and account-specific requirements before approval. Stories/resumable
Instagram uploads remain follow-up scope. The explicit Threads create/publish
sequence does not enable the provider's optional automatic text publication.

## Temporary minimal vendor closure

The pure clients require `publishing/__init__.py`, `_http/__init__.py`,
`_http/runtime.py`, `_http/transport.py`, package initialization and `py.typed`,
plus the declared pydantic dependency. Workflow/media/compose and provider SDKs are
not needed for Broker calls. Any temporary vendoring must select final reviewed
commit/blob hashes including private helpers, retain MIT/provenance/NOTICE, and
remain distinct from the aggregate's Core version requirement. No final vendor
hash is assigned before independent review.

Reference-only reads of Meta's [IGMedia field schema](https://github.com/facebook/facebook-python-business-sdk/blob/main/facebook_business/adobjects/igmedia.py)
and [Threads sample collection](https://github.com/fbsamples/threads_api/blob/main/postman/threads-api.postman_collection.json)
support the metadata request fields. No sample or SDK implementation is copied;
their licenses do not replace this slice's original return provenance. Direct Meta
container/error pages were inaccessible during this review; unknown constraints
above remain explicit rather than being supplied from memory.
