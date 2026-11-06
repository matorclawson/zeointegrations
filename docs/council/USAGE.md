# Bounded integrations

One aggregate wheel. No new provider SDK is needed for the HTTP catalogue. Listing
providers reads packaged JSON and imports no provider. Loading a provider imports
only that provider. Airbnb parsing uses the existing BeautifulSoup optional extra.

```python
from zeo_integrations.catalogue import providers, load, coverage, metadata

schemas = providers()["airtable"]["operations"]
Airtable = load("airtable")
client = Airtable(connect_bound_transport)
result = client.invoke(
    "list_records",
    {"base_id": "app_example", "table_id_or_name": "People", "params": {}},
    idempotency_key="read-0001",
)
```

`connect_bound_transport` implements `_http.Transport.request(Request) -> Response`.
There is deliberately no default socket/HTTP implementation or environment-key
lookup. This is an adapter boundary for the Connect owner to implement, not a
claim that the supplied Connect server already supports every operation.

The adapter receives provider, operation, HTTP method, validated destination,
query/body, original idempotency key, remaining deadline and maximum response bytes.
It must bind the account, verify grants, inject credentials in the provider-specific
location, forbid redirects, limit response bytes while reading, enforce the timeout,
and durably deduplicate/reconcile effects. For native SDK/SMTP/DB adapters, the same
requirements apply to the injected connection or SDK. A caller-supplied
`allow_effect=True` is consent to dispatch, **not** a substitute for Broker admission.
SDK retries must be disabled by the owner of the injected SDK. Network policy and
DNS/IP checks remain necessary in the real transport, especially for custom origins.

Every non-GET/HEAD HTTP operation is conservatively treated as an effect, including
POST search endpoints and GraphQL. A write is never automatically retried, nor can
an upstream helper swallow a transport failure and turn it into a successful result.
After the first dispatched effect, another HTTP request in that invocation is refused.
An uncertain result stays uncertain; resubmit/reconcile the original key and body
through Connect. A 2xx HTTP response does not independently prove business success:
provider `errors`, `ok`, asynchronous job state and receipt fields still matter.
The library returns those payloads, not a fabricated publication/delivery receipt.

Inputs have closed per-operation outer models and a total JSON byte cap. Provider
parameter dictionaries intentionally remain provider-defined. Responses are bounded
JSON or explicit base64 envelopes; these are not exhaustive provider response schemas.
Pagination is explicit: call the next page with its documented cursor. Bulk reads
have a request ceiling; no unbounded page drains. The copied provider API dialects
are pinned to the supplied VeyraX commit; vendor evolution requires fixture updates.

`configuration` holds non-secret provider settings. Jira and Confluence require an
explicit `cloud_id`, Sentry requires `org_slug`; no first-account auto-selection is
used. N8N and the generic HTTP adapter require `origin=...` equal to the injected
transport's bound `origin`. Generic HTTP is limited to that HTTPS origin. Facebook,
Instagram and X profile helpers can use an explicitly configured profile/username.
No X publishing operation is provided. The RapidAPI-based social and travel readers
retain that provider identity; they are not silently substituted with official APIs.

## Data-only UI

```python
from zeo_integrations.ui import status_card
card = status_card(
    provider="Airtable", operation="airtable.list_records", invocation="call:123",
    result_id="result:123", produced_at="2026-10-31T12:00:00Z",
    summary="The requested page was read.", state="healthy",
)
```

The builder validates the actual Core wire contract. It emits no HTML, JavaScript,
or actionable authority, and does not copy arbitrary provider data into a UI card.
Caller-supplied summaries must accurately describe the receipt. This read-only
projection works with Core's card subset; ephemeral action grants remain Core/Connect
owned. The collection declares no duplicate Core entry points.

## Native adapters and limits

- PostgreSQL, NeonDB, Snowflake and ClickHouse accept DB-API connections. Use the
  driver's DB-API interface, not its unrelated native query client. SQL uses bound
  parameters and bounded `fetchmany`; all arbitrary SQL requires effect admission
  because even SELECT may invoke mutating functions. Connect owns transaction
  isolation, statement timeout and the caller's connection lifecycle. The caller
  must provide an idle connection with no unrelated transaction. Unknown commit
  outcomes are not retried. Supabase SQL is exposed separately as `supabase.sql`.
- Amazon supports product search on a caller-supplied PA-API SDK; this is not a port
  of every catalogue operation. E2B supports foreground commands on an injected
  sandbox; provisioning and lifecycle remain with Connect/Pomar.
- Mail supports SMTP submission. WhatsApp supports submission through an injected
  authenticated session bridge. Neither claims recipient delivery. IMAP and QR
  enrollment are not implemented here.
- Migrated Core providers preserve their legacy public APIs and credential behavior.
  They are source migrations, not a new credentialless Broker route. The GitHub App
  signer remains in Core. Existing Google/Kit/HubSpot/Revolut APIs are retained.

See COVERAGE.md for every row and held work. There is no release, live provider
exercise, Connect admission certification, or hosted consumer acceptance in this
archive. No registry settings, publishing workflows or live accounts were changed.

## Connect follow-up

See [CONNECT.md](CONNECT.md) for the concrete HTTPX transport, Loops result
adapter, native operation additions and host-owned execution requirements.
