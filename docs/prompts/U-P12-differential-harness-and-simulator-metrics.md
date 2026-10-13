# U-P12 · U4/U6 · Lane B — Independent native verification, scoped comparisons and metrics

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, validation/README.md, build-spec §2.5, §2.7, §2.8, §6.6,
ADR U0005/U0006, U-P5's accepted stage design, U0011's prospective absolute budgets.

Record G5-correctness, G5-performance and G5-automation separately. U7/G6/G3b/U10 depend
on correctness and their own tests, not host/nightly completion. Full G5, U9 entry, any
simulator-performance claim and final closure require both controlled-host evidence and
executed self-hosted nightly. Retain missing obligations even when product work proceeds.

TASK: build verification alongside the bounded native stage in U4, and complete independent
qualification/metrics in U6. This is not a second timing simulator or mandatory fork harness.

1. Create a stage-indexed corpus with expected counts, transfers and durations independently
   derived from the declared model: fixed-delay critical paths, exact clock edges, resident
   GEMM, latency-bound DMA, exclusive-resource serialization and legal independent overlap.
   Include human-worked U-P8 fixtures. No production helper manufactures its own expected
   answers. Record the derivation, applicability, author/reviewer and implementation binding.
2. Exercise conservation, dependency order, capacities and outstanding-request limits,
   contention at represented levels, attribution and refusal semantics through the real
   public native boundary. Demonstrate a discriminating fault for each mechanism, including
   an extra hop cycle, ignored DMA limit, missing dependency and dropped work. Capture before,
   broken and restored outcomes; setup errors are not correct refusals.
3. Determinism: repeated native result bytes in U4; table workers 1/N in U7/G3b; debug/release native replay;
   saved mapped inputs with producers disabled. Full threaded checks remain U9. Nightly
   must execute real native debug tests by G5. Before then run required selections explicitly
   on approved Linux correctness CI. Add Ramulator ASan checks only when the bridge exists.
4. Optional external comparisons use matched work/precision, resolved tiles/placement,
   architecture parameters, levels and initial state. Reject mismatched equivalence claims;
   record unavailable, unsupported and same-code cases. Criteria and scope are registered
   before results. Failures cannot be hidden by removing the reference after observing them.
   A narrow component match never verifies the complete chip. No mandatory 3%/95% full-grid
   fork agreement or native/fork speed ratio. U-P8 owns the admitted reference selection.
5. validation/perf/: record host instructions per simulated cycle via perf where permitted,
   otherwise host ns per simulated cycle, explicitly distinct. Record events per simulated
   cycle and per completed job, memory usage, host elapsed time, and cross-thread/sync metrics
   (zero by construction before U9). Set a regression threshold only after measuring the
   noise floor in the declared environment and obtaining U0012 acceptance. A synthetic 2×
   slowdown must trip the checker. No events-per-second headline or WSL performance claim.
6. Bounded early conformance: test the nine rules and permitted vendored IterationCost
   interfaces using small analytic fixtures. Record what runs through real vendored code
   and what is adapter scaffolding. Never relabel C0/C1 as C2, replace null with zero or
   claim rk-sim integration/independent validation. Interpolation/serving/orchestrator and
   future consumer coverage remain pending until implemented. Propose protected vectors
   through the normal schema process; no production rk import or rk-sim edit.
7. Keep `uarch diff <table-a> <table-b>` for matched component comparisons and U-P14 design
   studies. Label the comparison purpose: design variants may intentionally differ, but
   that difference is not an engine-equivalence experiment. Preserve provenance and scopes.

ACCEPTANCE:
- U4a: independent literal corpus and discriminating public-boundary tests for admitted
  mechanisms; required missing tests block stage acceptance. U0006 reductions remain exact.
- U4b/G3a: actual reference-suite work/replay and attribution used by G4 pass.
- U7/G3b: table/replay/worker determinism and required complete-work counts pass.
- U6/G5: all required native cases executed, reviewed, no unresolved correctness failures;
  representative mesh admission, diagnostics, mutant detection/attribution and controlled-host
  metrics complete; applicable integrated regressions rerun. No full C1 mesh grid required.
- Mismatched inputs are refused for equivalence claims; same-code references never earn
  independent status. Optional missing evidence is explicit, not fabricated success.
- Performance gate catches the synthetic slowdown; no positive badge or silicon claim.

GUARDRAILS: Report failures to A; do not fix production in the reviewer session or tune the
model. Retain counterexamples and unsupported cases. No second substantial Python engine.

ADR: docs/decisions/U0012-native-verification-and-simulator-metrics.md (proposal for human
commit): required scopes, independent derivations, optional references and their limits,
performance noise floor and regression threshold. The old native-vs-fork title is retired.
```
