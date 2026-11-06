# Integration coverage — 31 October 2026

All 111 supplied rows are accounted for below. HTTP counts are exposed client operations, not a claim of parity with VeyraX service actions. Synthetic request tests stop at the injected dispatch boundary. Existing and migrated providers have their own APIs.

| Integration | Source | State | Scope |
|---|---|---|---|
| airbnb | VeyraX | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| airtable | VeyraX | HTTP source port | 21 executable catalogue operations; synthetic request vectors; not live-qualified. |
| amazon | VeyraX | selected injected-adapter operations | Injected product search, item lookup, variations, browse nodes; local product URL parsing. |
| apollo | VeyraX | HTTP source port | 6 executable catalogue operations; synthetic request vectors; not live-qualified. |
| asana | VeyraX | HTTP source port | 26 executable catalogue operations; synthetic request vectors; not live-qualified. |
| bannerbear | VeyraX | HTTP source port | 53 executable catalogue operations; synthetic request vectors; not live-qualified. |
| binance_p2p | VeyraX | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| brave | VeyraX | HTTP source port | 4 executable catalogue operations; synthetic request vectors; not live-qualified. |
| browser_use | VeyraX | HTTP source port | 11 executable catalogue operations; synthetic request vectors; not live-qualified. |
| browserbase | VeyraX | HTTP source port | 17 executable catalogue operations; synthetic request vectors; not live-qualified. |
| bybit_p2p | VeyraX | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| cal | VeyraX | HTTP source port | 10 executable catalogue operations; synthetic request vectors; not live-qualified. |
| clickhouse | VeyraX | DB-API adapter | Bounded parameterized SQL transaction execution; injected connection; explicit effect admission. |
| cloudinary | VeyraX | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| coda | VeyraX | HTTP source port | 25 executable catalogue operations; synthetic request vectors; not live-qualified. |
| common | VeyraX | excluded by brief | Not a provider; auth/custody not copied. |
| confluence | VeyraX | HTTP source port | 4 executable catalogue operations; synthetic request vectors; not live-qualified. |
| docusign | VeyraX | HTTP source port | 7 executable catalogue operations; synthetic request vectors; not live-qualified. |
| dropbox | VeyraX | HTTP source port | 8 executable catalogue operations; synthetic request vectors; not live-qualified. |
| dub | VeyraX | HTTP source port | 28 executable catalogue operations; synthetic request vectors; not live-qualified. |
| duckduckgo | VeyraX | HTTP source port | 1 executable catalogue operations; synthetic request vectors; not live-qualified. |
| e2b | VeyraX | selected injected-adapter operations | Injected foreground commands and code execution returning text/logs. |
| exa | VeyraX | HTTP source port | 3 executable catalogue operations; synthetic request vectors; not live-qualified. |
| facebook | VeyraX | HTTP source port | 13 executable catalogue operations; synthetic request vectors; not live-qualified. |
| falai | VeyraX | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| figma | VeyraX | HTTP source port | 12 executable catalogue operations; synthetic request vectors; not live-qualified. |
| firecrawl | VeyraX | HTTP source port | 7 executable catalogue operations; synthetic request vectors; not live-qualified. |
| github | VeyraX | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| gmail | VeyraX | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| google_calendar | VeyraX | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| google_docs | VeyraX | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| google_drive | VeyraX | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| google_maps | VeyraX | HTTP source port | 7 executable catalogue operations; synthetic request vectors; not live-qualified. |
| google_sheets | VeyraX | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| hacker_news | VeyraX | HTTP source port | 9 executable catalogue operations; synthetic request vectors; not live-qualified. |
| heygen | VeyraX | HTTP source port | 25 executable catalogue operations; synthetic request vectors; not live-qualified. |
| hilvl | VeyraX | HTTP source port | 51 executable catalogue operations; synthetic request vectors; not live-qualified. |
| http_request | VeyraX | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| hunterio | VeyraX | HTTP source port | 8 executable catalogue operations; synthetic request vectors; not live-qualified. |
| instagram | VeyraX | HTTP source port | 7 executable catalogue operations; synthetic request vectors; not live-qualified. |
| ipinfo | VeyraX | HTTP source port | 3 executable catalogue operations; synthetic request vectors; not live-qualified. |
| jira | VeyraX | HTTP source port | 19 executable catalogue operations; synthetic request vectors; not live-qualified. |
| linear | VeyraX | HTTP source port | 14 executable catalogue operations; synthetic request vectors; not live-qualified. |
| linkedin | VeyraX | HTTP source port | 15 executable catalogue operations; synthetic request vectors; not live-qualified. |
| mail | VeyraX | selected injected-adapter operations | Injected SMTP send plus read-only IMAP UID listing and UIDVALIDITY-fenced message reads. |
| motion | VeyraX | HTTP source port | 20 executable catalogue operations; synthetic request vectors; not live-qualified. |
| n8n | VeyraX | HTTP source port | 4 executable catalogue operations; synthetic request vectors; not live-qualified. |
| neondb | VeyraX | DB-API adapter | Bounded parameterized SQL transaction execution; injected connection; explicit effect admission. |
| notion | VeyraX | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| okx_p2p | VeyraX | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| openweather | VeyraX | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| outlook | VeyraX | HTTP source port | 10 executable catalogue operations; synthetic request vectors; not live-qualified. |
| perplexity | VeyraX | HTTP source port | 0 executable catalogue operations; synthetic request vectors; not live-qualified. |
| postgresql | VeyraX | DB-API adapter | Bounded parameterized SQL transaction execution; injected connection; explicit effect admission. |
| posthog | VeyraX | HTTP source port | 34 executable catalogue operations; synthetic request vectors; not live-qualified. |
| postman | VeyraX | HTTP source port | 16 executable catalogue operations; synthetic request vectors; not live-qualified. |
| readwise | VeyraX | HTTP source port | 4 executable catalogue operations; synthetic request vectors; not live-qualified. |
| reddit | VeyraX | HTTP source port | 20 executable catalogue operations; synthetic request vectors; not live-qualified. |
| replicate | VeyraX | HTTP source port | 28 executable catalogue operations; synthetic request vectors; not live-qualified. |
| resend | VeyraX | HTTP source port | 25 executable catalogue operations; synthetic request vectors; not live-qualified. |
| revid | VeyraX | HTTP source port | 5 executable catalogue operations; synthetic request vectors; not live-qualified. |
| sentry | VeyraX | HTTP source port | 17 executable catalogue operations; synthetic request vectors; not live-qualified. |
| skyscanner | VeyraX | HTTP source port | 11 executable catalogue operations; synthetic request vectors; not live-qualified. |
| slack | VeyraX | HTTP source port | 5 executable catalogue operations; synthetic request vectors; not live-qualified. |
| snowflake | VeyraX | DB-API adapter | Bounded parameterized SQL transaction execution; injected connection; explicit effect admission. |
| supabase | VeyraX | DB-API adapter | Bounded parameterized SQL transaction execution; injected connection; explicit effect admission. |
| svgl | VeyraX | HTTP source port | 4 executable catalogue operations; synthetic request vectors; not live-qualified. |
| tavily | VeyraX | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| ticktick | VeyraX | HTTP source port | 11 executable catalogue operations; synthetic request vectors; not live-qualified. |
| todoist | VeyraX | HTTP source port | 31 executable catalogue operations; synthetic request vectors; not live-qualified. |
| trello | VeyraX | HTTP source port | 20 executable catalogue operations; synthetic request vectors; not live-qualified. |
| twentyfirst_dev | VeyraX | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| typeform | VeyraX | HTTP source port | 42 executable catalogue operations; synthetic request vectors; not live-qualified. |
| uploadthing | VeyraX | HTTP source port | 10 executable catalogue operations; synthetic request vectors; not live-qualified. |
| vercel | VeyraX | HTTP source port | 17 executable catalogue operations; synthetic request vectors; not live-qualified. |
| veyrax | VeyraX | excluded by brief | Not a provider; auth/custody not copied. |
| veyrax-mcp | VeyraX | excluded by brief | Not a provider; auth/custody not copied. |
| veyrax_auth | VeyraX | excluded by brief | Not a provider; auth/custody not copied. |
| whatsapp | VeyraX | selected injected-adapter operations | Injected send and account-bound chat/history/contact reads. |
| x | VeyraX | HTTP source port | 15 executable catalogue operations; synthetic request vectors; not live-qualified. |
| yelp | VeyraX | HTTP source port | 4 executable catalogue operations; synthetic request vectors; not live-qualified. |
| youtube | VeyraX | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| zillow | VeyraX | HTTP source port | 12 executable catalogue operations; synthetic request vectors; not live-qualified. |
| zip_code | VeyraX | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| github | zeocore | Core source migrated | Provider source and travelling tests; Core registrations unchanged; legacy APIs retain credential behavior. |
| google.mail | zeocore | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| google.drive | zeocore | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| google.calendar | zeocore | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| google.docs | zeocore | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| google.sheets | zeocore | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| google.slides | zeocore | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| pandoc | zeocore | Core source migrated | Provider source and travelling tests; Core registrations unchanged; legacy APIs retain credential behavior. |
| llms | zeocore | Core source migrated | Provider source and travelling tests; Core registrations unchanged; legacy APIs retain credential behavior. |
| ffmpeg | zeocore | Core source migrated | Provider source and travelling tests; Core registrations unchanged; legacy APIs retain credential behavior. |
| notion | zeocore | Core source migrated | Provider source and travelling tests; Core registrations unchanged; legacy APIs retain credential behavior. |
| supabase | zeocore | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| hubspot.marketing | zeocore | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| kit.marketing | zeocore | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| jupytext | zeocore | Core source migrated | Provider source and travelling tests; Core registrations unchanged; legacy APIs retain credential behavior. |
| social.bluesky | zeocore | Core source migrated | Provider source and travelling tests; Core registrations unchanged; legacy APIs retain credential behavior. |
| revolut.business | zeocore | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| loops | new | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| mastodon | new | existing or migrated source | See provider tests and API; module presence does not prove full VeyraX action parity. |
| telegram | new | Telegram client imported and tested | Receive, durable-prefix ACK, send and callback client; Connect server not included. |
| substack | new | not implemented | Notes requested by operator; unofficial client and distributed 1rps emission fence remain to implement. |
| stripe | new | HTTP source port | 2 executable catalogue operations; synthetic request vectors; not live-qualified. |
| voice router | zeocore direction | Core-owned dependency | Shared MediaSource/router successor was not supplied as merged code. No competing router or migration created. |
| cloudflare | new | held by brief | Waits on ZEOconnect; seats do not run cf. |
| storage box media sink | new | held by brief | directions/DIRECTION-operator-storage-box-media-sink-2026-10-29.md |
| tiktok | publishing decision | selected publishing operations | Original official publishing client; see docs/council/PUBLISHING.md for supported operations and deployment gaps. |
| x publishing | publishing decision | selected publishing operations | Original official publishing client; see docs/council/PUBLISHING.md for supported operations and deployment gaps. |

## Follow-up implementation

The HTTP operation count remains 803; the native adapters are separate surfaces.
Amazon now includes items, variations and browse-node lookups. Mail includes
read-only IMAP listing and message fetch. WhatsApp includes bound chat/history
reads, and E2B includes text-only code execution results. The HTTPX transport and
Loops Connect result adapter are implemented. See CONNECT.md for the remaining
host wiring and the observed Connect/Core dependency conflict.

The publishing target now also includes Threads, which was absent from the original
111-row list. See PUBLISHING.md for the nine-platform matrix; source-row coverage
is not publishing completion.
