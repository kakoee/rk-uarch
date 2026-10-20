# Finite benchmark agreement proposal, revision 2

**52 proposed measured units; unsigned, unadmitted and unobserved.**
[Machine-readable units](suite-proposed.json) specify dimensions, precision, work, native
support, individual/fused status, mapping, state and device boundary for every selected unit.
[All 70 dispositions](DISPOSITIONS.md) explain every retention, replacement, merge or omission.
The original [70-row JSON](../suite.json) remains byte-for-byte unchanged.

| Class | Units | Coverage |
| --- | ---: | --- |
| Matrix | 12 | Six shapes per precision: (M,K,N)=(1,128,128), (8,128,128), (128,128,128), (1024,1024,1024), (1024,4096,4096), (4096,4096,4096); BF16 and raw signed INT8 |
| Memory | 9 | Read+sum, write/broadcast and distinct-buffer copy, each at 1/16/256 MiB |
| Operator | 24 | Twelve units at decode B=1/S=1/T=2048 and prefill B=1/S=T=128; all required decoder vocabulary covered |
| End-to-end | 4 | Full decoder layer at decode B=1/8/32 and one B=1/S=128 prefill |
| DRAM gather | 2 | Valid context 2048, pages 16 and 32 tokens; both tail=2049 variants retained as correctness tests |
| Launch overhead | 1 | Runtime FP32 scalar add with materialized output; smallest non-eliminated device event |

The twelve decoder units per mode are Q+RoPE, K+RoPE, V, output projection, RMSNorm,
residual addition, FFN up, FFN gate, FFN down, gated SiLU, KV append and fused attention.
Attention covers the required QK score, softmax and AV operator work. Q and K each cover
**their own** rotation and both cast directions. Those merges remove separate timing rows,
not mathematical work. Embedding and LM head are the four omitted optional head/tail rows;
they do not belong to the one-layer subtotal. No native standalone cast operator is needed
for this measured suite, but native casts inside the enclosing units are required.

## Exact workload choices

Use an explicit 8B-class shape, not a claim of exact equivalence to a named model:
H=4096, Hq=32, Hkv=8, D=128, FFN=14336, TP=1, one layer, no bias/dropout/collectives.
Two RMSNorms (epsilon=1e-5), gated SiLU and two residual adds occur in the full layer.
GQA maps query head h to KV head floor(h/4), without physically repeating the KV payload
unless the supplied mapping explicitly does so. Causal prefill has 32*128*129/2 valid
attention pairs; any dense masked issued work is recorded in addition to useful pairs.
Scale/mask, exp, reduction, reciprocal, cast and padding work cannot disappear behind the
analytic 5-ops-per-softmax-pair or 6-ops-per-RMSNorm-element conventions. Those conventions
are useful-work totals; they are not instructions with identical service times.

BF16 dots accumulate FP32 and convert at the declared final output. The Q/K projection
boundary deliberately includes a BF16 output rounding point before widening for FP32
rotation, then BF16 rotated output; compiler fusion must preserve these semantics. RoPE
uses full R=128, split-halves pairing, separate-round RNE/1, positions [2047] at decode and
[0..127] at prefill. Recommend unscaled theta=10000 coefficients for this explicit synthetic
8B-class shape. Produce and freeze one exact `RotaryCoefficients` bit-table and existing
content identity during input preparation; no default generator during replay. Its bytes
are **not supplied or authenticated by this package**. This is a finite input-preparation
item, not a numeric hardware placeholder. The existing v2 coefficient and cache binding
remains authoritative; do not insert fresh source-attestation requirements.

Raw INT8 dots use signed int8 inputs restricted to [-7,7], INT32 accumulation/output, no
scales or quantization/dequantization in the measured unit. For K<=4096 the maximum absolute
sum is 200704, inside INT32. This tests supported integer matrix work without commissioning
an INT8 decoder or per-channel quantization model. Four-byte output traffic differs from
BF16. INT32 must be represented as an operand/accumulator storage dtype in the additive
native interface, not added as a generic rk-sim compute precision without justification.

Memory read includes FP32 widening, E-1 sum adds and one scalar output. Memory write
broadcasts a runtime BF16 scalar. Copy requires distinct endpoints. Those are complete
measurement envelopes rather than promises of pure HBM timing. Small repeated buffers may
stay local: confirm actual transfers or mark HBM granularity unavailable. A materialized
functional output alone does not prove an HBM access on every iteration. Gather uses
explicit reverse-order page indices, separate K/V arrays and contiguous materialized
outputs; page indices are int32 and their loads/arithmetics are included. No seed-only
permutation identity or conditional unspecified reduction is left in the proposed gather.

