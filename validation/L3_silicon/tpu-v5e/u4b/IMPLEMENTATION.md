# Implementation handoff for the same mapper and engine

Revision 2 uses the user-approved 52-unit implementation scope and the complete nominal
[model](MODEL.md), including numeric STUB estimates; the interface remains under review.
This reconciles [NATIVE-WORK](../NATIVE-WORK.md) against actual installed /4 code at
`c6438fe`. It replaces the old proposal's generic gaps with the following finite order.
It is not implementation acceptance, another engine or a sequence of per-field approvals.

## Installed reuse and exact deltas

| Existing seam | Reuse | R change needed |
| --- | --- | --- |
| `contract/uarch_contract/ordinary.py` | Data hashes, versioned software identity, strict closure, result checks | Add an explicit R format/capability after protected review; current scope is B only, production npu-l4/cold/BF16, source=None |
| `contract/uarch_contract/mapped.py` | TaskGraph dependency/coverage/lifetime vocabulary, original v2 source carriers | New reference hardware branch, MXU IDs, dtype/transfer/vector records, reuse v2 mathematical fields in an R closure without constructing a placeholder legacy HardwareSpec; existing vector enum/steady State are not execution support |
| `src/rkuarch/workload/ordinary.py` | Ordinary job assembly and packaging | Currently calls component completeness, BF16 and clocked hardware projection. Dispatch completeness and hardware resolution by the new model, never skip them |
| `src/rkuarch/mapping/component.py` | Deterministic graph assembly, topological dependency handling, explicit buffers | Extend the same mapping entry/module with a versioned R policy: 1 shared core/4 MXUs, M/N/K tiles, accumulator reuse/spill, vector/fused units, exact page spans; do not remove bounds and reuse old placements |
| `src/rkuarch/workload/{producer_v2,prepared_v2,capacity_v2}.py` | Rotary coefficient/position and cache-key binding, complete mathematical graph and known capacities | Select one decoder group with correct repeat/edges, no forced head/tail. Add required microbenchmark vocabulary and INT32 storage; bind the supplied exact coefficient bytes from inputs/. Whole-model analytic bundles are not native sources by themselves |
| `native/crates/uarch-engine/src/{component,component_admission,component_accounting}.rs` | Kernel/event wheel, resource queues, dependencies, observed completed work, allocation lifetimes and deterministic event ordering | Explicit R admission and service branch in the same engine; separate matrix owner from core; vector/scalar work, aggregate HBM, partial sums and priming. `TaskKind` today has only Compute/Dma/Unicast/Barrier; Compute only carries M/K/N |
| `src/rkuarch/verification/component/` | Packaged independent arithmetic/observation/checker design, retained issue-edge causes | One model-dispatched checker, R laws and records added; no importing native calculated durations as expected answers. B's phase/32-cycle laws must not validate R |
| `src/rkuarch/engines/native/ordinary.py`, Rust ordinary boundary | Bounded process transport, data validation and saved replay | New schemas/dispatch shipped with package, reference refusal before events, complete result validation; preserve version/hash provenance without executable approvals |
| Analytic `rotary_v2.counts` and U-C0 paths | Existing work conventions and aggregate/per-op baseline structure | Not an independent oracle and not a reference timing source. Add INT32/memory/scalar envelopes and missing precision conversions if used; use the proposed nominal STUB resolver/profile, preserve old profiles, and complete first-consumer checks before prediction |

## Finite implementation sequence

1. **Install reviewed semantic changes, then reference admission.** The owner reviews the
   combined model/contract proposal in `protected-amendments.patch`. Implement the scoped
   carriers and generated schemas under normal human ownership/U0002 procedures. The nominal
   model supplies all required values, including permitted numeric STUBs. Reference production
   refuses genuinely missing fields, unsupported precision/work, false source joins,
   invalid placements and budgets before dispatch. Keep /4 and npu-l4 regression behavior.
   Do not install this preparation patch as authorization to execute reference predictions.
