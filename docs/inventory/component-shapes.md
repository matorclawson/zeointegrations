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

## Shape fit check on the owner's proposed design

Read zeocore-SOW-38 rev 3 at
`matorclawson/org-zeroemployeeorg@7179ffe2cea91eaa0c83028fc6aa7510a4072aac`,
`projects/zeocore/sow/zeocore/zeocore-SOW-38-data-only-ui-component-schema.md`
(SHA256 `8aa231381ffd3e74ee7d11b44ec5061f0ef1d813528d729e0b816ceeed22343e`).
This is a consumer shape fit check, not acceptance or implementation of a new
contract. The contract owner and council decide its resolution.

The five source families fit bounded card/table summaries with authoritative
structured results retained separately. Long message bodies, arbitrary Notion
properties, nested attendee/member data and long provider strings do not fit
losslessly into the proposed scalar cells and 12 card facts; use an explicit
summary and an admitted read/paging interface. Do not label a summary as a
complete export. Missing/null values and inert provider links must stay
distinct from zero/false and actionable URLs. The inventory has no need for
scatter charts, executable JSX or components that authorize effects.

Three design details need owner clarification before an accepted version:

- Section 3 still says 200 table rows and 1,000 chart points, and refusal vector
  V9 uses 201/1,001, while the reconciled section 5 budget says 100/500. The
  vocabulary, examples and boundary vectors must use one bound.
- Counting every object/array toward 100 nodes per component conflicts with a
  100-row table: each `{id, cells}` row requires at least two object nodes, so
  100 rows need at least 200 nodes before columns, metadata and arrays. The
  effective page budget needs a precise counting rule and acceptance/refusal
  vectors; a producer cannot promise 100 rows under both limits.
- A 4 KiB fallback cannot reproduce an arbitrary large authoritative result.
  Clarify that it is a bounded, explicit summary, how omissions/partial views
  are represented, and how to access the authoritative recorded result. Never
  silently truncate an actionable preview to meet the budget.

These observations preserve the data-only boundary. No schema, fixture payload,
renderer, provider route, action or extra dependency is introduced here.

## Recheck of the owner's council-reviewed revision 8

Read the self-contained zeocore-SOW-38 rev 8 at
`matorclawson/org-zeroemployeeorg@e1371cc84ec27b219422a1ef6d5eff4522eb68bd`,
SHA256 `00d62145c766b2f2f1eb38ed23f285b0a341b90bf703d289f20b5b12f579e9e1`.
The owner reports council DESIGN ADEQUATE, verdict `zc-zcore38-e137-design-v1`.
The three revision-3 shape findings above are resolved: 100 rows/500 chart
points and consistent boundary vectors, no node-count cap (byte/depth/count
bounds apply), and a required `complete` boolean with a bounded summary and
disabled effectful actions when the authoritative preview is incomplete.

Shape fit is confirmed for bounded card/table summaries of the inspected source
families, with nested/large data retained separately. Oversized or unrepresentable
provider cursors stay in the retained result; omit next_page and show partial
and incomplete status rather than truncate or rewrite the cursor. Provider links
remain inert text. The council's carried note that partial/next-page tables
must have `complete: false` is retained as a pilot limitation.

Revision 8 is the owner's and council's recommended pilot pin, subject to the
Architect's decision and the producer's exact-pin confirmation including the
required `complete` key. Revision 6 and revision 8 must not be treated as wire
compatible merely because both name zeo.ui-result/v1. No pilot, schema, renderer
or component implementation is created by this inventory fit check.
