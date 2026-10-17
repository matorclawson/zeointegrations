# VeyraX component shape evidence

Source review for zeointegrations-SOW-01, 2026-10-17. Canonical source is
`VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df`, read through
the identical local fork. This records data needs for the zeocore owner's
component-schema design. It defines no runtime ABI and imports no source.

In `aci_server/integrations/<name>/component.json`, the populated assets below
contain `name`, `version`, `description`, `related_endpoints`, `component`,
`exampleProps`, and `schemaRef`. Their implementation field is `component.jsx`:
it is executable frontend code and must not be copied into data-only results.
The examples are static source examples, not evidence of admitted operations.

| Integration | Source example components | Data shape needed by a future data-only view |
|---|---|---|
| Gmail | GmailMessageCard, GmailMessageList | Message id, subject, sender, recipient, date, snippet, provider link; list under messages |
| Google Calendar | GoogleCalendarEventCard | Event list with id, summary, description, location, start/end, attendees, organizer, status, recurrence metadata and provider link |
| Notion | NotionPageCard, NotionDatabaseTable | items list with next_cursor and has_more; page/database properties need typed cells or plain text |
| GitHub | GitHubRepositoryCard, GitHubIssueCard, GitHubPullRequestCard, GitHubCommitCard | Separate lists under repositories, issues, pull_requests or commits, with next_page |
| Slack | SlackMessageCard, SlackMessageList, SlackChannelList, SlackChannelMembers | Message text and author/time/thread metadata; messages, channels or members list with cursor |

These fit summaries/cards and bounded tables. List pagination and optional/null
values must remain explicit. Provider links are data to validate under the
renderer/Broker URL policy, never an instruction to fetch, execute or invoke.
Source examples do not establish a reusable chart, form or action-button ABI;
do not manufacture one from JSX handlers. Other inventory examples include
empty component objects/lists, so structured results and plain-text fallback
must work without a component.

Do not put JSX, HTML, JavaScript, handlers, arbitrary styling code, credential
values, token refresh/enrollment information, or raw credential-store records in
a component. Strings from provider content remain untrusted text. Any future
action must refer to an admitted named operation and preserve Broker approval
semantics; a component cannot authorize it. Version selection, strict unknown
field rejection, row/byte/nesting bounds and accessibility fields are for the
zeocore/renderer/Broker owners to settle in the reviewed contract. No package
will implement against an unreviewed proposal here.
