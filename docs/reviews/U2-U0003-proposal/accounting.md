# Accounting investigation, before a producer exists

**PROPOSED semantic choices; executed arithmetic probes only.** Evidence is
`accounting-evidence.json`, reproducible by running `python3 accounting-probe.py.txt` from
Lane A root using the full package-relative path. The script reads only the committed
snapshot, writes only review evidence and never calls rk, iteration_cost, a producer or an
engine. Stored oracle durations are copied, never generated or recomputed as expectations.

## Exact sources and access

Inspected actual contract models/schema/fixtures, protocol stub, hardware/workload/engine/
table READMEs, parity.py, test_flop_parity.py, test_projection_scope.py, scripts/vendor_rk.py,
accepted ADRs and relevant A-F9/A-F12/B-F16 review/responses. Required build-spec §§2.2–2.7,
§§5–7 and U-P3/U-P4 copies, standalone prompts/template, execution plan, how-it-works,
closeout/adoption/kickoff obligations and coordinator kickoff/U0021 were read.
Pinned checkout `/home/jjaff/AI-infra-simulation/rk-sim-u1-pin` exists, HEAD is
`1e5706e0ebfcc67c1a7333079a35b75f693e9963`, status output empty. The original investigation read the two named compute YAMLs without executing the oracle.
For revision 2, pinned compute/loader/orchestrator source was inspected to specify a separate
nominal candidate and full synthetic loader/private-adapter selection was run with oracle
entry points trapped. Eighteen checks passed, zero oracle calls; exact source fingerprints
are in loader-probe-results.json. No generated expected counts/durations, dependency install
or upstream edit occurred. Empty Git status is not a strict generator pristine-clone audit.

The frozen set has 864 records, 432 decode-null writes, no vector channel in any record,
two components and zero npu-l4 records. All baseline shapes have kv_heads=8, tp=1 or 8,
and divisible vocabulary. A-F12's existing supported baseline remains intact; replication
and padding examples remain separate valid-shape/runtime tests with unsupported parity
projection. Oracle manifest is `b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d`.
Full source file SHA256 values and each selected component digest accompany the evidence.

## Independent tensor arithmetic, not a parameter-share adjustment

Let D=model width, h=D/n_heads, L=layers, V=vocabulary, W=one expert's FFN width and
A=experts_per_token (1 for dense). Per-layer Q/K/V/O matrix weights are
2D²+2D×kv_heads×h. Active FFN matrix weights are 3DWA for gated MLP. There is ONE dense
lm_head V×D; embedding is a gather with zero matrix operations. Norm/router parameter
storage is not matrix work. For n input tokens, all-token head matrix work is
2n×[L(2D²+2D×kv_heads×h+3DWA)+VD]. Add 4LD×T for decode attention or 4LD×Q for
full-square prefill attention. This is independently derived operator accounting under
explicit full-square/all-token conventions, not a finished runtime or a frozen oracle.
Causal triangular attention and last-token-only head would lower prefill matrix work further.

Exact selected placeholder FP16/FP16 tp1 examples (IDs share model/fp16/fp16/tp1/
asic_placeholder.yaml; suffix /0 is decode B1,T128, /12 is prefill n1,L128):

| Model/query | Frozen matrix ops | Independent matrix ops | Raw error | Best residual after spending full 5% |
| --- | ---: | ---: | ---: | ---: |
| 8B /0 | 16,127,108,864 | 15,076,425,728 | -6.515012361% | 1.515012361%: fails |
| 8B /12 | 2,059,974,967,296 | 1,929,782,493,184 | -6.320099816% | 1.320099816%: fails |
| 70B /0 | 141,535,544,320 | 139,338,973,184 | -1.551957246% | Could fit budget; no accepted adjustment |
| 70B /12 | 18,095,074,836,480 | 17,835,388,567,552 | -1.435121276% | Could fit budget; no accepted adjustment |
| Mixtral /0 | 25,867,108,864 | 25,562,185,728 | -1.178806405% | Could fit budget; no accepted adjustment |
| Mixtral /12 | 3,306,694,967,296 | 3,271,959,773,184 | -1.050450509% | Could fit budget; no accepted adjustment |

