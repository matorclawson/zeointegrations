# Contributing

The approved direction is zeocore-SOW-36 rev 5 at
`matorclawson/org-zeroemployeeorg@0f2bf62e2`, with the Architect's rulings
`ans_cbd9dfb83a794f92`. This repository starts with tooling and an inventory;
no provider package or release is present yet.

## Development

Install Python 3.14 and uv, then run:

```sh
make setup
make verify
```

The root is a development project, not a distribution or an umbrella installer.
The locked development dependency is Ruff; verification uses the standard-library
test runner and never imports the inventoried source or calls providers.

## Package layout

Each package PR will introduce:

```text
packages/<name>/
  pyproject.toml
  src/zeo_integrations/<name>/
  tests/
  LICENSE
  NOTICE
  <data-only manifest, format coordinated with zeocore and zeoconnect-tools>
```

Use an implicit `zeo_integrations` namespace so distributions can coexist. External
services use `zeo-integration-<name>`, local capabilities `zeo-plugin-<name>`.
Both use the `zeo_core.integrations` entry-point group and preserve existing names.
One `zeo-integration-google` owns `google.mail`, `google.drive`, `google.calendar`,
`google.docs`, `google.sheets`, and `google.slides`.

The design requires manifest metadata for distribution name, `kind` (`plugin` or
`integration`), entry-point names, secret names only, operations, minimum zeocore,
license and provenance. Its serialization and the typed tool/component contracts
must be agreed with their owners. This skeleton does not invent a runtime schema.

Package PRs must extend `make verify` with manifest conformance, real installed
entry-point discovery in a clean environment, wheel/sdist builds and contents,
license/provenance checks, and provider-fake tests. A filename ban alone cannot
prove that a component contains no HTML or JavaScript; validate data against the
zeocore component schema. Google additionally needs a Broker-path no-401-retry
test. The initial skeleton gate verifies its own tooling only.

## Migration and credentials

Move one package per PR, coordinated with zeocore's duplicate-name guard, extras,
compatibility shims and downstream runtime-host bindings. The credential-free
ffmpeg pilot follows zeocore groundwork. Remaining local plugins precede the
credentialed migrations. Each move keeps a per-operation map to the Broker;
package availability does not prove a Broker route is composed or admitted.

Credentialed execution belongs inside ZEOconnect. Packages accept credentials
injected there; they do not own token storage, refresh custody, enrollment or
seat-side secret discovery. Existing zeocore credential paths are changed only by
its owner and only under the approved per-operation migration rule.
Revolut enrollment is a separate principal-host-only package with no entry point.
The GitHub App signer stays local in `zeo_core.release.app_tokens`.

## Licensing and review

Preserve source copyright and MIT permission notices on every copied portion.
Record upstream repository, full source commit, paths and local destinations in
each package's NOTICE and the root NOTICE. The first VeyraX port requires council
license compatibility review. Do not copy its credential store or frontend code.

Ask zeo-rt to mint SOW ids. Every commit includes `sow: <minted id>`; line 1 of a
PR body is exactly that line. Push `zeointegrations/<slug>` branches to the fork
with at most one open non-draft upstream PR per repository. Open a new PR only
when the work is ready and the full repository gate has passed on that exact
head, including new draft PRs. Existing drafts stay draft until their gate passes.
Council reviews, the
Architect signs, and the merging app merges.

### Own-fork backups and required gates

Push daily backups to your own fork's `zeointegrations/wip/<topic>` branch.
Only that own-fork WIP route uses root Ruff lint and format checks instead of
running the full suite for the backup push. Test regularly on the work branch
with the full gate in your own lane, independently of backup pushes. A PR may
use that branch only after the exact-head full gate passes. Opening or updating
a PR must never start the heavy suite; PR checks remain light. Later scheduler
placement does not turn the PR into the full-gate trigger.
Before descendant Git/check commands, clear Git-local environment variables in
an isolated subshell using `git rev-parse --local-env-vars` and `unset` so a
parent hook's repository context cannot leak into another checkout. Run root
`uv run --frozen --offline --no-sync ruff check .` and
`uv run --frozen --offline --no-sync ruff format --check .` with a combined
wall-clock deadline below 180 seconds. Missing tools/cache, a timeout or a failed
check stops the backup push; never substitute a full suite or bypass a hook.
Prepare the approved tools and frozen cache separately before the quick check.
This repository currently has no installed pre-push hook: these are required
maintainer checks, not a claim that an automatic WIP mechanism is installed.

Every other push requires full own-repository `make setup` and `make verify` on
the exact candidate head in the maintainer's own lane (ENG-UK by default).
Before any final approval, Architect signature or merge, record that full gate's
HEAD, clean DIRTY status, host, EXIT and complete log SHA256 in the PR body.
The requirement also applies before a new PR opens and when an existing draft
becomes ready; rerun on any changed candidate head before updating its PR. A backup, quick check or draft is not qualification, release or
consumer acceptance. Preserve disabled upstream pushes and normal independent
Council review, Architect signing and merging-app integration.

Record baseline failures with the base commit, failing tests and original gate
evidence in the PR body, and name the repair owner and date. The maintainer
repairs main in its own PR. Never waive, skip or relabel a failure as passing,
and never use `--no-verify` or another actor or route to bypass a hook/refusal.
This text-only policy amendment adds no hook, checker, tool or configuration.

Full qualification runs locally and independently at council until pomar CI on
ENG-UK posts its signed gate. Public Actions is one three-minute dependency-free
PR smoke job, not the full gate. Under the operator's
DECISION-local-ci-on-pomar-actions-minimal-v1-2026-10-18, zeo-rt aligns required
checks with the smoke/council gate and later `zeo-ci/gate`; no removed full-CI
job may remain required. See docs/ci-toolchain.md for exact inputs and limits.
PyPI publication waits for operator-approved trusted-publisher setup; there is
no publishing workflow in this skeleton.
