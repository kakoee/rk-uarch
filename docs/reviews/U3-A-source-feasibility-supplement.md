# U3 Lane A: source feasibility and decision supplement

Status: **PROPOSED; feasibility blocked; no U0005 acceptance or G2 result.**
Javid (@jjaffari) is the acting human decision-maker for both lanes. Reza has not
approved anything and remains unavailable. This supplements, without rewriting,
[pre-registration](U3-U0005-proposal.md), [expectations](U3-G2-physical-expectations.md)
and [prior handoff](U3-A-planning-handoff.md), introduced by
`f581b50da69ff9b75b0c6c7a68342da647270200` and
`c7fcb6f9a49dcc5afadc93d452151b1c4e8b92f7`.

Lane A fetched and fast-forwarded its own clone/main to
`89d5d6aff5f9735a219ebc7d63a86fa2fe420e21` before this inspection. B's
[analytic preparation](U3-B-analytic-preparation-handoff.md), including tests at
`42eb1691ed29bf9ba7d129ac8e63a7bce5744e98`, is preserved. Coordinator receipt and
independent arithmetic reconciliation are evidence about the planning documents,
not independent U-REVIEW, simulator execution or gate acceptance. U2's annotated
`u02-end` still peels to `79bc1f014306e520aacba3491d60ae6c644b26a8`.

## 1. Feasibility before interface design

All upstream references below are pinned: **O** = [ONNXim
`a1e86296e080fa1c82f8ad3f1b6de1079c192afc`][O]; **P** = [PyTorchSim v1.0.0
`5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3`][P]. Source was inspected read-only;
no candidate code was built, imported or executed. The two papers were read in full
for the preceding proposal; their compatibility/performance claims do not establish
physical G2 evidence. Paths in the table resolve within O or P, not moving upstream.

Three quantities must remain separate: (1) independent counts over declared physical
prepared extents, including explicit padding/replication and repeats; (2) work
actually executed and completed; (3) additional issued tile/lane/transaction work.
An input-shape formula proves only (1). Counters of instructions or simulated cycles
prove neither scalar work nor complete correspondence. No expected value may be
inserted as a missing observation, and no unknown/Dummy/CPU-fallback path can pass.

