# U4 build provenance scope correction

**Direction approved; exact protected text and implementation remain proposals.** Javid
asked: “reconsider that added requirement while preserving the original build identity,
testing and reproducibility objectives.” This records that direction, not approval of
unseen source changes, an installed ADR, a build or public execution.

## Decision

Remove exhaustive build-read tracing as a mandatory gate. Keep the practical chain from
source and declared build inputs to the tested executable, run and result/table. Do not
mark absent trace evidence complete. Preserve startup assurance and all semantic checks.

The exact [proposed U0011 section](proposed-U0011-section.md) defines retained checks and
claim limits. [policy-and-plan.patch](policy-and-plan.patch) synchronizes U0011,
execution-plan, U-P7/U-P8/U-P11a/U-P11b/U-P11c and their build-spec §8 copies. It is unapplied.
CLAUDE.md reserves docs/decisions/ installation to humans: “Agents propose and stop on
contract/, tests/golden/expected/, CLAUDE.md, docs/decisions/.” This package does not install
that protected text. The user's scope direction is sufficient to prepare the successor;
there is no request to repeat that direction as another general approval.

## Why this is a scope correction

At u03-end, U-P11a required pinned tools/lock, tests and replay; the normative U3 interface
bound source/model/compiler/lock identities and operational executable digests. Detailed
read inventories appeared in A's K2 construction proposal at 1a52fa8; B's f6072ac proposal
made exhaustive construction-read observation explicit. Coordinator follow-ups reinforced
it. These later stronger claims are not necessary merely to identify the source of a table.
Historical decisions/evidence are retained, not rewritten to suggest the expansion never
happened.

## Current exact subjects and supersession

A source aecc6a27e1533eee43e884380ed095cfc1edfd20; handoff
e550a8801525c722792d375f78f623aebb72caeb; manifest
193d6621a1c1ad508048efffa990ac9ab08c8244c52c7200ff74700f5e9e4b23.
B confirmation b6d68aac54fff12eab629e2e1d53c3e645428a96.
Their 11-postimage package remains historically exact; it must not be installed wholesale
as the successor without separating retained work from tracing-only prerequisites.

- Retain exact construction argv/environment, source/generated/tool identities and useful
  startup enumeration; retain EOF/D3/deadline/resource/cleanup corrections and B's actual
  independent consumer. Fix the two disclosed return-annotation diagnostics in the successor
  with an explicit identity transition, without rebinding old executables.
- Supersede the mandatory activation trace-plan prerequisite in item 8 of
  U4-A-component-runtime-stage2-v1/proposals/activation-and-authority.md and its descendants.
  Preserve item 8's changed-source/new-identity and honest historical-evidence obligations.
- Supersede compulsory tracing/canary/diagnostic-policy acceptance in the current construction
  package and coordination prompts. No need to finish compiler-line allowlists as a gate.
  Existing capture tools remain optional, with their current strict evidence claims.
- Preserve items 4–7's campaign, image/host, immutable startup and A-F3 prerequisites.
  This decision does not resolve A-F3 or license retrying blocked verification.

## Engineering transition still required

The installed component_host.prepare_component currently requires
read_audit_complete=true in runtime-review/1. The proposed D3 path also carries the boolean.
Changing only prose will not release execution. A/B must propose an explicit successor
review record and consumer transition that checks actual build provenance and independent
startup assurance separately, rejects old/missing/mismatched evidence, and never fills the
old flag with a fabricated true. K2's historical host/authority is outside this migration.
See [transition checklist](transition-checklist.md).

## Work allocation and stopping point

Send [Lane A](lane-A.txt) and [Lane B](lane-B.txt) to the existing author sessions in their
normal independent clones. They can complete their owned work in parallel, publish one
interface batch and make one final join. They prepare a reviewable successor, without
building another intermediate candidate. Independent review targets changed gates and
provenance behavior; unchanged simulator/campaign evidence is reused with attribution.
After that review, prepare the concrete protected installation and clean-build decision.
Do not claim tracing removal alone makes public first use or U4 closure ready.
