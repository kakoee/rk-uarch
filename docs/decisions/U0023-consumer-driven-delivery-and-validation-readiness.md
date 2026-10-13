# U0023 — Consumer-driven delivery and validation readiness

**Status:** direction approved by Javid on 2026-10-12 after the independent post-fork
review and coordinator response; this exact amendment takes effect upon human installation
and commit. No runtime implementation or gate acceptance is granted by this document.

## Context

U0005 correctly selected one progressive production Rust simulator. Its schedule retained
full-table prerequisites from the retired fork plan. The U4 npu-l4 grid is not an input to
U5's TPU benchmarks; the accepted inputs cannot meet its FP8/output-stationary/ragged
requirements. Reference-chip preparation was unscheduled, U10 could admit C1 as C2, and
runner requirements blocked correctness work independently of any performance claim.
The independent review and coordinator response are in
`docs/reviews/U3-post-fork-plan-review-v1/`. They are analysis, not blanket acceptance of
the detailed A/B proposals.

## Decision

Keep one Rust timing engine, the analytic baseline, independent verification, optional
matched external references and frozen-prediction silicon validation. Change delivery
order and prerequisites prospectively:

1. **U3/G2:** accept the bounded stage design and exact verification obligations. Identify
   each remaining analytic check's first consumer (including roofline checks, not just
   silicon). Unrelated analytic report completion does not block kernel development.
   Applicable checks must pass before reliance; no missing/failed case becomes a pass.
2. **U4a:** M prepares the mapped protocol, component mapper and fixtures. K1 implements
   internal fixed-delay time/event/resource mechanics after accepted semantics and exact
   toolchain/license decisions; it may overlap M. K2 wires the public boundary only after
   the human-approved mapped carriers exist. Then build the bounded models B. Private Rust
   unit fixtures are not a second public workload format. Detailed A assumptions, schema
   fields and host budgets still require their own concrete decisions.
3. **U4b/G3a — silicon readiness:** extend to the actual U5 suite, not the old full npu-l4
   grid. Before prediction freeze, verify reference-chip representation and admission,
   required operators/precisions, complete workload accounting, mapped replay, initial-state
   behavior, independent cases/faults and attribution used in the verdict. A GEMM-only stage
   does not complete G3a. No full-table, interpolation, FP8 or second-policy prerequisite
   exists unless the actual benchmark needs it. U-P9 retains its no-engine-change rule;
   reference support is implemented and verified before that prediction-only task.
4. **U5/G4 and U8/G7:** retain TPU v5e and Blackhole campaigns and existing numerical
   thresholds, benchmark classes, evidence scopes and ordering. Schedule sourcing,
   representation, measurement-observability and native-admission readiness before each
   freeze. For Blackhole, B's U-P16 S completes the reference, A's U-P15a implements/tests
   admission, U-P15 separately verifies and freezes, and U-P16 M measures afterward. Unknowns are explicit; carrier placeholders are not physical estimates. If a
   required benchmark is not meaningfully representable/measurable, return a scope/target
   decision rather than invent facts or silently remove it. Hardware access/spend remain
   separately authorized. No early silicon pilot is authorized. A future pilot needs an
   explicit development-versus-held-out protocol; exposure must not be called independent
   validation. G4's attribution-based 70% rule selects an investigation hypothesis, not a
   proven cause of error; qualification precedes its use and thresholds are unchanged.
5. **U6/G5:** qualify expanded mesh admission at declared representative points, diagnostics,
   independent verification and measured host cost. Re-run applicable integrated regressions,
   but do not rebuild the kernel or require a full C1 mesh table. Its technical prerequisite
   is accepted/verified bounded execution and the scope being qualified, not a successful
   silicon campaign. Silicon delays do not block independent engine development.
   Record G5-correctness, G5-performance and G5-automation separately. Full G5 requires
   all three. Only G5-correctness gates U7/G6/G3b and U10 (with their own required tests).
   Missing host measurements/nightly do not block those correctness/product milestones;
   they keep full G5 open. Both controlled-host performance evidence and executed
   self-hosted nightly remain required for full G5, U9 entry, any simulator-performance
   claim and final closure. Diagnostic host observations may be collected to establish
   readiness but must not be presented as qualified performance claims while either is
   missing. Chip-duration predictions in unvalidated tables are not host-speed claims.
6. **U7/G3b — first full product table:** generate full tables for declared study/demo
   consumers; the demo's npu-m256/70B/FP8/tp8 scope remains unless separately amended.
   G6 establishes the actual C2 mechanisms; G3b establishes the complete product table,
   public pipeline, worker determinism, required grid/error jobs and approximation bounds.
   Resolve hardware, precision/RoPE, ragged composition and schema decisions before their
   dependent runs. Required points cannot disappear to pass. Use suite points for studies
   and scale checks when sufficient; implement any needed point-result adapter explicitly.
   No mandatory full npu-l4 C1 or 32×32 grid remains without an identified consumer.
