# zeointegrations

This repository owns the integration collection. Coordinate package moves with
the Core project and execution with the Broker project. Core edits belong to
the Core repository.

- Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing packaging.
- Run `make setup`, then full local `make verify`. Independent review repeats
  the exact-head gate until pomar CI supplies its signed gate. Public Actions is one optional
  three-minute smoke job, not the full gate.
- Work on a `zeointegrations/<slug>` branch in the fork; one open non-draft PR
  per repository. Open a new PR only when the work is ready and its full gate
  has passed on the exact head, including new draft PRs. Existing drafts stay
  draft until their gate passes. See CONTRIBUTING.md for the
  own-fork `zeointegrations/wip/<topic>` backup and quick-check policy.
  The project prefix before `/` is required; keep the branch topic neutral.
  This public repository uses exactly `sow: public` as the first PR body line
  and in every commit. Do not include internal work identifiers, role names,
  session trailers or message identifiers in public files or PR metadata.
  Keep those records in the private governance repository.
- Test regularly on the work branch in your own lane; PR creation or updates
  must never trigger the heavy suite. Keep PR checks light.
- Full exact-head verification is required before every non-WIP push and before
  final approval, signing or merge. Record HEAD, DIRTY, host, EXIT and the full
  log SHA256 in the PR body. Never skip baseline failures or bypass a hook.
- Independent review and required signing precede merging-app integration.
  Keep the upstream push URL disabled. No direct main pushes or developer tags. The
  operator's 26 October 03:51 ruling supersedes the per-provider PyPI route:
  one `zeo-integrations` distribution depends on published `zeocore>=0.43`;
  Core must not import this collection at import time. No per-provider PyPI
  project or pending publisher. Automatic aggregate publishing and scripted
  GitHub setup are a separate reviewed workflow PR; normal merger requires
  its Workflows permission. Do not dispatch the superseded HubSpot workflow.
  One aggregate PyPI trusted-publisher registration is the only PyPI bootstrap;
  it is not a per-release approval. No publication is claimed by source moves.
- No secrets in source, fixtures, logs, PRs or messages. Never call live providers
  during verification. Use injected credentials only inside ZEOconnect.
- Keep MIT notices and per-file provenance on copied code; update NOTICE.
- Keep existing entry-point names in Core during migration. The aggregate
  registers no duplicate plugins. Google is one family within the collection
  for its six current entry points; other provider SDKs are optional extras.
- Contracts belong to zeocore; UI components are data only, without provider HTML
  or JavaScript. Coordinate the machine manifest contract before implementing it.
- Keep internal coordination and work records in the private governance system;
  report completed changes or concrete blockers through that system.

All builds/tests/gates run on ENG-UK in the seat-gates workspace, maximum20GB.
Mat is for authoring/commits/push/mail. The required org-records metadata hook
may run unchanged under taskpolicy -b at push time by the explicit metadata-hook
exception; do not extend that exception to source gates. Each contributing seat
uses its own seat branch prefix and at most one open PR per repository. WIP
backup branches are never PR heads. Provider moves include travelling tests and
old/new file/blob provenance (M2); fresh Core imports must not load the aggregate
(M1). Core owns all Core edits, and legacy lazy shims follow actual aggregate
PyPI availability; repository installation can be used before that.
