# Exact R work needed for the proposed suite

> **Current implementation handoff:** [u4b/IMPLEMENTATION.md](u4b/IMPLEMENTATION.md) reconciles this checklist with installed ordinary /4 code and the finite revision-2 suite. The historical checklist below is preserved; no native support is asserted.

This is a representation/implementation checklist, not installed contract changes. Every
row in suite.json has native_status=not_run. Current B allows only npu-l4/ratio1/TP1/BF16
q_projection with K,N≤256 and M≤1024; TPU hardware and all listed 8B dimensions remain
unadmitted. Do not substitute npu-l4 parameters or the old TPU placeholder for missing fields.

| Suite family | Existing mathematical carrier to preserve | Required native/measurement join before freeze |
|---|---|---|
| BF16/INT8 dots | OpSpec M/K/N, inputs/output, reduction K; per-shape precision | Arbitrary required K/N tiling, four MXUs and accumulator behavior; INT8 precision/scales/accumulation and output conversion need a reviewed exact contract. Compiler padding/layout work reported separately from useful operations. |
| Q/K/V/output projections | q_projection, k_projection, v_projection, output_projection; Q output4096, K/V output1024 for Hq32/Hkv8/D128 | Full supplied matrix tiles and transfers, no hidden TP division. Projection+RoPE fusion must retain both operations when measurement combines them. |
| QK score / AV | qk_score and av_application with B,Hq,query length,valid context,D | Exact grouped-query KV replication and valid tail. If measured within attention_fused, prediction must use that enclosing unit and not a fictitious intermediate score DMA. |
| Softmax / activation | softmax and activation, separately declared vector work | Native vector/reduction/exponential costs need explicit assumptions and exact operation coverage. Never infer throughput from BF16 matrix peak. Lowest observable fused unit must agree with the predicted unit. |
| Normalization / residual | normalization and residual_addition, each on B×new_tokens×4096 | Preserve reduction/add work and all payload/materialized intermediates. Compiled fusion may change memory traffic, not remove mathematical coverage. |
| FFN up / gate / down | ffn_up, ffn_gate, ffn_down;4096→14336→4096 | Gated activation/product and precision conversions retained; canonical group dependencies and all repeats. No GEMM-only “full FFN” claim. |
| KV append / fused paged attention | kv_write, attention_fused; v2 KV descriptors and group/precision bindings | Rotate new K before store; preserve V, valid token count versus page allocation, append bytes and replicated local KV. Read2048 or2049 valid tokens as declared; partial page is not a full payload page. No hidden scores, missing softmax or second TP division. |
| RoPE Q/new-K | Installed v2 rotary spec, authenticated coefficient artifact, positions, pairing and R | FP32 arithmetic plus explicit source/output casts, cos/sin gathering and full-tail transfers. Exact coefficient/position bytes and hashes remain outstanding. Producer-disabled replay must not generate defaults. |
| Cast pairs | v2 precision/conversion accounting where already represented | Native standalone/fused conversions and materialized bytes. If standalone cast is not representable, prepare exact additive protected proposal; do not invent an extra workload language. |
| Embedding / LM head | embedding and lm_head (extra head/tail controls), vocab128256 | Token-hit distribution and rank-local vocabulary semantics; these are outside the one-layer internal operator subtotal and cannot be counted twice. |
| Memory / gather | BufferRange/Dma/Fragment and page tables, payload versus256B B-model transaction vocabulary | TPU request/channel mapping is unknown, so B's256B/8-channel rule is not a TPU law. R must admit actual reference scope and preserve compiler copies/reductions. |
| Minimal launch | Runtime-dependent scalar operation; installed B has no scalar job kind | Exact scalar/control representation or agreed measurable enclosing unit; a fixed-delay fixture is not a physical launch predictor. |
| Complete layer | Prepared v2 groups with one-layer repetition, no embedding/head duplication | Complete work graph, explicit capacities/memory, steady priming, compiler fusion mapping and independently qualified attribution. A q_projection component cannot stand in for the layer. |

Additional first-use decisions: exact reference hardware leaf schema for unknowns; four-MXU
resource identity; any INT8/standalone cast/scalar scope extensions; device trace granularity;
precise block size and shape-bin characterization; trusted coefficient/position inputs;
steady state/cache protocol; permitted compiler FLOP/byte differences. Any resulting protected
change must be supplied as an exact unapplied diff at that decision, then installed by its
human owner. No speculative diff that invents hardware is included here.

A/B can finish mathematical coverage and CPU-only synthetic kit preparation without TPU
access. Actual compiler/device granularity and cache/counter availability remain decisions
or observations to establish under separately authorized future work, before predictions
rely on them. No pilot measurement or compilation on rented devices is authorized here.
