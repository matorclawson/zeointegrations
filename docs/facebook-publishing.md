# Facebook Page publishing: first library increment

`zeo_integrations.publishing.facebook` provides explicit Page-token identity,
feed post, hosted-photo publish, photo-story lookup and known-post read steps.
It creates no registration, Broker operation, credential flow, grant or UI.
Hosted Page video submission/readback is added below. Reels, resumable video,
multi-photo orchestration, scheduling, targeted audiences and host acceptance remain
required follow-up scope. Unmodeled options are refused, not silently dropped.

The host selects `page_id` and an explicitly supported `api_version` (no default),
injects the Page credential in its owned transport, and proves the credential
subject matches the selected Page. `identity` reads `/me`, not the public Page
resource. The host must retain that identity binding with the same credential
and recheck it after credential/account changes. The class does not authenticate
authority from a caller-supplied ID or local flag. Current permission scopes,
Page tasks/roles, app review/access, version eligibility and account approval
must be established by the receiving host before enabling any operation.
The library neither enrolls credentials nor increases their authority.

Each method makes at most one request, with effect admission for writes, host
idempotency context, fixed Graph origin, bounded response and existing deadline
controls. No retry, polling, scheduling, file read or ambient network transport.
The key does not assert that Facebook deduplicates requests. All dispatched
write errors in this first increment remain unknown, including Graph errors:
there is no endpoint-specific no-mutation proof here. Preserve the original
claim/outcome and reconcile; never create again to settle a missing answer.
Malformed, partial or wrong-Page receipts cannot become successful writes.

Inputs are strict, frozen, closed models. Message/caption (10,000 characters),
alt text (1,000), links (4,096) and decimal object IDs (40 digits per component)
have conservative local bounds; they are not provider limits or promises of
eligibility. IDs stay strings with no integer/float coercion. A composite post
ID must name the selected Page. Feed creation requires that composite form;
a bare post ID is accepted only by later reads with the required author check. Link posts require host-allowed link origins. Hosted images
require separately host-allowed media origins. The host owns exact-content and
URL approval, asset identity/type/expiry/availability and any signed fetch URL;
the library fetches no asset itself. Captions and alt text travel unchanged.

Feed creation returns a stored post ID with `created`, not public visibility.
Photo creation returns only the confirmed photo ID (`photo_created`), never a
fabricated post ID from that different object. `read_photo` checks object and
Page author, then returns the optional `page_story_id`; a missing story stays
unlinked. `read_post` checks the exact stored post ID and Page author and reports
only the provider's `is_published` fact and a bounded Facebook permalink. That
fact is not proof of visibility outside the Page's actual audience or of delivery.
Readbacks are for already-bound IDs, not a search for an uncertain creation.
Provider error prose, raw responses and known credential-bearing permalink queries
are not returned as metadata.

The protocol facts were checked against Meta's public generated business SDK
at a pinned commit, recorded in facebook-provenance.json. It confirms the Page
feed/photos edges, field names and Post/Photo response fields. No SDK code was
copied, imported or made a dependency. Official Meta Pages/Graph documentation
returned429 during authoring on3November2026 and was not retried or bypassed.
Permissions, eligibility and current-version behavior were not verified by a
live provider call; host design/review and real-account acceptance remain separate.
The synthetic fixture version is an example of host selection, not a statement
that it is the newest supported Graph release. No production install or account
activation is part of this source increment.


## Hosted Page video increment

`FacebookPageVideo` takes an approved `video_url`, optional title and description.
`publish_video` submits exactly one form request to the fixed
`https://graph-video.facebook.com/{version}/{page_id}/videos` edge with
`file_url`, title, description and `published=true`. The host must explicitly
admit this additional origin and inject its Page credential inside custody;
there is no fallback to another origin or retry. The supplied asset must have a
host-allowed media origin. This library fetches no video or local file.

The receipt contains only a numeric `video_id` and `stage=submitted`. Store it
with the selected Page/credential and original claim. It is not a feed post ID,
processing readiness, audience visibility or delivery proof. An invalid/lost
receipt or any dispatched write failure remains outcome-unknown; never resend
it just to obtain an ID. Host exact-content approval covers the complete URL,
title and description plus immutable media bytes, type, duration and availability.
The local title/description/URL caps are not provider format/size limits.

`read_video` performs one explicit Graph read of that already-bound ID, checks
both returned ID and Page author, then returns only the closed `video_status`
(processing/ready/error) and optional strict-boolean `provider_published` fact.
Unknown/missing status fails closed; missing published remains unknown (`None`).
Encoding-ready does not establish public visibility. No provider status prose,
raw response, permalink or media URL is returned. Scheduling follow-up reads,
retaining claims and handling failed/ambiguous publication belong to the host.
No automatic polling or second write follows a status result.

This increment is hosted Page video only. Reels' separate start/upload/finish
flow, resumable byte upload, multi-photo and live account/host adoption remain
required follow-up scope. Meta SDK Page/AdVideo fields and the video uploader's
fixed origin/status vocabulary were read as protocol facts at the same pinned
source commit; no SDK code was copied, imported or executed. Current Page token
permissions, supported version, media eligibility and actual reach are unverified.
