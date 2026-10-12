# U3-RoPE-and-verification-v1 — proposed acceptance package

Status: ready for Javid's decision; not accepted. Coordinator review only, not independent
U-REVIEW. Primary main is ce0bb13f486146ad6babd2ac42aea5dedcdb208c, containing both authors'
unchanged proposal files. No runtime or protected path changed during reconciliation.

## A: U0022 semantic decision

Subject: docs/reviews/U3-RoPE-semantics-proposal.md at
7d15c5aa73504c38eac3b3dc162d2885cc1f33dc, exact text between the ADR markers.
U0022 is absent from current ADRs and no competing assignment is recorded. Reserve it
for this decision when acceptance is recorded; do not create another assignment.

Recommend accepting the proposed explicit Q/new-K rotary semantics, positions, coefficient
inputs, precision/conversion counts, traffic/rank rules and versioned historical separation.
This adds modeled vector work and memory traffic; it adds no matrix work or learned
parameters. The precomputed profile does not claim coefficients match a named model without
supporting inputs. U2's published results remain historical results for a graph lacking
RoPE, with the proposal's exact limitation; they are not rewritten as complete decoder work.

After semantic acceptance, prepare the human-owned U0022 ADR commit. Then A's next task is
the exact additive schema/compatibility and implementation/lifecycle proposal, with tests
specified first. This acceptance does not authorize production or protected-schema edits,
oracle generation/adoption, or the implementation of that future diff. Publish current
limitation prose only through a concrete coordinated scope; do not edit historical evidence.

## B: U0006 and standalone report scope

Subjects at 428b7bb29664b7de2b8c8ef8ce3a8bad2e5245ee:
- docs/reviews/U3-U0006-report-supplement.md
- docs/reviews/U3-U0006-report-example.json

Recommend accepting exact section 1 ADR wording, revised sections 2–4 source profile and
reductions, and section 6 standalone implementation/test scope. Section 5 production
carrier/eligibility integration and section 7 future fork telemetry remain proposals,
not additional implementation permission.

After acceptance and the human-owned U0006 ADR commit, authorize B to write the specified
discriminating tests and standalone generator/validator under validation/reporting/ using
existing dependencies and carriers. Retain all actual calls and failures; internal framework
counts remain null when unobserved. Qualifying replay uses a frozen corpus; missing cases,
changed implementation and false completion refuse. The complete current illustration is
skipped-only, not a tested actual-run example; the implementation must supply actual passing
controls in both modes and populated-case/refusal tests as specified. No production loader,
model card, source eligibility, A-owned or protected paths are included. No badge promotion.

## Coordinator checks executed

Independently recomputed all four RoPE vector/read/write examples from per-pair operations,
and both adjacent/split-halves pairing examples; all agree. B example validates against
existing EngineIdentity/AssumptionSet, matches current assumptions and lock hash, and has
consistent plan/corpus hashes, both-mode empty case coverage and none/not_run reduction.
Verified the three live proposal files are byte-identical to their author commits.

These are proposal arithmetic/identity checks, not implemented semantic/parser tests,
independent review, a full-suite rerun or physical validation. The illustrated runner does
not yet exist and no report is attached as evidence.

## Approval and remaining boundaries

Javid may approve U3-RoPE-and-verification-v1 as both decisions, or identify A/B separately.
On approval, record acceptance against the commits above and prepare exact ADR files for
human commit under the existing CLAUDE/U0000 rules. This proposal alone creates no ADR.
Normal lane-owned commits and pushes continue on main; protected commits remain separate.

The fork-tool choice, additional candidate investigation, instrumentation, fallback,
U0005/200-second limit, licence/resource decisions and G2 verdict are not approved here.
Runner registration/manual nightly is still pending with Reza. No sprint closure follows.
