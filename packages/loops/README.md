# zeo-integration-loops

sow: zeointegrations-SOW-02

Typed API client for the account, draft campaigns, revision-bound LMX messages,
audience, themes/lists, asset creation/completion, contacts and webhook verification.
No send, schedule, preview, workflow, contact deletion or suppression-removal API.
Credentials are injected by the caller; this package has no credential store,
environment lookup, Core lifecycle registration or import-time network activity.

```python
from zeo_integrations.loops import LoopsClient

with LoopsClient(injected_key) as client:
    account = client.test_api_key()
    draft = client.create_campaign("Draft issue")
```

The fixed origin is `https://app.loops.so/api`. Redirects, environment proxies
and implicit mutation retries are disabled. HTTP and invalid-response errors
are normalized without provider bodies/headers. Transport failures can have an
unknown mutation outcome; callers must reconcile, not retry blindly. Request and
response sizes are bounded; injected transports remain trusted caller components.
The conservative 60-attempt/60-second per-client limiter does not infer which
different keys belong to the same team: Broker must also enforce its aggregate
per-team limit. Lists preserve pagination; there is no hidden all-pages loop.

`LoopsRejected` (with `.status` and `outcome_unknown=False`) covers definite
400/401/403/404/405/409/410/413/415/422/429 refusals. `LoopsUnknown` covers
408, 5xx, redirects, transport faults and invalid answers; specific typed errors
inherit the appropriate group. `LoopsApi` aliases `LoopsClient` for consumption.
Typed models use snake_case attributes; adapters may call `model_dump()` at their
own boundary. Theme pages retain `.data` and pagination, not just an item list.
LMX is limited to 60,000 UTF-8 bytes, audience filters to 20 conditions and request
JSON to 64 KiB. Official required response fields are not silently defaulted.

Campaign methods build explicit payloads with no `scheduling`. All API writes,
including contact upserts that can subscribe an address, remain subject to Broker
approval and consent policy. A signature-verified webhook is not itself a consent
decision. The receiver owns replay deduplication, event validation, two-secret
rotation policy, durable commit and HTTP acknowledgment. Signature verification
accepts raw bytes and rejects timestamps more than 300 seconds from its clock.

`create_upload` returns a typed ticket; it never follows the signed URL or leaks
the API credential to storage. The caller owns the separate approved asset upload.
Ticket repr omits its signed URL. API `fromEmail` values are sender local-parts.

Install from the reviewed full Git commit using `subdirectory=packages/loops`,
then commit the consumer lockfile and retain the offline build closure. No PyPI
release or qualified pin is available at this source checkpoint. Uses existing
Approved dependencies httpx0.28.1/pydantic2.13.4 and Core's hatchling build backend;
exact locked versions/artifacts must be received before qualification.
Broker's current lock is pydantic2.13.5; its adoption needs the coordinated lock
alignment requested after the Architect's explicit 2.13.4 dependency ruling.

OpenAPI reference: official `https://app.loops.so/openapi.json`, version1.22.6,
received SHA256 `518500f5f94aeba4c242d8474ce050b0607dd356f4875dc0279a6120df18a811`.
Architect's independently supplied YAML carrier SHA256
`e2a4a01eed1e72484319c2ea76460a5bd4ce7ef27e8708ff66f3f2820e081914`.
Webhook algorithm: Broker `reader-database-design-rev-e.md`, section3.2.
No generated SDK or third-party implementation was copied. See LICENSE/NOTICE.
All package execution/build/install/full-gate checks are NOT_RUN until receipted
in the Runtime-provided venue. A source commit is not a usable consumer acceptance.
