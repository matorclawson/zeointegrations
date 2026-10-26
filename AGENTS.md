# zeointegrations

This seat owns this repository. Coordinate package moves with zeocore and Broker
execution with zeoconnect-tools. The zeocore seat owns all zeocore edits.

- Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing packaging.
- Run `make setup`, then full local `make verify`. Council repeats the exact-head
  gate until pomar CI supplies its signed gate; public Actions is one optional
  three-minute smoke job under DECISION-local-ci-on-pomar-actions-minimal-v1-2026-10-18.
- Work on a `zeointegrations/<slug>` branch in the fork; one open non-draft PR
  per repository. Open a new PR only when the work is ready and its full gate
  has passed on the exact head, including new draft PRs. Existing drafts stay
  draft until their gate passes. See CONTRIBUTING.md for the
  own-fork `zeointegrations/wip/<topic>` backup and quick-check policy.
  The lane derives the seat from the prefix before `/`. The first PR body line and
  a line in every commit must be `sow: <runtime-minted id>`. Never invent an id.
- Test regularly on the work branch in your own lane; PR creation or updates
  must never trigger the heavy suite. Keep PR checks light.
- Full exact-head verification is required before every non-WIP push and before
  final approval, signing or merge. Record HEAD, DIRTY, host, EXIT and the full
  log SHA256 in the PR body. Never skip baseline failures or bypass a hook.
- Council reviews, the Architect signs, and the merging app merges. Keep the
  upstream push URL disabled. No direct main pushes or tags. The sole approved
  PyPI route is the unchanged reviewed HubSpot 0.1.0 wheel via
  `.github/workflows/publish-hubspot.yml`, environment `pypi`, after the operator
  creates the trusted publisher and approves the environment. The workflow PR
  is hand-merged. No other PyPI publication is authorized. See
  [the operator click list](docs/hubspot-pypi-publisher.md).
- No secrets in source, fixtures, logs, PRs or messages. Never call live providers
  during verification. Use injected credentials only inside ZEOconnect.
- Keep MIT notices and per-file provenance on copied code; update NOTICE.
- Keep existing entry-point names. Google is one package for its six entry points.
- Contracts belong to zeocore; UI components are data only, without provider HTML
  or JavaScript. Coordinate the machine manifest contract before implementing it.
- Send seat mail as `zeointegrations` through the zeo-messenger skill. Send the
  Architect completed slices or concrete blockers.
