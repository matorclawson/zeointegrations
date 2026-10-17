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
| uv installer | `astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e` (v6.8.0 commit, peeled from the annotated v6 tag) |
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

Council SOURCE verdict `zc-zi1-8de0-v1` identified the previous setup-uv pin as
an annotated tag object, not a commit. The corrected pin above was verified
through GitHub's tag and commit APIs. Both pinned actions use node20. Checkout
does not persist its token. Before the gate, CI adds only the workspace path
to Git's safe.directory list, accounting for the container/runner UID boundary.
The whitespace gate compares the empty tree to committed HEAD, so a clean
checkout still checks all committed text.

Draft jobs are skipped and GitHub may count that as a passing required check.
When adding `verify` to the ruleset, the Architect must retain the lane's draft
refusal and require an actual successful run on the reviewed head. A skipped
draft job is not qualification. Source review and tool-pin acceptance remain
distinct from the first real CI outcome.

## Pinned installer source check

Read-only review of setup-uv v6.8.0 at the exact commit above addresses the
question of installing uv 0.12.2 after that action was released. In
`src/download/download-version.ts`, an explicit version is retained; a missing
local manifest entry falls back to the corresponding GitHub release archive.
On the download path, the supplied checksum is validated before extraction.
`src/utils/platforms.ts` maps linux/x64 with glibc to the GNU x86_64 artifact
whose URL and digest are recorded above. There is no static maximum-version
check on that path. This supports the proposed route; it does not prove an
actual installation or execution of the bundled action.

There is a separate tool-cache path: `src/setup-uv.ts` first tries the runner's
tool cache and returns a hit without entering the download/checksum function.
`enable-cache: false` controls restoration of uv's dependency cache, not that
early tool-cache lookup. Thus the prior cache statement means no cross-run uv
dependency-cache restoration; it does not prove a cache miss for the uv binary.
Before claiming tool closure, the approved run must retain which installer
path occurred and the installed tool identity; a version string alone cannot
prove the archive checksum was applied to a tool-cache hit. Fresh-tool-cache
selection or installed-binary verification remains an Architect/Runtime review
decision. No new tool was installed or executed for this source check.

Immutable upstream references:

- [Version and download path](https://github.com/astral-sh/setup-uv/blob/d0cc045d04ccac9d8b7881df0226f9e82c39688e/src/download/download-version.ts)
- [Tool-cache branch](https://github.com/astral-sh/setup-uv/blob/d0cc045d04ccac9d8b7881df0226f9e82c39688e/src/setup-uv.ts)
- [Checksum handling](https://github.com/astral-sh/setup-uv/blob/d0cc045d04ccac9d8b7881df0226f9e82c39688e/src/download/checksum/checksum.ts)
- [Platform selection](https://github.com/astral-sh/setup-uv/blob/d0cc045d04ccac9d8b7881df0226f9e82c39688e/src/utils/platforms.ts)
