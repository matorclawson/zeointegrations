sow: zeointegrations-SOW-02

Register ONE PyPI pending trusted publisher for the aggregate

Open https://pypi.org/manage/account/publishing/ while signed in to the PyPI account that will own zeo-integrations. In “Add a new pending publisher”, select GitHub and enter:

| Field | Value |
|---|---|
| PyPI project name | zeo-integrations |
| Owner | zeroemployeeorg |
| Repository name | zeointegrations |
| Workflow name | publish-integrations.yml |
| Environment name | leave BLANK |

Click Add once. Check that the pending row has exactly these values. No API token, password in GitHub, per-provider project or environment is needed. The pending row does not create/reserve the project until its first successful upload.

Done when: after the reviewed workflow is merged through the normal merger and its CI venue is ready, the first eligible push/merge to main automatically creates https://pypi.org/project/zeo-integrations/ with the metadata version's wheel and sdist, an OIDC publishing receipt and PyPI provenance attestations. No release approval or operator workflow dispatch is required. An already-published metadata version is skipped; subsequent releases require a reviewed package-metadata version increase, not a new publisher setup.

Undo: before first publication, remove this pending publisher from the same account Publishing page. After publication, remove the trusted publisher at https://pypi.org/manage/project/zeo-integrations/settings/publishing/ to revoke future uploads. This does not remove already-published files or recall installed packages; the maintainer handles any release rollback/yank through the established release path.

Official instructions: https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/ ; automatic attestations: https://docs.pypi.org/attestations/producing-attestations/ . Exact account URL verified to redirect to PyPI login when signed out, 26 October 2026. No registration or upload was performed by this seat.
