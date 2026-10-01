# U-P2 · U1 · Lane B — The vendored rk-sim snapshot and FLOP parity

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, contract/README.md, contract/vendor/README.md, ADR U0001 (the SHA
it names), build-spec §6.4 (the one-way dependency). From rk-sim, READ-ONLY at that SHA:
rk/engine/f0/compute.py, rk/schema/ (and the schema bundle `make gen` writes), Makefile.

TASK: prove, mechanically and on every CI run, that uarch's copy of rk-sim's vocabulary is
exact and that uarch counts work the way rk-sim does, without CI ever touching rk-sim.

1. scripts/vendor_rk.py and `make vendor-rk SHA=<sha> RK=<path-to-rk-sim-clone>
   [PARAMS=<component.yaml> ...]`. A HUMAN RUNS IT; CI never does. It:
   a. checks the clone is at <sha> with a clean tree and refuses otherwise;
   b. copies rk-sim's generated schema bundle plus the source of rk/provenance.py,
      rk/schema/{fidelity,channels,execution,workloads}.py into
      contract/vendor/rk-sim@<sha>/, read-only (chmod a-w), with a MANIFEST listing sha256s;
   c. GENERATES PARITY FIXTURES BY EXECUTING rk-sim's OWN iteration_cost(), in rk-sim's own
      environment (subprocess `uv run --project <rk>`), never by reimplementing the formula.
      Fixtures cover at least 3 ModelSpecs (one dense GQA ~8B, one dense ~70B, one MoE) ×
      2 precisions × tp ∈ {1, 8} × at least 24 queries spanning decode (B, T) and prefill
      (T, Q); the decode queries include B ∈ {1, 8, 32} × context per sequence ∈ {512, 4096}
      (gate G2(c)'s points). Each fixture records IterationCounts.matrix_ops,
      memory_read_bytes, memory_write_bytes, the query, the tp, and rk-sim's own durations
      (decode_s or prefill_s from IterationCost) for each component params file it was run
      with: rk-sim's library entries asic_placeholder.yaml and nvidia_h100_sxm.yaml always,
      plus every PARAMS file the human passes (in U2, `uarch rk-component` output for the
      designs). A duration is rk-sim's output, never ours: these are the oracle for U-P3's
      U-C0 parity test.
   A REIMPLEMENTED FORMULA IS A MIRROR, NOT AN ORACLE. If you find yourself writing
   2*P_active anywhere under contract/, stop: the point is that rk-sim's code produced it.
2. contract/tests/test_vendored_round_trip.py. Load the vendored classes by path, not by
   import name, so nothing named `rk` is ever importable from production code:
   - a uarch claim SourcedValue round-trips through rk-sim's SourcedValue exactly (dropping
     `kind`);
   - A uarch STIPULATION IS REFUSED BY rk-sim's CLASS. Assert the refusal. This pins the gap
     honestly: the day rk-sim adopts the stipulation kind (rk-sim P19), this test fails
     loudly and is updated in the same ADR, never quietly deleted;
   - ModelSpec and PrecisionFormat: every field and member name and value identical;
   - uarch Row.counts keys are a subset of rk-sim's Channel literal values.
3. contract/tests/test_flop_parity.py, the harness later prompts plug into. Given a
   callable (ModelSpec, ModelShape, precision, query) -> counts, compare against every
   fixture: pass if within 0.5%, or if the difference is fully attributed to named declared
   deviations with no single deviation above 5%. U-P3's workload graph is the first callable.
   Until then the test runs against a stub callable that returns the fixture itself, and is
   marked so the report says it is a harness self-test, not a parity result.
4. ModelShape sidecars for the three fixture models under contract/fixtures/model_shapes/,
   each sourced (URL to the model card or config.json) and passing check_parity.
5. CI: the contract job reads the committed snapshot. It needs no rk-sim credentials. It fails
   if MANIFEST sha256s do not match the files, naming the stale file.

ACCEPTANCE TESTS (write first):
1. Tamper test: flip one byte in a vendored file in a temp copy, and the manifest check fails
   naming it.
2. Round-trip suite green; the stipulation-refusal test passes because rk-sim refuses.
3. Parity harness self-test green; a deliberately wrong callable (matrix_ops × 1.1) fails
   with the fixture id and both numbers.
4. import-linter: nothing under src/ or contract/uarch_contract/ imports from
   contract/vendor/.
5. `make vendor-rk` run twice at the same SHA produces byte-identical output.
6. Every fixture carries a tp, a component params file name and rk-sim's duration for it,
   and the fixture set contains G2(c)'s six decode points.

GUARDRAILS: Never hand-edit anything under contract/vendor/; regenerate it. Never give CI
access to rk-sim. Do not "fix" a parity failure by widening the tolerance. Declare the
deviation with a name and a reason, or report it. Changing rk-sim is out of scope for every
uarch prompt except U-P19 and U-P20, which run inside rk-sim.

ADR: docs/decisions/U0002-the-vendored-snapshot-and-parity-discipline.md.
```
