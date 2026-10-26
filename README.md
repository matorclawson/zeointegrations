# Zeo integrations

One distribution, `zeo-integrations`, containing provider modules under
`zeo_integrations.<provider>`. The collection depends on published `zeocore`;
Core does not import the collection at import time. Provider SDKs are optional
extras, for example `pip install 'zeo-integrations[google]'` after the single
aggregate publication exists. During migration, install from this repository
at an exact reviewed commit. Do not register per-provider PyPI projects.

This first foundation supplies shared packaging for the provider move PRs;
it does not claim every provider is present yet. Google remains one family.
Existing Core entry-point names stay in Core, so installing the collection does
not register duplicate plugins. Core's optional lazy compatibility shims follow
actual aggregate PyPI publication. No base-contract extraction or injected ports.

The older per-provider source directories and hash-bound release files remain
historical/consumer evidence during transition; they are not additional future
PyPI distributions. Core-shaped whole provider moves and earlier standalone
hardened/read-only APIs have different scope and must not be silently co-installed.

# zeointegrations

Integrations for zeo tools: install only the packages a tool needs, discovered
through `zeo_core.integrations`. Split out of zeocore under zeocore-SOW-36.

External services use `zeo-integration-<name>`; local capabilities use
`zeo-plugin-<name>`. Google is one package with six existing entry-point names.
Credentialed integrations execute inside ZEOconnect with injected credentials.

This initial repository contains the development skeleton and a
[read-only source inventory](docs/inventory/README.md). No provider package is
installable yet. PyPI publication requires the approved trusted-publisher setup.
The first slice is tracked as `zeointegrations-SOW-01`, minted by zeo-rt.

```sh
make setup
make verify
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for layout, qualification, migration and
review rules; [NOTICE](NOTICE) records source attribution.
