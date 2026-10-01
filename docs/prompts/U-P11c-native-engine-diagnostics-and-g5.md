# U-P11c · U6 · Lane A — Native engine diagnostics, traces, G5 and the measured speed factor

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/engines/README.md, build-spec
§2.3.3 (diagnostics), §2.5 and §2.8, ADR U0005 (the fork's ladder table), U0011, U-P11b's
handoff, and U-P12's harness (validation/L2_differential/native_vs_fork/).

TASK: make the native engine's output complete and checked: diagnostics, traces, agreement
with the fork at matched levels, and the speed factor against the one written first.

1. Diagnostics: fill the row diagnostics the running levels model, and null for everything
   else (NoC contention statistics at NoC level 0, for example). Never 0 for unmodelled.
2. With --trace, a Chrome-trace JSON per-resource timeline from STAT_SAMPLE and job events.
3. G5 with U-P12's harness: onnxim-compat@1 driving both engines, the fork in the
   configuration ADR U0005 classifies as matching native's levels. If no fork configuration
   matches {compute: 1, noc: 0, dram: 0}, do not compare mismatched levels: record which
   subsystem mismatches, and G5 moves to U7, after U-P13a–c, at the closest matching
   configuration.
4. Measure the speed factor against the fork on npu-l4 and the 16×16 mesh, and the
   single-point wall-clock on the npu-m256 grid against U0011's budget.

ACCEPTANCE TESTS (write first):
1. G5: durations agree within 3% on ≥ 95% of the npu-l4 grid at matched levels, or the level
   mismatch is recorded and G5 rescheduled as item 3 says.
2. Diagnostics: at NoC level 0 every NoC statistic is null, and no null diagnostic renders as
   0 in `uarch report`.
3. The trace of a golden request loads as valid Chrome-trace JSON, and no two intervals on
   one resource overlap.
4. The speed factor and the single-point wall-clock are recorded next to the numbers written
   first.

GUARDRAILS: If the speed factor disappoints, record it; do not trade determinism for it. Do
not fix a disagreement with the fork by tuning: bisect it with U-P12's attribution and record
it. No threads.

ADR: complete docs/decisions/U0011-the-native-engine-core.md with the measured speed factor,
the single-point wall-clock against the budget, and G5's result or its rescheduling.
```
