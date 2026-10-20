# U-P11c · U6 · Lane A — Native qualification, diagnostics and absolute host cost

_From build-spec §8. One prompt, one fresh session._

```text
TEMPORARY U0024 EXCEPTION: read docs/decisions/U0024-temporary-local-verification-and-deferred-native-ci.md.
During its multi-sprint deferral, passing current local checks and independent review may
support interim development under the normal task/contract prerequisites. Record remote
qualification pending; no local result becomes a hosted CI/nightly/performance pass.
Full G5, U9 entry, simulator-performance claims and final project closure keep their gates.

CONTEXT TO LOAD: CLAUDE.md, native/README.md, build-spec §2.3.3, §2.5 and §2.8,
ADR U0005/U0023/U0006/U0011, accepted bounded native handoffs, U-P8 and U-P12 results.

G5 OUTCOMES: record correctness, performance and automation separately. Correctness
releases dependent U7/G6/G3b/U10 work; full G5 requires all three and remains open if host
evidence or executed self-hosted nightly is missing. Both are required for U9 entry,
any simulator-performance claim and final closure. No implied waiver from proceeding.

ORDINARY EXECUTION AND BASIC PROVENANCE (U0011 simplification amendment):
Keep the native-first schedule. Use installed software/engine/model versions and existing
hardware/request/prepared-input/result/table data hashes. Ordinary execution requires no
development checkout/evidence, executable digest, host approval records, custom startup
assurance or exhaustive build tracing. Preserve model/capability admission, actual input
and result validation, independent tests and deterministic results. A-F3 is retired by
scope change, not a passing verification; do not retry its stopped experiment. Use an
explicit minimal schema transition, never dummy hashes or a new attestation framework.

TASK: qualify the existing native core, not build it again. Complete diagnostics and traces,
admit npu-m256 at declared representative points, and execute G5's verification obligations.
The bounded engine and this scope's verified inputs are prerequisites; TPU availability,
G3a completion and G4 success are not. Do not call those campaigns closed by proceeding.

1. Fill modeled diagnostics; unmodeled quantities remain null. Preserve actual levels and
   incomplete evidence, STUB/unknown error/unverified energy; no automatic badge promotion.
2. With --trace emit a deterministic Chrome-trace resource timeline. Check dependency
   edges, owner mutations, exclusive-resource serialization and explicitly permitted
   overlap; a blanket prohibition on overlap across different resources is incorrect.
3. Execute declared representative npu-m256 jobs using admitted mappings. Verify independent counts,
   transfers, clock edges, hand-worked critical paths, conservation, DMA/queue limits,
   shared-resource contention where represented and compute/DMA overlap under U-P12.
   Missing required cases fail G5; unsupported optional reference comparisons stay not_run.
4. Repeat exact saved mapped-input execution with producers disabled, debug/release builds
   and batch workers 1/N where delivered. Full table workers are G3b. Record exact
   environments and identities. Re-run applicable integrated regressions and the real native
   CI/nightly selection; a job that executes no native tests cannot discharge this gate.
5. Measure single-point host time/memory for the prospectively declared U0011 workload and
   host scope. Publish noise and regressions. No fork-relative speed requirement; exceeding
   the budget remains a finding and feeds the existing U9 admission decision.

ACCEPTANCE:
1. G5's required native verification matrix passes with independent review; public-boundary
   fault injections discriminate each required mechanism. No full-fork agreement substitute.
2. Unmodeled diagnostics render as not modeled, never zero; attribution sums to duration.
3. Trace and resource constraints hold; independent-resource overlap has a positive control.
4. Native replay, debug/release and applicable batch-worker determinism pass; representative
   mesh admission completes. No full C1 mesh table is required.
5. Controlled-host measurements are recorded against prospective budgets. Qualified
   performance claims require both host evidence and executed self-hosted nightly; until
   then observations are provisional and performance qualification remains pending. An executed
   applicable self-hosted nightly is required for G5 automation qualification; no-op jobs fail it.

GUARDRAILS: No threads, tuning to reference/silicon results or weakening expectations to
make the engine pass. Same-code and shared-assumption limits stay visible. L0–L2 is not L3.
A failed correctness case blocks G5-correctness and its dependent work; missing host/nightly
blocks full G5, U9 entry, performance claims and closure, not otherwise ready product work.
Any scope narrowing needs a new human decision.

ADR: propose completion of U0011 and U0012-native-verification-and-simulator-metrics.md
for human commit. Preserve historical observations; no changes to silicon thresholds.
```
