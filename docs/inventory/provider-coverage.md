# Provider coverage inventory

This is a coverage and implementation-order inventory, not a statement that all services are implemented or usable. It enumerates 84 reference folders: 66 fresh implementations, 13 extensions or reconciliations within existing families, and five excluded internal facilities. Existing family names do not establish operation parity, credential support or deployment.

## Evidence and interpretation

- Coverage reference: [veyrax-platform integrations](https://github.com/rodriveracom/veyrax-platform/tree/1cdddde9d5d76b9891896ca78a95e069647e81df/aci_server/integrations), pinned at `1cdddde9d5d76b9891896ca78a95e069647e81df`. Names, sampled operation coverage, credential-input identifiers and import metadata were inspected read-only. No reference implementation, function or test is copied or adapted. Fresh ports require their own official provider contract and tests.
- Existing aggregate baseline: [3a5c24db](https://github.com/zeroemployeeorg/zeointegrations/commit/3a5c24db7111935b44e6fe6752ef57e1404debbc). Core baseline: `653117d7098efa4a7d3af70fe81546528bab1809`, integration namespace only. The counterpart column is aggregate module / Core module; “none named” does not prove that no generic helper or other provider client exists elsewhere.
- Auth is an observed reference input kind, not proof of an official provider auth flow. In particular, API-key-backed social/search wrappers can be intermediaries. Their host, product, scopes and enrollment must be settled from official contracts before a fresh implementation. New clients take explicitly injected credentials and do not discover files or environment secrets. Credential custody and refresh remain with the executing host.
- Dependencies are observed import roots in sampled client/service/route modules, not package distribution names, pinned versions, exhaustive transitive closure or new dependency approvals. Shared `pydantic` models and reference-only FastAPI/Starlette routing are omitted from cells; those web frameworks are not a requirement for a library port. Existing optional extras stay optional. `dotenv` observations are legacy reference behavior to replace with injected inputs.
- Sizes are observed reference Python KiB, including schemas/tests, plus provisional S/M/L/XL bands (<=15/35/70/>70KiB). They are planning estimates, not a copied-code budget or elapsed-time commitment. Official operation census determines each actual slice.
- The tree has 84 folders and 80 `component.json` files. `bannerbear`, `common`, `neondb` and `veyrax` have no such file at the pin. Component presence is not the criterion for inclusion or a credential contract. No UI component, image, font or other asset is ported.

## Service decisions

PORT means write fresh client/models/tests. MERGE means reconcile or extend the named aggregate family, not copy reference source or silently replace a current API. SKIP retains the provider-independent Core/host facilities instead of importing reference internals. Each row has a coverage scope, auth input, observed dependencies, counterpart and batch order.

| Service | Coverage / decision | Auth input observed | Dependencies observed | Aggregate / Core counterpart | Size KiB / band | Batch |
|---|---|---|---|---|---:|---:|
| `airbnb` | PORT → airbnb: Listing search and details | No auth marker in sampled web client; access contract unresolved | `bs4`, `httpx` | none named / none named | 23.1 / M | 3 |
| `airtable` | PORT → airtable: Bases, tables, records and webhooks | Access-token input (Bearer observed) | `requests` | none named / none named | 47.0 / L | 2 |
| `amazon` | PORT → amazon: Product search, items and variations | Secret-key credentials input; signed product API contract to confirm | `amazon_paapi` | none named / none named | 18.8 / M | 3 |
| `apollo` | PORT → apollo: People and organization discovery | API-key input | `requests` | none named / none named | 20.4 / M | 3 |
| `asana` | PORT → asana: Projects, tasks, sections and goals | Access-token input (Bearer observed) | `requests` | none named / none named | 58.7 / L | 3 |
| `bannerbear` | PORT → bannerbear: Images, templates, video and render jobs | API-key input (Bearer observed) | `requests` | none named / none named | 63.6 / L | 3 |
| `binance_p2p` | PORT → binance_p2p: Peer-to-peer offer discovery | API-key input | `requests` | none named / none named | 9.5 / S | 3 |
| `brave` | PORT → brave: Web, news, images and video search | API-key input | `requests` | none named / none named | 20.0 / M | 3 |
| `browser_use` | PORT → browser_use: Remote browser task lifecycle | API-key input (Bearer observed) | `requests` | none named / none named | 15.2 / M | 3 |
| `browserbase` | PORT → browserbase: Remote browser sessions and contexts | API-key input | `requests` | none named / none named | 33.1 / M | 3 |
| `bybit_p2p` | PORT → bybit_p2p: Peer-to-peer offer discovery | API-key input | `requests` | none named / none named | 8.4 / S | 3 |
| `cal` | PORT → cal: Bookings, schedules and event types | API-key input (Bearer observed) | `requests` | none named / none named | 26.5 / M | 4 |
| `clickhouse` | PORT → clickhouse: Queries and schema discovery | Database credentials/password input | `clickhouse_driver` | none named / none named | 11.6 / S | 4 |
| `cloudinary` | PORT → cloudinary: Asset upload, metadata and deletion | API-key/credential input; signing details to confirm | `requests` | none named / none named | 36.3 / L | 4 |
| `coda` | PORT → coda: Documents, tables, rows and pages | API-key input (Bearer observed) | `requests` | none named / none named | 45.6 / L | 4 |
| `common` | SKIP: Shared internal auth/tool scaffolding; use existing host contracts. | Excluded internal facility; no credential migration | `requests` | none named / none named | 127.5 / excluded | — |
| `confluence` | PORT → confluence: Pages, spaces and content search | OAuth/access-token input; host owns refresh and scopes | `requests` | none named / none named | 24.3 / M | 2 |
| `docusign` | PORT → docusign: Envelopes, signing view and documents | OAuth/access-token input; host owns refresh and scopes | `PyPDF2`, `requests` | none named / none named | 23.4 / M | 4 |
| `dropbox` | PORT → dropbox: Files, folders, search, links and downloads | Access-token input (Bearer observed) | `requests` | none named / none named | 32.7 / M | 4 |
| `dub` | PORT → dub: Links, domains, customers and analytics | API-key input (Bearer observed) | `requests` | none named / none named | 40.3 / L | 4 |
| `duckduckgo` | PORT → duckduckgo: Search and fetched content | No auth marker in sampled search client | `requests` | none named / none named | 9.5 / S | 4 |
| `e2b` | PORT → e2b: Sandbox lifecycle, commands, code and files | API-key input | `e2b_code_interpreter` | none named / none named | 26.7 / M | 4 |
| `exa` | PORT → exa: Search, similar pages and contents | API-key input (Bearer observed) | `requests` | none named / none named | 10.7 / S | 4 |
| `facebook` | MERGE → publishing: Page/group/profile/post reads; reconcile existing publishing writes | Reference API-key input; official Meta auth parity not established | `requests` | `publishing` (writes/helpers; read surface incomplete) / none named | 39.8 / L | 5 |
| `falai` | PORT → falai: Model generation, jobs and uploads | API-key input | `httpx` | none named / none named | 18.5 / M | 5 |
| `figma` | PORT → figma: Files, nodes, components and images | Access-token input (Bearer observed) | `requests` | none named / none named | 23.0 / M | 5 |
| `firecrawl` | PORT → firecrawl: Crawl, scrape and search results | API-key input (Bearer observed) | `requests` | none named / none named | 24.2 / M | 5 |
| `github` | MERGE → github: Repositories, issues, commits, contents and pull requests | Access-token input; official token kind/scopes to confirm | `requests`, `yaml` | `github` / `github`; partial, reconcile behavior | 67.5 / L | 1 |
| `gmail` | MERGE → google/mail: Messages, drafts, send and trash | OAuth/access-token input; host owns refresh and scopes | `dateutil`, `google`, `googleapiclient` | `google/mail` / `google/mail`; partial, reconcile behavior | 34.1 / M | 1 |
| `google_calendar` | MERGE → google/calendar: Calendars and event CRUD | OAuth/access-token input; host owns refresh and scopes | `google`, `googleapiclient` | `google/calendar` / `google/calendar`; partial, reconcile behavior | 18.7 / M | 1 |
| `google_docs` | MERGE → google/docs: Documents, text search and batch updates | OAuth/access-token input; host owns refresh and scopes | `google`, `googleapiclient` | `google/docs` / `google/docs`; partial, reconcile behavior | 16.0 / M | 1 |
| `google_drive` | MERGE → google/drive: Files, folders, permissions and downloads | OAuth/access-token input; host owns refresh and scopes | `aiohttp`, `dateutil`, `google`, `googleapiclient`, `requests` | `google/drive` / `google/drive`; partial, reconcile behavior | 49.1 / L | 1 |
| `google_maps` | PORT → google_maps: Places, geocoding, directions and distances | API-key input | `requests` | none named / none named | 22.2 / M | 2 |
| `google_sheets` | MERGE → google/sheets: Spreadsheet values, sheets and formulas | OAuth/access-token input; host owns refresh and scopes | `google`, `googleapiclient` | `google/sheets` / `google/sheets`; partial, reconcile behavior | 28.4 / M | 1 |
| `hacker_news` | PORT → hacker_news: Stories, comments, users and items | No auth marker; username is a lookup input | `requests` | none named / none named | 17.0 / M | 5 |
| `heygen` | PORT → heygen: Video, avatars, templates and generation jobs | API-key input | `requests` | none named / none named | 46.6 / L | 5 |
| `hilvl` | PORT → hilvl: HighLevel CRM resources; large surface requires operation census | API-key input (Bearer observed) | `requests` | none named / none named | 128.7 / XL | 5 |
| `http_request` | SKIP: Generic arbitrary-request facility, not a provider client. | Excluded internal facility; no credential migration | `requests` | none named / none named | 9.6 / excluded | — |
| `hunterio` | PORT → hunterio: Domain/person discovery and email checks | API-key input | `requests` | none named / none named | 33.3 / M | 5 |
| `instagram` | MERGE → publishing: Profile/media reads; add fresh adapter within publishing family | Reference API-key input; official Meta auth parity not established | `requests` | `publishing` family only; fresh adapter needed / none named | 22.6 / M | 5 |
| `ipinfo` | PORT → ipinfo: IP, ASN and bulk lookup | API-key input | `requests` | none named / none named | 10.9 / S | 5 |
| `jira` | PORT → jira: Issues, projects, users and transitions | OAuth/access-token input; host owns refresh and scopes | `requests` | none named / none named | 42.4 / L | 2 |
| `linear` | PORT → linear: Issues, teams, projects, labels and comments | Access-token input (Bearer observed) | `requests` | none named / none named | 45.4 / L | 2 |
| `linkedin` | MERGE → publishing: Profiles and pages; distinguish existing publishing composition from actual read transport | Reference API-key input; official LinkedIn auth parity not established | `requests` | `publishing` family only; fresh adapter needed / none named | 57.6 / L | 6 |
| `mail` | PORT → mail: Mailbox folders, messages and send; settle protocol/provider identity | Username/password input; mailbox protocol contract to confirm | stdlib email / IMAP / SMTP | none named / none named | 78.8 / XL | 6 |
| `motion` | PORT → motion: Tasks, projects, workspaces and scheduling | API-key input | `requests` | none named / none named | 45.6 / L | 6 |
| `n8n` | PORT → n8n: Workflow execution/configuration; credential objects remain Broker-owned | API-key input | `requests` | none named / none named | 55.6 / L | 6 |
| `neondb` | PORT → neondb: SQL queries and schema discovery | Database credentials via shared PostgreSQL adapter | shared PostgreSQL adapter → psycopg2 | none named / none named | 2.9 / S | 6 |
| `notion` | MERGE → notion: Pages, blocks, databases, users and media | Access-token input (Bearer observed) | `requests` | `notion` / `notion`; partial, reconcile behavior | 104.3 / XL | 1 |
| `okx_p2p` | PORT → okx_p2p: Peer-to-peer offer discovery | API-key input | `requests` | none named / none named | 8.2 / S | 6 |
| `openweather` | PORT → openweather: Current weather and forecasts | API-key input | `dotenv`, `requests` | none named / none named | 8.6 / S | 6 |
| `outlook` | PORT → outlook: Messages, drafts, send, calendars and events | Access-token input (Bearer observed) | `requests` | none named / none named | 30.3 / M | 1 |
| `perplexity` | PORT → perplexity: Completion requests through approved execution boundary | API-key input (Bearer observed) | `requests` | none named / none named | 8.0 / S | 6 |
| `postgresql` | PORT → postgresql: SQL queries and schema discovery | Database credentials/password input | `psycopg2` | none named / none named | 11.7 / S | 2 |
| `posthog` | PORT → posthog: Analytics resources; require scoped operation census | API-key input (Bearer observed) | `requests` | none named / none named | 74.1 / XL | 6 |
| `postman` | PORT → postman: Collections, environments and workspaces | API-key input | `requests` | none named / none named | 40.9 / L | 6 |
| `readwise` | PORT → readwise: Reading/highlight resources | API-key input | `requests` | none named / none named | 12.6 / S | 7 |
| `reddit` | PORT → reddit: Posts, comments, community reads and edits | OAuth/access-token input; host owns refresh and scopes | `aiohttp`, `requests` | none named / none named | 44.7 / L | 2 |
| `replicate` | PORT → replicate: Models, predictions, training and deployments | API-key input (Bearer observed) | `requests` | none named / none named | 90.7 / XL | 7 |
| `resend` | PORT → resend: Email, contacts, audiences, domains and broadcasts; keys remain Broker-owned | API-key input (Bearer observed) | `requests` | none named / none named | 53.6 / L | 7 |
| `revid` | PORT → revid: Video jobs, status and publishing | API-key input | `requests` | none named / none named | 17.2 / M | 7 |
| `sentry` | PORT → sentry: Issues, organizations, projects, releases and alert rules | OAuth/access-token input; host owns refresh and scopes | `requests` | none named / none named | 43.2 / L | 7 |
| `skyscanner` | PORT → skyscanner: Flights, hotels and price calendars; settle licensed API identity | API-key input | `requests` | none named / none named | 37.4 / L | 7 |
| `slack` | PORT → slack: Channels, histories, threads, messages and direct messages | Access-token input | `slack_sdk` | none named / none named | 28.1 / M | 1 |
| `snowflake` | PORT → snowflake: SQL queries and schema discovery | Database credentials/password input | `snowflake` | none named / none named | 12.5 / S | 7 |
| `supabase` | MERGE → supabase: SQL and schema discovery; existing REST/storage client is not arbitrary SQL parity | Database credentials via shared PostgreSQL adapter; not REST parity | shared PostgreSQL adapter → psycopg2 | `supabase` / `database/supabase`; partial, reconcile behavior | 2.9 / S | 2 |
| `svgl` | PORT → svgl: Catalog/search identifiers only; never copy or move image/font assets | No auth marker in sampled catalog client | `requests` | none named / none named | 7.6 / S | 7 |
| `tavily` | PORT → tavily: Search and extraction | API-key input (Bearer observed) | `requests` | none named / none named | 10.5 / S | 7 |
| `ticktick` | PORT → ticktick: Projects, tasks and completion | Access-token input (Bearer observed) | `requests` | none named / none named | 15.7 / M | 7 |
| `todoist` | PORT → todoist: Tasks, projects, sections, comments and labels | Access-token input (Bearer observed) | `requests` | none named / none named | 48.9 / L | 8 |
| `trello` | PORT → trello: Boards, lists, cards and checklists | Access-token input | `dotenv`, `requests` | none named / none named | 27.3 / M | 8 |
| `twentyfirst_dev` | PORT → twentyfirst_dev: Component search and prompt generation; returned code is untrusted data | API-key input | `requests` | none named / none named | 7.2 / S | 8 |
| `typeform` | PORT → typeform: Forms, responses, workspaces and webhooks | Access-token input (Bearer observed) | `requests` | none named / none named | 38.2 / L | 8 |
| `uploadthing` | PORT → uploadthing: Uploads, files, callbacks and usage | API-key input | `requests` | none named / none named | 60.8 / L | 8 |
| `vercel` | PORT → vercel: Projects, deployments, domains and environment metadata; credentials stay Broker-owned | Access-token input (Bearer observed) | `requests` | none named / none named | 64.3 / L | 8 |
| `veyrax` | SKIP: Internal memory service, excluded. | Excluded internal facility; no credential migration | No additional import root observed | none named / none named | 9.9 / excluded | — |
| `veyrax-mcp` | SKIP: Internal deployment and connection management, excluded. | Excluded internal facility; no credential migration | `httpx`, `upstash_vector` | none named / none named | 12.0 / excluded | — |
| `veyrax_auth` | SKIP: Internal enrollment and credential custody, excluded. | Excluded internal facility; no credential migration | `requests`, `supabase` | none named / none named | 12.6 / excluded | — |
| `whatsapp` | PORT → whatsapp: Session/chat/history surface differs from existing Twilio WhatsApp; settle supported transport, never copy session/DB custody | Session/QR bridge; no token marker, enrollment contract unresolved | `qrcode`, `requests` | none named / none named | 57.9 / L | 2 |
| `x` | MERGE → publishing: Timeline, tweets, users, spaces and lists; current publish/thread/media helpers are partial coverage | Reference API-key input; official X OAuth parity not established | `requests` | `publishing` (writes/helpers; read surface incomplete) / none named | 52.5 / L | 2 |
| `yelp` | PORT → yelp: Business discovery, details and reviews | API-key input | `requests` | none named / none named | 24.0 / M | 8 |
| `youtube` | MERGE → google/youtube: Search, video, captions and transcription | API-key input; transcript helper has separate access behavior | `dateutil`, `googleapiclient`, `youtube_transcript_api` | `google/youtube` / `google/youtube`; partial, reconcile behavior | 15.3 / M | 1 |
| `zillow` | PORT → zillow: Property, market, valuation, comps and history | API-key input | `requests` | none named / none named | 41.5 / L | 8 |
| `zip_code` | PORT → zip_code: City and postal-code lookup | API-key input | `requests` | none named / none named | 9.4 / S | 8 |

## Batch order and acceptance

Each batch is a queue of about ten service coverage lines. Each source PR remains a small coherent concern: freeze official operations and credential/error/pagination/resource boundaries before code, and split oversized surfaces explicitly. Listing ten services does not promise full-service parity in one PR. Sheets leads the first batch because of its existing injected-credential consumer path.

| Batch | Ordered queue |
|---|---|
| 1 | `google_sheets`, `gmail`, `google_calendar`, `google_docs`, `google_drive`, `youtube`, `github`, `notion`, `slack`, `outlook` |
| 2 | `linear`, `jira`, `whatsapp`, `x`, `reddit`, `supabase`, `postgresql`, `google_maps`, `airtable`, `confluence` |
| 3 | `airbnb`, `amazon`, `apollo`, `asana`, `bannerbear`, `binance_p2p`, `brave`, `browser_use`, `browserbase`, `bybit_p2p` |
| 4 | `cal`, `clickhouse`, `cloudinary`, `coda`, `docusign`, `dropbox`, `dub`, `duckduckgo`, `e2b`, `exa` |
| 5 | `facebook`, `falai`, `figma`, `firecrawl`, `hacker_news`, `heygen`, `hilvl`, `hunterio`, `instagram`, `ipinfo` |
| 6 | `linkedin`, `mail`, `motion`, `n8n`, `neondb`, `okx_p2p`, `openweather`, `perplexity`, `posthog`, `postman` |
| 7 | `readwise`, `replicate`, `resend`, `revid`, `sentry`, `skyscanner`, `snowflake`, `svgl`, `tavily`, `ticktick` |
| 8 | `todoist`, `trello`, `twentyfirst_dev`, `typeform`, `uploadthing`, `vercel`, `yelp`, `zillow`, `zip_code` |

For the four social services, keep per-service contracts distinct. Existing X thread/media/publishing helpers do not implement all timeline/user/space/list reads. Facebook publishing does not imply page/group/profile reading. Instagram and LinkedIn require fresh bounded transport adapters despite sharing a publishing family. Likewise, the existing Supabase REST/storage client does not establish the reference SQL execution surface, and the existing WhatsApp transport does not establish session/chat-history parity.

Acceptance for each fresh slice includes strict Pydantic v2 request/response models, explicit credentials, the shared Core integration result contract, data-only outputs, bounded resource/error handling and synthetic offline tests that refuse live network traffic. Unknown write results must be reconciled, not blindly retried. Library code, installed consumer acceptance, provider enrollment and live operation remain separate outcomes.

Core removals are a separate coordinated change. Preserve all unique code until deliberately moved or superseded, reconcile module and operation differences, and confirm literal plus dynamic consumers at their actual pins. Generic Core contracts, routing, loaders, runtime and credential custody stay in Core. Entry points, catalogs and compatibility imports must change only under the documented publication and consumer-transition requirements. No deletion is authorized by this inventory.

Full exact-head repository qualification and independent review are required before source publication. Optional smoke checks do not replace the full gate. This inventory introduces no runtime dependency, credential route, provider call, workflow or package release.
