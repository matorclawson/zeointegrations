# S1a fixture-only inventory comparison

sow: zeointegrations-SOW-02

Prepared source, **NOT_RUN** pending Runtime's own admitted venue/resources/queue.
No parser, imports, tests, formatter, lint, or full gate has been executed for this
slice. Source approval, production admission, and package qualification are pending.

The coordination source is
`matorclawson/org-zeroemployeeorg@e08c51f2e1c6211ea4914dabcf383020063354df:projects/zeoconnect/evidence/zeoconnect-tools/zeoconnect-tools-SOW-02/catalogue-source-and-qualification-handoff-v1.md`,
section S1a, confirmed in Messenger `ans_527217bf82164744` with explicit parser
interpretations. This is an original implementation of that fixture proposal;
it copies no provider/client/auth code and changes no production manifest ABI.

`tools.inventory_fixture.compare_fixture(bytes)` accepts at most 16,384 UTF-8
bytes and 64 items per array. Root keys are exactly `fixture_version` (integer 1),
`case_id`, `revision_label`, `required_names`, `admitted_artifacts`,
`installed_artifacts`, and `expected` (`accept` or `refuse`). Artifact objects have
exactly `distribution`, `version`, `artifact_sha256`, `dependency_lock_sha256`.
Strings contain 1–256 Unicode codepoints, excluding lone surrogates; digests are
64 lowercase hexadecimal characters. Duplicate/unknown keys and malformed
fields refuse. Names are exact case-sensitive fixture labels, with no package
name normalization. Empty arrays are valid; required names must be unique.

Installed names must equal required names, with one tuple per name. Every installed
version/artifact/dependency tuple must appear in that name's admitted alternatives.
Rollback to an admitted tuple accepts; a dependency mismatch refuses. Expected is
an assertion target and never changes the comparison verdict. Malformed fixtures
raise a bounded `FixtureRefusal`; valid fixtures return an immutable `Comparison`.
Labels and digests establish no provenance, approval, or execution authority.

The source uses only the standard library. It does not read paths, import packages,
discover entry points, install dependencies, call providers, store keys, or change
Broker composition. Prepared tests cover forward/rollback membership, mismatched
dependency closure, duplicate/missing/extra names, malformed/unknown fields,
duplicate JSON keys, Unicode, and byte/array limits. Those are planned assertions,
not successful qualification evidence. Existing `make verify` is the intended
gate only after Runtime binds its venue. S1c remains public GitHub
`get_repository`/`get_issue` after actual foundation PR2 merge and separate gates.
