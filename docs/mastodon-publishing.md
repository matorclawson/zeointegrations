# Mastodon publishing through a bound Connect adapter

This original client has no SDK, default HTTP engine, token argument, environment
lookup, OAuth flow or credential store. Inject a Connect-owned `BoundTransport`;
Connect holds credentials and retains organisation, device, operation and browser
approval controls. Library availability does not enable a live Broker operation.
The adapter proposal still requires Connect/Tools receiving agreement. There is
no production adapter, deployment or consumer acceptance claim in this source.

## Transport boundary

`MastodonClient(transport, origin=approved_https_origin, max_upload_bytes=operation_byte_cap)`
requires an opaque `transport.binding` and matching `transport.origin`.
`request(method, relative_path, *, fields, upload, headers, timeout_seconds)`
returns `Response(status, body, origin, headers, redirected=False)`.
All requests use constructed allowlisted paths; no caller URL is fetched.
The operation must carry only a staged-object reference, not upload bytes through
the64KiB Broker invoke body. Connect must bridge its verified UploadSource into
this seekable-reader port; that bridge is not present or claimed here. The
Broker supplies its execution key as the client idempotency key; the adapter
must enforce that match and reject attempts to choose another key.
The client emits only the caller's status `Idempotency-Key`, never auth headers.

Connect's adapter must inject auth only inside custody, disable ambient proxy
credential propagation, refuse redirects before following them, bind every
request to the approved origin/account, cap response bytes/time, and perform one
HTTP attempt without hidden retry. It returns sanitized errors and observed final
origin/redirect metadata. Client-side readback detects mismatches but cannot undo
a redirect already followed by an incorrectly implemented adapter. A protocol
object alone does not establish these runtime guarantees. Connect/Tools owns
that integration and its separate acceptance evidence; shared contracts remain
Core-owned. Do not plug in a credential-returning or generic default transport.

## Bounded operations

- `discover_limits()` reads `/api/v2/instance`, validating per-instance positive
  status/media caps, supported MIME types and description limit. Invalid/missing
  required configuration fails explicitly rather than assuming example caps.
  Instances predating the description limit are explicitly unsupported.
- `upload_media(MediaUpload(stream, size, filename, mime_type, description))`
  preflights declared size against instance and operation byte caps, checking
  the remaining length of a seekable stream without reading it into memory.
  It forwards chunks of at most64KiB and never buffers the full media file.
  Non-seekable input is explicitly unsupported until the Connect UploadSource
  bridge is agreed. It does not close the caller's stream. Reads must honor
  normal bounded BinaryIO contracts; an indefinitely blocking caller reader
  cannot be interrupted synchronously. The adapter must consume chunks until
  EOF rather than assume a no-argument read returns all bytes. Early EOF or
  changed length during dispatch refuses streaming, with unknown write outcome.
  Connect must supply a stable staged object with verified size/SHA256 and check
  digest again at dispatch; this library has no object-store custody or SDK.
  PNG/JPEG/other advertised non-GIF images use the discovered image byte cap;
  advertised video MIME types use video byte cap.
  Audio and image/gif are refused because the configuration descriptions alone
  do not establish their cap classification. No media is fetched by URL. The
  provider still validates actual format, pixel dimensions and frame rate;
  client-side byte/type checks do not decode or certify those properties.
- Upload200 must contain a processed attachment;202 starts bounded GET polling
  of `/api/v1/media/{id}`.206 remains processing,200 needs matching id and a
  valid HTTPS URL,422 fails processing. A preview URL is insufficient. Returned
  CDN URLs may use another host, but are never fetched. Deadline/attempt failure
  does not publish and does not reupload automatically.
- `publish_status(text=..., visibility=..., idempotency_key=..., media=...)`
  requires explicit public/unlisted/private/direct visibility and a stable key.
  Optional spoiler_text, sensitive and two-letter language are supported. Text
  or completed media is required. ReadyMedia receipts must match this binding;
  each ID is rechecked before POST so caller-constructed dataclasses cannot
  bypass readiness. Duplicate IDs and count overflow are refused.

Text validation is a deliberately conservative upper bound, not exact Mastodon
Unicode grapheme/link counting. It counts all text and spoiler code points, and
adds the discovered URL reservation for each dot variant or `://` marker as a
possible link. This overcounts long URLs, punctuation and some Unicode text;
valid borderline posts can be refused. It never claims provider-exact remaining
characters. A later exact counting implementation needs review, not a guessed
universal500-character limit.

## Rate limits, deadlines and outcomes

Caller policy sets finite overall/request timeouts, polling interval, read
attempt cap and operation byte cap; these are not provider quotas. Inject clocks and
sleep for fake tests. The adapter must enforce the supplied timeout. GETs may
retry explicit429/500/502/503/504 within policy. Retry-After and exhausted
X-RateLimit-Reset headers defer requests within the deadline; invalid selected
rate headers fail explicitly. This synchronous client is not a global account
quota scheduler: Connect must coordinate shared admission across clients.
401/403 stop without retry. Redirects stop without following them.

No POST is automatically retried, including429. `MastodonError.code` is a fixed
safe category; `outcome_unknown` distinguishes definite rejection from a write
whose result was lost or malformed. A valid media upload receipt is not a
published status. `PublishedStatus` contains validated nonempty id and HTTPS URL;
no response body or token is logged or included in errors. Keep the caller's
operation record and reconcile unknown effects rather than submitting another
upload or changing status keys. Mastodon's status idempotency retention is up to
one hour, not indefinite duplicate protection. Do not replay a stale key as if it
were a permanent once-only guarantee. Acknowledged pending media can remain
unattached after a failed workflow; this slice does not delete attachments.

Scheduling, polls, quotes, edit/delete, timeline crawling, app registration,
remote media downloads and custody changes are outside this client. All tests
use injected fakes. Full gate and Python floor run only in admitted ENG; actual
Connect-backed consumer publishing requires separately authorized observation.

## Primary references

API behavior was researched on2026-10-29; documentation is reference data,
not copied implementation:

- [Instance configuration](https://docs.joinmastodon.org/entities/Instance/#configuration)
- [Instance method](https://docs.joinmastodon.org/methods/instance/)
- [Media methods](https://docs.joinmastodon.org/methods/media/)
- [Status methods](https://docs.joinmastodon.org/methods/statuses/)
- [Rate limits](https://docs.joinmastodon.org/api/rate-limits/)
