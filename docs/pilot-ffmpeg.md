# ffmpeg preparation and qualification limits

The package is prepared on a separate branch under zeointegrations-SOW-01.
Skeleton PR2 remains the only open PR. This branch does not change its reviewed
head or activate CI. No package PR or PyPI publication is implied.

Source is zeocore at 3682eb120c6b02b3927c97e6530c9cd1d976be3a, the core
owner's slice1 handoff. Its release uses distribution name `zeocore`, version
0.24.0. The source modules retain shared core dependencies, both public factory
surfaces and their behavior; own-package imports change namespace. The original
MIT notice and per-file source hashes are in the package LICENSE and NOTICE.
Neither the five adapter modules nor the metadata tests run native media tools.

The manifest follows the eight owner-confirmed fields. It is UTF-8 JSON with
16384 bytes maximum (bounded read before parsing), 64 items per array, 256 Unicode
code points per string and nesting depth8. Duplicate keys, unknown fields,
control characters and malformed types are refused. Distribution names compare
after lowercase and replacement of runs of dash/underscore/dot with dash.
The pilot minimum version is an exact numeric major.minor.patch, matching the
literal dependency floor; this is deliberately not a general PEP440 parser.
The dependency is `zeocore>=0.24.0`, as the core maintainer requires. A
`<0.25.0` ceiling would exclude the following core release that removes its
in-tree registration, preventing the transition the plugin exists to support.
The manifest minimum remains 0.24.0.

Provenance uses an HTTPS GitHub repository, a 40-lowercase-hex commit and relative
POSIX paths: no absolute, backslash, empty, dot or parent segments. Metadata never
fetches a repository or imports a target. Entry-point names equal the package's
entry-point table; the actual target must still be proved by installed discovery.
Local `operations` values are existing Python method names, not Broker operation
IDs or authorization. ffmpeg has no secrets and must remain kind plugin.

The validator checks descriptive metadata. A string ban cannot prove that code
has no executable behavior. Its seven new tests cover metadata agreement and
refusal cases; they neither import the plugin nor prove media behavior. Existing
skeleton tests still use inert/mock fixtures. The complete local author gate
does not replace package qualification or actual hosted CI.

Hatchling 1.32.0 is proposed as the exact build backend, aligning with the version
identified by council in core's existing toolchain. The earlier 1.27.0 preparation
pin had no demonstrated compatibility reason to differ and is superseded.
It has not been acquired
or executed here. New builder/dependency acquisition and installed testing need
the reviewed tool inputs and appropriate evidence, separately from skeleton
tool acceptance. All build/runtime/transitive dependencies are new to this
repository: operator approval through Architect is required before adoption or
a pilot PR, in addition to Runtime/owner qualification. The Python 3.14-only
candidate environment is deliberate initial coverage; it does not qualify every
future Python version allowed by the package's open-ended `>=3.14` declaration.
Do not describe a declared backend as qualified.

Before opening the pilot PR after the skeleton lands: obtain builder/dependency
input review; build wheel/sdist and inspect contents/notices/namespace; perform
clean installed entry-point discovery and duplicate refusal; port the upstream
behavior tests using fake probe/recipe/binary/filesystem effects; obtain the
core-owner shim/extra/entry-point-removal handoff and publish smoke; send exact
head to the core maintainer and council. The core0.24.0 wheel still owns ffmpeg,
so installing it together with the new registration must be refused. Do not
remove or disable the guard to obtain a passing pilot. Operator-approved release
and trusted publishing remain separate gates. No source in zeocore is edited.
