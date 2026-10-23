# TPU v5e benchmark agreement — accepted 52-unit U5 freeze

> **Human acceptance, 2026-10-22:** Javid accepted the unchanged current 52-unit agreement and reference APIs in place of outstanding A/B signatures. Actual compiler/device correspondence remains U5 measurement work, with predictions frozen first. [Acceptance and scope](../../../docs/reviews/U4-closeout-acceptance.md). The dated proposal below is preserved as history.

> **Historical revision 1:** the 70-row proposal and `suite.json` below remain evidence history. The installed selection is 52 units. Use [BENCHMARK-PLAN.md](BENCHMARK-PLAN.md) for current execution status, all selected IDs, proposed device comparisons and remaining agreement; [u4b/DISPOSITIONS.md](u4b/DISPOSITIONS.md) accounts for all 70 candidates. Pending claims below describe 2026-10-16, not today's installed simulator.


## Operative U5 agreement (recorded before prediction generation)

**Human agreement: Javid, 2026-10-22**, replacing Lane A and Lane B signatures
for this unchanged suite, exactly as recorded in the linked acceptance. Neither lane's
signature is invented. Lane A owns prediction freezing; Lane B owns the measurement kit.
The operative list is the 52 IDs and complete per-row work/envelopes in
[u4b/suite-proposed.json](u4b/suite-proposed.json), interpreted by
[BENCHMARK-PLAN.md](BENCHMARK-PLAN.md). Historical pending fields are superseded only
by the human acceptance; no suite shapes or boundaries change here.

Coverage: 12 matrix (six shapes each BF16/raw INT8), nine memory (read/write/copy at
1/16/256 MiB), 24 operator envelopes (12 decode and 12 prefill), four full layers
(decode B=1/8/32 and prefill S=128), two paged gathers (16/32 tokens), and one
minimal scalar-add device envelope. Fused attention covers QK/scale/mask/softmax/AV;
Q and K projection envelopes include their respective RoPE and casts. The 8B-class
layer uses H=4096, Hq=32, Hkv=8, D=128 and FFN=14336, TP1.

The accepted [shape worksheet](u4b/shape-regimes.json) spans low/middle/high nominal
arithmetic-intensity regimes and underfilled/full matrix arrays, including 4096³
beyond decoder-only shapes. These are count-based bins, not observed utilization.
Installed reference preparation and U-C0 APIs replace the legacy HardwareSpec
characterize command under the explicit closeout adjustment.

Every unit is **device-side only**, from first included activity to last completion,
including internal gaps, excluding host dispatch/launch gaps, compilation and transfers.
Every mapping match is **compiler-chosen**. The supplied local ws-rowsplit/3 graph is
not asserted to equal XLA. Initial state is **steady**, with one native priming iteration
and unchanged logical inputs for the next invocation. Device warm-up/sample counts remain
Lane B's kit agreement; simulator priming does not prove device retention. Compiler FLOPs,
bytes and event membership are unobserved and must be recorded separately during U5
measurement. Incomparable device envelopes retain their original frozen predictions.

No TPU timing, pilot or device inspection is part of this freeze. Diagnostics retain F3/F6
verification limits; F4's /4 error-code limitation and F5's serialized staging remain.

## Historical proposal (preserved)

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
