# First-hour read-only inventory

Prepared 2026-10-17 by the zeointegrations seat under charter v1 and runtime-minted
`zeointegrations-SOW-01`. Mint record:
`matorclawson/org-zeroemployeeorg@d72aba45ac75f20d302295352dd50f3572894ffb:projects/zeointegrations/sow/zeointegrations/zeointegrations-SOW-01-integration-inventory-packaging-skeleton-and.md`.
Sources:

- VeyraX: canonical `VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df`,
  inventoried through the identical local `rodriveracom/veyrax-platform` fork.
- zeocore: `zeroemployeeorg/zeocore@2e7cb11fa9aaf133876c02c1eea8f1ccd94bba04`.
- Council-reviewed design: zeocore-SOW-36 rev 5,
  `matorclawson/org-zeroemployeeorg@0f2bf62e2`, with Architect rulings
  `ans_cbd9dfb83a794f92`.

The [VeyraX table](veyrax.md) covers **84 directories, 79 registered routers,
79,296 Python lines including tests, and 5,026,896 tracked bytes**. The
[zeocore table](zeocore.md) covers all **17 registered entry points**. Exact
sizes, direct import roots, test-only imports and existing dependency declarations
are in [snapshot.json](snapshot.json). All inspected Python parsed successfully.

## Findings that affect the order

1. This VeyraX snapshot contains no HubSpot or Stripe integration. HubSpot already
   exists in zeocore; Stripe requires another licensed source or a fresh
   implementation. Neither should be represented as a VeyraX port.
2. VeyraX has Gmail code, but `gmail_router` is only imported in `main.py`: it is
   absent from `INTEGRATION_ROUTERS` and `catalog.json`. DocuSign, Hilvl and
   veyrax-mcp also have source without registration. `common` is shared support.
   Source presence does not establish a working deployed integration.
3. Catalog auth `none` conceals server credentials for Apollo, Binance P2P,
   Bybit P2P, OKX P2P, IPinfo, Skyscanner, Yelp and Zillow. Their routes/clients
   read server API keys; they are credentialed integrations under this charter.
4. Custom auth is not uniform: Amazon uses access/secret keys and associate tag;
   Cloudinary uses key/secret/cloud name; mail uses SMTP/IMAP credentials;
   Sentry uses API key/org slug (and has an OAuth branch). Facebook, Instagram,
   LinkedIn and X combine profile inputs with server RapidAPI credentials.
   `db_access` means database connection credentials; `api_key_with_base` also
   accepts a base URL. WhatsApp uses a QR/session bridge. Port credential and
   origin handling through the Broker's approved interface.
5. VeyraX NeonDB and Supabase delegate to its PostgreSQL service. Its Supabase
   SQL operations are not equivalent to zeocore's Supabase SDK integration.
   Google Maps uses an API key, distinct from Google Workspace OAuth. Its
   YouTube implementation does not establish coverage of zeocore's upload path.
6. Shared VeyraX `common` code includes token lookup, refresh and custody. That
   infrastructure belongs to ZEOconnect and will not be copied into packages.
   Existing HTML/component assets need translation into zeocore's data-only
   schema, not direct frontend copying.
7. `veyrax_auth` is VeyraX's own Supabase-backed credential store with shared
   encryption; catalog `none` is not credential-free execution. `veyrax` is
   a per-user memory store over Supabase `users_memory`. Both remain outside
   the provider-port queue.

## Proposed order

The approved SOW-36 package migration order and this charter's priority for new
ports are separate queues. Coordinate each move with zeocore; keep one open PR.

1. This skeleton and CI. After merge, the Architect adds the `verify` check to
   the main ruleset. No publishing workflow or provider package in this slice.
2. zeocore-owned groundwork: local App signer relocation and duplicate-entry
   guard; then the credential-free **ffmpeg pilot** in its own package PR.
   The pilot can prove packaging/discovery, not Broker credential custody.
3. Local plugins: pandoc, jupytext, notebook (the last keeps no entry point).
4. Existing credentialed moves in reviewed order: Bluesky; Google (one package,
   six names); HubSpot; Kit; Notion; Supabase; GitHub; LLMs; Gemini; Meetings;
   Revolut last. Google/YouTube has its own follow-on split. zeocore owns shims,
   extras, removals and compatibility. Package moves alone admit no Broker route.