| Mandatory work / binding | O: actual source path and obstacle | P: actual source path and obstacle |
| --- | --- | --- |
| Q/K/V, output projection; FFN up/gate/down; once-only lm_head | `src/operations/OperationFactory.cc:24–61` maps Gemm/MatMul to GemmWS, which generates matrix instructions. Native `src/models/LanguageModel.cc:159–367` combines QKV and up/gate, adds biases and starts from hidden activations; it never executes embedding, initial pre-attention RMS norm, final norm or lm_head. The declared `LmHead` string is not an executed head. Exporting separate Gemms could represent matrix extents, but cannot rescue the missing nonmatrix work below. | `PyTorchSimFrontend/mlir/mlir_lowering.py` maps mm/addmm/bmm to GEMM/BMM templates; `mlir_gemm_template.py` emits tiled `linalg.matmul`. `tests/Mixtral_8x7B/model.py:119–125` does call final norm/output, but receives hidden activations, not token IDs. Backend `TileGraphParser.cc:563–576` creates COMP from supplied latency/type, with no scalar matrix extents. Matrix templates alone do not establish executed per-op counts or a complete diagnostic. |
| Fused QK → softmax → AV; GQA | O `Attention.cc` emits QK/AV GEMM and vector instructions with SRAM logits; this is a real path to inspect, not proof of parity. ONNX constructor sets `_nkvh=_nh`, not the prepared 32:8 ratio. Native path passes `heads_per_kv` as `num_heads` (`:108–139`); `:358` asserts `num_heads <= _nkvh`. Proposed tp8 gives 4 <= 1, false with assertions enabled. Disabling assertions does not validate the indexing or semantics. Stop this route, no assertion removal. | Example calls `F.scaled_dot_product_attention` after repeating KV heads (`tests/Mixtral_8x7B/model.py:177–181`). Separate BMM/softmax/BMM lowering and ordinary fusion examples do not demonstrate the required QK-softmax-AV fusion with no score/probability DRAM tensor. No verified fused execution path was established at this pin; generic PyTorch compatibility is insufficient. Do not substitute unfused attention or claim its mapping equivalent. |
| kv_write; valid-token paged KV reads | Native O `KVCacheConcat.cc:57–76` grows contiguous cache dimensions by input length; ONNX constructor throws “Not implemented”. The native tile is marked skip, and the write-address code uses the key tensor for both K/V. `Attention.cc:100` derives attended length from the grown key tensor. There is no page-table/valid-token binding matching the prepared policy here. Starting with S then appending makes S+1; choosing S−1 privately changes the input. | Example `KVCache.update` (`model.py:80–91`) uses `torch.cat`, not paged append. No supplied block table, valid-token length or per-page mask binding is present. Generic indirect indexing is not evidence of this path; KV repetition can also materialize extra physical traffic. Stop the example route rather than infer paged support. |
| attention_norm, ffn_norm, final_norm; two residual adds | U2 execution assumptions explicitly select `rms-6md/1`. O `SkipLayerNorm.cc:108–144` issues LAYERNORM then ADD and does not issue the RMS weight work required by that assumption; the native graph places these after attention/FFN and omits final norm. Factory lacks generic RMSNorm/Add support: unknown operators become Dummy. A differently named norm is not an acceptable replacement. | Example RMSNorm (`model.py:203–213`) computes mean-square/rsqrt in float then casts and scales; block forward has both residual adds. Generic reductions/elementwise operations lower through `mlir_codegen_backend.py`, then compiler-generated compute latencies. These are plausible source paths, but generated instruction/traffic correspondence, dtype roles and absence of host fallback remain unverified. |
| SiLU × gate activation | O native BiasAct halves the doubled FFN output and emits SWISH plus MUL, but also emits bias MOVIN/ADD unconditionally in `BiasAct.cc:82–159`. `SystolicWS.cc:150–153` labels SWISH TODO and uses GELU latency. Factory offers BiasGelu/FastGelu, not a faithful SiLU/gating graph route. Do not repair this physics to gain parity. | `tests/test_activation.py:67` expresses `F.silu(gate)*x`; generic elementwise lowering is a candidate path. That example is not proof that both prepared projection terms and the gate multiply survive compilation, or that the emitted work uses the declared precision. |
| Embedding with rank-local hit vector | O `EmbedLayerNorm.cc:57–65` produces a skip tile with no instructions. Generic Gather goes to Dummy. Native LM omits the gather. Zero matrix ops does not excuse missing reads/output. | `tests/test_indirect_access.py:32–46` defines a compiled embedding example, but its main invocation is commented out; the Mixtral caller embeds outside the shown transformer. `extension_device.cpp:275–309` includes CPU fallback for index and other operations. There is no prepared conserved-hit-vector/rank binding or evidence that zero-hit and nonzero-hit cases execute correctly in the simulator. |
| RoPE | **U2 boundary gap:** `contract/uarch_contract/operators.py` has no RoPE operator and `workload/prepare.py:175–270` emits none. O factory has no RoPE execution path. The prior expectation prose naming RoPE as work to preserve does not create captured RoPE work. | The example actually calls `apply_rotary_emb`, explicitly marked dummy and returning `x*freqs_cis` (`model.py:226–228`). The adjacent `apply_rotary_emb2` contains paired rotation arithmetic but is not the called function. Switching functions or inserting RoPE is not authorized. Human semantic disposition is required; neither invent it in translation nor silently declare it an accepted omission. |
| Precision | O `SimulationConfig.precision` is a global byte width; Tensor sizes and timing use it. `full_precision` is another width, not a proof of BF16 operands/FP32 accumulation. Cast explicitly becomes Dummy. Independent weight/activation/KV/accumulator roles have no established faithful path. | `mlir_common.py` names bf16/f16/f32, and low-precision reduction initialization promotes to f32. But BMM template `:31–47` hardcodes f32 reinterpret/initialization alongside DATA_STYPE, and GEMM uses one DATA_STYPE for input/output. Exact BF16/BF16 plus FP32 accumulator coverage is unresolved; dtype names alone do not pass. FP8 remains refused under this diagnostic. |
| Group repeat, work_repeat, rank shapes | O native config divides heads/widths by tp and optionally simulates one layer; it is not a replay consumer of already resolved extents. Replicated KV where Hkv<tp would floor to zero. It has no arbitrary prepared group/work-repeat or embedding-hit binding. Never divide imported shards again or extrapolate one layer to a measured full model. | Python layer loops and compiler loop nodes can repeat work, but have no U2 group/work-repeat/rank identity. Static shape specializations require their own compiled work. No evidence binds padding, KV replication, vocabulary tail or unequal embedding ranks to complete execution. |

