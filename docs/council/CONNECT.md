# Connect integration follow-up

The supplied `zeoconnect-improved-20261031(1).zip` was inspected as an interface
reference. Its package declares a proprietary license. No Connect server source,
travelling tests, custody implementation or private contracts are redistributed
in this MIT package. New code in this follow-up is original implementation.

## What is implemented

`zeo_integrations._http.HttpxTransport` executes the collection's Request objects
using an explicitly injected HTTPX BaseTransport. It streams bounded responses,
refuses redirects and encoded bodies, does not carry cookies between operations,
sets per-call timeouts, checks elapsed deadlines, and removes exception chains.
There is no default network transport. The injected transport must enforce DNS and
egress policy, inject credentials inside custody, and disable retries. A blocking
custom transport that ignores HTTPX timeout extensions cannot be interrupted by
this synchronous wrapper; use only a host-controlled implementation.

`zeo_integrations.loops.connect.ConnectLoopsClient` adapts the existing typed
LoopsClient to dictionary results expected by Connect's newsletter dispatchers.
It accepts the host's shared pacer. It preserves draft-only operations and refuses
activity filters, which are outside Connect's current approval contract. It uses
the public client's stricter provider response validation. It does not replace
Connect's request/approval validators, helpers or operation registration.

Inside Connect's existing custody callback, the provider-call object can be built
as follows (imports are from the aggregate package):

```python
from zeo_integrations.loops import LoopsClient
from zeo_integrations.loops.connect import ConnectLoopsClient

api = ConnectLoopsClient(
    LoopsClient(credential_api_key(credential), transport=transport),
    wait=pacer_for(str(request.connection.connection_id)).wait,
)
try:
    return existing_dispatcher_work(api, parsed_arguments, context)
finally:
    api.close()
```

`credential_api_key`, `pacer_for`, request binding, validated arguments and the
work callback above remain Connect-owned. Connect must catch the aggregate
`LoopsRejected` / `LoopsUnknown` types; its old locally defined error classes are
not the same classes. No provider operation is activated merely by installing
this package.

## Concrete integration constraints found

- Connect's manifest and README pin `zeocore[bluesky,google,youtube]==0.12.0`.
  This aggregate requires `zeocore>=0.43.0,<1`. They cannot resolve together under
  those manifests. The supplied latest Core is 0.44.0. Updating Connect's Core
  dependency and qualifying its full server gate is a separate coordinated change;
  this packet does not silently change a reference repository or its frozen lock.
- Connect's MemberBroker owns exact argument approval, account binding, operation
  revisions, durable claims, stops and custody. A broad catalogue of 803 client
  methods is not an allowlist and is not automatically registered with it.
- Its AgentClient sends named operations. It is not a raw HTTP execution endpoint.
  Do not send a collection Request URL or provider credential through that API.
- The existing Loops contacts batching/workflow checks remain in Connect. The
  shared pacer must cover newsletter and contacts calls together.

## Additional native operations

- Amazon: bounded items, variations and browse-node lookup; local product URL
  parsing without following redirects or making a request.
- IMAP: UID-based listing and full-message reads, read-only mailbox selection,
  UIDVALIDITY fencing, BODY.PEEK to preserve unread state, bounded partial fetch
  requests, identity checks and refusal of truncated results. The injected IMAP
  session must impose socket timeouts and literal-allocation limits. No expunge,
  delete, login or connection close is performed.
- WhatsApp: account-bound chats, messages, contact search and single-chat reads on
  an injected bridge. No global user enumeration or destructive disconnect.
- E2B: typed code execution on an already bound sandbox, explicit effect admission,
  bounded text/log results. Active HTML/SVG/JavaScript display representations are
  omitted. The host owns sandbox lifecycle, credentials and durable files.

Native SDK callbacks must enforce allocation limits and deadlines before returning
objects; the library's JSON limit applies after return. They are not managed
Broker routes by themselves. Synthetic tests validate these protocols locally;
real-account acceptance has not been performed.

E2B run_code keyword compatibility was checked against the official Python SDK
reference: https://e2b-preview.mintlify.app/sdk-reference/code-interpreter-python-sdk/v1.2.1/sandbox
(the documented timeout/language interface; no SDK network execution).
