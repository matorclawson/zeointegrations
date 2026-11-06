# External council implementation assessment

This archive expands the collection substantially. It does **not** establish full
VeyraX action parity or production qualification. Read COVERAGE.md and USAGE.md
before integrating it into Connect.

## What changed

- 64 credentialless HTTP provider modules, exposing 803 operation methods through
  one bounded transport implementation. All have closed outer argument models and
  request-construction vectors. HTTP SDKs are not eagerly imported.
- Shared limits for JSON bytes, response bytes, deadlines, request counts, allowed
  origins, explicit effects, no write retry, no follow-on request after a dispatched
  effect, sanitized errors and preservation of uncertain outcomes. Error swallowing
  in an upstream helper cannot turn a rejected transport call into a success.
- Telegram 933d55a imported from its complete-history bundle and tested against
  the supplied Core, including receive/ACK recovery and send/callback cases.
- Loops added to the aggregate wheel and made Python 3.12 compatible. Historical
  standalone packages remain for compatibility and their gates still run.
- GitHub, Notion, FFmpeg, Pandoc, Jupytext, Notebook, LLMs, Gemini and Bluesky source
  copied from the supplied Core with internal provider import relocation and
  travelling tests. Shared contracts, signer and entry points remain Core-owned.
- Parameterized, bounded DB-API execution for PostgreSQL, NeonDB, Snowflake and
  ClickHouse, plus a separate Supabase SQL surface; selected injected Amazon, E2B,
  SMTP and WhatsApp operations; original read-only Stripe operations.
- Lazy local discovery, per-operation JSON input schemas, corrected auth metadata,
  a complete 111-row coverage map, MIT notices and source/blob provenance.
- Follow-up adds Amazon lookups, IMAP reads with UIDVALIDITY fencing, bound
  WhatsApp history reads, E2B code execution, HTTPX streaming and a Loops Connect
  result adapter. See CONNECT.md for exact host responsibilities and limits.
- Read-only data-only status cards validated through Core's actual UI wire contract.
- An explicit no-network test fixture exposed an inherited localhost dependency
  probe. The fixture now refuses connections with the normal OS connection-error
  semantics. SDK construction tests also isolate host proxy settings. No live
  provider or credentialed acceptance calls were performed.

## What was learned from VeyraX

The source has separate route, service and client layers. Route actions are not
one-to-one with client methods: services often assemble arguments, normalize results,
and add frontend components. These ports expose client operations, not a drop-in
replacement for VeyraX's FastAPI routes. Component names and provider HTML are not
copied into Core UI. OAuth refresh, token lookup, databases of credentials, the
QR/session server and the platform memory store remain outside this package.

The attached archive's 550 files exactly match commit
1cdddde9d5d76b9891896ca78a95e069647e81df. Its auth labels alone are insufficient:
several nominally no-auth integrations require server keys. The corrected inventory
labels those routes explicitly. RapidAPI-backed readers remain RapidAPI readers;
they are not represented as official Facebook, Instagram, LinkedIn or travel APIs.

## Remaining work and boundaries

1. **Connect deployment:** a concrete streaming HTTPX transport and original Loops
   result adapter now exist; see CONNECT.md. The latest private server source was
   inspected. Its Core 0.12.0 pin conflicts with the aggregate's >=0.43 requirement.
   Coordinate that upgrade and operation registration; retain server-owned account
   binding, grants and durable claims. No Broker route was activated.
2. **Provider parity:** the HTTP catalogue is broad, but it is not a port of every
   VeyraX route/service transformation. The native SDK adapters intentionally cover
   selected operations only. E2B provisioning/lifecycle,
   IMAP mutation operations, WhatsApp QR/session custody and some binary upload/download paths still need
   dedicated implementations. Unsupported raw upload/arbitrary-URL helpers are not
   advertised as executable catalogue operations. Closed nested provider request
   and response schemas also remain incomplete; outer models and byte limits are
   enforced now.
3. **Source freshness:** VeyraX ports use the pinned API dialect. Synthetic tests
   prove request construction and local safeguards, not that every upstream API
   endpoint is still available. Provider-specific acceptance and response fixtures
   must accompany deployment. Native protocol fakes are not real-cloud acceptance.
4. **Migration landing:** Core's lazy shims and registry migration are separate.
   Existing entry-point names still resolve to Core. Legacy migrated APIs retain
   their original environment/credential behaviors; new HTTP adapters do not.
5. **Explicit holds:** Cloudflare and signed media hosting retain their ownership
   boundaries. The operator has since requested social publishing: TikTok and X
   publishing primitives now exist; Substack Notes remains unimplemented, not
   prohibited. See PUBLISHING.md for the updated scope. The Core-owned voice/MediaSource successor was not
   supplied as a merged implementation; no competing router was introduced.
6. **Qualification:** this external Linux run is evidence, not the internal ENG-UK
   admission, independent council signature, release, or consumer acceptance.
   See VERIFICATION.md for exact commands, outcomes and remaining test conditions.

The archive contains source, a wheel, source identities, the complete diff and
ordered family patches. There are no invented SOW ids, commits, PRs, releases,
GitHub settings changes or deployment claims. The internal owner can apply the
patches under its actual minted work record and run its required exact-head gate.

## Publishing direction

The operator now requires a Buffer/Postiz-style product. New official publishing
primitives cover Instagram, Threads, X, LinkedIn and TikTok alongside existing
YouTube, Bluesky and Telegram write paths. Read PUBLISHING.md: these primitives
are not a finished composer, calendar or deployed cross-platform workflow.