The ~6.54% 8B embedding PARAMETER share is not used as an operation/time correction.
The above percentages come from explicit operators against exact fixture channels, including
attention and rounded nominal inputs. Frozen nominal ModelSpec inputs remain unchanged:
8B 8.03B vs shape-implied 8,030,261,248; 70B 70.6B vs 70,553,706,496; Mixtral active
12.9B vs 12,879,925,248 and total 46.7B vs 46,702,792,704. The accepted 1% identity test
is not the 0.5% parity test and neither authorizes subtracting those parameter differences.

Memory lower bounds in the JSON count selected matrix weights, gather and decode KV only;
they OMIT intermediate activation traffic, norm weights and additional terms and are labelled
lower bounds, never final count results or measured failures. For 8B /0 the lower bound is
15,026,102,272 vs frozen reads 16,076,777,216. Do not claim a full-read failure from a lower
bound. Actual resolved-ops/1 counts must include all declared accesses. Fused attention never
materializes quadratic score DRAM; unfused imports must charge it. At L32768 the full-square
score domain is large but not a DRAM operand of attention_fused.

KV: in the independently authored tiny fixture T17/block16 means two pages, 136 paired
K/V valid bytes per layer (bf16,Hkv1,D2), while physical allocation reserves 32 tokens.
Full-page read traffic would be 256 bytes, an explicit alternative to valid-token reads.
For real 8B decode /0, append K/V writes alone are 131,072 bytes. The frozen channel is null,
not zero. No adjustment can legalize known positive actual vs null under the accepted harness.
Softmax vector operations are also known under the proposed convention, while the oracle
omits vector_ops entirely. Missing is not a reference zero or an achieved vector parity pass.

MoE example: Mixtral one-expert FFN weights/layer = 3×4096×14336 = 176,160,768;
active FFN matrix work/token across 32 layers = 2×176,160,768×2×32 = 22,548,578,304.
Expert resident weights = 176,160,768×8×32 = 45,097,156,608 parameters. Shared attention
and head are separate, and router performance is omitted. Multiplying expanded expert
width and work_repeat again is a double count. A-F9 requires the exact MOE_OMISSION sentence
in graph and table for Mixtral; no report may call router performance modelled.

Head/tail repeat once, layer template repeats n_layers. The synthetic graph has 14 decoder
ops×2+embedding+final_norm+lm_head=31 invocations. Fixtures pin each term independently;
changing n_layers cannot multiply embedding/lm_head. The model includes two embedding weight
matrices when untied even though only lm_head is dense work. Tied storage remains one matrix.

## Duration is an independent blocker

`...8b/fp16/fp16/tp1/asic_placeholder.yaml/12` has stored upstream duration
0.03745409031447272 s and declares 100 TFLOPS, 1 TB/s plus scalar efficiency 0.55.
As an isolated diagnostic, feeding that fixture's OWN frozen counts as inputs to an
unmodified peak max(compute,memory) gives 0.02059974967296 s, 45% below the stored duration.
This is NOT actual workload parity and is NOT an expected oracle duration. It isolates a
scope difference in the proposed peak analytic model even before shape accounting changes.
The known upstream duration remains the sole expectation. The test-only generator calls
upstream iteration_cost and decode_s/prefill_s; it does not supply an independent physical
workload. H100 likewise records the 0.55 model contributor, not a hardware-peak reduction.

An explicit component-model factor in a test adapter could isolate upstream algebra, but
must never alter derive_rk_params or silently change the peak roofline. Mapping this factor
into a production model assumption is a NEW semantic decision needing exact provenance,
versioning and a separately named model. No factor is accepted/implemented in this proposal.
Even a successful anchor with that factor would not fix the 8B count conflict or known/null
channels, and passing count residual does not establish ±0.1% duration agreement.

## D8 disposition in revision 2

Javid selected S for proposal drafting. The old count/duration gates remain operative until
exact replacement acceptance. See two-track-amendment.md for old/proposed exits, separate
physical and nominal model ownership, candidate input isolation, independent tests and costs.
The above arithmetic is preserved without retuning. A frozen-count diagnostic remains a
self-test and is not the proposed nominal candidate. H and R remain documented alternatives
for rationale, not a request to choose the drafting direction again.

No over-budget example is relabelled unsupported_projection. A-F12 remains limited to
replication/padding. All 864 baseline records remain in coverage, with each original component
and stored duration. Proposed refresh adds actual human-generated npu-l4 BF16 artifacts; no
synthetic fixture in this package claims to supply those. Physical failed/unknown channels
are hash-bound report inputs under the proposed C2 policy, never a passing-only summary.
