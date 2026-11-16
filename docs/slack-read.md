# Slack conversation listing

`SlackClient` implements one bounded `conversations.list` page. Supply an explicit
host-owned `_http.Transport`; there is no socket transport, OAuth flow, token
parameter, credential discovery or new SDK dependency. The host injects scoped
OAuth authorization and owns consent, origins, DNS/egress, deadlines and rate
policy. A transport must not retry or follow redirects. Installing the library
or selecting conversation types grants no provider permission.

Pass a `ConversationListRequest` and an invocation `key`. The method returns Core's
`IntegrationResult[ConversationPage]`. Query options are a limit of 1–200, an optional
opaque nonempty cursor, conversation types, an archived-channel filter and optional
team ID for org-wide tokens. Limit 200 is a client policy, not Slack's API maximum.
The default type is public channels and archived channels are included unless the
caller excludes them. The configured host token still determines actual visibility.

Output deliberately projects conversation IDs, names and nullable classification
flags. Missing flags remain unknown rather than false; unrelated provider fields
are ignored. This is not a complete conversation object or a permission decision.
The next cursor stays opaque. Under Slack's documented pagination contract,
empty/null/absent cursors mean no continuation; a short or empty page with a cursor
still has continuation. The client never follows pages automatically.

Responses are capped at 1 MiB before JSON decoding. Require HTTP 200, strict `ok=true`,
a channels array and valid cursor/projection fields. Duplicate JSON keys, nonfinite
numbers, invalid UTF-8, wrong destinations and unexpected page sizes are refused.
HTTP 200 with `ok=false` is an API failure. Known auth/scope/cursor errors map to fixed
`slack_*` codes; unknown provider errors and transport exceptions never expose raw
messages, bodies or credential values. HTTP 429 returns `slack_rate_limited` without
automatic retry; the transport host owns the original headers and retry policy.

This slice does not read message history, send messages, join channels or mutate
workspace state. Its public/private visibility facts are data, not authorization.

Official contracts:

- [conversations.list](https://docs.slack.dev/reference/methods/conversations.list/)
- [Conversation objects](https://docs.slack.dev/reference/objects/conversation-object/)
- [Cursor pagination](https://docs.slack.dev/apis/web-api/pagination/)

Implementation and synthetic fixtures are fresh. No reference client/function/test
is copied, and no provider traffic is used for verification.
