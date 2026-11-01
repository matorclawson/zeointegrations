# Instagram and Threads publishing clients

InstagramPublisher uses a linked professional account through Facebook Login,
with explicit account_id, api_version and allowed media origins. ThreadsPublisher
uses its own account and provider origin. Both require injected transport; neither
reads credentials or creates a network transport.

Create media/carousel containers, retain their identifiers, query status, then
explicitly publish the approved container. Container creation is processing, not
publication. Each call performs at most one request, without write retries. The
host binds containers, account, immutable media and operation occurrence, enforces
exact-post approval, and injects credentials inside a durable execution claim.
allow_effect is a local guard, not an authorization grant.

Travelling tests use synthetic HTTP transport and exercise a carousel through
Core hosted operations and durable workflow checkpoints. No live account is used.
This library slice registers no Broker operation and installs no service. Stories
and resumable uploads remain required follow-up features; real-account acceptance
and Meta app access/review remain separate.
