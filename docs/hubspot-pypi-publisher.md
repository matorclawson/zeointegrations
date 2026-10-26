# Operator click list: HubSpot 0.1.0 on PyPI

sow: zeointegrations-SOW-02

Authorized by Architect `ans_7d79a7764593271c` (26 October 2026).
Publisher owner: zeointegrations. This route publishes only the unchanged,
reviewed `zeo-integration-hubspot` 0.1.0 wheel from canonical release
`966aac8f7fa0832f50ecfdd98d7856356ab998fb` (PR10): 22,004 bytes, SHA256
`5225a18818d84d48f7d5df94c0d3b7d6c87856bdfb11ad10de20bbe1932e16d8`.
It creates no API token and requires no key transfer. No other package or feed
is authorized. Prepare/review/hand-merge the workflow PR before dispatching it.

1. In GitHub, open [repository environments](https://github.com/zeroemployeeorg/zeointegrations/settings/environments).
   Create environment **`pypi`**. Add the operator as a required reviewer;
   restrict deployment branches to **`main`**. Save and verify these protections
   before approving a run. Never dispatch with an unprotected environment.
2. Sign in to the intended PyPI owner account and open
   [account → Publishing](https://pypi.org/manage/account/publishing/).
   Under **Add a new pending publisher**, choose GitHub and enter exactly:

   | PyPI form field | Value |
   |---|---|
   | PyPI project name | `zeo-integration-hubspot` |
   | Owner | `zeroemployeeorg` |
   | Repository name | `zeointegrations` |
   | Workflow name | `publish-hubspot.yml` |
   | Environment name | `pypi` |

   The workflow path is `.github/workflows/publish-hubspot.yml`; the PyPI form
   takes its **filename**, not that full path. Click **Add**. You should see the
   pending publisher row with this project, owner, repository, workflow and
   environment. This does **not** create or reserve the project yet. Tell the
   Architect the pending publisher and protected environment are configured.
3. After the workflow PR is reviewed and **hand-merged**, open GitHub
   **Actions → Publish reviewed HubSpot wheel → Run workflow**, choose `main`,
   and run it once. Review the deployment waiting on environment `pypi` and
   approve it only after confirming the publisher fields above. The workflow
   fetches the fixed canonical release, checks the exact wheel hash/size and
   metadata, and publishes only that wheel using short-lived GitHub OIDC.
   It runs no build or test suite and cannot publish another version or package.
4. Success: the Actions upload step is green, PyPI shows
   [zeo-integration-hubspot 0.1.0](https://pypi.org/project/zeo-integration-hubspot/0.1.0/),
   and the pending publisher has become a normal project publisher. Verify the
   PyPI file SHA256 equals the value above before Core adopts `==0.1.0` and
   locks the hashes. Core then verifies same-class forwarding and actual locked
   consumer installation; publication alone is not consumer acceptance.

If a dispatch outcome is uncertain, inspect the run and PyPI file first; do not
blindly retry. Existing files cause failure (`skip-existing: false`). A publisher
mismatch or denied environment approval requires correction by the operator;
never substitute an API token, a new index, a rebuilt wheel or another account.

References: [PyPI pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
[GitHub environment binding](https://docs.pypi.org/trusted-publishers/adding-a-publisher/),
[pinned publisher action](https://github.com/pypa/gh-action-pypi-publish/tree/dc37677b2e1c63e2034f94d8a5b11f265b73ba33).
