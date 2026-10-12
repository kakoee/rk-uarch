# Bounded source evidence and coverage

Status: source inspection only, 2026-10-12. O = ONNXim
`a1e86296e080fa1c82f8ad3f1b6de1079c192afc`; P = PyTorchSim v1.0.0
`5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3`. Existing `/tmp/u3-a-planning/ONNXim`
and `/tmp/u3-a-planning/PyTorchSim` checkouts had these HEADs and empty porcelain status.
No source was changed or executed. Below, **S** = source-supported (not runtime-verified),
**C** = contradicted by the inspected route, **U** = unproven, **X** = explicitly outside
this proposed diagnostic. Categories 1–5 have the meanings in [README](README.md).
A row with a supported building block does not establish the complete route.

| Requirement | Immutable source path/symbol | Status | Missing work / proposed category | Remaining proof |
| --- | --- | --- | --- | --- |
| Embedding and conserved local hits, including zero-hit ranks | O [EmbedLayerNorm::initialize_tiles][oe], [factory][of]; P [indirect-access example][pi], [CPU registrations][pf] | O **C**, skip tile/no instructions; Gather Dummy. P **U**, embedding invocation commented out | O requires new operator **4**; P rank/hit program **1** only if it compiles faithfully, otherwise **4**; observations **3** | Actual reads/outputs by selected rank, no fallback or inferred all-rank equivalence; zero matrix count does not imply no work |
| Q/K/V, output, FFN up/gate/down and lm_head matrices | O [LanguageModel::initialize_model][ol], factory GemmWS; P [tuned_mm/addmm/bmm][pl], [GEMM render][pg] | Matrix primitives **S**; O complete native graph **C**, missing executed tail; P faithful BF16 path **C** | Existing matrix shape translation **1** cannot cure missing operations/precision **4**; per-op completion **3** | Correct physical extents, separate up/gate and Q/K/V attribution, complete head, two ops/MAC |
| All three norms, two residuals, activation/gating | O [SkipLayerNorm][on], [BiasAct][ob], [SWISH timing][os]; P [RMSNorm/FFN example][pe], [elementwise codegen][pc] | O **C**, wrong/omitted norm work, bias operations, SWISH uses GELU latency; P primitives **S**, exact work **U** | O **4**, P potential **1** with observed dtype/work preservation; **3** observations | Accepted rms-6md/1 correspondence, scales/reductions/casts, both residuals; no eliminated required work or substitute normalization |
| Fused QK-softmax-AV, no score/probability DRAM spill | O [Attention::initialize_instructions][oa]; P example SDPA, BMM templates | O SRAM logits **S**, diagnostic GQA **C**; P required fused execution **U** | O indexing fix **4**; P new fused kernel/template, if necessary, **4**; choosing spill **5** | Addressed transfers/dependencies demonstrating fusion, all QK/AV and softmax work; no “FlashAttention” inference from SDPA spelling |
| tp8 GQA and local Q/KV heads | O Attention passes heads_per_kv, asserts num_heads <= _nkvh; native divides heads | O **C**: 32/8→local 4/1→heads_per_kv=4, assertion 4<=1 false; P **U** | Never disable assertion. Fix **4**; preserve local heads without TP reconstruction **1** | Valid GQA reuse and execution/traffic counts; repeated K storage must not be silently multiplied to Hq |
| Valid-token paged KV reads and new K/V append | O [KVCacheConcat][ok]; P [KVCache.update][pe] uses cat | Native O **C**, skip tile, contiguous cache, key address used for K/V; ONNX constructor throws. P example **C**, generic paging **U** | P page/mask translation **1** only if capability exists, else **4**; O **4** | Noncontiguous page addresses, C valid tokens not page-rounded capacity, separate K/V destination, one append; C17 discriminator |
| Incoming cache and positions | O Attention derives length from grown key; P example cache cat | **U** for full accepted state | Explicit incoming C−1 at decode, append one to C **1** only if supported; semantic repair **4** | Existing keys rotated under same profile; new token at C−1; cold microstate must not erase prior cache |
| Q/new-K RoPE placement, V unchanged | O factory; P [apply_rotary_emb caller and definition][pe] | O **C**, no operator; P example **C**, called x*freqs dummy | O **4**; new P adapter expression may be **1** only using proven existing primitives; required compiler fixes **4** | Projection→RoPE→attention/KV dependencies; no rotating cached C keys or V |
| Exact coefficients/profile, positions, pairing, partial R | P example generates BF16 coefficients, unused paired helper only adjacent | Example **C**; generic compiler **U** | Supplied FP32 bit patterns/row gathers and explicit pairing/tail program **1** conditional; unsupported lowering **4** | Both pairings, R<D, cache/profile mismatch refusals, producer-disabled replay, no inferred theta/scaling or constant-folded identity work |
| FP32 separately rounded RoPE arithmetic/casts and coefficient/tail transfers | O Cast Dummy; P [codegen][pc] has conversion primitives but no established end-to-end profile | O **C**, P **U** | Explicit supported program **1**, compiler contraction/precision/timing repair **4**, execution evidence **3** | Four multiplies/two add-sub per pair, no FMA contraction, BF16↔FP32 casts, full D I/O and coefficient bytes per Q/K/node/repeat |
| BF16 operands, FP32 matrix accumulation, storage vs throughput | O [Common precision][oc]; P [GEMM][pg], [BMM][pb], [LLVM GEMM][pgl], [config][pconfig] | O global width **U** for numeric roles; P inspected matrix routes **C**, hard-coded f32, config precision=4 | Changing datatype/strides/rates/accumulator is **4**, changing diagnostic to FP32 **5** | Typed buffers, instructions/accumulator, actual memory widths, hardware-supported BF16 rate; dtype dictionary alone proves none |
| Padding, KV replication, rank/equivalent-rank scope | O native head/width division; P compiler receives shapes but no prepared rank contract | Native O **C** for replicated KV flooring; P **U** | Import already resolved physical shapes **1**; unsupported representation **4** or refuse | Tiny 928/1024 cases; replicated K once per local KV head; physical vocabulary and FFN padding retained; no extra TP division |
| Group/work repeats, once-only head/tail | O native layer loop and run_single_layer; P layer loops/TOG loops | Loops **S**, complete prepared correspondence **U** | Identity/repeat translation **1**, dynamic attribution **3** | Decoder group repeat once, work_repeat once, embedding/final norm/head once; no full-model claim from one layer |
| Hardware/config, named DRAM, initial state, mapping | O [Common][oc], [Dram][od], [Sram][osram]; P [Dram][pd], [main launch][pmain], config | Knobs **S**, H1 match **U**; exact supplied mapping **X** for current boundary | Existing knobs **1**, config locks **2**; missing physics **4**, altered fidelity **5** | Exact direct-timing configuration, field inventory/warnings, empty microstate vs cache contents, optional steady priming; delegate explicitly, refuse exact mapping |
| Per-op completed scalar matrix work, vector/bytes | O [Core completion/statistics][ocore], [Systolic issues][os]; P [Core completion/stats][pcore], [parser COMP][pp] | Native required observation **U**; present instruction/cycle counters **S** | Completion/lifecycle/identity **3**; missing kernel provenance is not repaired by logging | Extents/masks and completion for every operator, issued padding and skipped/eliminated work distinct; no input-formula substitution |
| Lower-level input / latency provenance | P [TOGGenerator.generate_tile_graph][pt], parser COMP, main launch | TOG input **S**, independent faithful latency **U**; missing-cycle default **C** as acceptance evidence | Existing authenticated TOG serialization **1**; invented kernel/latency **4** | Exact compiler/kernel/instruction→latency→TOG correspondence; refuse missing cycles rather than use 10; no relabelled analytic engine |
| Duration and critical-path attribution | O [Simulator completion][osim], Core; P [Simulator][psim], Core | Total cycles **S**, critical-path record **U** | Observation **3**, future result validation **1** after schema decision | Cross-domain conversion, boundaries, dependency path summing to duration without adding overlapping busy times |
| Complete three-run deterministic statistics | Both mains and [P simulator capture][pr] | Operational logs **S**; present complete-byte equality **U**, elapsed-time log unsuitable | New direct stable emitter **3** and prospective protocol decision; parsing **1** | Predeclared complete outputs, raw logs preserved, no stripping/sorting/selected counters to pass; three actual runs |
| Prefill execution, FP8, MoE/PP/EP/CP, full-model/table timing | Existing diagnostic and v2 admission | **X** for candidate G2 proposal; seven prefill points remain prepared coverage | Adding/dropping gate coverage **5** | Separate admission/coverage/preregistration; no claim inferred from this decode investigation |

