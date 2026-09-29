# U-P3 · U2 · Lane A — Hardware specs, the workload graph, and the analytic engine

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, hw/README.md, src/rkuarch/{workload,engines,table}/README.md,
contract/uarch_contract/, ADR U0001, contract/tests/test_flop_parity.py, build-spec §2.2–§2.4.
From rk-sim READ-ONLY: rk/components/library/compute/asic_placeholder.yaml and
nvidia_h100_sxm.yaml (the param names derive_rk_params must produce).

TASK: the first honest number end to end. Analytic only; the fork and the native engine come
later.

1. hw/ — four specs:
   - hw/designs/npu-l4.yaml — a PROPOSED large-core design (2×2 grid of big systolic cores,
     HBM). The class the forks model.
   - hw/designs/npu-m256.yaml — a PROPOSED mesh design (16×16 grid of small cores, SRAM per
     core, one or two 2-D NoCs, GDDR or HBM). The class the native engine will model.
   - hw/references/tpu-v5e.yaml and hw/references/blackhole-p100a.yaml — REFERENCE specs,
     claims only, every number with a URL to a vendor page or document. WHAT THE VENDOR DOES
     NOT PUBLISH IS provenance: stub WITH source: null. It is NOT a stipulation: a reference
     may not contain one, and the loader will refuse it. Record every stub in the spec's
     header comment as "unknown for this chip", because U-P9/U-P15 measure against these
     specs and the model card must say how many unknowns the method carried.
   Every stipulation in designs/ carries a rationale. Do not invent a number you would
   have to call a claim.
2. src/rkuarch/hw/derive.py — derive_rk_params(spec) -> the rk-sim component params
   (fp16_tflops and the other per-format peaks that apply, hbm_bw, hbm_capacity, tdp) as
   SourcedValues whose provenance is the WORST of the spec leaves each was computed from.
   STIPULATIONS STAY STIPULATIONS. A peak computed from stipulated MACs/cycle and a
   stipulated clock is a stipulation, never a claim. Plus `uarch rk-component <spec>`, which
   emits the rk-sim library YAML for the chip (kind: compute_resource, role: asic,
   design_status carried in a comment until rk-sim's schema has the field).
3. src/rkuarch/workload/ — (ModelSpec, ModelShape, precision, query) -> one iteration's
   operator graph at decoder-layer granularity, using contract/operators.py only. A query is
   a canonical batch (build-spec §2.3.4): decode = B sequences of context T/B; prefill =
   n prompts of L. layer_reuse=True means "one decoder layer instantiated n_layers times
   plus the non-repeated head and tail ops", and the graph says so in a field. MoE is
   active-parameter dense-equivalent ONLY, exactly as rk-sim: routing, imbalance and
   all-to-all are declared absent in a graph-level `omissions` list.
4. Plug the graph into the parity harness (contract/tests/test_flop_parity.py) as its first
   real callable. Every difference from rk-sim's closed form above 0.5% gets a named
   declared deviation in src/rkuarch/workload/deviations.py with a one-line reason: embedding
   or lm_head accounting, norm parameters, and whatever else you actually find. Report them;
   do not tune the graph to hide them.
5. src/rkuarch/engines/analytic/ — U-C0, uarch's own roofline of a HardwareSpec. Two modes:
   - aggregate: max(compute_time, memory_time) over the whole iteration, the same shape as
     rk-sim's IterationCost._time_s. This is the parity anchor.
   - per_op: the sum over ops of each op's own roofline. Always >= aggregate. It is the first
     place the chip's structure shows up.
   Both return a Row (the contract's row, via table/) with attribution_s split by which roof
   bound. Units in names. Seconds at the boundary.
6. src/rkuarch/table/ — the minimal path only: request -> grid points -> engine -> rows ->
   UarchCostTable, single process, no interpolation (U-P7 owns that). Hash it.
7. src/rkuarch/cli.py (typer): `uarch validate <spec>` (lists claims / stipulations / stubs
   with counts; refuses a bad spec with the path) and `uarch table <spec> --model <name>
   --precision <fmt> --engine analytic`.

ACCEPTANCE TESTS (write first):
1. U-C0 AGGREGATE REPRODUCES rk-sim C0: fed derive_rk_params(spec), aggregate-mode duration
   equals the parity fixtures' rk-sim durations within ±0.1% on every fixture (decode and
   prefill, both precisions). A test, not a claim.
2. per_op >= aggregate on every fixture query (a property test over random queries too).
3. FLOP parity: the workload graph passes the harness with every deviation named.
4. derive_rk_params: a stipulated-clock design yields stipulation-kind peaks. A reference
   yields claims whose provenance is the worst of their inputs. Test both.
5. `uarch table hw/designs/npu-l4.yaml --model llama-3.1-8b --precision bf16 --engine
   analytic` writes a table whose hash is identical across two runs, whose rows validate
   against the contract, and whose composite_fidelity is "C0" with engine "analytic".
6. `uarch validate` on a reference spec with a stipulation injected fails and names the path.
7. Omissions: an MoE ModelSpec's graph lists routing/imbalance/all-to-all as omitted, and
   the table's warnings carry that sentence.

GUARDRAILS: Do not touch the fork or the native engine; they are U-P5 and U-P11. Do not add
interpolation or a process pool; that is U-P7. Do not tune the operator graph to hit rk-sim's
numbers, because the deviations are findings. Never write a number you cannot source as a claim:
stipulate it in designs/ with a rationale, or stub it in references/.

ADR: docs/decisions/U0003-one-chip-one-set-of-facts.md, covering derive_rk_params and
the rule that a stipulation propagates as a stipulation.
```
