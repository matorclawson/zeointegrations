# Public GitHub source slice

sow: zeointegrations-SOW-02

`public_reads.py` implements the approved `get_repository` and `get_issue`
source slice with an injected Broker transport. It contains no HTTP client,
credential lookup, provider SDK, dependency, import-time registration or live call.
Repository public provenance and exact request/result identities are checked;
issue reads first establish the public repository. Results project a fixed set of
fields, limit text, and discard unselected provider fields and error details.

Tests use synthetic doubles with the public `python/cpython` identity. Their issue
number, title and body are invented fixtures, not recorded public or private API
responses. No VeyraX code/data is copied; this implementation is original source
under the repository MIT license. The scope comes from the Architect's accepted
S1c correction and SOW-02 additive amendment, following foundation PR #2's merge.

These package-local types are draft receiving inputs, not adopted Core contracts
or stable Broker operation IDs. The distribution metadata, entry-point target and
machine manifest await the existing Core/Tools receiving contract; no installable
release or live Broker operation is claimed. Packaging, installed discovery,
full exact-head qualification and independent review remain required. Gates have
not run on this source checkpoint; the existing runner admission restrictions
remain in force.
