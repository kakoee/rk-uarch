# U3 G2 independent physical expectation specification

Status: **PROPOSED**, part of [U0005 pre-registration](U3-U0005-proposal.md).
Authored before candidate execution. This is integer tensor arithmetic and future test
specification, not a generated oracle, runtime bundle, simulator measurement or independent
review of Lane A. No production counting function or upstream simulator was called to derive
these numbers. Acceptance must bind this file together with the proposal by Git revision.

Accepted U0022 coverage clarification (historical matrix expectations below are unchanged):

U2 physical-resolved/1 accounts for its captured operator graph. It excludes RoPE
rotation/conversion work and coefficient traffic; its vector/byte counts and timing
are not complete RoPE-equipped decoder work. This does not change historical numbers,
nominal compatibility outcomes, parameter counts or the matrix-count convention.

## Inputs and scope

Dimension source: unchanged [U2 8B shape](../../contract/fixtures/model_shapes/llama-3.1-8b.json)
at U2 baseline `79bc1f014306e520aacba3491d60ae6c644b26a8`:
D=4096, Hq=32, Hkv=8, d=D/Hq=128, F=14336, V=128256, gated dense MLP,
untied embedding/head. Source model has L=32. Proposed G2 diagnostic is explicitly synthetic
`g2-8b-shape-1layer`, L=1, preserving the other dimensions. Its exact parameter count is

    P(L) = 2VD + L(2D² + 2D Hkv d + 3DF + 2D) + D
    P(1) = 1,268,789,248; P(32) = 8,030,261,248.

The final D is final normalization; 2D inside each layer is its two normalizations.
No bias/router matrix work is inferred from rounded parameter counts. Both active and total
parameters equal P(1) for the synthetic dense model. This proposal does not alter the published
8.03B nominal model or adopted compatibility references. Later preparation must construct a
new declared intent and bundle, not edit an existing capture or falsify n_layers metadata.

One query = B sequences, one newly decoded token each, S valid attended context tokens per
sequence, T=B×S. The contract's S does not become S+1 inside an adapter. BF16/BF16, block=16,
frequency=1, cold state, selected rank r, no inter-chip collectives. Preserve every decoder
operator and the once-only embedding/final-normalization/lm_head groups. Fusion remains
qk_softmax_av; matrix counting does not license materializing scores in DRAM.

## Per-operator integer oracle

Let q=Hq/tp, k=max(1,Hkv/tp), f=F/tp, v=ceil(V/tp). Validate divisibility/replication
preconditions rather than flooring arbitrary input. These symbols describe already resolved
rank extents; the adapter does not recalculate or divide them again.

| Prepared matrix work | Rank operand extents | Operations per decoder, before group repeat |
| --- | --- | ---: |
| q_projection | [B,D] × [D,q·d] | 2B D q d |
| k_projection | [B,D] × [D,k·d] | 2B D k d |
| v_projection | [B,D] × [D,k·d] | 2B D k d |
| attention QK | B·q products of [1,d] × [d,S] | 2B q S d |
| attention AV | B·q products of [1,S] × [S,d] | 2B q S d |
| output_projection | [B,q·d] × [q·d,D] | 2B q d D |
| ffn_up | [B,D] × [D,f] | 2B D f |
| ffn_gate | [B,D] × [D,f] | 2B D f |
| ffn_down | [B,f] × [f,D] | 2B f D |
| lm_head, once outside decoder | [B,D] × [D,v] | 2B D v |

Embedding is a gather: **zero matrix ops**, even on a rank with token hits. Normalization,
RoPE, residual, activation, softmax and KV writes have zero matrix ops; they are still work
that must survive translation. For fused attention retain QK and AV contributions inside its
single operator count. Multiplying KV-head count instead of query-head count undercounts GQA.
For general imported groups multiply each operator's physical extents by its `work_repeat`
and its group's `repeat` exactly once, respecting any explicit padding/replication metadata.
This dense fixture has work_repeat=1 throughout, decoder repeat=L, head/tail repeat=1.

    Cdecoder(B,S,tp) = 4B D q d + 4B D k d + 6B D f + 4B q S d
    Cmodel(L) = L·Cdecoder + 2B D v

At tp1: (q,k,f,v)=(32,8,14336,128256), decoder projections/FFN per token=436,207,616;
attention=16,384·B·S; head per token=1,050,673,152.
At tp8: (q,k,f,v)=(4,1,1792,16032), decoder projections/FFN per token=54,525,952;
attention=2,048·B·S; head per token=131,334,144.
These particular shapes happen to divide evenly; that is not permission to divide arbitrary
physical totals by tp.

