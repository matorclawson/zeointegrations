# VeyraX source inventory

Canonical source: `VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df`, read through the identical local `rodriveracom/veyrax-platform` fork. All 84 tracked integration directories are listed, including shared code and unregistered directories. `routers` is the exact `INTEGRATION_ROUTERS` key, or an em dash when absent.

Dependencies are direct, static, non-standard-library **import roots**, excluding VeyraX modules; they are not a proposed install set. Shared `common` dependencies apply where imported. Test-only additions, exact byte sizes, all source requirement pins and parse errors are in [snapshot.json](snapshot.json). Lines count tracked Python files including tests; no source is imported or executed.

| Directory | routers | Auth observed (catalog unless qualified) | Dependency import roots | Python lines | zeocore overlap |
|---|---|---|---|---:|---|
| airbnb | airbnb | none | bs4, fastapi, httpx, pydantic, starlette | 635 | none |
| airtable | airtable | oauth | fastapi, pydantic, requests, starlette | 1247 | none |
| amazon | amazon | custom | amazon_paapi, fastapi, pydantic | 512 | none |
| apollo | apollo | server RapidAPI key (catalog says none) | fastapi, pydantic, requests, starlette | 579 | none |
| asana | asana | oauth | fastapi, pydantic, requests | 1589 | none |
| bannerbear | bannerbear | api_key | fastapi, pydantic, requests, starlette | 1945 | none |
| binance_p2p | binance_p2p | server RapidAPI key (catalog says none) | fastapi, pydantic, requests | 280 | none |
| brave | brave | api_key | fastapi, pydantic, requests | 529 | none |
| browser_use | browser-use | api_key | fastapi, pydantic, requests | 451 | none |
| browserbase | browserbase | api_key | fastapi, pydantic, requests, starlette | 1006 | none |
| bybit_p2p | bybit_p2p | server RapidAPI key (catalog says none) | fastapi, pydantic, requests | 257 | none |
| cal | cal | api_key | fastapi, pydantic, requests, starlette | 849 | none |
| clickhouse | clickhouse | db_access | clickhouse_driver, fastapi, pydantic | 360 | none |
| cloudinary | cloudinary | custom | fastapi, pydantic, requests, starlette | 978 | none |
| coda | coda | api_key | fastapi, pydantic, requests | 1380 | none |
| common | — | shared auth/custody support; not a provider | PyPDF2, aiohttp, cryptography, dotenv, fastapi, google, openai, pydantic, pydantic_core, requests, sentry_sdk, starlette, upstash_vector, yaml | 3584 | none |
| confluence | confluence | oauth | fastapi, pydantic, requests | 702 | none |
| docusign | — | OAuth (unregistered; route uses TokenService) | PyPDF2, fastapi, pydantic, requests, starlette | 565 | none |
| dropbox | dropbox | oauth | fastapi, pydantic, requests | 872 | none |
| dub | dub | api_key | fastapi, pydantic, requests, starlette | 1285 | none |
| duckduckgo | duckduckgo | none | fastapi, pydantic, requests, starlette | 293 | none |
| e2b | e2b | api_key | e2b_code_interpreter, fastapi, pydantic | 773 | none |
| exa | exa | api_key | fastapi, pydantic, requests, starlette | 356 | none |
| facebook | facebook | custom | fastapi, pydantic, requests, starlette | 1264 | none |
| falai | falai | api_key | fastapi, httpx, pydantic, starlette | 593 | none |
| figma | figma | oauth | fastapi, pydantic, requests, starlette | 617 | none |
| firecrawl | firecrawl | api_key | fastapi, pydantic, requests | 718 | none |
| github | github | oauth | fastapi, pydantic, requests, starlette, yaml | 1986 | github |
| gmail | — | OAuth (imported but unregistered in router registry/catalog) | dateutil, fastapi, google, googleapiclient, pydantic | 872 | google.mail |
| google_calendar | google-calendar | oauth | fastapi, google, googleapiclient, pydantic | 505 | google.calendar |
| google_docs | google-docs | oauth | fastapi, google, googleapiclient, pydantic | 434 | google.docs |
| google_drive | google-drive | oauth | aiohttp, dateutil, fastapi, google, googleapiclient, pydantic, requests | 1310 | google.drive |
| google_maps | google-maps | api_key | fastapi, pydantic, requests, starlette | 706 | none |
| google_sheets | google-sheets | oauth | fastapi, google, googleapiclient, pydantic | 722 | google.sheets |
| hacker_news | hacker-news | none | fastapi, pydantic, requests | 538 | none |
| heygen | heygen | api_key | fastapi, pydantic, requests, starlette | 1410 | none |
| hilvl | — | API key (unregistered; validate_provider_api_key) | fastapi, pydantic, requests, starlette | 3555 | none |
| http_request | http-request | none | fastapi, pydantic, requests | 240 | none |
| hunterio | hunterio | api_key | fastapi, pydantic, requests | 961 | none |
| instagram | instagram | custom | fastapi, pydantic, requests, starlette | 684 | none |
| ipinfo | ipinfo | server API token (catalog says none) | fastapi, pydantic, requests | 340 | none |
| jira | jira | oauth | fastapi, pydantic, requests | 1143 | none |
| linear | linear | oauth | fastapi, pydantic, requests | 1318 | none |
| linkedin | linkedin | custom | fastapi, pydantic, requests, starlette | 1608 | none |
| mail | mail | custom | fastapi, pydantic, starlette | 2063 | none |
| motion | motion | api_key | fastapi, pydantic, requests | 1146 | none |
| n8n | n8n | api_key_with_base | fastapi, pydantic, requests | 1602 | none |
| neondb | neondb | database credentials; delegates to postgresql | fastapi | 68 | none |
| notion | notion | oauth | fastapi, pydantic, requests | 2890 | notion |
| okx_p2p | okx_p2p | server RapidAPI key (catalog says none) | fastapi, pydantic, requests | 257 | none |
| openweather | openweather | api_key | dotenv, fastapi, pydantic, requests | 243 | none |
| outlook | outlook | oauth | fastapi, pydantic, requests | 839 | none |
| perplexity | perplexity | api_key | fastapi, pydantic, requests | 214 | none |
| postgresql | postgresql | db_access | fastapi, psycopg2, pydantic | 355 | none |
| posthog | posthog | api_key_with_base | fastapi, pydantic, requests, starlette | 1874 | none |
| postman | postman | api_key | fastapi, pydantic, requests | 1136 | none |
| readwise | readwise | api_key | fastapi, pydantic, requests, starlette | 342 | none |
| reddit | reddit | oauth | aiohttp, fastapi, pydantic, requests, starlette | 1320 | none |
| replicate | replicate | api_key | fastapi, pydantic, requests | 2345 | none |
| resend | resend | api_key | fastapi, pydantic, requests | 1504 | none |
| revid | revid | api_key | fastapi, pydantic, requests | 467 | none |
| sentry | sentry | custom | fastapi, pydantic, requests | 1257 | none |
| skyscanner | skyscanner | server RapidAPI key (catalog says none) | fastapi, pydantic, requests, starlette | 1158 | none |
| slack | slack | oauth | fastapi, pydantic, slack_sdk | 734 | none |
| snowflake | snowflake | db_access | fastapi, pydantic, snowflake | 378 | none |
| supabase | supabase | database credentials; delegates to postgresql | fastapi | 68 | supabase (different API: SQL, not SDK) |
| svgl | svgl | none | fastapi, pydantic, requests | 239 | none |
| tavily | tavily | api_key | fastapi, pydantic, requests | 312 | none |
| ticktick | ticktick | oauth | fastapi, pydantic, requests | 403 | none |
| todoist | todoist | oauth | fastapi, pydantic, requests, starlette | 1484 | none |
| trello | trello | oauth | dotenv, fastapi, pydantic, requests | 758 | none |
| twentyfirst_dev | twentyfirst_dev | api_key | fastapi, pydantic, requests, starlette | 224 | none |
| typeform | typeform | api_key | fastapi, pydantic, requests, starlette | 1020 | none |
| uploadthing | uploadthing | api_key | fastapi, pydantic, requests, starlette | 1730 | none |
| vercel | vercel | oauth | fastapi, pydantic, requests | 1773 | none |
| veyrax | veyrax | VeyraX internal workflow support; not a provider port | fastapi, pydantic | 270 | none |
| veyrax-mcp | — | bearer plus server Upstash token (unregistered) | fastapi, httpx, pydantic, starlette, upstash_vector | 331 | none |
| veyrax_auth | veyrax-auth | VeyraX credential store (Supabase/encryption); not a provider port | fastapi, pydantic, requests, supabase | 290 | none |
| whatsapp | whatsapp | whatsapp-qr | fastapi, pydantic, qrcode, requests | 1658 | none |
| x | x | custom | fastapi, pydantic, requests | 1410 | none |
| yelp | yelp | server RapidAPI key (catalog says none) | fastapi, pydantic, requests, starlette | 683 | none |
| youtube | youtube | api_key | dateutil, fastapi, googleapiclient, pydantic, youtube_transcript_api | 437 | google/youtube (unregistered) |
| zillow | zillow | server RapidAPI key (catalog says none) | fastapi, pydantic, requests, starlette | 1214 | none |
| zip_code | zip_code | none | fastapi, pydantic, requests | 249 | none |
