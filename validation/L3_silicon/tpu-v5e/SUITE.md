# Proposed TPU v5e benchmark agreement, revision 1

> **Human acceptance, 2026-10-22:** Javid accepted the unchanged current 52-unit agreement and reference APIs in place of outstanding A/B signatures. Actual compiler/device correspondence remains U5 measurement work, with predictions frozen first. [Acceptance and scope](../../../docs/reviews/U4-closeout-acceptance.md). The dated proposal below is preserved as history.

> **Historical revision 1:** the 70-row proposal and `suite.json` below remain evidence history. The installed selection is 52 units. Use [BENCHMARK-PLAN.md](BENCHMARK-PLAN.md) for current execution status, all selected IDs, proposed device comparisons and remaining agreement; [u4b/DISPOSITIONS.md](u4b/DISPOSITIONS.md) accounts for all 70 candidates. Pending claims below describe 2026-10-16, not today's installed simulator.

**Not signed or admitted.** Lane B agent proposal, 2026-10-16. Lane A signature: pending.
Human target/access decision: pending. No prediction or result files exist in this package.
The exact list is [suite.json](suite.json); each row binds work, measurement unit, timing,
state, compiler counts, mapping match and missing native capabilities. [Readiness](READINESS.md)
sets source and observability limits. No measurement may precede frozen predictions.

| Class | Rows | Proposed work and representation |
|---|---:|---|
| Matrix | 12 | Six explicit M/K/N shapes from 1×128×128 through 4096³, each BF16 and INT8. Installed BF16 q_projection carrier covers small mathematical subsets; R must add TPU hardware, larger shapes/tiling, INT8 scales/accumulation/casts. No peak-rate substitution for missing timing. |
| Memory | 9 | Read/write/copy at 1, 16, 256 MiB; observable compiled materialization/reduction. Explicit DMA fragments can describe traffic, but memory-only steady scope and TPU mapping are not admitted. |
| Operator | 40 | All 17 installed operator vocabulary entries at decode and prefill, plus Q/new-K RoPE and both BF16↔FP32 cast directions in both modes. Embedding/lm_head are additional head/tail controls beyond the decoder; attention_fused and split score/softmax/AV require separate agreed envelopes, never double-counted as one layer. |
| End-to-end | 4 | One 8B-class decoder layer, decode B=1/8/32 and prefill B=1/S=128. Include norm, QKV, rotary/casts/coefficient traffic, rotated-before-store KV append, paged fused attention, residual and FFN. Current component-only engine cannot represent this. |
| DRAM gather | 4 | Block sizes 16/32 tokens, contexts 2048/2049, BF16 K+V, 8 KV heads×128. The second context requires partial-tail handling. The exact intended rk-sim block size is an open agreement input, not assumed from these candidates. |
| Launch overhead | 1 | Runtime-dependent minimal scalar operation with observed device event. A compiled-away function is an unavailable benchmark, never zero launch time. |

Total **70**, six classes, all native cells `not_run`. This is larger than the ≥24 minimum
because required operator coverage cannot be silently discarded. The numerical matrix
shapes are candidate coverage anchors, not a claim that characterization bins have been
covered. Before signing, run the existing characterize preparation for intended request
families, bind the resulting shape/bin identities, and extend the list for uncovered regimes.
This is preparation, not a hardware measurement or timing prediction.

Common proposed layer dimensions: H=4096, Hq=32, Hkv=8, D=128, FFN=14336, vocab=128256,
TP1, one layer, BF16 payload, FP32 reduction/rotary arithmetic where the contract requires it.
Decode has 2047 prior tokens plus one new token; prefill has zero prior plus 128 new tokens.
RoPE R=128 positions are explicit; coefficient bytes and hashes still must be supplied.
KV contexts count valid tokens separately from allocated pages and transactions. No hidden
score DRAM buffer, second TP division or default coefficient generator is allowed.

Agreement before freeze must resolve, per row: exact compiled/fused work, whether device
intervals are separable, compiled FLOPs/bytes and padding/layout changes, observed counters
versus estimates, warm state/priming, device-only timing, repetitions, runtime/compiler pins,
shape-bin coverage and exact prepared/native/analytic identities. If a required unit cannot
be represented or timed, return that explicit scope/contract/target decision. Keep its row
open; do not rename it to a convenient smaller operator or invent unknown TPU parameters.

The installed PreparedOp/v2 rotary carriers provide mathematical provenance but do not
make the native B executor a rotary, cast, full decoder or TPU engine. R owns that native
work and its independent tests before G3a/U-P9. U-P10 owns the CPU synthetic dry-run kit,
ordering enforcement and separately authorized hardware execution after the freeze.
