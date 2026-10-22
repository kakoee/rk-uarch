# Installed U4b suite and planned TPU comparisons

Current reconciliation, 2026-10-22. This connects existing workload definitions to the
existing U5 measurement plan; it adds no workloads or timing laws.
Javid [accepted this unchanged agreement](../../../docs/reviews/U4-closeout-acceptance.md)
on 2026-10-22, replacing outstanding A/B signatures with human acceptance. The reference
APIs are accepted; actual compiler/device correspondence is checked in U5 measurement
work, with predictions frozen before measured timing. Unverified diagnostics cannot
support causal claims. U4 technical scope is accepted; the tag awaits completed CI.

The complete reviewed v2 implementation was human-installed at `36262735ba21cc75c9373216ed89153e6f31c2d6`
and published with its verification record at `6d443e1`. The [installation record](../../../docs/reviews/U4b-native-reference-install-decision-v1/next-decision.md)
confirms all 42 postimages. The [v2 handoff](../../../docs/reviews/U4b-native-reference-implementation-v2/README.md)
records the corrected resource loader and dependency-readiness checker, with remaining
limitations. One native engine supports ordinary component /4 and reference /5 jobs.

## Which list to use

The current implementation selection is the **52 IDs in [u4b/suite-proposed.json](u4b/suite-proposed.json)**.
The filename and its prospective status fields are preserved because they are inputs to
published evidence. Its `native_status: not_run` and empty signatures describe the old
proposal, not today's simulator execution status. This document supplies current status;
the human acceptance supplies the current agreement without inventing A/B signatures or
device evidence.

The older [suite.json](suite.json) is the historical 70-candidate proposal. Do not execute
both lists or combine their counts. [All 70 dispositions](u4b/DISPOSITIONS.md) account for
50 retained entries, two shape replacements, 12 merges, four optional omissions and two
correctness-only cases, yielding 52 timed units. Merged softmax/QK/AV work stays inside
attention; Q and K each retain their own RoPE/casts. Context-2049 gather tails remain
correctness tests. Embedding/LM-head controls are outside this one-layer scope.

## What has run, and what has not

The author's [52-row campaign](../../../docs/reviews/U4b-native-reference-implementation-v1/evidence/integration.jsonl)
reports three fresh release executions per unit, one debug execution, a two-prime
execution, installed producer-disabled replay and priming equality. All 52 IDs and their
classes match the selected list. Those results are inherited here, not rerun. The campaign's
earlier binary and final admission-only delta are distinguished in the author/reviewer
records; the independent review exercised 14 final-source units, and the v2 recheck
exercised eight installed units plus the corrected checker/replay controls. These are
implementation verification results, not U5 frozen predictions or TPU measurements.

The [nominal model](u4b/MODEL.md) has nine published fact leaves and 17 explicitly numeric
STUB estimates. Compilation behavior, actual device timing boundaries, retention and
physical counters have not been observed by this reconciliation. No measurement kit,
compiler run, device access or paid work is performed here.

## Corresponding measurements

Every row below uses its unchanged mathematical inputs and precision policy in
[u4b/SUITE.md](u4b/SUITE.md) and the machine-readable selection. Device execution is planned,
not observed. The current mapping-match label is **compiler-chosen**, not matched: our
mapper's tiling and staging need not equal the TPU compiler's choices.

| Class | Units | Intended device comparison | Existing point to settle before relying on the comparison |
| --- | ---: | --- | --- |
| Matrix | 12 | Complete BF16 or raw INT8 dot, including required layout, padding and output conversion | Preserve accumulation/output types and report compiler work; no INT8 decoder or hidden quantization |
| Memory | 9 | Read-and-sum, runtime-scalar fill, or distinct-buffer copy | Confirm materialization and distinguish compiler byte estimates from actual HBM traffic; read-and-sum includes vector/reduction time |
| Operator | 24 | Complete named operation or declared fused group | Q/K include their own rotation; attention includes QK/scale/mask/softmax/AV; do not compare isolated child timing with a fused parent |
| End-to-end | 4 | Entire single decoder layer with KV outputs | Include every selected operation once; do not add child intervals that overlap the layer interval |
| DRAM gather | 2 | Page-index lookup and distinct materialized K/V outputs | Compare the declared page order/size and valid extent; disclose serialized staging versus compiler overlap |
| Launch overhead | 1 | Smallest non-eliminated scalar-add device event | It includes useful work and data movement, so is minimal-kernel cost, not pure host launch latency |