| tp | B | S | One decoder ops | G2 L=1 complete model ops | Original L=32 complete model ops |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 512 | 444,596,224 | 1,495,269,376 | 15,277,752,320 |
| 1 | 1 | 4096 | 503,316,480 | 1,553,989,632 | 17,156,800,512 |
| 1 | 8 | 512 | 3,556,769,792 | 11,962,155,008 | 122,222,018,560 |
| 1 | 8 | 4096 | 4,026,531,840 | 12,431,917,056 | 137,254,404,096 |
| 1 | 32 | 512 | 14,227,079,168 | 47,848,620,032 | 488,888,074,240 |
| 1 | 32 | 4096 | 16,106,127,360 | 49,727,668,224 | 549,017,616,384 |
| 8 | 1 | 512 | 55,574,528 | 186,908,672 | 1,909,719,040 |
| 8 | 1 | 4096 | 62,914,560 | 194,248,704 | 2,144,600,064 |
| 8 | 8 | 512 | 444,596,224 | 1,495,269,376 | 15,277,752,320 |
| 8 | 8 | 4096 | 503,316,480 | 1,553,989,632 | 17,156,800,512 |
| 8 | 32 | 512 | 1,778,384,896 | 5,981,077,504 | 61,111,009,280 |
| 8 | 32 | 4096 | 2,013,265,920 | 6,215,958,528 | 68,627,202,048 |

The extra rank1/B1/tp8 cases have the same matrix counts as rank0, but embedding reads differ:
rank0 gathers D BF16 elements (8,192 bytes); rank1 gathers none. Never conclude rank
equivalence from matrix counts alone. Explicit hit vectors and `equivalent_ranks` must agree
with complete physical work across captured points.

Independently expected KV **payload** reads per decoder = 2·B·k·S·d·2 bytes;
append writes = 2·B·k·d·2 bytes. Allocated KV capacity uses ceil(S/16)·16 rather than
valid-token traffic. At B1/tp8/S512, reads=262,144 bytes, writes=512 bytes; at S4096,
reads=2,097,152 bytes, writes=512 bytes. These are KV payload terms only, not whole-model
traffic or candidate bus transactions. Transfers can include declared mapping granularity;
record that discrepancy rather than substituting transaction-rounded reads for input semantics.

## Discriminators to write before implementation

| Case / mutation | Required observation |
| --- | --- |
| Drop lm_head | tp8/B1 loses exactly 131,334,144 ops; decoder-only equality must fail the full-model gate. |
| Drop gate projection | tp8/B1 loses 14,680,064 ops; fusing up/gate cannot delete either term. |
| Drop QK or AV | tp8/B1/S512 loses 524,288 ops per omitted half; total attention must be 1,048,576. |
| Replace GQA query heads with KV heads | tp8 attention becomes one quarter of required work: fail. |
| Shard imported tp8 again / multiply all groups by L | Fail per-operator extents or once-only head accounting, even if an aggregate coincidentally agrees. |
| Report MACs as ops | Factor-two error fails; a named conversion returns exactly 2·MAC. Test channel units and integers before serialization. |
| Equal aggregate but swapped operator work | Fail per-operator/operator-identity correspondence. Expected constants cannot serve as candidate observations. |
| Tiny replicated KV and padded vocabulary | D=8,Hq=4,Hkv=1,d=2,F=16,V=9,tp=2,B1,S17,L1: q=2,k=1,f=8,v=5. Q=64,K=32,V=32,O=64,each FFN=128,attention=272,head=80; decoder=848, total=928 ops. KV replica factor=2. Rank1 physical vocabulary width=5, logical=4; do not truncate physical head to width 4. |
| Tiny page boundary | Above KV reads=136 bytes, writes=8 bytes, allocation=256 bytes per layer (two pages). Reading 256 payload bytes instead of 136 changes the prepared policy. |
| Connected physical FFN padding | In that tiny case extend f from 8 to 10 consistently in up/gate/activation/down: add 96 matrix ops, total=1024. Updating only one operand must fail validation. |
| Unequal embedding hits | Tiny tp2/B1 vector [1,0]: rank0 gathers 16 bytes, rank1 zero; [1,1] fails conservation. Representative-all-ranks scope fails. |
| Import/replay | Freeze content identity then disable local producer/model reconstruction; input rank shapes, counts and all dependent identities must survive. Refuse stale/missing coverage and mismatched hardware. |

The tiny cases are additional independent specification-level discriminators, not extra
candidate timing points or a claim that those imports are supported by either fork. If future
adapter support excludes one, test explicit refusal before launch and record the exclusion;
do not use it as executed coverage. Main G2 points cannot be relabelled optional this way.

Candidate observations must come from executed operator/tile records or exact native counters
with documented units and complete correspondence to prepared operators. Preserve issued
padding/tile-overhead work separately from operations over the declared physical input extents;
never subtract a fitted residual. If only cycles, utilization or padded aggregate counts are
available without a provable correspondence, G2(c) remains unproven/fails observability.
No engine patch may change physics or manufacture count parity. An instrumentation need is
an explicit prospective decision before work, not permission granted by this specification.

Keep physical-versus-nominal discrepancies bound to the same actual inputs and preserve
failure/null/unassessed outcomes. U0003's test-only nominal compatibility and adopted v3
references remain separate; their tolerances cannot discharge exact physical G2(c).
