# Proposed skeleton CI tool closure

Created 2026-10-17; zeointegrations-SOW-01. This records exact proposed inputs,
not independent qualification. Runtime agreed the isolated, secret-free fork-CI
shape in `ans_43eb0865c0915018` and requested these concrete bindings for review.
The Architect reviews new tools/pins. Keep the PR draft until that review is
received; draft PR jobs are skipped. No provider implementation is executed.

| Input | Exact selection |
|---|---|
| Job filesystem / Python | `docker.io/library/python:3.14.3-bookworm@sha256:647fc2dbb7df74521c75aac3f21668234b7e91433bda558abcf2547ee84c3ad3` (linux/amd64) |
| Container config | `sha256:743fa48c85547dcd834e4733974a8e278f913be7c03720c144c3a8614e80df83`; registry config declares `PYTHON_VERSION=3.14.3` |
| checkout | `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683` |
| uv installer | `astral-sh/setup-uv@d0d8abe699bfb85fec6de9f7adb5ae17292296ff` |
| uv | `0.12.2`, linux x86_64 GNU archive SHA256 `d66e96b5f1ca3b99806eee283a8125d33a0bd669e6e6d9bc4ab7ffda63c41bf4` |
| Ruff | `0.15.5`; selected platform wheel and sdist hashes are recorded in `uv.lock` |
| Python acquisition | Preinstalled exact container Python; `UV_PYTHON_DOWNLOADS=never` |
| Cache | Disabled in setup-uv; no cross-run restoration |
| Command | `make verify` with frozen dependency resolution |
| Credentials | GitHub contents-read token for checkout; no provider/repository secrets or publishing permissions |

Artifact routes: the Python Docker Official Image manifests/config come from
`registry-1.docker.io/v2/library/python`; uv's archive is
`https://github.com/astral-sh/uv/releases/download/0.12.2/uv-x86_64-unknown-linux-gnu.tar.gz`,
with its digest reported by the release asset metadata and enforced by setup-uv.
Ruff wheels come from `files.pythonhosted.org` at URLs/hashes in the frozen lock.
Container metadata and the uv digest were read from those upstream APIs without
executing downloaded code. Independent artifact/tool qualification is not claimed.

GitHub's `ubuntu-24.04` runner host and the action Node runtime are managed by
GitHub and cannot be selected by an immutable hosted-image digest in this
workflow. The job filesystem is pinned by the container digest, and CI records
the actual host `ImageOS`/`ImageVersion`. This is a stated host limitation for
the Architect/Runtime review, not a claim that the host is immutable. The only
development dependency is Ruff; provider code/packages, credential custody and
publishing are outside this job.

Local checks use the installed development tools and count as author results.
Attach actual GitHub run and source-head identities separately when received.