### Common timing and state boundaries

These are the already proposed boundaries, not new experimental requirements:

- Time the whole selected device interval from first included device activity through final
  completion, including internal gaps. Exclude compilation, host dispatch gaps and
  host-device transfer. Resolve how the nominal `kernel_startup_ps` term corresponds to
  that interval; it is a STUB device-entry cost, not a measured host-launch time.
- Record actual event membership where the compiler fuses, splits or eliminates work.
  If device observations show the declared unit cannot be timed meaningfully, mark that
  comparison incomparable and return the concrete unit/target decision. Preserve the frozen
  prediction; do not silently substitute a smaller unit or tune after seeing timing.
- Keep precision, coefficients, masks and required rounding points. Archive compiler
  FLOPs/bytes separately from physical counters; absent counters remain unavailable.
- Warm up the declared workload and preserve its logical inputs: decode repeats prior
  length 2047 and the same append destination; prefill starts at zero prior length.
  Simulator one-versus-two priming equality does not demonstrate device retention.
- Ten warm-ups and 30 samples remain historical proposals, not newly approved defaults.
  Final counts belong to the existing U5 measurement-kit agreement.

### Staging and diagnostic limitations that must travel with predictions

The current mapper serializes gather, attention packing and activation packing through a
single staging slot. The independent review reported **862.2 microseconds** for simulated
`gather-p16-c2048`, versus **19.5 microseconds** for bytes divided by peak HBM bandwidth;
95% of its simulated critical path was HBM latency. Fused decode attention was similarly
latency dominated. These figures describe this mapping/model, not TPU behavior and not a
measured hardware shortfall. The [v2 F5 disclosure](../../../docs/reviews/U4b-native-reference-implementation-v2/README.md)
is the attributed source. Keep the policy unchanged in this documentation pass. A later
mapping change requires the ordinary model decision and affected verification before freeze.

The independent checker does not fully establish non-HBM arbitration (F3) or causal
adjacency of critical-path entries (F6). Direct oversized /4 input retains the documented
error-code difference (F4). These remain non-blocking installation limitations, not fixed
findings. In particular, U-P10's causal error-attribution claim cannot be inferred from
these diagnostics alone; qualify the actual attribution used at that consumer or explicitly
resolve its scope. No extra checker work or gate is commissioned here.

## Exact 52-unit correspondence

Each row is present in the saved campaign with `status: passed`. That is inherited
simulator evidence. Each proposed device envelope is copied from the existing selection;
none is asserted to be observable yet. Detailed dimensions, data types, coefficients and
state are retained in the linked selection rather than redefined here.