2. **Matrix and mapping.** Implement M/N/K tiling for the six shapes and seven projection
   families. Use the proposed 128-wide physical K/N slices and M chunks <=1024; partial windows
   are VMEM-backed and charged to shared capacity/traffic. Follow MODEL exactly, not a
   future unspecified timing law. Actual compiler correspondence remains unobserved.
   Stable lexicographic tile allocation across MXU 0..3; shared local-memory capacity, no
   per-MXU VMEM replication. K tiles accumulate into one live logical output with the
   explicit VMEM partial stores/reloads defined in MODEL; an additional spill is separately
   mapped and accounted. Convert once at the final K
   boundary. BF16→FP32 and raw INT8→INT32 have distinct work/storage/service semantics.
   Validate sizes before allocating events; raise meaningful resource refusals, not silent
   retile. Bound graph expansion: a 256 MiB stream must not require one record per guessed
   256 B hardware request. Coalesce declared logical spans and keep tail information.
   ARITHMETIC records the installed 64 MiB wire caps and concrete request-count expansion;
   size finite R budgets with actual serialization, without removing required rows.
3. **Vector and complete decoder.** Add explicit arithmetic, reductions, special functions
   and casts for RMSNorm, gated SiLU, residual, stable attention and RoPE. Reuse v2 rotary
   pairing/numeric policy/coefficient identities. Preserve all conversion boundaries even
   under fusion. QK/AV map to matrix work; stable softmax owns FP32 reductions and exp/divide.
   Retain causal useful versus padded/dense issued work separately. Full-layer graph has
   two norms/residuals, one Q/K rotation each, append before attention, FFN up/gate product
   before down; omitting any contribution refuses completeness. No embedding/head required. Reuse the supplied coefficient/page-index data; keep
   generation outside execution/replay, and do not construct a dummy legacy HardwareSpec.
4. **Memory, KV and minimal kernel.** Implement read+reduction, runtime fill, real copy,
   reverse-page gather, valid-tail append and scalar add in the same TaskGraph path. Page
   indices and allocation versus useful bytes are explicit. Rotated K is stored once; V is
   unrotated; GQA can share cache data while executing four query heads per KV head. Copy
   source/destination aliases refuse the selected unit. Aggregate HBM arbitration and
   request latency/concurrency are model inputs, not physical-channel guesses. Include the
   observable scalar output and device-startup law for the launch unit.
5. **Steady state.** Preserve only declared SMEM metadata across priming and reported
   iterations under the nominal reload policy; restore the fixed logical invocation. Counters/attribution include only the reported
   iteration. Scratch allocation/credits must not leak; KV valid length must not grow.
   Compare one versus two primes at every selected point, report mismatches with their
   cause; fixture_resident is not evidence of convergence. Match whatever device retention
   procedure is later established. No new mandatory device warm-up/sample counts.
6. **Independent verification and integrated milestone.** At each seam use small literal
   cases below; after the interface is installed and implemented, run the approved selection
   through the ordinary shipping boundary. Three repeated fresh-process runs, debug/release equality,
   producer-disabled saved replay, altered hashes/coverage/tails and malformed results must
   discriminate. Extend the one packaged checker and qualify critical-path attribution:
   interval parts sum to duration, cause identity and overlap/serialization are independently
   checked. Apply appropriate existing L0/L0m/L1, overflow/capacity/lifetime and credit tests.
   Synthetic laws prove implementation of those laws, never TPU accuracy. No full table,
   second policy, exhaustive historical campaign or CI polling.
7. **Prediction/measurement join and remaining ownership.** Reconcile exact compiled units,
   runtime pins, state, shape characterization and both lane signatures before U-P9.
   U-P9 owns `validation/L3_silicon/check_ordering.py` and its synthetic histories/CI join;
   prepare it once before freezing (result-before, same-commit, valid strict ancestor,
   missing prediction and immutable-prediction cases). U-P10 consumes it and owns its kit,
   not a duplicate ordering checker. Existing SUITE's U-P10 ownership sentence is corrected
   by the pointer to this package. Actual prediction generation is U5 only. Human L1 GEMM
   and latency-bound DMA workings/review remain human work, independently available now.

Steps 2–5 proceed together once this semantic interface is accepted, using its nominal
STUB values. No published-internal-parameter prerequisite remains. Keep TPU v5e. This is
one substantial implementation milestone with appropriate seam tests and integrated
independent verification, not an A/B handoff chain. See ARITHMETIC for further independent
layout, reduction, service, staging and state examples; no second engine is introduced.

## Small independent examples to settle interfaces

These are agent arithmetic specifications for future tests, **not the human L1 worksheets**.
[check_package.py](check_package.py) executes only these count identities and document checks.
It does not invoke an engine, return a predicted duration or certify native support.

