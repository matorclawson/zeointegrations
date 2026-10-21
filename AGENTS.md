# zeointegrations

This seat owns this repository. Coordinate package moves with zeocore and Broker
execution with zeoconnect-tools. The zeocore seat owns all zeocore edits.

- Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing packaging.
- Run the full `make verify` gate at the committed head through the admitted
  Pomar shared runner, scheduled by zeo-rt-sched. Use the complete preinstalled
  locked environment; `make setup` is a separate installation act. Council
  reviews exact-head evidence; Python reruns use the admitted runner, not an
  assumed Council execution venue. Public Actions is one optional three-minute
  smoke job under DECISION-local-ci-on-pomar-actions-minimal-v1-2026-10-18.
- Work on a `zeointegrations/<slug>` branch in the fork; one open PR at a time.
  The lane derives the seat from the prefix before `/`. The first PR body line and
  a line in every commit must be `sow: <runtime-minted id>`. Never invent an id.
- Ordinary product review goes to zeoreviewer; sensitive C1-C6 changes go to
  Council. The Architect signs required lane evidence and sequences the supported
  merge route. Keep the upstream push URL disabled. No direct main pushes, tags,
  self-merges, or PyPI publication.
- No secrets in source, fixtures, logs, PRs or messages. Never call live providers
  during verification. Use injected credentials only inside ZEOconnect.
- Keep MIT notices and per-file provenance on copied code; update NOTICE.
- Keep existing entry-point names. Google is one package for its six entry points.
- Contracts belong to zeocore; UI components are data only, without provider HTML
  or JavaScript. Coordinate the machine manifest contract before implementing it.
- Send seat mail as `zeointegrations` through the zeo-messenger skill. Send the
  Architect completed slices or concrete blockers.
