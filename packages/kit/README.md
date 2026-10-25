# Kit read-only migration client (in preparation)

sow: zeointegrations-SOW-02 rev4

Architect ans_5a4c21e67ff1d50a, received2026-10-24T05:20:00.873063Z:
read-only current-API migration/audit replaces legacy API preservation.
No broadcasts or sequences, including reads. No subscriber/tagging/subscribing
writes, activation, enrollment, sends or scheduling; no write models/factories.

| Method | GET path | Response array / selected schema | Official contract |
|---|---|---|---|
| list_subscribers | /v4/subscribers | subscribers: id, state, created_at, email_address, first_name, fields | [Subscribers](https://developers.kit.com/api-reference/subscribers/list-subscribers) |
| list_tags | /v4/tags | tags: id, name | [Tags](https://developers.kit.com/api-reference/tags/list-tags) |
| list_forms | /v4/forms | forms: id, name, type, archived | [Forms](https://developers.kit.com/api-reference/forms/list-forms) |
| list_custom_fields | /v4/custom_fields | custom_fields: id, name, key, label | [Custom fields](https://developers.kit.com/api-reference/custom-fields/list-custom-fields) |

Contracts inspected2026-10-24 from official documentation HTML only; no account
or provider API requests. A separate .md documentation download returned403;
it was not retried. No credential acquisition or live proof is claimed.

Subscribers and forms explicitly default status=all for migration; subscribers
request slim=false to retain custom field values. Subscriber states are retained,
not promoted to active. All four endpoints use bounded cursor pages. The caller
passes PageRequest(after=previous.next_after); no automatic page loop/retry.
Missing/malformed pagination, repeated cursor, invalid/duplicate row identity or
missing subscriber state raises a safe RESPONSE error, never complete=true.
complete means a single first/last page, not an atomic account snapshot or
permission to reactivate subscribers. Eventual consistency limits audit snapshots.
A terminal page can have next_after=null and complete=false when earlier pages
exist. This does not itself mean a failed full scan. The receiver validates the
bounded full cursor chain, history and rate controls; Page.complete is not a
full-scan completion or historical-event guarantee.

When present, provider created_at is an extended ISO8601 calendar date and time with
seconds and explicit Z or numeric UTC offset, at most64 characters, with optional
fractional seconds. Calendar/time/timezone validation preserves the exact input
string, including offset and fraction, in JSON output. Missing or null dates remain
honest unknowns, represented as JSON null, preserving compatible pages. Present
nonstring, naive and malformed dates refuse the page; no capture-now fallback or timestamp
normalization is performed. The value is the provider creation date, not evidence
of a consent or stop event. All five raw states remain unchanged; the receiver
owns their consent mapping (including inactive/unknown eligibility), source=kit,
snapshot/received time, dedupe, stop-event reconciliation and export counts.
The current list snapshot cannot reconstruct event history or missing stop dates.
No include=canceled_at query is added; that field requires status=cancelled and
separate source/receiving coverage. No subscriber addresses, logs or CSV are
handled by seats during this synthetic source work.

Form embed scripts/URLs and unknown extra fields are excluded from returned data.

Forms side effects remain uncertain: the official REST reference describes
GET /v4/forms, while Kit's [AI connector documentation](https://help.kit.com/en/articles/15072804-ai-connector-tools)
marks list_forms as Write and says resolving form URLs may queue a public rebuild.
That AI-tool description does not prove the direct REST request triggers a
rebuild, and GET alone does not prove absence of side effects. This package
returns metadata only and never resolves, fetches or follows returned form URLs.
No qualified pure-read live execution is claimed. Preserve this uncertainty in
migration receiving evidence; source preparation is not live authorization.

Only injected credentials; fixed HTTPS origin, no environment proxy/redirects,
no automatic retries (including401), no logged provider bodies or retained original
exception context. Identity-encoded response bytes are streamed with a 1 MiB cap,
a 30-second monotonic deadline checked per unbuffered chunk and finite phase
timeouts (default10s, maximum30s). Encoded responses and JSON nesting over64
levels are refused. Direct transport callers also receive strict page/cursor/
status bounds. Injected credentials are nonempty printable ASCII, at most8192
characters; timeout values must be finite numbers, never booleans.
Transport itself refuses any non-GET or path outside these four exact lists.
Core retains service/lifecycle/KIT_* discovery and sole kit.marketing entrypoint;
no zeo_core imports, package entrypoint, compatibility redirect or Core dependency.

The committed uv.lock freezes dependencies. Run root make setup/make verify,
then populate this package's cache with uv sync --frozen --no-editable and run
make verify here for lint, formatting, installed synthetic tests and wheel/sdist
builds. Own-lane execution follows the Architect's 2026-10-24 standing ruling;
record clean HEAD, host, DIRTY, EXIT and full-log SHA256 for each exact-head gate.
Controls use stdlib unittest + injected httpx fakes, never real providers.
No Kit PR before Loops3 merge/rebase. Maintainer receiving, independent Council
review and pinned migration/audit consumer handoff remain separate acceptance.
This package is not a released or adopted integration.
