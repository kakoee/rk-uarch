# Next U4 wave: component inputs and independent verification

Prepared after coordinator reconciliation `41f286e` of B `4684cb9` and A `d9a22f0`.
These are scoped worker instructions under the accepted execution plan, not amendments to
its canonical prompts or an installation, component-native execution or gate approval.

## Order and sessions

1. Existing B finishes [the combined-runtime package](../U4-K2-combined-runtime-reconciliation-v1/lane-B-final-package.md).
   Do not replace that assignment or run a second B author against the same clone.
2. Fresh A may start [component mapping and execution preparation](lane-A.md) now in its
   normal A clone. This delivers substantive mapper/export/import code and tests, using the
   installed component carriers. It does not need successful fixed-delay native calls.
3. Once B publishes its complete package, start one fresh independent reviewer with
   [the optimization review prompt](reviewer.md) and the coordinator-pinned final package
   commit. Review the combined A/B runtime and deployment together, before restart. This
   is a mid-sprint boundary review, not the final per-lane U4 review or sprint acceptance.
   Findings return to the original A/B authors; the same reviewer adjudicates responses.
4. After its packaging handoff, fresh B may start [component verification and reference
   readiness](lane-B.md) in its normal B clone. Retain the old B session for packaging
   corrections, but never let two sessions edit that clone concurrently. New B work pauses
   only its conflicting edits if a packaging correction must be made; Git remains the record.
5. Coordinator handles exact runtime approval, human root placement, final preflight, the
   798-call campaign and replay. Start only when the reviewed package and actual approval
   permit it. Neither lane may edit the sealed campaign inputs or start a competing campaign.

The campaign, mapper work and independent corpus work converge once K2's applicable public
checks/replay are reconciled, independent review requirements are satisfied, and exact
component inputs/remaining decisions are ready. The coordinator then records the scoped
U-P11b B implementation release. Campaign completion alone is not that release. Component
model implementation/execution must not start on a guessed future pass.

## What follows the campaign

K2 verifies the public boundary for fixed-delay jobs. The next stage is U-P7 M completion
plus U-P11b **B (component stage, not Lane B)**: hardware-derived compute-1, NoC-0 and DRAM-0
models, DMA credits/bandwidth, overlap, completion-based observations and causal attribution.
Lane A implements; Lane B provides independent U-P8/U-P12 cases and controls. These remain
at-most-C1 component predictions, not a complete decoder, silicon validation or product table.
Then U4b/R admits the actual reference chip and benchmark suite for G3a; U5 freezes and measures
predictions. Full product tables remain U7, rk-sim production integration U10. Missing TPU
access stays an explicit readiness dependency rather than an invented measurement.

## Scope and efficiency

The current wave starts work that is independent of K2 acceptance. It is deliberately larger
than a single correction: complete mapper/input delivery, independent component corpus and
checker preparation, and a bounded reference-readiness dossier. Native component code is
sequenced after verified K2 by execution-plan section 2 and U-P11b. No new full-grid task,
second Python timing simulator, hardware purchase, dependency install or U0024 waiver.

Publish normal Git commits on main and exchange published APIs/fixtures directly through
Git. One substantive handoff per lane, not a coordinator approval for each ordinary API join.
Tests run against exact inputs; rerun only affected selections during development, applicable
integrated checks once at handoff. Baseline evidence can be inherited only with exact scope.
No full campaign repetition for mapper/docs changes that do not alter its pinned runtime.
Keep big builds/full suites off the workstation while the coordinator runs the campaign;
light editing/units may continue. Do not poll CI or wait in loops for a future release.

Human L1 workings remain required at their first-use gate: H-L1-GEMM-01 and H-L1-DMA-01.
Agents may prepare questions/independent answers separately, never invent human working.
Canonical rollout of Python speedups remains distinct from the isolated campaign deployment.
Do not silently use proposed optimization source as if installed on main.
