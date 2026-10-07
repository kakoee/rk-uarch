# U-P3 · U2 · Lane A — Hardware specs, the workload graph, and the analytic engine

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, hw/README.md, src/rkuarch/{workload,engines,table}/README.md,
contract/uarch_contract/, ADRs U0001 and U0002, docs/reviews/U2-kickoff-obligations.md,
contract/tests/test_flop_parity.py, build-spec §2.2–§2.4.
From rk-sim READ-ONLY: rk/components/library/compute/asic_placeholder.yaml and
nvidia_h100_sxm.yaml (the param names derive_rk_params must produce).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Keep the high-level standalone CLI and add file-based prepare/replay without requiring
rk-sim or a compiler. First propose and obtain acceptance of U0003's prepared-input schema,
hashing/provenance and any public request/table schema revision; coordinate it with U-P4.
At U0003 kickoff carry forward B-F16's component-precision and prepared-bundle parity
requirements, and the separately unresolved embedding-accounting obligation, from the
kickoff record and U0002. Preserve the approved parity budget, nominal inputs and explicit
unsupported-projection policy; U1 harness self-tests do not discharge actual U2 parity.
Use the existing OpSpec vocabulary and engine protocol. Workload construction belongs to
preparation; analytic engines consume resolved operators. No detailed mapper lands in U2.

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
   have to call a claim. All four specs fill the Rev-2 fields: dataflows, DMA
   max_outstanding and request_bytes, job_overhead_cycles, sync, DRAM organisation and timing
   (a reference cites JEDEC, the vendor, or a preset file at a pinned SHA), interleave and
   controller policy, and a pj_per_byte.sram consistent with sram.bytes. Unknown for a
   reference means stub.
