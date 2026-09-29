# U-P12 · U6 · Lane B — The differential harness, determinism gates, and simulator metrics

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, validation/L2_differential/README.md, build-spec §2.5, §2.8, §6.6
(determinism), ADR U0011's expected speed factor. You do not need the native engine to be
finished: you need the engine protocol, which already exists.

TASK: make "native agrees with fork" a measured, attributable, continuously checked fact,
and make simulator performance a regression-tested quantity rather than an anecdote.

1. validation/L2_differential/native_vs_fork/: given a request and a list of
   (engine, level-config) pairs, build both tables through the table interface, then report
   per-point relative deviation, the fraction of points within 3%, and per-subsystem
   attribution. Attribution uses each engine's attribution_s and busy times, so a
   disagreement can be bisected to compute, NoC, DRAM or sync. Only configurations where both
   engines run the SAME mapping (onnxim-compat@1) and MATCHING sub-model levels are
   comparable, and the harness refuses the rest with the mismatch named.
2. Determinism gates in CI, for every engine in the matrix:
   - table built twice → byte-identical;
   - --workers 1 vs --workers N → byte-identical;
   - nightly: the native engine's sanitizer build runs the golden requests clean.
3. validation/perf/: simulator-performance metrics recorded per golden request, per engine
   version, as data:
   - HOST INSTRUCTIONS PER SIMULATED CYCLE, via `perf stat` where the box permits it.
     Otherwise host nanoseconds per simulated cycle, labelled as such and never mixed with
     instruction counts;
   - events per simulated cycle, and events per completed tensor job;
   - cross-thread messages per simulated cycle, and sync operations per million simulated
     cycles. Both are 0 by construction until U-P17, and the report says so rather than
     omitting them;
   - NOT events per second as a headline. The vision note is right about this.
   A regression gate fails a PR that worsens host-cost-per-simulated-cycle by more than a
   threshold you set in ADR U0012 (with its noise floor measured first).
4. POWER: commit a mutant native engine that adds one cycle to every router hop. Assert the
   harness catches it, and attributes the disagreement to the NoC, not to compute or DRAM.
5. `uarch diff <table-a> <table-b>` prints per-point deviation and attribution. The design
   study (U-P14) reuses it.

ACCEPTANCE TESTS:
1. G5's criterion (≥95% of shared points within 3%) is computed and recorded for the npu-l4
   grid at matched levels.
2. The one-cycle mutant is caught and attributed to the NoC.
3. The harness refuses a comparison with mismatched mapping or levels, naming the mismatch.
4. Performance baselines are recorded for every golden request, and the regression gate trips
   on a synthetic 2× slowdown.

GUARDRAILS: Do not call agreement "validation" anywhere, in code, reports or ADRs. It is L2.
Do not fix a disagreement here. Report it with its attribution and hand it to Lane A.
Do not headline events per second.

ADR: docs/decisions/U0012-native-vs-fork-agreement.md, with the agreement fraction, the
per-subsystem attribution of what did not agree, and the performance noise floor.
```
