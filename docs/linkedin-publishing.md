# LinkedIn publishing client

LinkedInPublisher takes an injected Transport, a host-selected person/organization
author URN and explicit YYYYMM API version. It sends no credential argument and
never retries. The host injects Bearer authorization inside its custody callback,
binds author to the enrolled account, verifies exact text/media approval and
persists returned upload/post IDs before the next step. allow_effect is a local
guard, not authorization. Invalid/lost write receipts remain unknown.

The [official Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
documents version/Rest.li headers, text/media creation and x-restli-id on201.
Member posting uses w_member_social; organization posting needs
w_organization_social and appropriate Page authority. App access and account
state are deployment inputs, not proven by synthetic tests.

The [official Images API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api)
describes initialization, byte upload then processing. This client only returns
the upload URL and bound image URN; it does not upload bytes. The host must use
its bounded origin-pinned streaming uploader and retain immutable digest/size.
A successful initialization is awaiting_upload, not a published post. Status
checks require matching owner/URN. w_member_social alone is write-only for
versioned image GET, so host enrolment must not promise polling with that scope.
Current image documentation lists JPG/GIF/PNG, fewer than36,152,320pixels and
GIF<=250frames. Returned URL and current provider requirements need host checks.

Single image/video/document URNs or multiple image URNs can be referenced in a
post after a completed, account-bound upload. Video/document upload orchestration
remains follow-up; no synthetic media ID is evidence of provider availability.
No Broker operation, OAuth flow, deployment, payment or live post is installed.

## Plain-text approval and fixed first-release policy

Commentary is approved as literal text. The client escapes every reserved
character in LinkedIn's [little text grammar](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/little-text-format):
`| { } @ [ ] ( ) < > # \ * _ ~`. Input cannot request a mention or hashtag template.
Backslashes are escaped too; no unescaping or truncation occurs. LinkedIn's
[post help](https://www.linkedin.com/help/lms/answer/a528176) states a3000-character
post limit but does not establish how API escape sequences count. This client
therefore also imposes a conservative local cap of3000 UTF-16 units on the escaped
commentary. It can reject text the provider might accept; this is an explicit
local bound, not a claim about vendor encoding counts. Preview the literal text
and surface any encoded-limit refusal before requesting an effect.

The fixed policy is PUBLIC, MAIN_FEED, immediate publish request, reshare allowed.
Approval must show those choices. A valid201/x-restli-id returns stage `created`,
not proof of visibility. The [post schema](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/post-api-schema)
also permits PUBLISH_REQUESTED/PUBLISH_FAILED on read-back. Use the bound post ID
for a read; it cannot discover a missing write receipt. Optional empty titles are
omitted; documents require a nonblank title. A title on zero/multiple media or
duplicate URNs is refused before dispatch. Alt-text fields and richer mention or
hashtag models remain follow-up, never inferred from free text.

## Refusals and rate information

The [error guide](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/error-handling)
uses `status`, optional numeric `serviceErrorCode` and `message`; Posts also names
specific string codes. The parser keeps bounded status/code/subcode/Retry-After,
never message/body. A matching structured documented client-error refusal can be
reported as rejected. Unknown codes, malformed/mismatched status, transient flags,
409,5xx, lost replies and unstructured429 stay unknown for effects. No response
causes automatic retry. A host may hold a connection while keeping the original
write unresolved. A401 can mean invalid, expired or revoked credentials;500 can
also represent downstream token verification failure. No exact expiry subcode is
invented. Token repair does not prove a prior unknown write failed.

Retry-After and x-ratelimit-remaining pass only when present. No guaranteed header
or universal per-member/application quota is established here; use the current
Developer Portal and operation-specific access. Other LinkedIn usage headers do
not cross this transport's existing allowlist. Idempotency keys remain host-only;
provider deduplication support is not established, so an unknown write is never
repeated with a new key.

## Enrolment and renewal

`member_identity(key=...)` calls `/v2/me` and returns only `member_urn`, comparing
it to a configured person author. An organization author receives the member ID
without any organization grant. The [Profile API](https://learn.microsoft.com/en-us/linkedin/shared/integrations/people/profile-api)
is restricted to approved developers; its listed permissions include r_liteprofile
or r_basicprofile. Do not promise these scopes exist for an unapproved app.
OIDC `/v2/userinfo` with openid/profile is a distinct product; this client does not
assume its pairwise sub is interchangeable with a posting Person ID.

For an organization, the host must additionally use the approved
[organization access-control API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/organizations/organization-access-control-by-role):
`GET /rest/organizationAcls?q=roleAssignee`, with required version headers and
r_organization_admin/rw_organization_admin access as applicable. Compare an
APPROVED row's roleAssignee to the authenticated member and its organization
(or documented organizationTarget shape) to the selected author, and check a role
allowed for the actual posting operation. Process bounded pagination; missing
proof is unavailable, not authorization. No role is granted by this library.
URN aliases such as company versus organization must be resolved at enrolment;
reads compare exact owner/author and fail closed rather than silently normalize.

The [refresh guide](https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens)
describes default60-day access tokens and year-long programmatic refresh tokens
for approved MDP partners. Use actual returned expiry; refresh is not universally
available and can be revoked. The host implements custody/refresh and falls back
to reauthorization when required. This library creates no OAuth session or token
store, and makes no app-approval assertion.

## Image bytes and temporary vendor closure

The Images page links its upload step to the [image upload contract](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/vector-asset-api#upload-the-image):
PUT to the returned URL requires OAuth Bearer. Keep bytes and authorization in a
bounded Broker custody relay; do not export the token to a device or assume the
URL alone authorizes upload. Use an explicit host-approved content type (the
current official collection's binary-upload example uses application/octet-stream),
actual byte length and streaming digest checks; no redirects. This client does
not implement that relay or assert any bytes were uploaded. Signed upload URLs
are capabilities: never put them in logs, approval text or public records.
`upload_url_expires_at_ms` preserves the optional provider expiry; None does not
mean indefinite validity. The host refuses an expired ticket and resolves any
unknown initialization before requesting another.

Image states are WAITING_UPLOAD, PROCESSING, PROCESSING_FAILED and AVAILABLE;
only AVAILABLE permits the next host-approved media-post step. The existing
scope restriction for image GET still applies. The host verifies upload digest,
size, owner, processing and immutable occurrence binding before publishing.

Temporary vendoring keeps the implicit namespace `zeo_integrations` (no root
__init__.py), publishing/__init__.py, _http/{__init__,runtime,transport}.py, both
py.typed markers and MIT/NOTICE/provenance. Do not silently rename imports or add
a competing namespace initializer. Final hashes wait for exact-head independent
review and merge. No workflow/compose/media/compatibility file is needed by this
pure client closure.