## Additional source sites behind the delta

P setup [Scheduler/scheduler.py:166–198][psched] registers MLIRScheduling. Its
[lowering][pl] calls the GEMM/BMM classes whose render options fix f32, independently of the
bf16 name in `mlir_common.DTYPE_TO_MLIR`. Alternative LLVM GEMM render options fix
`DATA_TYPE="float"`, `DATA_STYPE="f32"`, `DATA_SIZE=4`; it is not an established BF16 escape.
These are source contradictions for the inspected routes, not a claim about every possible
uninspected upstream/custom kernel. Stop adapter design rather than patch these constants.

P [TOG generator lines 212–227][pt] consumes the provided cycle list and inserts 10 on
exhaustion, then derives overlap. [Simulator/simulator.py:161–189][pr] consumes offline Gem5
cycles; [TileGraphParser:563–576][pp] creates COMP with supplied cycles/type, no scalar
matrix extents. A compiler-issued shape is insufficient unless dynamic execution/masks and
completion establish which arithmetic actually occurred. Source shape recomputation is an
expectation, not independent executed-work evidence.

O [CMakeLists][ocmake] explicitly adds `extern/ramulator_custom` and links ramulator1;
P [CMakeLists][pcmake] adds Ramulator2 and STONNE and links `ramulator`/`sstStonne`.
The prior “both link Ramulator1” claim exceeded this evidence. P's vendored tree still needs
inventory if distributed; this correction is not a licence clearance. P [Dockerfile][pdocker]
and [base recipe][pbase] leave compiler assets and base/dependency closure unresolved.

