# Direct X publishing client

`XPublisher` is the direct API client extracted from the reviewed-source return;
`x/_ported.py` in the unlanded catalogue is a separate RapidAPI discovery
implementation and is not used here. No credentials, enrolment, grant, scheduler,
provider SDK or implicit HTTP client are added. The host injects the transport
inside its existing credential-custody and account-bound dispatch callback.

## One explicit step

Construct with the selected numeric `account_id`. `identity(key=...)` reads the
authenticated subject and refuses a different account. This is not a credential
store or an automatic identity call before writes: the host must bind each
user-context credential and approval to the selected subject on every dispatch.
OAuth, expiry/refresh/revocation and the developer app remain with the host.

`publish(XPost(...), key=..., allow_effect=True)` submits one create request.
The closed model includes text, at most four uploaded media IDs, and an optional
prior post ID for a single reply. Empty text is allowed when media is supplied;
empty content, duplicate IDs, malformed IDs and unknown fields fail before
network dispatch. Media IDs must already be uploaded, ready, unexpired, and
bound to the posting account. The host must verify media kind/cardinality and
account capabilities; four IDs does not mean four videos are permitted.

Incoming Snowflake IDs remain exact canonical unsigned64-bit decimal strings,
including 20-digit values. Outbound media, reply and known-post parameters follow
the endpoint schema's 19-digit limit; no float coercion or truncation occurs.

The 280-character field bound is a **local input cap**, not X's weighted length
algorithm, premium long-post eligibility, URL weighting or a truncation promise.
Unicode is retained without transformation; the provider can reject content.
Other X create options are not silently dropped: unmodeled options are refused.

Creation requires HTTP201 and a valid numeric returned ID, with no partial/error
result. The receipt says `created`, not externally visible or delivered.
Persist that ID before the next approved thread step. A known-ID `read_post`
requests the author field and checks both post ID and selected account; it is
not a search/reconciliation mechanism for a lost creation response.

## Failure and host obligations

One transport call per method, no retry, polling, refresh or multi-post loop.
Only enumerated structured X problem identities paired with their documented
HTTP status are definite refusals. Missing/mismatched structure, generic errors,
timeouts, conflicts, server failures, partial results and malformed write
receipts preserve uncertainty. Metadata retains bounded status/problem identity
and Retry-After, never provider titles, messages, request values or bodies. A401
stops; generic401 is conservatively unknown and never retried by this client.
The key is host idempotency context, **not a claim that X deduplicates requests**.
An unknown write remains on the host's reconciliation path, not a fresh create.

The companion [media and thread library](x-media-thread.md) supplies explicit
upload/processing steps and a pure whole-thread value and step planner. Durable
orchestration and live host integration remain Connect's responsibility.
It does not implement the returned RapidAPI client or call its origin. Installing
this library does not register Broker operations or demonstrate a real account.
No live provider call was used for verification.

## Primary protocol references

Read2November2026; documentation reference only, no vendor implementation copied:

- [Create or Edit Post](https://docs.x.com/x-api/posts/create-post): request shape,
  media/reply handling, user-context authorization and201 response.
- [Authenticated subject](https://docs.x.com/x-api/users/get-my-user) and
  [known post lookup](https://docs.x.com/x-api/posts/get-post-by-id): identity and
  explicit author projection.
- [X ID representation](https://docs.x.com/fundamentals/x-ids).
- [Errors and partial results](https://docs.x.com/x-api/fundamentals/response-codes-and-errors).
- [OAuth2 scopes](https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code):
  the host must arrange user-context `tweet.read`, `tweet.write`, `users.read`,
  with `offline.access` only if it actually implements refresh custody.

Actual app access, credits, account grants and current charges are unverified;
this change buys nothing and creates no account or token. Full media and thread
requirements remain in the delivery backlog, not represented as completed here.
