# One-time aggregate publishing bootstrap

sow: zeointegrations-SOW-02

This supersedes the earlier blank-environment block under Architect17:52/17:53.
The operator owns these one-time account/admin changes; no per-release human
reviewer or manual workflow dispatch is added.

1. Open https://github.com/zeroemployeeorg/zeointegrations/settings/environments
   and select the existing **pypi** environment. Under deployment branches/tags,
   choose **Selected branches and tags** and add exactly one **Branch** rule:
   **main**. Keep required reviewers disabled, wait timer zero and no secrets.
   No wildcard, tag rule or unrestricted/default policy. The maintainer must
   read back `custom_branch_policies: true` and the sole branch rule `main`
   before the workflow PR merges. Without this rule another branch can claim
   the environment: the workflow declaration alone is insufficient.
2. Open https://pypi.org/manage/account/publishing/ while signed in to the PyPI
   owning account. Add one pending GitHub publisher with these exact values:

| Field | Value |
|---|---|
| PyPI project name | zeo-integrations |
| Owner | zeroemployeeorg |
| Repository name | zeointegrations |
| Workflow name | publish-integrations.yml |
| Environment name | pypi |

Click **Add** once; if a pending aggregate row already exists with a blank
or different environment, replace it with this row. Do not create any provider
project. Remove any retired HubSpot-only pending publisher if one is present
in the same account list; no such registration was performed by this seat.
An existing standalone project's trusted publisher, if one exists, must also be
revoked by its PyPI owner. Deleting its workflow does not revoke trust. Record
what actually exists; do not claim a pending row from an unrelated account is
visible or removed. Pending publishers do not reserve a project name.

Done when: API readback confirms the main-only/no-reviewer environment policy,
the normal reviewed workflow merge triggers the first eligible main push, and
https://pypi.org/project/zeo-integrations/ has that metadata version's wheel,
sdist and OIDC/provenance receipt. Only a complete matching wheel/sdist pair skips; partial or conflicting
versions refuse without upload.
Every new main commit automatically uses the source metadata base plus a PEP440
post-release counter from its complete Git first-parent history: for example,
`0.1.0.post42`, then `0.1.0.post43`. No manual version edit is needed for a merge.
The same commit always derives the same version, independent of the workflow
run/attempt, tags, or commit timestamps. Both jobs fetch full history and refuse
shallow checkouts. The base version is stamped only into each extracted source
archive before the two builds; the source checkout and lock remain unchanged.
The receipt binds this derived version to the source commit/tree, and the publish
job independently derives it again. A retry skips only matching complete bytes;
the digest-conflict refusal remains in force. This assumes protected main history
is extended normally, never rewritten to reuse a historical counter.
Build and publish use
the authorised hosted ubuntu-24.04 packaging-only venue; full gates remain ENG.
No environment setup, publisher registration or upload was performed by this
seat while preparing this block.

Undo: revoke the PyPI publisher first: remove its pending row from account
Publishing before first upload, or remove its trusted-publisher row at
https://pypi.org/manage/project/zeo-integrations/settings/publishing/ afterwards.
Keep GitHub's main-only policy while that trust remains. The maintainer can
then disable publication through the normal reviewed source path. Revocation
does not remove published files or recall installed versions; any yank/rollback
requires the established release procedure.

Official setup: https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
Security model: https://docs.pypi.org/trusted-publishers/security-model/
