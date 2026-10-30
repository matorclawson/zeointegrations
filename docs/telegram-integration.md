# Shared Telegram receive/ACK slice

sow: zeointegrations-SOW-04 rev1

This source increment implements the agreed bounded READ/ACK client only.
Sending, inline buttons and answerCallbackQuery remain unfinished under this SOW.
It is not a bot receiver, running poll loop, installed Broker route, live grant,
App ingress, notification acceptance or full SOW completion.

The injected Core HostedConnectionClient owns pairing and the authenticated
transport; Connect alone owns bot credentials and provider URLs. Core's pinned
0.12.0 request has no expect field: the client supplies only connection_id,
operation_id, arguments and idempotency_key. It never manufactures tenant,
origin, HTTP method, header, offset or token. Connector revision comes from
the bound connection. The READ response's Broker-asserted bot_id identifies the
bot; update sender IDs do not. No Core contract or dependency is changed.

Contract: Connect Telegram addendum6 (5d750f3f5, blob254001c38999cd59d3da4b32c94025ad35b06f56),
addendum7 (9f496a053, blobff561064bcb857f092a14eec2a777ad3e0479dde),
Core wordingv10 supplies the hosted boundary and pin limitation. Later
own-addressed Connect adoption ans_9950ead5e0708a51 GOVERNS the condition freeze:
receipt.condition is required, null when no Broker-specific condition applies;
the closed replay token is transient_replay, superseding Add7's
result_not_retained. Unknown tokens/code mismatches/missing required condition
fail closed. An absent-key-as-null alternative is NOT selected here; that would
need an actual owner/Council disposition. receipt.replayed is a boolean.
Error messages and provider_detail never drive control. Generic kernel refusal
gains no invented not_permitted label; null is not a grant or successful effect.
No unknown top-level member is used: the Broker-pinned Core model rejects it.

READ arguments contain max1..100 only. The Broker owns getMe/webhook checks,
lease, pending/confirmed provider offsets and redacted observation history.
The client accepts only bounded message/callback batches and immutable local
copies. Unknown kinds or schema drift prevent ACK; no events are silently
discarded to move the queue. Empty batch is distinct from unavailable.
Broker Add10 adds a nonnegative reset epoch to READ. It is carried unchanged
to the verifier; only Broker advances it on a recorded reset. A lease fence
never changes business identity. Numeric IDs do not define delivery order:
the client preserves Broker batch order and rejects duplicate IDs within it.
Broker records unsupported old queued types as dropped without raw content;
an issued cursor may therefore cover a batch with no delivered updates.
The trusted verifier must still confirm previous deliveries/all consumers
before ACK; Broker must prove its drops before advancing that boundary.
Unsupported raw types leaking through to this client remain a schema refusal,
not a client-authorized drop.

No automatic READ, ACK, backoff or write retry is performed.
A client instance is synchronous; its owning dispatcher serializes calls.
It is not a thread-safe shared receiver or lease service.

ACK accepts only the actual batch issued to this client and only after the
injected TRUSTED DurablePrefixVerifier confirms all configured consumers
durably handled the entire delivered prefix, including prior deliveries.
That verifier is an adapter to the consumer's real authenticated durable
store, not a boolean from Telegram or App input. Stable (bot_id,update_id)
dedup on (bot_id, epoch, update_id), changed-payload conflicts within an
epoch and consumer routing belong to that store.
The verifier receives the immutable CURRENT batch with its payloads, so a stored
ID alone cannot be mistaken for a disposition of changed redelivered content.
The library cannot independently prove a caller supplied a trustworthy adapter.
Only the opaque issued cursor is echoed. There is no integer provider offset.
After an ambiguous invocation, the original batch/key must reconcile unless
the Broker explicitly opens the linked NEW-prefix recovery below. The client
retains only volatile pending context, not a durable outbox. The owning
consumer store preserves original intents and records returned execution
links; neither a READ nor a new client object proves the old outcome.

