# X media and thread library

These are library steps, not a deployed Broker operation or credential route.
Connect owns OAuth custody, enrolment, account and media ownership binding,
allowlists, durable claims, approval, dispatch and installed consumer acceptance.
No token, path, arbitrary URL, header or automatic retry enters this API.

`XMediaClient` exposes explicit initialize, append, finalize and status steps.
Initialize uses the closed timeline MIME/category model. Append accepts immutable
bytes, at most 512 KiB, with a segment index from 0 through 9999. It builds the
complete bounded multipart body with a fixed filename; it reads no file. The
transport must explicitly advertise `supports_raw_body = True`; older transports
refuse before dispatch. Request bodies are exclusive: JSON, form or raw. The
HTTPX adapter counts metadata plus the entire raw multipart envelope against its
request byte cap (1 MiB default), preserves existing origin/redirect/deadline and
response limits, and hides raw bytes from Request's representation.

A confirmed append means only that segment was accepted. Missing, malformed or
lost write receipts remain unknown; abandon that upload rather than guessing
which bytes arrived or retrying a segment. The host persists each claim before
I/O, manages total bytes, ordered indexes and expiry, and binds the uploaded
asset to the selected account. `expires_at` is preserved as vendor metadata;
this library does not infer its units. Finalize and status interpret explicit
processing states; only confirmed finalize may treat absent processing_info as
ready. No status polling happens implicitly. Expired media is never ready.
Provider readiness is not proof that the account may attach it to a post.
This client deliberately requires `media_key` and `expires_after_secs` even
though the provider schema marks them optional. An otherwise valid answer that
omits either field is unconfirmed here; an upload may consequently be abandoned.
This stricter receipt policy avoids inventing asset identity or expiry facts.

`XThread` contains immutable ordered posts: the root has no reply link and every
later post links exactly to the immediately preceding index. Branching to an
earlier post is refused to match the host's chain mapping.
Its canonical complete JSON preview includes account, all text/media/link fields,
provider and version. It refuses previews over 6000 UTF-8 bytes without cutting
content. The separate 25-post cap does not promise that 25 maximum-length posts
fit: 25 times 280 ASCII characters already exceeds the byte cap before metadata.
The digest binds the entire preview, including later posts and selected account.

`next_step` returns a fresh single-post input and an unconfirmed step record.
The host must persist that record before dispatch, then store the confirmed
returned ID or UNKNOWN. Each step digest binds the whole thread, index, account
and resolved reply ID. `next_index` advances only through a contiguous confirmed
prefix and stops after any unknown or unconfirmed step. It performs no I/O,
creates no approval and provides no cross-call durable deduplication. Callers
must supply the complete trusted execution prefix; omitting a record or
inventing an ID cannot be detected by a pure value helper. Hosts must never
discard uncertain steps and reconstruct an empty history to resend a thread.

The step value has no REFUSED state. A host may exclude a definitely refused
final attempt from the planning prefix only when it retains the attempt and its
definite-refusal evidence in its durable audit. Such evidence must prove no
write occurred: an explicit pre-dispatch refusal or the client's validated
`definite_refusal` result, never a generic HTTP status or missing receipt. The
host must still perform fresh admission and approval checks before any later
attempt. This is no automatic retry instruction. Never exclude an UNKNOWN,
timeout, lost answer, partial result or otherwise unconfirmed attempt; stop and
reconcile it. All confirmed prior steps remain bound to their recorded IDs and
request digests. The helper cannot itself authenticate this external evidence.

Incoming IDs retain the full uint64 decimal representation. Outbound post,
reply and media-ID parameters follow the endpoint schema's 19-digit limit;
an unrepresentable confirmed parent ID is preserved but cannot advance a reply.
The text limit remains a conservative local character cap, not a vendor weighted
length calculation. This increment does not implement live enrolment or grant
new account/media permissions.

Primary protocol references (read 2 November 2026):

- https://docs.x.com/x-api/media/quickstart/media-upload-chunked
- https://docs.x.com/x-api/media/initialize-media-upload
- https://docs.x.com/x-api/media/append-media-upload
- https://docs.x.com/x-api/media/finalize-media-upload
- https://docs.x.com/x-api/media/get-media-upload-status

Original MIT implementation by Zero Employee Organizations. No vendor SDK,
credential code or provider source was copied. Existing shared HTTP and X code
is extended in place with its provenance retained. The binary seam and pure
thread boundary were agreed with the receiving host maintainers; host design
and credential custody remain their responsibility.
