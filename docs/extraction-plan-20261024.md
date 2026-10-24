# Integration extraction: delivery order and compatibility

sow: zeointegrations-SOW-02

Operator priority relayed by Architect
`msg-architect-architect-zeointegrations-top-priority-20261024`.
Source inspected: `zeroemployeeorg/zeocore` at
`25a9c899c17ac6cdf54f4949e54b0fcc800cce91` (directory tree, Kit/HubSpot
clients and transport, shared base, and registered entry points). This replaces
the old inventory as the extraction starting point; each move repins its base.
PR #2 merged at 03:26:26 UTC on October 24 as `60988bde`; do not rewrite that PR
or create a duplicate workflow follow-up. No provider package is delivered yet.

## Order

The supplied list contains **21 directories**, not 20 provider distributions.
Shared infrastructure stays in Core; families can contain several providers.

| Wave | Existing directories | Destination / acceptance dependency |
| --- | --- | --- |
| 1 | `kit`, `hubspot` | `zeo-integration-kit`, `zeo-integration-hubspot`; newsletter consumers first. Preserve `kit.marketing` and `hubspot.marketing`, public types, review/confirmation guards and transport behavior. |
| 2 | `ffmpeg`, `pandoc`, `jupytext`, `notebook` | Optional `zeo-plugin-*` packages; preserve the three existing registered names and notebook direct imports. Reuse parked ffmpeg preparation only after its coverage is reactivated. |
| 3 | `github`, `notion`, `social` | Optional integration packages; preserve `github`, `notion`, `social.bluesky`. Move GitHub provider code only after its App signer is separated in Core. Classify other social subproviders separately. |
| 4 | `google`, `meetings` | One `zeo-integration-google` for all six existing Google names; meetings follows its Google/Notion dependencies. No duplicated Google distributions or custody stores. |
| 5 | `database`, `llms`, `gemini` | Provider-specific packages, starting with existing `supabase` and `llms` names; classify database subproviders and Gemini consumers before moving them. No umbrella dependency that reinstalls every provider. |
| 6 | `agents`, `briefing_sources`, `model_ops` | Classify provider-specific adapters versus orchestration with Core; extract adapters after their provider dependencies. Pure shared orchestration is not a provider package. |
| 7 | `revolut` | Preserve `revolut.business`; separate principal-host enrollment with no entry point. Credentialed execution and enrollment custody must not migrate into a general package. |
| Retained infrastructure | `core`, `hosted`, `environments` | Keep generic contracts, registry/loader, custody class and hosted/environment machinery in Core. Move provider-specific catalog entries/adapters out in their matching provider wave. |

**Loops goes FIRST**, per Architect `ans_e2264e94650214a6`; open the Kit/HubSpot
PR immediately after Loops merges, keeping one open PR at a time. Loops is born
only in `packages/loops`:
campaigns, LMX email messages, audience, uploads, contacts and webhook signature
checking. No key custody, send or schedule operation. Broker supplies credentials
and owns execution/permissions. Agree the canonical API and connector consumption
with zeoconnect before choosing endpoints or a similarly named third-party SDK.

## What stays and how consumers move

Core owns the shared client/protocol/result contract, registry, generic custody
and host boundary. Provider URLs, request/response models, transports and business
operations live in their optional package. Provider-specific custody is not copied
into a package; existing custody transitions require the Core/Broker owner.
No new provider implementation lands in Core; a thin compatibility import is not
a second implementation.

Until releases exist, use a **full commit-pinned Git dependency with a package
subdirectory**, one distribution per requested capability. Commit each consumer's
lockfile and verify the exact wheel contents/import origin; no branch pins,
editable installs, floating dependency or automatic PyPI publication. Reuse the
existing approved dependency set; any new build/runtime dependency needs its
individual checkpoint. Packages using the shared contract depend on minimal Core,
never its all-provider extra. Core compatibility extras select only the requested
package; resolver/install tests must cover that transition without duplicate names.

The Core maintainer supplies explicit forwarding modules for old public imports,
preserving class identity, exports and signatures; no catch-all import hooks or
silent credential fallback. Transfer each entry-point registration in the paired
Core/package change so installed discovery sees exactly one provider. Package
availability alone is not Broker composition or permission. Keep MIT notices and
per-file source provenance. Delete old implementation only after package, shim,
installed-discovery and consuming newsletter tests pass under independent review.

## Immediate acceptance checkpoints

1. Kit/HubSpot: owner-agreed pinned exports/dependencies, package contents and
   isolated installed tests; Core-owned shims/registry/extras; newsletter consumer
   runs against those packages with provider doubles before a live rollout.
2. Loops: zeoconnect agrees canonical API/LMX/signature contract and import target;
   build API client and refusal/contract tests with injected credentials/transport.
   Verify absence of send/schedule and credential persistence; draft PR target
   12:00 UTC, newsletter extraction PR target 18:00 UTC on October 24.
3. Full gates require an actually permitted venue. The native Swift Pomar91 lane
   is not an extraction prerequisite. Its withdrawn receiving request is parked;
   GitHub S1c source remains preserved at `4c19eac` without priority over extraction.

The same Architect ruling explicitly covers this implementation under the
operator's extraction direction; no further issuer coverage is a source-start
condition. Request the Python gate on ENG-UK through Runtime independently of
Pomar91. If no venue is bound by 11:00 UTC, open the Loops PR marked NOT_RUN;
Council may review it, but merge waits for the actual green gate.
