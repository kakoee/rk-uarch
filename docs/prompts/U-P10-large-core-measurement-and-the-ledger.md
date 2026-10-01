# U-P10 · U5 · Lane B — The large-core measurement kit, the ledger, and promotion

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, measure/README.md, validation/L3_silicon/README.md,
validation/ledger/README.md, validation/L3_silicon/tpu-v5e/SUITE.md, build-spec §2.6–§2.7.
From rk-sim READ-ONLY: docs/prompts/P10-measurement-kit-write-before-renting-anything.md,
rk/calibration/ (the ledger's shape), docs/decisions/0021 and anchor-semantics.md.

TASK: measure the reference chip, compare against the frozen predictions, and let the ledger,
and only the ledger, decide what the model card may say.

1. measure/tpu-v5e/, the kit, WRITTEN AND DRY-RUN BEFORE ANY PAID HOUR. Code for every
   benchmark in SUITE.md, runnable end to end on CPU JAX as a dry run that produces
   correctly shaped (fake, labelled SYNTHETIC) result files. Warm-up and repetition counts
   stated per benchmark; device-side timing via the XLA/JAX profiler at the granularity SUITE.md
   fixes; XLA's compiled cost analysis (FLOPs and bytes accessed) per benchmark; whatever
   device counters the profiler exposes (HBM bytes, utilisation), recorded as data;
   environment capture (TPU type, runtime and library versions, VM image) into every result.
2. Run it on Cloud TPU v5e ONLY AFTER check_ordering passes for every prediction. Raw results
   go to validation/L3_silicon/tpu-v5e/results/, and are immutable once committed. These are
   records of spent money, like rk-sim's measure/results/.
3. validation/ledger/: one entry per comparison, recording the question it answers
   (benchmark id and granularity), its applicability dimensions (architecture family, op
   class, precision, shape regime, load regime, mapping match), predicted, measured, signed
   relative error, and the engine and spec versions. The ledger REFUSES a second entry with
   the same key and a different prediction, as rk-sim's does. Workload fidelity is its own
   entry type: predicted vs compiler-reported FLOPs and bytes, with declared deviations for
   fusions, layout copies and padding. It never promotes a duration card; a deviation above
   5% with no declared reason is published as a finding. Diagnostic fidelity is another
   entry type: each predicted diagnostic against the device counter that measures it, where
   one exists. It never promotes a duration card either.
4. Gate G4 (execution-plan §4), evaluated by script and written to the ledger either way:
   median |relative error| ≤ 25% across all benchmarks, and no class median above 50%. It is
   evaluated separately for matched and compiler-chosen benchmarks, and the verdict names the
   group; an empty group is reported as "no evidence", never as a pass. The same script
   computes G4's fail-branch attribution exactly as execution-plan §4 defines it.
5. Promotion: provenance/ reads the ledger. A model card moves from stub to estimated ONLY
   through ledger entries, ONLY for the family and op classes those entries cover, with
   validated_error_band set to the observed band for that scope. Never by hand, and never
   by averaging across classes to get under a threshold.
6. The two honesty rules, enforced in code:
   a. SUBSYSTEM EVIDENCE DOES NOT COMPOSE INTO SYSTEM EVIDENCE. Memory-class and
      matrix-class agreement do not validate end-to-end numbers; only end-to-end entries do.
   b. A COVERED COMPONENT WITH AN INAPPLICABLE ANCHOR CANNOT MAKE A RUN LOOK VALIDATED
      (rk-sim ADR 0021). A mesh-design request against large-core evidence gets stub.
7. `uarch ledger` prints the table; `uarch report` gains a ledger section.

ACCEPTANCE TESTS (write first):
1. Dry run: the full kit runs on CPU JAX and writes SYNTHETIC-labelled files that the ledger
   REFUSES to ingest.
2. The ledger refuses a duplicate key with a changed prediction.
3. Promotion: with fixture entries at 18% median error, a large-core design's card becomes
   estimated for {matrix, memory, operator, end-to-end}; npu-m256's card stays stub, and
   says the family mismatched.
4. Subsystem-only fixture evidence does not promote end-to-end rows.
5. G4 is evaluated and recorded, pass or fail, per mapping-match group.
6. Workload-fidelity entries exist for every benchmark that has compiler-reported counts.
7. A fixture where only the compiler-chosen group passes promotes only within that group's
   scope.

GUARDRAILS: Do not run paid hardware until predictions are frozen and ordering passes. If G4
fails, PUBLISH THE ERRORS ANYWAY. Then follow G4's fail branch (execution-plan §4), and do not
start adjusting the model in this session. Never average away a failing class.

ADR: docs/decisions/U0010-the-first-validation-verdict.md, whichever way it went, with the
table of errors by class.
```