7. **U10/G9:** real rk-sim integration requires G6 plus G3b and rk-sim's separately accepted
   boundary. Its C2-only reader must refuse non-C2 or inconsistent composite detail. A small
   test-only conformance check against permitted vendored interfaces may precede U10, but
   it is neither production integration nor independent validation. Nulls never become
   zero; analytic fixtures never become C2 merely for the test.

**Tables and silicon are separate:** passing G4/G7 is not required to generate or use
verified, explicitly unvalidated tables. Nor does a full table establish accuracy. The U7
placement reflects the first planned full-table consumers, not a ban on earlier useful
small tables. Accuracy/error/badges follow actual applicable evidence; STUB, unknown error
and unverified energy remain wherever evidence is absent. U11 still requires the recorded
campaign verdicts and product demonstration; this amendment does not silently waive them.

## Correctness, performance and automation

- Native correctness/build work may run on approved Linux environments and hosted Linux CI
  with pinned toolchains/dependencies. The existing conditional native CI job is not proof
  of readiness: it must execute the real fmt/clippy/tests/license checks and the required
  debug/release cases when code exists. No source-empty/no-op job discharges a gate.
- Simulator-performance claims, noise-aware regression thresholds and U9 scaling require
  both controlled-host performance evidence and executed self-hosted nightly, with the
  designated Linux environment/allocation recorded. Both also gate U9 entry, even if the
  synchronization experiment is separately funded. No WSL performance claim. Toolchain acceptance is separate from host-budget measurement approval.
- Long runs require an authorized environment with adequate limits/capacity; duration alone
  does not require a particular GitHub runner. The self-hosted nightly must be operational,
  with an executed applicable suite, for G5-automation. Missing performance/automation
  leaves full G5, U9 entry, performance claims and final closure blocked; it does not gate
  U7/G6/G3b or U10 once correctness and their own admission requirements pass. Before then, required
  correctness suites run explicitly; their names/markers do not justify leaving them unrun.
- Prospective sprint correctness closure requires a fresh GitHub checkout on hosted Linux
  and a separate fresh local clone at the same published commit, recording actual commands,
  environments and no-ops. Controlled-host checks remain additional where applicable.
  U0020/U0021 and historical receipts are unchanged. Automation, server registration,
  hardware allocation and paid resources are not authorized by this documentation decision.

## Lifecycle, ownership and consequences

U0002's current binding and human generation/adoption rules remain operative. A separate
proposal must audit generator/support dependencies, including dynamic imports, data and
environment, before narrowing its inventory. Require relevant-change refusal controls,
unrelated-change controls and a reviewed migration. No automatic CI generation or adoption
is authorized here. Existing protections and historical artifacts are unchanged.
Before M's protected mapped-carrier installation, complete the dependency audit and
present its policy/migration decision. If the repair is not ready, explicitly record
Javid's decision to retain current enforcement and budget the required adoption cycles
for M/K2/B; no implicit waiver or unbounded deferral. The repair itself is separately
approved and need not be rushed merely to satisfy this planning milestone.

This ADR prospectively supersedes these U0005 requirements:
- full-table-before-silicon ordering and the U6 full-table requirement;
- unconditional runner prerequisite and complete-M-before-kernel ordering;
- completion of all applicable analytic U-P6 work as a G2 prerequisite: each required case
  now has a first-consumer deadline and must pass before reliance, with no fabricated pass;
- the old U4b full-table scope requiring the npu-l4 grid with both mapping policies and
  FP8 plus BF16 coverage. G3b instead requires the declared npu-m256/70B/FP8/tp8 demo
  consumer scope; BF16, npu-l4, tp1 and second-policy work remain required only at their
  separately declared consumers (including U-P14). No silently narrowed accepted consumer
  envelope or precision is allowed; a change to that scope needs its own decision.
U0005's original text remains as history with a supersession pointer. It also governs the
corresponding plan/prompt dependencies; U0001/U0002/U0003/U0004/U0006/U0019/U0022 otherwise
remain unchanged. Exact public contracts, semantic extensions and protected installs keep
their normal human review. No benchmark threshold, tolerance or fidelity promotion rule is
relaxed. No engine implementation, native test pass, measurement, table or sprint closure
is claimed. Re-estimate the revised tasks; old T ranges and per-point ceilings are not
current effort or runtime forecasts.
