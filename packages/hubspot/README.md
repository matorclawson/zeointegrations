# HubSpot marketing provider client

sow: zeointegrations-SOW-02

Provider extraction from Core 6bd62fbb; exact per-file source blobs are in NOTICE.
Python >=3.12. Inject SecretStr credentials or an HTTP transport explicitly. No
Core dependency, environment discovery, service factory or entry point is added.
Core retains its lifecycle and the sole hubspot.marketing registration. Existing
Core submodule forwarding and class identity are separate Core-owned receiving
changes; this source does not claim those shims are installed.

The existing client supports marketing email drafts and reviewed publishing,
campaigns, subscription preferences and a strictly bounded linear email workflow
subset. Existing confirmation/revision/content-digest/audience/consent guards
remain. Package code grants no permission to send, schedule, enroll or change
consent; actual credentialed execution remains inside Broker's approved workflow.
No live provider or subscriber data is used in verification.

The first commit preserves four Core module blobs exactly. Transport hardening
is a separate tested commit. A full current-head gate, installed-source identity,
namespace, wheel/sdist/license/NOTICE checks and compatibility controls are needed
before source approval. Gates run only with present interpreters; unavailable
Python 3.12 is NOT_RUN, never a fabricated pass. No interpreter download is
implied by this package's declared floor.

Release and adoption are separate: Architect requires the existing signed
vendored-wheel route, no PyPI/new feed, and a pinned HARD dependency from Core
once the wheel is actually installable. Core shims must not merge first.
Newsroom and Broker install no separate extra; their exact released-Core locks
and consumer checks must pass. No release grant, cryptographic wheel signature,
publication, installed Core forwarding or consumer readiness is claimed here.
A hash-bound lane record alone is not a cryptographic signature.

Pagination returns one page; complete=true is not an atomic account snapshot.
Callers bound cross-page cursor history and total reads. Mutation errors can have
outcome_unknown and require provider-state reconciliation, never automatic retry.
Dynamic audiences and mutable provider assets retain their existing race limits.