| Workload ID | Class | Planned device envelope |
| --- | --- | --- |
| `matrix-bf16-01` | matrix | single compiled dot including required layout/padding/output conversion |
| `matrix-bf16-02` | matrix | single compiled dot including required layout/padding/output conversion |
| `matrix-bf16-03` | matrix | single compiled dot including required layout/padding/output conversion |
| `matrix-bf16-04` | matrix | single compiled dot including required layout/padding/output conversion |
| `matrix-bf16-05` | matrix | single compiled dot including required layout/padding/output conversion |
| `matrix-bf16-06` | matrix | single compiled dot including required layout/padding/output conversion |
| `matrix-int8-01` | matrix | single compiled dot including required layout/padding/output conversion |
| `matrix-int8-02` | matrix | single compiled dot including required layout/padding/output conversion |
| `matrix-int8-03` | matrix | single compiled dot including required layout/padding/output conversion |
| `matrix-int8-04` | matrix | single compiled dot including required layout/padding/output conversion |
| `matrix-int8-05` | matrix | single compiled dot including required layout/padding/output conversion |
| `matrix-int8-06` | matrix | single compiled dot including required layout/padding/output conversion |
| `memory-read-1048576` | memory | whole device interval for input read, widening, reduction and scalar store; report reduction as included work |
| `memory-read-16777216` | memory | whole device interval for input read, widening, reduction and scalar store; report reduction as included work |
| `memory-read-268435456` | memory | whole device interval for input read, widening, reduction and scalar store; report reduction as included work |
| `memory-write-1048576` | memory | device interval for scalar read/broadcast and materialized destination write; no constant folding |
| `memory-write-16777216` | memory | device interval for scalar read/broadcast and materialized destination write; no constant folding |
| `memory-write-268435456` | memory | device interval for scalar read/broadcast and materialized destination write; no constant folding |
| `memory-copy-1048576` | memory | device interval for real distinct-buffer copy; optimized alias/donation-only work is unavailable, not zero |
| `memory-copy-16777216` | memory | device interval for real distinct-buffer copy; optimized alias/donation-only work is unavailable, not zero |
| `memory-copy-268435456` | memory | device interval for real distinct-buffer copy; optimized alias/donation-only work is unavailable, not zero |
| `operator-q_projection-decode` | operator | whole projection plus Q rotation envelope, including all numeric boundaries; K output is rotated before separate KV append |
| `operator-k_projection-decode` | operator | whole projection plus new-K rotation envelope, including all numeric boundaries; K output is rotated before separate KV append |
| `operator-v_projection-decode` | operator | whole compiled dot with required layout/padding/output conversion; materialized BF16 output |
| `operator-output_projection-decode` | operator | whole compiled dot with required layout/padding/output conversion; materialized BF16 output |
| `operator-normalization-decode` | operator | complete RMSNorm envelope including gamma, epsilon, FP32 intermediates and output cast |
| `operator-residual_addition-decode` | operator | two runtime operands through materialized residual output |
| `operator-ffn_up-decode` | operator | whole compiled dot with required layout/padding/output conversion; materialized BF16 output |
| `operator-ffn_gate-decode` | operator | whole compiled dot with required layout/padding/output conversion; materialized BF16 output |
| `operator-ffn_down-decode` | operator | whole compiled dot with required layout/padding/output conversion; materialized BF16 output |
| `operator-activation-decode` | operator | complete gated SiLU product envelope; no omission of multiplication by up |
| `operator-kv_write-decode` | operator | only K/V append into materialized cache; consumes already rotated K, does not duplicate projection/RoPE |
| `operator-attention_fused-decode` | operator | one paged QK/scale/causal-mask/stable-softmax/AV envelope from already rotated Q and resident logical KV inputs to BF16 O; no separate scores/softmax timings |
| `operator-q_projection-prefill` | operator | whole projection plus Q rotation envelope, including all numeric boundaries; K output is rotated before separate KV append |
| `operator-k_projection-prefill` | operator | whole projection plus new-K rotation envelope, including all numeric boundaries; K output is rotated before separate KV append |
| `operator-v_projection-prefill` | operator | whole compiled dot with required layout/padding/output conversion; materialized BF16 output |
| `operator-output_projection-prefill` | operator | whole compiled dot with required layout/padding/output conversion; materialized BF16 output |
| `operator-normalization-prefill` | operator | complete RMSNorm envelope including gamma, epsilon, FP32 intermediates and output cast |
| `operator-residual_addition-prefill` | operator | two runtime operands through materialized residual output |
| `operator-ffn_up-prefill` | operator | whole compiled dot with required layout/padding/output conversion; materialized BF16 output |
| `operator-ffn_gate-prefill` | operator | whole compiled dot with required layout/padding/output conversion; materialized BF16 output |
| `operator-ffn_down-prefill` | operator | whole compiled dot with required layout/padding/output conversion; materialized BF16 output |
| `operator-activation-prefill` | operator | complete gated SiLU product envelope; no omission of multiplication by up |
| `operator-kv_write-prefill` | operator | only K/V append into materialized cache; consumes already rotated K, does not duplicate projection/RoPE |
| `operator-attention_fused-prefill` | operator | one paged QK/scale/causal-mask/stable-softmax/AV envelope from already rotated Q and resident logical KV inputs to BF16 O; no separate scores/softmax timings |
| `layer-b1-s1` | end-to-end | whole single-layer device interval with KV outputs materialized; encompass compiler fusions once; weights, input activation and prior KV preplaced |
| `layer-b8-s1` | end-to-end | whole single-layer device interval with KV outputs materialized; encompass compiler fusions once; weights, input activation and prior KV preplaced |
| `layer-b32-s1` | end-to-end | whole single-layer device interval with KV outputs materialized; encompass compiler fusions once; weights, input activation and prior KV preplaced |
| `layer-b1-s128` | end-to-end | whole single-layer device interval with KV outputs materialized; encompass compiler fusions once; weights, input activation and prior KV preplaced |
| `gather-p16-c2048` | DRAM gather | entire page-index lookup and materialized K/V gather interval; output is distinct HBM storage; no reduction added to this proposed boundary |
| `gather-p32-c2048` | DRAM gather | entire page-index lookup and materialized K/V gather interval; output is distinct HBM storage; no reduction added to this proposed boundary |
| `launch-minimal` | launch overhead | smallest non-eliminated device event containing this add, its input/output and device dispatch; host launch gap excluded; it measures minimal-kernel cost, not pure launch latency |

