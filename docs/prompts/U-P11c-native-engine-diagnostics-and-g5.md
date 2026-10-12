# U-P11c · U6 · Lane A — Native qualification, diagnostics and absolute host cost

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, build-spec §2.3.3, §2.5 and §2.8,
ADR U0005/U0006/U0011, U4b's native/table handoffs, U-P8 and U-P12 verification results.

TASK: qualify the existing native core, not build it again. Complete diagnostics and traces,
expand to the initial npu-m256 table, and execute G5's independent verification obligations.

1. Fill modeled diagnostics; unmodeled quantities remain null. Preserve actual levels and
   incomplete evidence, STUB/unknown error/unverified energy; no automatic badge promotion.
2. With --trace emit a deterministic Chrome-trace resource timeline. Check dependency
   edges, owner mutations, exclusive-resource serialization and explicitly permitted
   overlap; a blanket prohibition on overlap across different resources is incorrect.
3. Build the initial npu-m256 table using admitted mappings. Verify independent counts,
   transfers, clock edges, hand-worked critical paths, conservation, DMA/queue limits,
   shared-resource contention where represented and compute/DMA overlap under U-P12.
   Missing required cases fail G5; unsupported optional reference comparisons stay not_run.
4. Repeat exact saved mapped-input execution with producers disabled, debug/release builds
   and table workers 1/N. Record exact environments and identities. Run the real native
   CI/nightly selection; a job that executes no native tests cannot discharge this gate.
5. Measure single-point host time/memory for the prospectively declared U0011 workload and
   host scope. Publish noise and regressions. No fork-relative speed requirement; exceeding
   the budget remains a finding and feeds the existing U9 admission decision.

ACCEPTANCE:
1. G5's required native verification matrix passes with independent review; public-boundary
   fault injections discriminate each required mechanism. No full-fork agreement substitute.
2. Unmodeled diagnostics render as not modeled, never zero; attribution sums to duration.
3. Trace and resource constraints hold; independent-resource overlap has a positive control.
4. Native replay and debug/release/worker determinism pass; the initial mesh table completes.
5. Absolute performance measurements are published against the prospective budgets. Missing
   measurements leave performance qualification pending, not a claimed pass.

GUARDRAILS: No threads, tuning to reference/silicon results or weakening expectations to
make the engine pass. Same-code and shared-assumption limits stay visible. L0–L2 is not L3.
A failed correctness case blocks G5; any scope narrowing needs a new human decision.

ADR: propose completion of U0011 and U0012-native-verification-and-simulator-metrics.md
for human commit. Preserve historical observations; no changes to silicon thresholds.
```