5. New operation/port work by use: first review HubSpot gaps against its existing
   package, then Gmail/Google gaps against the unified package; source Stripe
   separately; then Notion, GitHub and Slack. Start credentialed proof with an
   already admitted operation and a synthetic provider double agreed with
   zeoconnect-integrations. Runtime priorities remain subject to owner agreement.
6. Remaining VeyraX work only as a consumer needs it: task/workflow tools
   (Linear, Jira, Asana, Todoist, Trello); mail/storage (Outlook, Dropbox, Resend,
   SMTP); database family (PostgreSQL/Neon/Supabase SQL, ClickHouse, Snowflake);
   search/research and remaining API-key tools; heavier browser, media, social,
   QR bridge and unregistered adapters after their runtime dependencies are
   reviewed. This is a proposed demand order, not authorization for 79 ports.

## Contract and runtime boundary

SOW-36 specifies manifest metadata, package names, entry-point preservation and
qualification, but no implemented machine serialization or new Broker ABI.
zeoconnect-tools confirmed this remains joint zeocore/maintainer/council design
(`ans_a055ed6a622cf24d`). Its loader will bind explicitly pinned installed
packages through ConnectorRevision and observation/effect dispatchers after
admission and custody callback. No package-owned OAuth, refresh/store custody,
caller-selected origin, or credentials in logs/results.

The reviewed design says Broker composition covers two Gmail reads, HubSpot/Kit
newsletter operations, and two Revolut reads that are HELD; it does not run
zeocore integration packages today. This is a cited design snapshot, not a claim
about current live allowlists. Confirm exact per-operation composition and
admission with the owners before each migration. An existing entry point is not
proof of an equivalent Broker operation.

The source tree's distribution is named `zeocore`; the design sometimes spells
it `zeo-core`. Package requirements must use the owner's confirmed actual name
and minimum compatible version, with real installation proof.

## Method and reproducibility

`tools/inventory.py` obtains the source HEAD commits, uses `git archive` into
memory, and parses Python AST, TOML and JSON. It executes no source code, loads
no source environment, reads no live credentials, installs no provider packages,
and writes only the report outside the source repositories. Dependency lists
are direct static imports; they do not prove dynamic imports or full transitive
closure. Lines include comments/blanks and tests. Shared-family sizes are
identified explicitly rather than counted six times.

```sh
uv run --frozen python tools/inventory.py \
  --veyrax /path/to/veyrax-platform \
  --zeocore /path/to/zeocore \
  --output docs/inventory/snapshot.json
```

Use checkouts at the cited commits to reproduce this snapshot. Tables are derived
from the JSON with auth and overlap qualifications from source review. External
import roots map to distributions as follows; exact VeyraX source pins appear in
the JSON and require review for Python 3.14 rather than blind reuse.

| Import root | Distribution |
|---|---|
| bs4 | beautifulsoup4 |
| googleapiclient | google-api-python-client |
| google | google-auth / google-auth-oauthlib (submodule dependent) |
| dotenv | python-dotenv |
| dateutil | python-dateutil (not directly pinned in source requirements) |
| starlette | starlette (transitive through FastAPI) |
| amazon_paapi | python-amazon-paapi |
| clickhouse_driver | clickhouse-driver |
| e2b_code_interpreter | e2b-code-interpreter |
| psycopg2 | psycopg2-binary |
| snowflake | snowflake-connector-python |
| slack_sdk | slack-sdk |
| sentry_sdk | sentry-sdk |
| upstash_vector | upstash-vector |
| yaml | PyYAML |
| youtube_transcript_api | youtube-transcript-api |
| pydantic_core | pydantic-core |
| notion_client | notion-client (zeocore) |
| ffmpeg_zeo | ffmpeg-zeo (zeocore) |
| docx | python-docx in zeocore; VeyraX separately pins docx |

Other displayed roots use their distribution spelling (normalizing underscores
to hyphens where applicable). No VeyraX implementation is copied in this slice.
Its complete MIT notice is preserved in [VeyraX-MIT.txt](../licenses/VeyraX-MIT.txt).