Evidence entry points: [O factory][OF], [O native LM][OL], [O attention][OA],
[O operation implementations][OO], [O vector timing][OS], [P lowering/templates][PM],
[P example][PE], [P parser][PP], [P CPU fallback][PF]. O's unsupported export path
and native LM route are stopped. P's supplied model route is stopped; its generic
compiler route remains unproven, not a demonstrated impossibility for every future
program. There is **no feasible complete route established for this pre-registration**.
This is a source feasibility finding, not a measured “both failed G2” decision and
not permission to start the execution-plan fallback. No simulator extension is proposed.

The independent 12 count rows, tiny total 928, padded total 1024 and parameter counts
remain the [expectation specification](U3-G2-physical-expectations.md), as reconciled
by the coordinator. Its zero-matrix work still requires observable execution/traffic.
Tiny adversarial shapes are refusal/coverage discriminators, not extra timing points.

## 2. Native outputs, equality and instrumentation decision

| Native source/output | Fields and units actually present | Limit |
| --- | --- | --- |
| O stdout via spdlog: `Simulator.cc:203`, `Core.cc:218–231`, `SystolicWS.cc:170–175` | `Simulation Finished at … cycle … us`; `MatMul active cycle`, `Vector active cycle`, idle/bubble cycles; utilization in percent; `Systolic Inst Issue Count`, `Systolic PRELOAD Issue Count` in instructions. | No native per-prepared-op integer MAC counter. Core's matmul statistic is tile-volume divided by array area (`Core.cc:285–291`), not scalar operations. Trace tile m/k/n lacks sufficient complete op/mask correspondence. `Stat.h` declares structs; it is not a serialized stats file. |
| O Ramulator1 `./ramulator.stats` (`extern/ramulator_custom/src/Ramulator.cpp:31,118–120`) | `Memory.h` registers `dram_capacity` bytes, `dram_cycles` and `ramulator_active_cycles` DRAM cycles, `incoming_requests`, per-core `read_requests`/`write_requests`, per-channel requests, `maximum_bandwidth` B/s. Controller adds further fields. | This is DRAM-only, configuration dependent; request counts are not valid payload bytes or matrix counts. `StatType.h:99–116` conditionally omits non-displayed/zero fields. Ramulator2 instead calls each channel's `print(stdout)` (`src/Dram.cc:197–200`); do not pretend it writes this same file. No complete candidate-wide deterministic stats file is established. |
| P captured backend stdout: `Simulator/simulator.py:241–250` | Default file `<model-directory>/backendsim_result/<len(directory)>`, overridable result directory. Backend `Core.cc:418–439`: opcode `inst count`, `skipped inst count`, COMP split GEMM/Vector (instructions); systolic/vector/TMA active/idle cycles, utilization %, DRAM BW GB/s and response count, NUMA hit/miss counts, total core cycles. `Simulator.cc:294`: `Total execution cycle`. | GEMM instruction count is not MAC count; no per-op dimensions/masks. The Python result parser still looks for older O-style MatMul/utilization strings, so its selected result dictionary is not a complete authoritative record. Numeric filenames also depend on previous directory contents. |
| P offline Gem5 `m5out/stats.txt`, `m5out/sto.log` (`Simulator/simulator.py:161–189`) | Consumer reads `system.clk_domain.clock` (tick period per clock) and `system.cpu.numCycles` (cycles), dropping the final cycle-list entry. Backend COMP receives precomputed cycle/type. | External Gem5 asset revision is missing, so its complete fields, units and nondeterministic host statistics cannot be frozen from this repository. Offline latency preparation is part of the proposed timed invocation, not free preprocessing. |