Deadlines are absolute monotonic caller deadlines, checked before and after
invoke. These checks CANNOT interrupt a blocking hosted transport. Its owning
adapter must enforce the original deadline and response-size limit itself;
there is no invented timeout request field. The local1MiB response ceiling
is client policy, not a provider limit or pre-download allocation guarantee.
No installed transport timing qualification is claimed.

[Telegram's primary API](https://core.telegram.org/bots/api#getupdates) explains
why a higher getUpdates offset acknowledges earlier updates. READ must use only
the Broker's last successfully confirmed durable ACK offset, never pending
intent. Negative offsets can forget queued updates. ACK is a separate guarded
effect; incidental updates in its answer are discarded by Broker, not passed
to this client as processed events. Retention age is a lower-bound/proxy only;
lost_to_retention means possible loss without a fabricated count.

Qualification: authored fakes are NOT RUN on Mat. Admitted ENG-UK make setup,
full make verify/Python floor, exact-head logs, independent Council review,
Architect signature and merger remain required before an ordinary push/PR.
Actual send/receive/inline consumer use remains a later separately evidenced
stage. No live Telegram call or new SDK/lock/package change is authorized here.

## New provider-page constraints and unresolved Broker guard

Connect Add10 at03de621fd (blob83bf858d9630da0ae43f3632c054febd226476cf)
supersedes the partial Add9 reading. Primary API was independently rechecked:
a random update ID can follow a quiet week, allowed_updates is sticky when
omitted, and error_code is not a stable discriminator. Broker owns provider
offsets, fixed allowed_updates on READ and ACK, reset/drop receipts and
HTTP/ok/parameters.retry_after classification. This client does none of that
provider traffic and infers no concurrent-poller409 behavior.

The five-day stale READ policy alone does not guard an OLD ACK cursor. After a
quiet week an old high cursor could confirm new lower IDs through the effect.
Returned to Connect: guard old/stale ACK before provider dispatch, including
ambiguous resend, and do not refresh freshness from an ACK without checking
the reset boundary. Same-key identity alone is not safe reconciliation after
a provider ID reset. No client reset/retry or old-effect success is invented.
Broker guard and reset recovery remain unbuilt/require owner qualification.

## Explicit linked stale recovery (Connect Add12)

The frozen Add12 atfa652d481 (blobfb6f4399a231e6637d357672f6dffe1c74942e14)
amends Add11: cursor_stale and recovery_required are Hosted FAILED_SAFE with
REQUEST_REFUSED and typed receipt.condition. receipt.pending_ack contains
state unresolved_stale and the original execution_id, not a new Core state.
A fresh READ may return receipt.recovery {open:true,supersedes:E1}. Neither
metadata object is evidence that E1 succeeded or failed.

Only acknowledge_recovery on the actual issued fresh batch starts an explicit
NEW prefix operation under caller-supplied NEW keyK2 and the Broker-asserted
supersedes_execution_id=E1. It still requires the current durable-prefix
verifier. It does not reuse K1 with another body, generate a key, loop, or
bypass Broker open-intent/freshness/epoch checks. Ordinary acknowledge rejects
an unlinked batch when recovery is required. Unknown/malformed/mismatched
metadata, caller-forged batches, reused known keys and wrong intent references
fail closed.

A lost E2 reply retains C2/K2 AND the same supersedes member for same-key resend;
it does not create K3. Original parent context stays until E2 is confirmed. Once the Broker has
declared an attempt unresolved_stale, local resend of that old cursor/key is
blocked; only a fresh Broker-granted linked prefix can advance.
The acknowledgement returns E2 plus superseded_execution_ids as LINKS ONLY;
it never resolves or overwrites E1. The local chain is bounded at16 prior
links; exceeding that requires owning recovery, not an automatic context purge.

After restart, authenticated Broker recovery metadata can supply the E1
reference for a newly issued batch without reconstructing E1's body or outcome.
The actual durable consumer still owns all original intent/key/history and
must establish the full handled prefix; this library is not a crash-safe
outbox or a grant from caller-provided identifiers. A fresh key is allowed
only for this explicitly linked new operation; ordinary unknown writes retain
their original invocation identity. No live recovery or source gate PASS is
claimed.
