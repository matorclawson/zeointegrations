# Packages

Each integration or local plugin will be added in its own reviewed PR. See
[the package layout](../CONTRIBUTING.md#package-layout) and
[the inventory and proposed order](../docs/inventory/README.md).

`loops/` is the first API-client package source, consumed directly by Broker;
it has no Core lifecycle entry point or credential custody. Qualification and
release status are recorded in its README. Kit and HubSpot extraction follows
Loops under the operator's October 24 priority; the ffmpeg pilot remains parked.
