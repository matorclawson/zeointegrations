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
PR body is exactly that line. Push branches to the fork and open one upstream PR
at a time. Council reviews, the Architect signs, and the merging app merges.
After this CI lands, the Architect adds its `verify` check to the main ruleset.
PyPI publication waits for operator-approved trusted-publisher setup; there is
no publishing workflow in this skeleton.