[of]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/operations/OperationFactory.cc#L24
[oe]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/operations/EmbedLayerNorm.cc#L57
[ol]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/models/LanguageModel.cc#L34
[oa]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/operations/Attention.cc#L108
[ok]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/operations/KVCacheConcat.cc#L10
[on]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/operations/SkipLayerNorm.cc#L108
[ob]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/operations/BiasAct.cc#L82
[os]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/SystolicWS.cc#L125
[oc]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/Common.cc#L54
[od]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/Dram.cc#L136
[osram]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/Sram.cc#L18
[ocore]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/Core.cc#L272
[osim]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/Simulator.cc#L203
[ocmake]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/CMakeLists.txt
[pi]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/tests/test_indirect_access.py#L32
[pf]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimFrontend/extension_device.cpp#L275
[pe]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/tests/Mixtral_8x7B/model.py#L80
[pl]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimFrontend/mlir/mlir_lowering.py#L23
[pg]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimFrontend/mlir/mlir_gemm_template.py#L201
[pb]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimFrontend/mlir/mlir_bmm_template.py#L251
[pgl]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimFrontend/llvm/llvm_gemm_template.py#L117
[pc]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimFrontend/mlir/mlir_codegen_backend.py
[pconfig]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimFrontend/extension_config.py#L6
[psched]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/Scheduler/scheduler.py#L166
[pd]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimBackend/src/Dram.cc#L52
[pmain]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimBackend/src/main.cc#L15
[pcore]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimBackend/src/Core.cc#L347
[pp]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimBackend/src/TileGraphParser.cc#L563
[pt]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/AsmParser/tog_generator.py#L212
[psim]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimBackend/src/Simulator.cc#L294
[pr]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/Simulator/simulator.py#L161
[pcmake]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimBackend/CMakeLists.txt
[pdocker]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/Dockerfile
[pbase]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/Dockerfile.base