| Case | Literal expectation | Discriminating fault |
| --- | --- | --- |
| BF16 M=3,K=5,N=7 dot | 105 MACs / 210 matrix ops; X=30 B, W=70 B, Y=42 B; FP32 live accumulator=84 B | Count padded work as useful; use BF16 accumulator size |
| Same raw INT8 dot | 210 integer ops; X=15 B, W=35 B, Y=84 B; INT32 accumulator=84 B; no scale bytes | Reuse BF16 output width or attach decoder quantization |
| M=3,K=130,N=7, split K=128+2 | 2730 MACs / 5460 ops; X=780 B, W=1820 B, Y=42 B; same 84 B accumulator across both K tiles; one final output store | Convert/store both partial outputs as final results; drop K tail or duplicate it |
| BF16 RoPE B=S=1,Hq=2,Hkv=1,D=R=4 | 12 elements; 36 arithmetic ops plus 24 casts; X read=24 B, Y write=24 B; logical coefficient reads=32 B across Q/K operators, unique shared coefficient row=16 B | Cast counted as arithmetic only; coefficients broadcast per head without declared reuse; rotate V |
| Full workload decode Q/K RoPE B=S=1,R=128 | 5120 elements; 15360 arithmetic ops plus 10240 rotary casts; projection final-output casts remain additional | Deduplicate projection rounding because projection and rotary share an envelope |
| KV p=16,C=17,Hkv=2,D=4 BF16 | Valid K+V payload=544 B; two allocated pages hold 1024 B; append one token=32 B; gather read=544 B and output write=544 B; two int32 page entries add 8 input bytes | Round useful payload to full allocation; forget output materialization or page indices |
| GQA B=1,Hq=4,Hkv=2,S=1,T=3,D=2 | QK+AV=96 matrix ops; K+V unique BF16 payload=48 B; query/O each=16 B; conventional softmax=60 ops | Multiply KV payload by Hq/Hkv without a mapped copy; omit one matmul |
| Causal B=1,Hq=2,S=T=3,D=2 | 12 useful pairs, 96 QK+AV ops, 60 conventional softmax ops; dense issued work may exceed these | Apply triangular masking to decode S=1,T=3; treat masked dense work as no execution |
| Memory read E=4 BF16 | Read=8 B, four widen casts, three FP32 sum adds, write=4 B | Report only input bytes and call the reduction free |

Additional behavior expectations under the proposed timing laws: same MXU tiles serialize;
different MXUs may overlap only where shared issue/staging permits; four active MXUs cannot
independently exceed the declared chip rate. An infeasible imported mapping refuses after an accumulator-window reduction. Compare
a mapper-prepared explicit spill counterpart for the same mathematical work/policy and
verify the extra local traffic and non-shortening expectation; never silently retile at runtime.
Halving DMA outstanding capacity must not improve a latency-bound synthetic stream.
These fixtures use explicit synthetic parameters, not TPU estimates and not a production
`--test-only` workaround. Check zero-duration edge handling, same-time credit releases,
incorrect blocking causes and restored baselines with the existing corrected ordering.

## Tests worth reusing, with their actual scope

- `tests/unit/test_u4_a_component_mapper.py` and `test_u4_component_mapper_v2.py`: explicit
  mapping/lifetime literals. Old profile/registry fixtures are historical /3 development
  scaffolding, not requirements to restore in R.
- `tests/unit/test_ordinary_native.py`, `tests/native/test_ordinary_process.py`,
  `native/crates/uarch-engine/tests/ordinary.rs`: /4 transport, ordinary versions/data
  integrity, refusal, replay and independent result checking. Extend analogous R cases.
- `native/crates/uarch-engine/src/{component_tests,component_admission_tests}.rs` and
  `validation/component/`: resource/credit/issue/lifetime and accounting discrimination.
- `tests/rotary_v2/test_{boundary,pairing_reference,adversarial,preparation}.py` and
  `contract/tests/rotary_v2_cases.py`: literal rotary/causal/count and producer-disabled
  replay inputs. These currently verify analytic/preparation behavior, **not native R**.
- `validation/L0_invariants`, `validation/L0m_metamorphic`, `validation/L1_limits`,
  `validation/analytic_checks.py`: select applicable identities/limits and first-consumer
  analytic baselines. New R expectations must not call production counters as their oracle.

No test results in this package are inherited as new passes. The work changes preparation
artifacts only, so no Rust rebuild, native test campaign or analytic duration generation
is justified here. U0024 still defers native hosted/nightly/performance qualification;
independent review of implementation, human worksheets, G3a and U4 closure remain pending.
