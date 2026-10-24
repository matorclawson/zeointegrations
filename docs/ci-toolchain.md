# Local gate and minimal public smoke

Updated 2026-10-18 under zeointegrations-SOW-01. The operator ruling
DECISION-local-ci-on-pomar-actions-minimal-v1-2026-10-18 supersedes the earlier
full GitHub CI/fresh-uv-acquisition proposal. Architect instruction
ans_e86749d038ad9111 directs this PR to a minimal smoke workflow and local gate
plus council's own run at the head. No actual GitHub run is required to prove the
full gate under this transitional ruling. A smoke outcome never replaces it.

## Full qualification gate

Run `make verify` at the committed source head: frozen Ruff lint/format,
standard-library inventory/artifact tests and whole committed-tree whitespace.
The local development inputs remain Python 3.14, uv with required-version
>=0.12.2 and Ruff 0.15.5 in the unchanged hash-bearing uv.lock. These existing
local tools were used for author verification; no new local tool was installed.
Put the exact head, command, test count and outcome in the PR body. Council runs
the full gate independently at that head before its final verdict.

The permanent full gate belongs to isolated pomar CI on ENG-UK, scheduled by
zeo-rt-sched with retained signed receipt and separate CI identity posting
`zeo-ci/gate`. Until that receipt/status exists, the operator ruling uses the
seat's full local gate plus council's run. This repository does not implement a
new runner, CI identity, scheduler, native installation or permission grant.

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

The PR body distinguishes author gate, council gate and optional smoke. Source
approval from an earlier head does not approve changed workflow bytes. Council
reviews this minimal workflow class and independently runs the exact-head gate;
Architect includes approved workflow-file changes in the operator's hand-merge
batch. No seat self-merges. zeo-rt owns required-check alignment: replace any
removed full-CI check requirements with the ruling's smoke/council/transitional
local gate, later zeo-ci/gate. Never leave an obsolete check blocking every PR.