## Remaining work under the existing plan

| Item | Current status | Existing owner/boundary |
| --- | --- | --- |
| Native representation and selected execution | Installed and reviewed, with the limits above | U4b implementation; no new campaign here |
| Human L1 DMA and GEMM workings | Javid explicitly accepted the [DMA](../../L1_limits/hand/H-L1-DMA-01.md) and [GEMM](../../L1_limits/hand/H-L1-GEMM-01.md) workings as human-validated calculations using AI assistance | Human-working acceptance is recorded with exact attribution. Applicable simulator L1 evidence remains separately assessed; no new native pass or physical-chip validation is inferred |
| Final benchmark agreement and measurement observability | All 52 envelopes accepted by Javid; human acceptance replaces outstanding A/B signatures. Actual compiler/event/state correspondence remains unobserved | U5 measurement work, preserving prediction-before-measurement; mismatched envelopes are incomparable, not silently revised |
| Shape coverage and characterize interface | [Count-only regimes](u4b/shape-regimes.json) exist; old `uarch characterize` wording assumes a HardwareSpec, whereas installed reference uses TpuV5eReference | [Existing-API route](../../../docs/reviews/U4-closeout-reconciliation-v1/README.md) accepted by Javid; no new engine or invented physical fields |
| Prediction ordering | Implemented in the existing CI job; synthetic histories check strict ancestry and immutable bytes, including results without predictions | Original U-P9/U-P10 requirement. No current predictions or measurements; infrastructure alone does not close G3a |
| Prediction freeze | Not performed by U4 campaign or this document | [U-P9](../../../docs/prompts/U-P9-large-core-reference-and-frozen-predictions.md), before any measurement |
| Device kit, access and measurement | Not executed here | [U-P10](../../../docs/prompts/U-P10-large-core-measurement-and-the-ledger.md); hardware access/spend separately authorized |
| Remote/native/nightly and controlled-host qualification | Deferred under U0024 | Existing deferral; no local run is labelled a hosted or performance qualification |

The [human acceptance](../../../docs/reviews/U4-closeout-acceptance.md) resolves the U4
agreement and G3a scope decisions. Publication of the closeout tag awaits completed CI;
this is not permission to measure. The [reconciliation](../../../docs/reviews/U4-closeout-reconciliation-v1/README.md)
binds the accepted AI-assisted L1 workings to existing arithmetic/native evidence.
Optional trace output, runtime optimization and compatibility cleanup remain separate
follow-ups, not new prerequisites for accepting the installed implementation.
