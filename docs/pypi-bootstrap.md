# Package publication boundary

The retained `publish-integrations.yml` workflow is checks-only. A main push
validates reproducible package builds and the installed-wheel import boundary,
then retains check artifacts. It has no PyPI job, deployment environment,
OIDC write permission, registry upload or GitHub release step. A successful
check artifact is not a release candidate or a published release.

Publication belongs to the separately reviewed release path: build a candidate
once on an admitted Linux gate host, bind its commit and artifact checksums,
review and sign it, and have the normal merger promote those same bytes without
rebuilding. Candidate and release implementation are separate work; this change
cuts neither a candidate nor a release.

Earlier automatic publish-on-main bootstrap instructions are superseded. Do not
create, replace or revoke publisher registrations or change environment policy
using this document. Removing a workflow job does not revoke existing PyPI trust
or remove already published versions. Publisher/account policy remains with its
owner through the approved release process; no account or settings change is
claimed here. Historical bootstrap instructions remain in Git history.
