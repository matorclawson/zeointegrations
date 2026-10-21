# Full gate and minimal public smoke

Updated 2026-10-21 under zeointegrations-SOW-02. This follow-up corrects the
review and execution wording from the approved foundation without changing its
workflow, tool pins, tests or required checks. The operator's
DECISION-local-ci-on-pomar-actions-minimal-v1-2026-10-18 replaced the earlier
full GitHub CI/fresh-uv-acquisition proposal. Its later evidence-review addendum
and RULING-476 control the execution boundary described here. A public smoke
outcome never replaces the full gate.

## Full qualification gate

Run `make verify` at the committed source head: frozen Ruff lint/format,
standard-library inventory/artifact tests and whole committed-tree whitespace.
Current verification commands use `uv run --frozen --offline --no-sync`; the
receiver must provide and qualify the complete existing locked environment.
No-sync does not prove that an installed executable matches the lock.

The development inputs remain Python >=3.14, uv >=0.12.2 and Ruff 0.15.5 in the
unchanged hash-bearing uv.lock. Setup/acquisition is a separate approved act;
missing dependencies cannot be installed or downloaded during qualification.
Keep the whole committed-tree whitespace check, not a working-tree-only check.
A receiver using Git history must retain the actual pinned source identity;
history-free input is not an automatic replacement for that gate.

Full qualification runs through the owner-admitted Pomar shared runner,
scheduled by zeo-rt-sched. Runner owners retain admission, deadlines, resource
limits, process cleanup, log bounds and execution receipts under RULING-476.
The project supplies its fixed application command and behavioral assertions,
not another executor. Source preparation or a queued request grants no venue.

Record the exact head, command, environment/tool bindings, test count and outcome
in the review evidence. Distinguish author development checks, actual shared-runner
qualification, any independent rerun and optional smoke. Council reviews the
exact-head evidence; a Council verdict does not imply a Python rerun. Schedule
required Python reruns through zeo-rt-sched in the admitted venue. No signed
runner receipt or posting of `zeo-ci/gate` is implied by this documentation.

## Optional public PR smoke

One `pull_request`-only job, `smoke`, with a three-minute timeout. It compiles the
skeleton Python and runs the dependency-free standard-library fixture tests.
It does not install uv, Ruff, provider packages or build backends. The abandoned
fresh-uv helper and its installer-only mock tests are removed with that proposal;
inventory/artifact behavior tests remain. Full lint/format remain in make verify.

| Input | Selection |
|---|---|
| Job filesystem/Python | `docker.io/library/python:3.14.3-bookworm@sha256:647fc2dbb7df74521c75aac3f21668234b7e91433bda558abcf2547ee84c3ad3` |
| Checkout | `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683` |
| Python command | `/usr/local/bin/python3.14` from the pinned container |
| Host | GitHub-managed `ubuntu-24.04`; host image is not claimed immutable |
| Token permissions | `contents: read`; checkout does not persist its token |
| Secrets | None; no repository/provider secret, publishing or custody |

No push, schedule, dispatch, matrix or second PR job. The container has no native
media operation; tests use in-memory source fixtures and retained inventory data.
A draft skips smoke and is not qualified. New package acquisition and release
remain separately reviewed under their own dependency/executor/publication gates.

## Review and merge

The PR body distinguishes author development evidence, actual full gate,
independent reruns and optional smoke. Approval from an earlier head does not
approve changed source or workflow bytes. Ordinary product review goes to
zeoreviewer; sensitive C1-C6 changes go to Council. Reviews bind the exact head
and retain any unmet conditions.

The Architect signs required lane evidence and sequences a supported merge
route, including workflow-capable handling when needed. No seat self-merges or
changes actor permissions to make a merge succeed. A posted approval is not a
claim that a merge has happened or a receiving environment is installed.

zeo-rt owns required-check alignment. Do not add an obsolete full-CI or `verify`
job requirement: current installed lane/check policy and its reviewed successor
control the names. The intended signed Pomar gate is not an installed check
merely because it is documented here. This follow-up changes no workflow,
required-check configuration, tool pin or runner implementation.
