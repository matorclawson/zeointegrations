# Packages

Each integration or local plugin will be added in its own reviewed PR. See
[the package layout](../CONTRIBUTING.md#package-layout) and
[the inventory and proposed order](../docs/inventory/README.md).

`loops/` is the first API-client package source, consumed directly by Broker;
it has no Core lifecycle entry point or credential custody. Qualification and
release status are recorded in its README.

`kit/` is a current-API, read-only migration/audit client for subscribers and
their states, tags, forms and custom fields. It has no entry point, Core
dependency, subscriber writes, broadcast or sequence surface. Core retains its
legacy service and registry; legacy write consumers are not redirected here.
Qualification, independent review and actual migration/audit consumer receiving
remain unfinished until their separate receipts are recorded. No provider
retirement or live readiness follows from package source.

HubSpot follows under the operator's October 24 priority; the ffmpeg pilot
remains parked.

`hubspot/` extracts the existing provider client, models, transport and workflow
validator, preserving reviewed guards. Core retains credential discovery, service,
factory and sole entry point. Core forwarding and the pinned hard dependency wait
for an actually installable, separately approved release; no consumer adoption
or provider execution is established by this source package.