The vendored rk-sim execution schema defines `KVPolicy.block_size` as a required positive
integer, not a universal value. Recommend 16 as the primary integration point and 32 as the
second page-size control. The future consuming plan must explicitly match one of these.
If it chooses another size, the evidence does not cover that plan: revise the agreement
before freeze, do not silently call 16 the established rk-sim block size.

## Mapping, state and measurement agreement

All rows are one chip, `compiler-chosen`, no collectives. The mapper supplies deterministic
tiles/placement/fusion to the same native engine; XLA is not assumed to implement that policy.
Use a separately versioned mapping for four MXUs on one shared TensorCore. Tile extents,
physical padding, K-reduction ownership, buffers and transfers are resolved before execution;
execution never searches for or repairs a mapping.

Predict and measure the complete selected envelope, from its first included device event
through its final included completion, including internal gaps/dependencies. A fused unit
may occupy several device events; preserve its enclosing interval and event membership.
Exclude compilation, host dispatch gaps and host-device transfer. For full-layer reporting,
never add overlapping fused children to their parent. Keep per-op work attribution even
when per-op device timing is unavailable. The minimal-kernel row contains useful work and
memory traffic: it does not establish pure dispatch latency without an independent separation.

Steady procedure repeats identical shapes, addresses and logical contents. For decode,
restore logical prior length=2047 and rewrite the same append position; do not grow context
on each warm-up. Prefill repeats a zero-prior invocation. Reset logical workload metadata
without flushing all modeled physical residency. Prime one complete iteration inside the
same engine, exclude its counts/time, report the next, and compare a second-priming run.
Do not preload everything as a substitute. The compiler/device retention behavior remains
unobserved; a state mismatch stays an explicit limitation or blocks that comparison.

Later agreement binds optimized HLO, runtime/compiler versions, flags, numeric policy,
materialized buffers, static FLOPs/bytes, device event interval and available counters.
Static compiler byte estimates are not physical HBM counters. Every current observability
cell is `not_demonstrated`; if an envelope is eliminated, further fused, or cannot be timed,
return a concrete changed unit/target decision **before** its prediction freeze. No assumed
XLA event, pilot or measurement is claimed. Historical 10 warm-ups/30 samples remain proposals,
not acceptance gates. Human access/budget and later observation permissions remain separate.

## Shape regimes: concrete arithmetic, limited claim

[shape-regimes.json](shape-regimes.json) is a count-only worksheet, not an EngineResult.
It uses the installed U0001 bin definitions: OI/ridge low <0.5, middle 0.5..2, high >2;
array underfill M<128 or N<128. Chip nominal ridges are 197e12/858993459200 for BF16 and
393e12/858993459200 for INT8. Byte formulas explicitly include INT32 output for INT8.
Original matrix 04 (256-cube) is low/full for both. Revision 2's 1024-cube is middle/full
for both, removing a genuine BF16 hole while keeping six shapes per precision. Both
precisions now span low/underfilled, low/full, middle/full and high/full. Large full shapes
are saturation **candidates**, not measured saturation.

The worksheet also checks the selected decoder projection dimensions at M=1,8,32,128.
Decode projections are low/underfilled; prefill includes low/full and middle/full. Matrix
anchors extend selection beyond the 8B layer. This bounds the intended initial family
scope to these classes/precisions/regimes; it is not evidence for every large-core request.
Fused-envelope traffic, compiler padding, reduction-special-function throughput and unknown
NoC/DRAM load regimes still need their own scope match. INT8 coverage is isolated dots only.

`uarch characterize` currently calls analytic `capture()` and emits timing predictions;
it is not a count-only entry point. Also no valid TPU HardwareSpec exists. Running it with
npu-l4 or invented clock/vector inputs would not establish TPU shape coverage and would
violate this task's no-predictions boundary. Thus U-P9's final **characterize binding is
not satisfied here**. After the model decision and admitted reference, reuse that command
on the exact prepared selection before freeze, and reconcile its per-op scopes against
this worksheet. If new bins appear, amend the finite selection explicitly rather than
starting a full grid. No waived shape requirement or fabricated characterize receipt.