2. src/rkuarch/hw/derive.py — derive_rk_params(spec) -> the rk-sim component params
   (fp16_tflops and the other per-format peaks that apply, hbm_bw, hbm_capacity, tdp) as
   SourcedValues whose provenance is the WORST of the spec leaves each was computed from.
   STIPULATIONS STAY STIPULATIONS. A peak computed from stipulated MACs/cycle and a
   stipulated clock is a stipulation, never a claim. Plus `uarch rk-component <spec>`, which
   emits the rk-sim library YAML for the chip (kind: compute_resource, role: asic,
   design_status carried in a comment until rk-sim's schema has the field; uarch's proposed
   maps to rk-sim's proposed and reference to shipping).
3. src/rkuarch/workload/ — the standalone, separately versioned preparation producer:
   (ModelSpec, ModelShape, precision, tp, query) -> the operator
   graph of ONE RANK of a tp-way tensor-parallel split, for one iteration, at decoder-layer
   granularity, using contract/operators.py only. The split is build-spec §2.3.4's: heads
   and KV heads (replicated when kv_heads < tp), FFN columns and rows, and the vocabulary
   divided by tp; no collective ops, because rk-sim prices them; ShardIndivisible if a
   dimension does not divide. Attention is one attention_fused operator per layer (scores on
   chip, DRAM operands Q, K, V, O). A query is
   a canonical batch (build-spec §2.3.4): decode = B sequences of context T/B; prefill =
   n prompts of L. layer_reuse=True means "one decoder layer instantiated n_layers times
   plus the non-repeated head and tail ops", and the graph says so in a field. MoE is
   active-parameter dense-equivalent ONLY. MoE d_ff and expert_d_ff both name one
   expert's width and must agree. Multiply expert work by experts_per_token exactly
   once; total expert weights use n_experts once; account shared terms separately.
   Dense d_ff is unchanged. As in rk-sim, routing, imbalance and
   all-to-all are declared absent in a graph-level `omissions` list, together with
   host/runtime time, address translation, coherence and mixed prefill/decode iterations
   (build-spec §2.3.4). KV operands are paged: the graph carries page-granular KV reads for
   the request's kv_layout.block_size_tokens.
4. Plug the graph into the parity harness (contract/tests/test_flop_parity.py) as its first
   real callable. Every difference from rk-sim's closed form above 0.5% gets a named
   declared deviation in src/rkuarch/workload/deviations.py with a one-line reason: embedding
   or lm_head accounting, norm parameters, and whatever else you actually find. Report them;
   do not tune the graph to hide them. B's adapter emits the revised typed FlopParity:
   kind, identities, fixture/channel/unit attribution and all four ratios must survive.
   Total absolute adjustments <=5% per fixture/channel, residual <=0.5%; refuse adjustments
   for raw-inside-tolerance or zero/null references. Self-tests are never workload parity.
5. src/rkuarch/engines/analytic/ — U-C0, consuming a validated prepared operator graph and
   resolved HardwareSpec without importing/calling the workload builder or mapping policies.
   Record the explicit analytic mapping scope and preparation identity. Two modes:
   - aggregate: max(compute_time, memory_time) over the whole iteration, the same shape as
     rk-sim's IterationCost._time_s. This is the parity anchor.
   - per_op: the sum over ops of each op's own roofline. Always >= aggregate. It is the first
     place the chip's structure shows up.
   Both return a Row (the contract's row, via table/) with attribution_s split by which roof
   bound, its parts summing to duration_s. Units in names. Seconds at the boundary. U-C0
   uses peak DRAM bandwidth with no refresh derating, because it is the parity anchor for
   rk-sim C0; derating starts at native level 0. U-C0 leaves every diagnostic null.
6. src/rkuarch/table/ — the minimal path: high-level request -> grid-point preparation
   OR validated prepared bundle -> engine -> rows -> UarchCostTable. Both paths share engine
   execution and hashing; imported payloads bypass local preparation. Single process, no
   interpolation (U-P7 owns that). Include input content and producer versions in identity.
   Require table.hardware_spec_hash == request.hardware_spec_hash == spec_hash(spec).
   Resolve every conditional_on path in the referenced proposed HardwareSpec and require
   its complete stipulated SourcedValue to match; refuse missing/mismatched paths or values.
   This is the producer's artifact-aware check, not a guarantee supplied by the U1 carrier.
   Producer enforcement: when request.model.n_experts > 0, copy the contract's
   MOE_OMISSION warning (routing, imbalance and all-to-all) into table.warnings, alongside
   every common omission. Test with the Mixtral sidecar. The U1 table carrier has no
   model payload and cannot infer this condition from request_hash; no new MoE indicator
   is added here. Cross-check HardwareSpec against fidelity_detail: an existing shared
   SRAM must have an explicit level, including unrepresented when unsupported.
   Javid approved the interim A-F12 rule: Lane B must refuse parity comparisons requiring
   replicated KV or padded vocabulary that uniform /tp cannot represent, pending an approved
   component-aware projection. Keep A's legitimate shape support; do not change oracle counts,
   conceal the mismatch with deviations, or widen tolerances. Aggregate compatibility is
   not proof of physical rank-local correctness; U-P3 must test the latter independently.
7. src/rkuarch/cli.py (typer): `uarch validate <spec>` (lists claims / stipulations / stubs
   with counts; refuses a bad spec with the path) and `uarch table <spec> --model <name>
   --precision <fmt> [--tp N] --engine analytic` (tp defaults to 1).
8. `uarch characterize <spec> --model <name> --precision <fmt>`: for every op across the
   request's grid, its FLOPs, bytes, operational intensity, op class and shape regime (the
   bins ADR U0001 fixed), as hashed JSON plus a Markdown twin. U-P9 and U-P15 pick their
   benchmark shapes from it, and U-P14 picks its workload suite from it.

9. Add `uarch prepare <request> --out <bundle>` and
   `uarch table --prepared-input <bundle> --engine analytic`. The bundle explicitly covers
   its grid/query points, their resolved OpSpecs/dependencies, precision, shard scope,
   hardware binding, producer identity and analytic mapping scope. Reject ambiguous mixed
   high-level/prepared overrides. Round-trip the actual prepared payload, not a recipe that
   calls the builder again. Preserve model-based table/characterize convenience commands.
10. Implement the U0003-approved protocol/schema fixtures and a read-only freshness check.
    Reuse these fixtures in the fork adapter and Rust protocol work; do not create another IR.

ACCEPTANCE TESTS (write first):
1. U-C0 AGGREGATE REPRODUCES rk-sim C0: fed each fixture's own component params (U-P2
   records the file and rk-sim's duration for it), aggregate-mode duration equals that rk-sim
   duration within ±0.1% on every fixture (decode and prefill, both precisions, tp 1 and 8).
   A test, not a claim. Then a human runs `make vendor-rk ... PARAMS=<uarch rk-component
   output for npu-l4>` and the same test covers derive_rk_params(npu-l4). Never compute an
   expected duration yourself.
2. per_op >= aggregate on every fixture query (a property test over random queries too).
3. FLOP parity: the workload graph passes the harness with every deviation named.
4. derive_rk_params: a stipulated-clock design yields stipulation-kind peaks. A reference
   yields claims whose provenance is the worst of their inputs. Test both.
5. `uarch table hw/designs/npu-l4.yaml --model llama-3.1-8b --precision bf16 --engine
   analytic` writes a table whose hash is identical across two runs, whose rows validate
   against the contract, and whose composite_fidelity is "C0" with engine "analytic".
6. `uarch validate` on a reference spec with a stipulation injected fails and names the path.
7. Omissions: an MoE ModelSpec's graph lists routing/imbalance/all-to-all as omitted, and
   the table's warnings carry that sentence, alongside the other declared omissions.
8. `uarch characterize` on the demo request (npu-m256 × Llama-3.1-70B × fp8) writes a
   hash-stable report in which every op has a shape regime.
9. KV reads are page-granular: the number of KV page reads per sequence per layer equals
   ceil(context / block_size_tokens).
10. The shard: at tp = 8 the graph's matrix_ops equals the tp = 1 graph's divided by 8, except
    for named deviations (replicated KV heads, vocabulary padding), and a model whose heads do
    not divide by tp raises ShardIndivisible.
11. Attention: a prefill at L = 32768 yields an attention_fused operator whose DRAM bytes are
    Q, K, V and O only, and the graph contains no L × L tensor.

ADDITIONAL ACCEPTANCE — prepared inputs:
- Export locally prepared inputs and replay them with the local builder unavailable:
  engine results and table bytes match under identical engine/version/run conditions.
- A hand-authored supported prepared fixture executes with no rk-sim clone or compiler.
  Independent expected operator dimensions/dependencies pin the local producer's output.
- A changed operator shape or declared preparation/mapping version changes request/cache
  identity; moving unchanged files does not. Tampering with a declared hash is refused.
- Wrong tp/rank scope, precision, hardware binding, unknown schema version, missing query
  coverage and unsupported detailed mapping fail before engine execution.
- Architecture checks prove the analytic execution path does not invoke preparation.
  Public schemas, prompt-sync and the protocol fixtures are fresh.

GUARDRAILS: Do not touch the fork or the native engine; they are U-P5 and U-P11a–c. Do not add
interpolation or a process pool; that is U-P7. Do not tune the operator graph to hit rk-sim's
numbers, because the deviations are findings. Never write a number you cannot source as a claim:
stipulate it in designs/ with a rationale, or stub it in references/.

ADR: docs/decisions/U0003-one-chip-one-set-of-facts.md, covering derive_rk_params,
stipulation propagation, the standalone/prepared-input boundary, payload/schema ownership,
content identity, import refusals, and any public contract-version revision. Settle its
boundary and share the schema with Lane B before implementation; record validation after.
```