Both entry points use default spdlog formatting, whose pinned
[v1.11.0 full formatter][SL] emits wall date/time to milliseconds. O `main.cc:127–128`
also emits elapsed host seconds and tiles/second; P `main.cc:152` emits host seconds.
P frontend diagnostics include host paths/addresses and progress output. None of
these can be certified byte-identical. The captured backend log is itself mixed
stats/host content; merely stripping timestamps or selecting stable counters would
violate the current proposal. Ramulator-only equality cannot establish whole-run
work. No three-run equality can presently be claimed from native complete outputs.

**Separate instrumentation proposal, not authorization:** if a feasible route is
later identified, seek approval for observation-only emission at actual instruction
issue/completion and memory request/response sites. O scope would be Core matrix/
vector completion, load/store handling and stable existing tile/layer identity;
record opcode, actual tile extents, execution multiplicity, precision/config identity,
completed versus skipped status, and request sizes. Full attribution to prepared ops,
including Q/K/V and up/gate inside fused native nodes, must be demonstrated rather
than assigned from expected counts. P backend COMP lacks these extents: backend-only
logging cannot create them; exact compiler/kernel provenance and executed masks would
also be needed, with external tool pins. That is a separate feasibility/authorization
question, not permission to implement a compiler extension.

A future approved observation record must expose completed integer 2×MAC per op,
issued padding separately, and nonmatrix/traffic evidence. A stable emission order
and complete deterministic simulation-statistics output would need prospective file/
field/version registration; raw mixed logs and all host telemetry remain preserved.
No output sorting, stripping, rounding or oracle substitution after execution. No
changes to timing, scheduling, op generation, memory addresses, precision, masks or
physics; instrumentation cannot cure the semantic blockers above. B must test missing,
duplicated, swapped, skipped and padded work and source/record correspondence before
accepting any such evidence. Until those decisions, stats equality/observability block G2.

The existing procedure remains prospective: identical captured inputs/image/config/seed 7,
three fresh processes and fresh output directories in fixed point order, identical internal
paths, cleared per-point compilation caches, no forced OS cache drop, no overlap with
builds/nightly. Each invocation includes validation through statistics parsing. At 200 s
terminate its whole process tree, then kill after at most 5 s cleanup; timeout fails regardless
of cleanup time. Preserve partial/raw evidence and distinct crash/OOM/refusal/interruption
outcomes; no successful partial parse or automatic rerun to erase failure. Compare complete
predeclared stats bytes plus parsed results, not only expected counts. This procedure is not
runnable under the current unresolved stats and host conditions.

## 3. Boundary questions blocked on feasibility

