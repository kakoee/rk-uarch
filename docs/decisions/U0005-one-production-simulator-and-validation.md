# U0005 — One production simulator and scoped verification and validation

**Status:** direction approved by Javid on 2026-10-12; this exact amendment takes effect
when human-installed and committed. This is the first accepted U0005, not a rewrite of an
accepted fork-selection verdict. No candidate was built or run and no empirical G2 result
is asserted. The source-only investigation at `42fc3414d6329675164940aa40289689d7ef81ea`
remains historical evidence, including its now-unselected Python U-C1 design recommendation.

## Prospective sequencing amendment

Once human-installed, [U0023](U0023-consumer-driven-delivery-and-validation-readiness.md)
supersedes this ADR's delivery ordering and host/runner prerequisites as specified there.
The original decision below is preserved; use U0023 and the current execution plan for
future task release. The one-engine direction and verification/validation limits remain.

## Context

The previous plan required a complete external simulator before the native engine, then
permanent matched native/fork agreement; its fallback commissioned a substantial Python
contention engine. Source inspection has not established a faithful adapter-only route at
the inspected ONNXim/PyTorchSim pins. Extending those tools substantially would introduce
our own modeling assumptions without establishing independent whole-chip truth.

## Decision

Develop one production timing simulator progressively in Rust. Retain the existing Python
U-C0 analytic baseline, preparation, mapping, orchestration, reports and historical nominal
compatibility checks. They are not a second detailed simulator. Do not commission a second
substantial Python contention engine or require a complete external fork to proceed.

Correctness and accuracy have separate obligations:

1. Independent mathematical expectations: small counts, transfers, dependency/critical-path
   timing and clock-edge cases with derivations independent of production helpers.
2. Behavioral verification: resource conservation, causality, capacity/queue limits,
   contention where represented, permitted overlap, exact replay and deterministic output.
   Discriminating mutants must fail at the public boundary; empty/skipped checks never pass.
3. Optional scoped external references: compare only matched represented work, numeric
   formats, architecture parameters, mapping, initial state and abstraction. Record tool
   revision, dependencies, implementation overlap and limits. Same-code comparisons are
   integration checks, not independent L2 evidence. Unsupported/unmatched cases are not_run,
   not passes. Admitted comparisons have prospectively declared criteria; removing a tool
   after observing disagreement cannot erase the finding or turn a failure into a pass.
4. Silicon validation: freeze predictions before measurements; progress from microbenchmarks
   to operators/fused units to end-to-end workloads; publish errors, unknown parameters,
   unsupported regions and mapping differences. Component evidence never validates a whole
   chip or an arbitrary proposed design. U5/G4 and U8/G7 thresholds remain unchanged.

Small test-only reference calculations and event-order oracles are allowed. They must not
become a second production engine. Rust safety and internal agreement do not establish
physical accuracy. Functional tensor-value execution remains outside simulator scope;
completed-work observations may be derived from executed jobs, never merely echo expected
input totals and claim them as independently observed work.

## Ordering and replacement gates

- **U3 / G2: native-stage design and verification readiness.** Repurpose U-P5 to design
  a bounded first native stage, explicitly covering v2 RoPE and legacy admission/refusal.
  Human acceptance of the exact mapped protocol and stage scope is required before runtime
  work. Complete U-P6's applicable analytic verification and disclose remaining cases.
  G2 is a design/readiness decision, not a measured simulator pass or U3 closure by itself.
- **U4a: bounded native stage.** U-P7 first delivers the approved minimal mapped-input
  boundary and hand fixtures; U-P11a then builds the single-threaded kernel; U-P11b first
  supports a small declared workload/hardware/precision slice. NoC/DRAM start at level 0,
  compute at level 1, composite C1 at most. Capability refusals remain explicit. B develops
  U-P8 limits and the foundational U-P12 verification alongside these stages.
- **U4b / G3: full table.** Expand the same engine to the existing declared U4 grid only
  after the bounded stage passes. Deliver both mapping policies, all required operator and
  precision coverage, worker determinism and measured table approximation errors. A bounded
  prototype is not the full-table exit. Unsupported required points block G3 or require a
  separately accepted scope change; they cannot be omitted to pass it.
- **U5 / G4:** first silicon campaign remains after G3; hardware/budget authorization is
  separate. There is no dependency on future U6 qualification to avoid a cycle.
- **U6 / G5: native qualification and diagnostics.** Complete U-P11c/U-P12, extend to
  the initial mesh table, independently verify resource behavior, replay, diagnostics and
  attribution, and record absolute host cost against prospective budgets. Delete the
  mandatory 3%-on-95% fork-agreement and fork-relative speed-factor requirements. G5 is
  replaced, not waived; failures block U7 or require explicit scope amendment.
- **U7–U11:** deeper models, silicon, conditional parallelism, product integration and
  hardening remain. Remove only deferred whole-fork comparisons and obsolete dependencies.

No mandatory ONNXim-compatible policy, fork container/adapter or complete-fork maintenance
campaign remains. Optional component tools and the planned Ramulator library are separate
choices. The existing 10% NoC comparison bound below 70% reference saturation is retained
when a compatible independent NoC reference is admitted; no forced match to an incompatible
abstraction. Optional L2 absence is disclosed, never substituted for required L0/L0m/L1 or L3.

## Consequences and limits

The complete first-stage design, mapped schema, exact acceptance corpus, failure reductions,
license/toolchain decisions and prospective host budgets are subsequent concrete decisions;
this ADR supplies no invented measurements or automatic implementation release. The old
200-second one-layer fork proposal is not adopted for native. Re-estimate U3–U6 after the
bounded design; old totals/calendar and the 16–28 hour U-C1 design estimate are not forecasts.

A real designated Linux host and self-hosted `uarch` runner with an executed manual nightly
remain prerequisites before native implementation/build/performance work. Documentation and
analytic preparation may proceed while these are pending. No existing CI no-op is evidence
of native or nightly readiness. No server registration, paid resource use or hardware purchase
is authorized by this decision.

U0001/U0002/U0003/U0004/U0006/U0019/U0022 retain contract ownership, artifact lifecycle,
workload semantics, replay and evidence restrictions. Historical accepted ADRs remain intact;
this prospective decision supersedes only their future fork-delivery assumptions where they
conflict. Existing v1/v2 carriers and fixtures are not changed by this documentation amendment.
Any later new native/optional-reference carriers need their normal human schema decision.
No artifact refresh, runtime change, badge promotion, prediction generation, sprint tag or
closure follows from this ADR. STUB, unknown error and unverified energy remain in force.
