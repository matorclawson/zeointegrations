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
