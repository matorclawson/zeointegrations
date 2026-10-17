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