No complete new interface/schema is designed while no route qualifies. Existing
[U2 APIs and ownership](U3-U0005-proposal.md#6-ab-interfaces-and-concrete-human-decisions)
remain authoritative: `PreparedBundle` is `uarch-prepared/1`, `mapping_scope=analytic_ops`;
`validate_execution_bundle` enforces analytic-ops@1/C0; `prepare_engine_job` binds an
analytic identity; `EngineResult` enforces roofline/null detailed telemetry; `capture`
executes all points and has no fork injection. Preserve saved U2 replay and public
analytic capture → table → report. Do not weaken a validator to insert a candidate.

Questions for Javid and B, to resolve only against an identified faithful route:

- Which versioned prepared/execution variant can preserve bundle and selected point hashes,
  hardware/intent/assumption identities, rank/equivalent-rank/hit metadata, every op/group
  ID, repeat, physical operand dtype/layout/extent, padding/replication, mask and KV access?
  RoPE's absence requires explicit human semantic disposition, not an adapter default.
  Preserve the already selected RMS semantics; do not reopen them as a new policy.
  Changes to protected carriers require a human commit.
- How will source/patch revision, immutable image digest, exact configuration/preset bytes,
  tool/compiler/latency-input identity and delegated mapping be bound to that point? No
  image exists. Delegation must refuse an exact imported mapping it cannot honor and
  cannot be reported as mapping equivalence. Unsupported precision/fusion/page/rank/repeat,
  nonmatrix work, state mode and missing attribution must fail closed before launch.
- How will a separate result validator check complete observed work, integer units,
  determinism/completion and honest null/unsupported outcomes without reusing analytic
  roofline equations as simulator evidence? A owns future engine/config/translation;
  B owns report/provenance and verification closure. B must reconcile U0006 capability
  wording, DMA control volume, clock/queue premises, and canonical source-report payload
  under VerificationRecord, as listed in its handoff. Busy-cycle sums cannot masquerade
  as critical-path attribution. No private evidence ledger or invented review.
- How will point-select diagnostic execution coexist with U2's required decode+prefill
  grid and once-only head/tail work? B/Javid must agree coverage and warning semantics.
  A/B must coordinate concrete shared-file diffs before editing. Bound input changes
  retain U0002 human generation/adoption and strict support currentness.

## 4. Licence/dependency decisions before any image

The [original pin table](U3-U0005-proposal.md#3-candidate-pins-full-paper-reading-and-licence-dependencies)
retains source identities. Pinning a repository is not proof of a reproducible or licensed
image. No image was pulled, built or scanned, and no dependency was installed here.

| Exact unresolved item | Proposed disposition for Javid; evidence still required |
| --- | --- |
| Both Conan files: boost/1.79.0, robin-hood-hashing/3.11.5, spdlog/1.11.0, nlohmann_json/3.11.2 | Freeze recipe/package revisions, target settings and transitive source identities/notices, including bundled fmt. Boost's [BSL-1.0][BL] is outside the current literal allow-list. Propose an explicit BSL-1.0 exception for this exact closure only; no exception has been granted and no allow-list changes are made. |
| O Ramulator2 FetchContent yaml-cpp `yaml-cpp-0.7.0`, spdlog `v1.11.0`, argparse `v2.9`; P distinct Ramulator2 gitlink | Resolve tags to immutable commits, all nested fetches and corresponding notices before build. Audit P's own transitive closure rather than transplant O's pins. Vendored Ramulator1 is linked by both CMake recipes and needs complete notices even if runtime selects Ramulator2. |
| P root at `5ec17f…`; STONNE `97804185f00e98e56f74638e4282b9aecab8cfce`; BookSim `1d69c9d9db190d130087471b373d12ed4605bf6e`; both torch2timeloop gitlinks in prior table | Obtain exact grant/notice coverage for P root and STONNE (no root licence found), audit every compiled/incorporated BookSim wrapper beyond the two BSD-noticed source files, and establish torch2timeloop use/licence. STONNE is linked by P CMake even for a proposed dense path. A paper's MIT statement or cpptoml's MIT header cannot license the rest. Unknown grants are blockers, not proposed permissive exceptions. |
| O Dockerfile: `ubuntu:20.04`, apt packages, CMake 3.22.0 tarball, Python wheels (including unpinned onnx/onnxruntime/torchvision/optimum) | Missing base digest, apt snapshot/exact versions, archive checksum, wheel versions/hashes and complete transitive notices. Named conan1.57.0/transformers4.40.1/torch2.3.1 are not complete locks. |
| P Dockerfiles: `torchsim_base:latest`, `pytorch:2.2.0-cuda12.1-cudnn8-runtime`, externally supplied GEM5_ASSET_ID/LLVM_ASSET_ID, moving Spike `TorchSim`, RISC-V nightly archives 2023.12.14, apt/pip | Need both base digests, asset IDs plus source revisions/build recipes/checksums, Spike commit, toolchain source closure/notices and package locks. riscv-pk is already pinned at `4f3debe4d04f56d31089c1c716a27e2d5245e9a1`; its incorporated components still need review. Never supply credentials or fetch binaries merely to fill this table. |

Proposed scan scope: all candidate/submodule/vendored and generated/linked/header-incorporated
code; compiler/runtime libraries and offline latency tools; build-stage and final image
layers with base OS/Python/transitive packages; notices accompanying artifacts. Distinguish
build-only tools, runtime linkage and distributed contents with evidence. No broad source
file manifest or copied checkpoint tree is requested. Source pins, lock/download identities,
necessary notice records and eventual actual-image inventory suffice.

Known outside-list BSL requires human disposition. Recipes also name GCC/GNU toolchains
(GPL-family tools/runtime exceptions), glibc (LGPL-family runtime), and P's CUDA/cuDNN base
(non-allow-listed vendor terms); exact versions/incorporation and notices are **unverified**.
The existing narrow LGPL tool allowance does not automatically cover these. Propose a human
scope decision separating unmodified build tools from linked/runtime and redistributed
components, then narrowly identified exceptions if acceptable. Otherwise the recipe remains
blocked. A CPU-only recipe is a future option requiring proved closure, not an automatic
fallback or permission to remove/replace dependencies. No legal-compliance conclusion.

## 5. Host, unchanged budget and effort

Javid's reported native preflight for `javid@152.53.209.203` found **12 logical CPUs**,
**MemTotal 32,863,040 kB (~31.3 GiB)** and **962,551,283,712 bytes free in home** at that
time. These are reported observations, not this session's measurements. Physical-core/SMT
topology, current free capacity/load, cgroup delegation and exclusive allocation remain
unverified. Python3.12.14, uv0.12.13, Rust/cargo1.99 and tmux are reported available;
Podman/Docker and newuidmap/newgidmap are absent. Subordinate-ID ranges alone do not establish
a working rootless runtime. Runner state is unverified and nightly paused.

Rootless Podman remains a **proposal requiring administrator provisioning** and verified
user namespaces, OCI runtime/storage and delegated resource enforcement. Requested allocation
remains one pinned physical core without sibling contention, one process tree/thread/table
worker across both lanes, 24 GiB RAM and 100 GiB scratch; build at most two jobs in a separate
window. None is reserved or granted. Twelve logical CPUs do not establish twelve physical
cores; total memory and historical disk free do not establish available reservation capacity.
No root access, installation, privilege workaround, alternate host or waiver is authorized.

Keep **200 seconds per run** unchanged: 168 points/precision × two precisions = 336 intended
table points, 86,400 s envelope minus
20% reserve = 69,120 s; /336 = 205.714… s, rounded down prospectively. This is a planning
allocation, not a demonstrated table cost. Mandatory candidate diagnostic remains 14 decode
rank/point cases × three runs for synthetic `g2-8b-shape-1layer`, BF16/BF16, not the full
32-layer 8B model, not FP8 coverage and not proof of a 24-hour full-model table. The 42-run
ceiling is 8,400 s before failure cleanup/build; no measurements have tuned this threshold.
Any changed diagnostic or cost scope requires a new explicit prospective decision.

Remaining bounded decision preparation estimate: A 4–8 h for agreed source follow-ups and
exact proposals; B 2–4 h for boundary/evidence reconciliation; separate human/reviewer
reading/decision effort 2–4 h. These are estimates, not time already spent. Prior A 64–112 h
ONNXim and +32–64 h PyTorchSim implementation estimates are **suspended pending a feasible
route**, not commitments that instrumentation can repair these blockers. Do not subtract
B's completed work from its prior estimate without B's re-estimate. Administrator setup
remains a separate provisional 2–6 h once available. Administrator, Javid decision, runner/
manual-nightly and independent-review **waiting times are unbounded and excluded** from
engineering hours and the diagnostic runtime budget.

## 6. Exact decision list and handoff

Javid's decisions are separate; accepting one does not grant the others:

1. **Feasibility/scope:** record the stopped O paths and blocked P route; choose a specifically
   bounded next source investigation or defer the fork. No automatic extension, relaxed
   coverage, C1 fallback implementation or measured G2 failure is authorized by this finding.
2. **Diagnostic/budget:** accept or amend the exact one-layer 14-point/three-run scope and
   prospective 200 s limit as such, separately from any full-model/table objective. U0005
   must be human-owned and committed before U-P5 or candidate measurement; this is not acceptance.
3. **Semantics/schema/evidence:** decide the RoPE gap and candidate feasibility first; then
   resolve §3 with B and separately approve or reject observation-only instrumentation (§2).
   No complete schema proposal or runtime changes proceed while these questions remain blocked.
4. **Licences:** decide exact BSL/scope exceptions, if any, and require missing pins/notices
   and actual-image closure before acceptance. Unknown licence coverage stays blocked.
5. **Host:** grant or revise the proposed reservation only after topology/current availability/
   cgroup checks and administrator provisioning; establish the online `uarch` runner and one
   green manually triggered nightly before U-P5. Reza's absence remains a dependency, not approval.

This session owns only this supplement. Original planning and peer files are untouched;
normal Git history/diffs carry the handoff. Applicable validation results are recorded below
before commit. No full suite is repeated for prose: B's published receipt reports 1420 passed,
29 explained skips at its analytic checkpoint, not a test result produced by this author.
No native/simulator/performance checks or independent review were attempted. The next dependency
is Javid's feasibility/semantic disposition, followed by the separately gated schema/licence/
host and accepted committed pre-registration work. **Stop here; U-P5 remains gated.**

Validation at integrated main `89d5d6a` plus this prose: ruff, both current CI mypy
commands (`src contract/uarch_contract scripts`; `--no-explicit-package-bases contract/tests`),
lint-imports (two contracts), prompt-sync/third-party pytest (6 passed, no skips), and
`vendor_rk.py --check` passed. Commands used `uv run --no-sync` against the existing environment;
no dependency synchronization/install. Local document references and Git whitespace/scope
were checked. No full suite rerun for prose; no new tests mirror this document. The final
session handoff supplies the enclosing commit ID; retrieve it with
`git log -1 --format=%H -- docs/reviews/U3-A-source-feasibility-supplement.md`.

[O]: https://github.com/PSAL-POSTECH/ONNXim/tree/a1e86296e080fa1c82f8ad3f1b6de1079c192afc
[P]: https://github.com/PSAL-POSTECH/PyTorchSim/tree/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3
[OF]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/operations/OperationFactory.cc
[OL]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/models/LanguageModel.cc
[OA]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/operations/Attention.cc
[OO]: https://github.com/PSAL-POSTECH/ONNXim/tree/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/operations
[OS]: https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/SystolicWS.cc
[PM]: https://github.com/PSAL-POSTECH/PyTorchSim/tree/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimFrontend/mlir
[PE]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/tests/Mixtral_8x7B/model.py
[PP]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimBackend/src/TileGraphParser.cc
[PF]: https://github.com/PSAL-POSTECH/PyTorchSim/blob/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3/PyTorchSimFrontend/extension_device.cpp
[SL]: https://github.com/gabime/spdlog/blob/v1.11.0/include/spdlog/pattern_formatter-inl.h#L932
[BL]: https://github.com/boostorg/boost/blob/boost-1.79.0/LICENSE_1_0.txt
