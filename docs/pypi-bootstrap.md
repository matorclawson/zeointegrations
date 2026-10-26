# One-time PyPI bootstrap: zeo-integrations

sow: zeointegrations-SOW-02

The operator performs one PyPI owner-account registration. Everything on GitHub
is configured by reviewed scripts/CI through an authorized administration owner.
There is no per-provider publisher and no per-release human deployment approval.

Open [PyPI account Publishing](https://pypi.org/manage/account/publishing/),
choose **Add a new pending publisher → GitHub**, and enter:

| Field | Exact value |
|---|---|
| PyPI project name | `zeo-integrations` |
| Owner | `zeroemployeeorg` |
| Repository name | `zeointegrations` |
| Workflow name | `publish-integrations.yml` |
| Environment name | `pypi` |

Click **Add**. The pending-publisher row should show these exact five values.
The name is not reserved until the first upload. Do not register
`zeo-integration-hubspot` or follow the superseded per-provider click list.
No token, key, API password or credential transfer is needed.

After the one registration, main merges that change the collection publish
without an operator dispatch or reviewer click. CI computes `major.minor.N`
from the reviewed source version and immutable first-parent commit count;
builds/tests run on ENG, and the publish-only Linux job uploads the digest-bound
artifacts using OIDC. PyPI version/file hashes and source URL are read back.
Core optional lazy-shim/extra receiving is a later Core-owned PR; ordinary Core
imports remain independent of the collection.

GitHub administration owner runs `python3 tools/configure_integrations_release.py`
for a read-only plan and the same command with `--apply` for setup/readback.
It configures `pypi` with main-only deployment, no reviewers and no wait timer;
it stops if Administration-write permission is unavailable. Runtime must supply
an admitted ENG runner with labels `self-hosted`, `macOS`, `ARM64`,
`eng-uk-0006`, `zeointegrations`, its existing pinned toolchain/UV_PYTHON and
20GB workspace/cleanup. Those runner labels are a requested binding, not an
existing runner claim. The workflow PR uses the normal merger after the
operator's already-requested mator-merger Workflows permission update.
Do not use a hand merge or alternate actor to bypass that permission boundary.

No pending publisher, environment settings or actual upload were performed by
preparing this document. Setup and first automatic publication remain observable
acceptance steps. A failure retains its exact source/log/artifact hash; it is not
relabelled as a published or consumer-accepted version.
