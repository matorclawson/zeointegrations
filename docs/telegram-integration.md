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
Core wordingv10. receipt.condition is validated against the closed declared
set; receipt.replayed is a boolean. Error messages and provider_detail never
drive control. result_not_retained is the agreed replay token, superseding
the earlier local transient_replay proposal. Missing condition on a generic
kernel refusal is preserved without inventing not_permitted.

READ arguments contain max1..100 only. The Broker owns getMe/webhook checks,
lease, pending/confirmed provider offsets and redacted observation history.
The client accepts only bounded message/callback batches and immutable local
copies. Unknown kinds or schema drift prevent ACK; no events are silently
discarded to move the queue. Empty batch is distinct from unavailable.
No automatic READ, ACK, backoff or write retry is performed.
A client instance is synchronous; its owning dispatcher serializes calls.
It is not a thread-safe shared receiver or lease service.

ACK accepts only the actual batch issued to this client and only after the
injected TRUSTED DurablePrefixVerifier confirms all configured consumers
durably handled the entire delivered prefix, including prior deliveries.
That verifier is an adapter to the consumer's real authenticated durable
store, not a boolean from Telegram or App input. Stable (bot_id,update_id)
dedup, changed-payload conflicts and consumer routing belong to that store.
The verifier receives the immutable CURRENT batch with its payloads, so a stored
ID alone cannot be mistaken for a disposition of changed redelivered content.
The library cannot independently prove a caller supplied a trustworthy adapter.
Only the opaque issued cursor is echoed. There is no integer provider offset.
After an ambiguous invocation, the original batch/key must reconcile; the
client retains only volatile reconciliation context, not a durable outbox.
After restart the owning durable consumer must restore/reconcile the original
intent; starting a new client/key is not evidence that the write never occurred.

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
