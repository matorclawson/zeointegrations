# zeointegrations

This seat owns this repository. Coordinate package moves with zeocore and Broker
execution with zeoconnect-tools. The zeocore seat owns all zeocore edits.

- Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing packaging.
- Run `make setup`, then `make verify`. CI runs the same gate, without credentials.
- Work on a branch in the fork; one open PR at a time. The first PR body line and
  a line in every commit must be `sow: <runtime-minted id>`. Never invent an id.
- Council reviews, the Architect signs, and the merging app merges. Keep the
  upstream push URL disabled. No direct main pushes, tags, or PyPI publication.
- No secrets in source, fixtures, logs, PRs or messages. Never call live providers
  during verification. Use injected credentials only inside ZEOconnect.
- Keep MIT notices and per-file provenance on copied code; update NOTICE.
- Keep existing entry-point names. Google is one package for its six entry points.
- Contracts belong to zeocore; UI components are data only, without provider HTML
  or JavaScript. Coordinate the machine manifest contract before implementing it.
- Send seat mail as `zeointegrations` through the zeo-messenger skill. Send the
  Architect completed slices or concrete blockers.
