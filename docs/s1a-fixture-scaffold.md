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

## Prepared mutation qualification, not executed

Each row below is a planned isolated semantic mutation and the behavioral
assertion that must kill it. These are ten test methods in prepared source,
not ten successful runs or kills. The eventual gate must run the unmodified
baseline first, apply one mutant at a time to an isolated copy, and verify the
named assertion fails while the mutant still imports and runs. Restore the
baseline between rows. Record killed/survived/accepted/not-applied/invalid
separately; import/build failure, panic, and timeout are not assertion kills.
No mutation runner or source execution is authorized by this plan.

| Planned mutation | Required behavioral assertion |
| --- | --- |
| Remove duplicate JSON-key rejection | Otherwise valid root and artifact duplicate keys raise `FixtureRefusal`; malformed roots alone are insufficient |
| Permit duplicate installed names | Two admitted copies of `demo` produce refusal |
| Permit missing or extra installed names | Empty installation or extra distribution refuses against required `demo` |
| Ignore installed version | Unadmitted version refuses |
| Ignore artifact digest | Changed artifact digest refuses |
| Ignore dependency digest | Changed closure and mixed rollback tuple refuse |
| Reject all rollback alternatives | Exact admitted version1/artifact/closure accepts |
| Let expected override actual comparison | Valid set with expected=refuse still accepts and fails the expected assertion |
| Accept uppercase/nonhex digest | Uppercase or nonhex digest raises `FixtureRefusal` |
| Remove byte bound or count characters | Exactly16384 UTF8 bytes accepts; one extra byte refuses, including multibyte labels |
| Permit65 array entries | Each artifact array accepts64 structurally;65 raises `FixtureRefusal` |
| Count UTF8 bytes as string codepoints | Label of256 multibyte codepoints accepts;257 refuses |

The artifact-array boundary fixtures distinguish malformed input from valid
comparison refusal:64 extra installed names refuse at comparison, while65 fail
shape validation. An eventual signed receipt must name the exact qualified
candidate head, readable log hash and honest mutation result split. Current
source remains **NOT_RUN**, without a signed receipt or submission approval.
