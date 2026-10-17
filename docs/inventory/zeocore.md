# zeocore source inventory

Source: `zeroemployeeorg/zeocore@2e7cb11fa9aaf133876c02c1eea8f1ccd94bba04`. Exactly 17 registered entry points: 14 credentialed names in nine families and three local plugin names. Names below stay unchanged. Package names are proposed distribution names from SOW-36, not published projects.

| Entry point | Source directory | Auth | Dependency import roots | Python lines | Proposed package | Existing extra |
|---|---|---|---|---:|---|---|
| github | github | token / GitHub App (signer stays in core) | cryptography, httpx, pydantic, requests | 3527 | zeo-integration-github | github |
| google.mail | google/mail | OAuth 2 | googleapiclient, pydantic | 1523 | zeo-integration-google | google, gmail |
| google.drive | google/drive | OAuth 2 | googleapiclient, pydantic | 2729 | zeo-integration-google | google, drive |
| google.calendar | google/calendar | OAuth 2 | googleapiclient, pydantic | 1312 | zeo-integration-google | google, calendar |
| google.docs | google/docs | OAuth 2 | pydantic | 1206 | zeo-integration-google | google, docs |
| google.sheets | google/sheets | OAuth 2 | googleapiclient, pydantic | 1574 | zeo-integration-google | google, sheets |
| google.slides | google/slides | OAuth 2 | googleapiclient, pydantic | 983 | zeo-integration-google | google, slides |
| pandoc | pandoc | local; no provider credential | bs4, docx, pydantic | 5821 | zeo-plugin-pandoc | pandoc |
| llms | llms | provider API keys | anthropic, openai, pydantic, requests, tiktoken | 4377 | zeo-integration-llms | llms |
| ffmpeg | ffmpeg | local; no provider credential | ffmpeg_zeo, pydantic | 884 | zeo-plugin-ffmpeg | ffmpeg |
| notion | notion | bearer / OAuth 2 | httpx, notion_client, pydantic | 2553 | zeo-integration-notion | notion |
| supabase | database/supabase | service/API key | pydantic, supabase | 1939 | zeo-integration-supabase | supabase |
| hubspot.marketing | hubspot | bearer access token | httpx, pydantic | 1270 | zeo-integration-hubspot | core httpx |
| kit.marketing | kit | access token / API key | httpx, pydantic | 1199 | zeo-integration-kit | core httpx |
| jupytext | jupytext | local; no provider credential | pydantic | 2214 | zeo-plugin-jupytext | jupytext |
| social.bluesky | social/bluesky | app password / session | platformdirs, requests | 1281 | zeo-integration-bluesky | bluesky |
| revolut.business | revolut | OAuth refresh; separate local enrollment key/cert | cryptography, httpx, platformdirs, pydantic | 2231 | zeo-integration-revolut | revolut (enrollment) |

Google shared family: **13936 Python lines**, including shared auth/config and unregistered YouTube. Its aggregate runtime imports are `google`, `google_auth_oauthlib`, `googleapiclient`, `httpx`, `platformdirs`, `pydantic`. The six rows above count only their subdirectories; do not sum them as the whole package. Supabase and Bluesky rows count their exact entry-point subdirectories; the older design counted their parent directories.

Direct import roots omit dynamically loaded tools and transitive dependencies. Existing declared extras, including jupytext/nbformat and Google SDK dependencies, are retained in [snapshot.json](snapshot.json); use those plus installed-package tests when setting requirements.

## Unregistered and shared code

| Area | Migration treatment |
|---|---|
| core, hosted, boot, loader, config, environment | Stay in zeocore; registry and shared contracts |
| environments | Named exception: catalog/credential copying stays with zeocore and follows each per-operation migration |
| notebook | Local plugin, no new entry point; direct import compatibility |
| gemini | Credentialed integration, no Broker route in reviewed design |
| meetings | Consumer of Google and Notion; move after them or use hosted profile |
| google/youtube | Separate provider/credential-free transfer split; no registered entry point |
| model_ops | Remains pending owner decision |
| database/bigquery, database/sqlite | Empty; disposition with database slice |
| github/app_tokens | zeocore seat moves to zeo_core.release.app_tokens before GitHub move |

Revolut enrollment has its own `zeo-integration-revolut-enroll`, principal host only, depends on read package and registers no entry point. Keep `revolut.business` unchanged until its explicitly reviewed Broker-backed replacement.
