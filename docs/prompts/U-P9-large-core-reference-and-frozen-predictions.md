# U-P9 · U5 · Lane A — The large-core reference model, and predictions frozen before anyone measures

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, validation/README.md, validation/L3_silicon/README.md, build-spec
§2.7 (rung L3), hw/references/tpu-v5e.yaml, ADR U0005, the chosen fork's paper (its TPU
validation section: what it measured, and how). From rk-sim READ-ONLY: docs/prompts/P11-*.md
and docs/execution-plan.md S7–S8 (the A100-fits, H100-held-out discipline this copies).

TASK: produce, and COMMIT BEFORE ANY MEASUREMENT EXISTS, uarch's predictions for a suite of
microbenchmarks on Google Cloud TPU v5e, the large-core reference. This prompt never sees a
measurement. That is its whole design.

1. Agree the microbenchmark list with Lane B FIRST, in writing, in
   validation/L3_silicon/tpu-v5e/SUITE.md. Lane B's U-P10 builds the kit that runs it. At
   least 20 benchmarks across at least 3 classes:
   - matrix: isolated matmuls at ≥ 6 shapes spanning MXU-underfilled to saturated, bf16 and
     int8 where the chip supports them;
   - memory: HBM streaming read, write, and copy at ≥ 3 sizes;
   - operator: each decoder-layer operator in contract/operators.py at a decode and a prefill
     shape for an 8B-class model;
   - end-to-end: one full decoder layer, decode B ∈ {1, 8, 32} and one prefill.
   EACH BENCHMARK STATES WHAT IS MEASURED, AND AT WHAT GRANULARITY, in words both lanes sign:
   XLA fuses operators, so "the softmax" on silicon may not be a separable event. Where a
   uarch operator has no separable silicon counterpart, the benchmark measures the smallest
   fused unit that contains it, and the prediction is made for THAT unit. This is rk-sim's
   anchor-semantics problem one level down, and getting it wrong makes every comparison
   meaningless while looking fine.
2. Configure the engine for the reference: the fork via config_writer from
   hw/references/tpu-v5e.yaml. Every microarchitectural parameter the vendor does not publish
   is a STUB claim in that spec (never a stipulation). Count them, and list them in
   predictions/UNKNOWNS.md: the L3 error will be method error plus unknown-parameter error,
   and the card must say how many unknowns there were.
3. Predictions: for each benchmark, uarch's predicted duration (and bytes/ops where
   measurable) from the fork AND from U-C0 aggregate and per_op, written to
   validation/L3_silicon/tpu-v5e/predictions/<id>.json with engine versions, image digest,
   spec hash and mapping policy. Commit them in ONE commit whose message begins
   "FROZEN PREDICTIONS:".
4. validation/L3_silicon/check_ordering.py and a CI job: fails if any file under results/
   exists in a commit earlier than, or equal to, the commit that added its prediction file.
   The ordering is enforced by git history, not by a promise.

ACCEPTANCE TESTS:
1. SUITE.md signed off by both lanes (both names, in the file) before predictions are
   generated.
2. ≥ 20 prediction files, ≥ 3 classes, each with full provenance fields.
3. The ordering check fails on a synthetic history where a result precedes its prediction.
4. UNKNOWNS.md lists every stub in the reference spec that the engine actually read.

GUARDRAILS: DO NOT LOOK AT, REQUEST OR ESTIMATE ANY MEASUREMENT IN THIS SESSION. Do not edit
a prediction after it is committed. A new prediction is a new file in a new commit, and the old
one stays. Do not tune the reference spec towards published TPU results. Do not change the
engine in this prompt; U-P10 and the G4 verdict decide what happens next.

ADR: docs/decisions/U0009-the-large-core-reference-and-what-it-can-support.md. Say which
architecture family this reference can support evidence for (few large systolic cores),
and which it cannot (anything mesh-shaped).
```
