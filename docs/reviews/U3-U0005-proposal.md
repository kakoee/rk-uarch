# U3 / U0005 proposal — G2 pre-registration

Status: **PROPOSED, NOT ACCEPTED; no candidate measurements.** 2026-10-10, Lane A.
Javid (@jjaffari) is the acting human decision-maker for both lanes. No Reza approval
is asserted. Acceptance must identify this exact Git revision and its linked expectation
specification; a human must commit U0005 under `docs/decisions/` before measurements.
This document is not that ADR. Unresolved prerequisites below prevent U-P5 starting.

Baseline: annotated `u02-end` peels to `79bc1f014306e520aacba3491d60ae6c644b26a8`.
The independent Lane A clone has its own `.git` and local main. Preserve later peer commits,
accepted U0003/U0004/U0019/U0021, U2 evidence and strict support currentness. Historical
pending-tag wording in U2 documents is not the current publication state.

## 1. Proposed pre-registered criteria

Evaluate ONNXim first at the pin in §3. Only after its documented failure evaluate
PyTorchSim at its pin, against the identical work, limits and evidence requirements.
If ONNXim passes all five criteria, record PyTorchSim as **not evaluated**, with this reason.
A blocked host, unresolved licence or unavailable counter is not a measured timeout.
Neither candidate is currently selected, passed or empirically failed.

| Gate | Exact proposed acceptance |
| --- | --- |
| G2(a) build | A clean clone builds the pinned image unattended on the designated native Linux host, using a recorded script, complete dependency pins and numbered build patches. Record exit status, tool versions, source revisions and resulting image digest. A downloaded prebuilt image alone does not pass. |
| G2(b) determinism | For each mandatory point, three consecutive fresh-process runs, fixed input bytes/image/configuration/seed, produce byte-identical complete designated simulation stats files and deterministic parsed results. Preserve raw stdout/stderr separately, including nondeterministic host timing. No sorting, rounding, stripping, cherry-picking counters or replacing candidate statistics with expected counts to manufacture equality. |
| G2(c) physical counts | All mandatory points in §2 and the [independent expectations](U3-G2-physical-expectations.md) preserve physical operand shapes, precision roles, repeats, rank scope, fusion, KV access and omissions. Compare integer per-operator matrix counts and their sum exactly, at two operations/MAC; missing work or unobservable actual work cannot pass. No adjustment allowance, tolerance, nominal substitution or extra division by tp. |
| G2(d) cost | Each of the three one-layer decode invocations at every mandatory point completes in **≤200 seconds** of monotonic host wall time, measured from adapter invocation through completed stats collection and parse. This includes validation, translation, any per-point compilation/latency preparation, process/container startup and simulation. No median-only pass. Derivation below precedes measurements. |
| G2(e) licences | Complete actual image/dependency inventory and linked/header-incorporated component scan are green under the existing allow-list. Missing notices, unknown coverage or out-of-list licences block acceptance until resolved by humans. The top-level MIT description is insufficient. |

The result must also meet U-P5's adapter conditions: exact prepared replay with producers
disabled; explicit refusal of unsupported exact mappings; every unrepresented hardware/state
field propagated to warnings; no silent DRAM preset; truthful fidelity and complete provenance.
Counts passing does not excuse incorrect precision, dropped vector work, changed fusion,
unrepresented required matrix work or fabricated critical-path attribution. A candidate's
inability to represent mandatory work fails that capability, even if other points run.

**Budget derivation.** Plan toward build-spec §2.3.3's default grid:
decode B={1,2,4,8,16,32,64,128}, S={128,512,1024,2048,4096,8192,16384,32768};
prefill n={1,2,4,8}, L={128,512,2048,8192,32768}; frequency ratios={1.0,0.6}.
That is (8×8+4×5)×2 = **168 points per precision**, and **336** for BF16/BF16
plus FP8/FP8 at one fixed tp=8, hardware and model. Proposed table-family build budget:
24 elapsed hours with one worker. Reserve 20% (17,280 s) for preparation, packaging and
error experiments; 69,120 s / 336 = 205.714… s/point. Round down to **200 s**;
336×200 = 67,200 s leaves another 1,920 s margin. This is a planning allocation, not a
claim that prefill, all-layer validation or the error experiments fit it. Image build time
is separate; compulsory per-point compiler/TOG latency preparation remains inside 200 s.
No precomputed latency cache from an unaccounted run is allowed for the gate.

The 70B-class, dual-precision full-grid U4 ambition has unresolved hardware/precision and
capacity coverage, including high-context KV residency. H1 currently supports BF16 only;
70B BF16 tp=1 exceeds its 32 GB capacity. This planning budget does not authorize FP8 on H1,
changing capacity, building a grid now, or treating G2's smaller test set as a G3 pass.
An agreed narrower later product would need a prospective budget/scope revision; it cannot
retroactively relax the G2 measurement limit.

## 2. Prepared work, precision and rank coverage

Propose mandatory G2 work `g2-8b-shape-1layer`: a **synthetic one-decoder-layer model**
using the published U2 8B shape dimensions, with n_layers=1 and independently calculated
active_params=total_params=1,268,789,248. Retain source attribution for the dimensions;
this is not the 32-layer Llama model or its performance. The [expectation specification](U3-G2-physical-expectations.md)
fixes the integer parameter derivation and head/decoder/tail counts before a producer exists.
No protected fixture is edited, no captured bundle is sliced/mutated, and no runtime fixture
is created in this planning session. Javid must accept this diagnostic model/scope as part
of the exact pre-registration. The specification also gives the original 32-layer counts
so later all-layer checks cannot silently scale the head and tail.

Use unchanged accepted `hw/designs/npu-l4.yaml` (H1), BF16 compute and BF16 KV, seed=7,
frequency_ratio=1.0, KV block=16, cold initial state, fused qk-softmax-av, no collectives,
all-token lm_head, dense gated MLP, full-square attention convention. S is the count of valid
KV tokens attended by each decode query, not S+1; append writes remain separate. All groups
of the one-layer model execute, including embedding, norms, residuals, activation and lm_head.

Mandatory matrix: B={1,8,32} × S={512,4096} × tp={1,8} = **12 points** at selected rank 0.
Add tp=8/B=1/rank=1 at both contexts = **14 invocations per repetition**, **42 per candidate**.
Explicit synthetic embedding hit vectors: tp1=(B); tp8/B1=(1,0,0,0,0,0,0,0), B8=(1,…,1),
B32=(4,…,4). Rank 0 and rank 1 differ at B1; do not declare them representative of all ranks.
Use one future bundle per (tp,B,selected rank), with the two S values: seven bundles.
U2's `Grid` requires nonempty decode **and prefill** axes. Preserve that coverage with an
additional prepared prefill n=1/L=8 point in each bundle (synthetic balanced hits); those seven
prefill points are not candidate executions or G2 evidence. Do not delete them from captured
coverage. Future G2 selects the 14 decode payload hashes explicitly; existing `capture()`
executes every point and cannot yet provide that fork selection seam. This limitation belongs
to the boundary decision in §6, not an implicit change to the U2 validator.
For tp8/B1, rank0 has equivalent_ranks=(0), rank1=(1,2,3,4,5,6,7); both are selected-rank
scope. B8/B32 bundles have equal work at every included point and representative scope with
all eight equivalent ranks. The replay input preserves these scopes/vectors unchanged.
42×200 s = **8,400 s (2 h 20 min)** maximum successful measured invocations per candidate,
plus at most 5 s timeout cleanup each; builds/reviews and prerequisite waits are separate.

| Coverage | Present U2 / proposed candidate boundary |
| --- | --- |
| BF16/BF16, the 14 points above | H1 admits preparation; candidate preservation and actual execution are **unproven**. ONNXim's byte width is not by itself evidence of BF16 compute/FP32 accumulation. |
| FP8, mixed BF16/FP8, BLOCKFP8 and other formats on H1 | Explicit refusal; H1 has no such admitted format. H2 analytic FP8 support is not evidence for either fork. No opportunistic precision substitution. |
| Imported physical padding or replicated KV heads | Keep authoritative extents/metadata. Separate hand-authored discriminators below; do not claim broad support from the divisible main matrix. Refuse if candidate cannot honor them. |
| Exact mapped TaskGraph | Not a U2 public payload. Explicit refusal; future mapping delegation requires a separate, recorded user choice, never replay equivalence. |
| Prefill, MoE, PP/EP/CP, heterogeneous non-embedding shards | Outside this bounded G2 declaration; existing analytic behavior remains. Refuse unsupported candidate input rather than translating it approximately. |
| Steady | U-P5 requires priming and reporting iteration two where supported. If unsupported, explicitly unrepresented/warn or refuse; never label cold as steady. Cold G2 here earns no steady-state evidence. |

## 3. Candidate pins, full-paper reading and licence dependencies

Read both complete papers, including figures/tables, references and PyTorchSim's artifact
appendix, on 2026-10-10. Source was inspected read-only in temporary Git checkouts; no
upstream code, scripts, compilers, simulator binaries or artifact images were executed.

- [ONNXim, arXiv:2406.08051v1, full text](https://arxiv.org/html/2406.08051v1):
  §§II–III describe heuristic tile lowering, core double buffering and deterministic tile
  latency with separately simulated shared resources. Core validation isolates Gemmini
  execution; it is not validation of this H1 workload. The paper uses Ramulator and compares
  simple versus BookSim NoC. Its full-model timing experiments are different work/hosts;
  they neither set our threshold nor demonstrate G2. Read through §IV and all references.
- [PyTorchSim, MICRO 2025, DOI 10.1145/3725843.3756045, pp.1363–1380](https://jongse-park.github.io/files/paper/2025-micro-pytorchsim.pdf):
  §§3.2/3.6.4 exclude sub-16-bit quantization and FlashAttention, and describe recompilation
  for new shapes. §§3.7–3.8 obtain TOG compute latencies through offline Gem5/Spike;
  §4.1 excludes compilation from published speed timings. Our proposed 200 s boundary includes
  this point-specific work. §§5–7, references and Appendix A were also read; the appendix's
  prebuilt Docker workflow does not satisfy our clean source build. Its stated 20 GB RAM /
  50 GB disk minimum informs feasibility only, not measured host availability.

| Component | Proposed exact source identity | Licence / unresolved closure |
| --- | --- | --- |
| ONNXim (first) | [`a1e86296e080fa1c82f8ad3f1b6de1079c192afc`](https://github.com/PSAL-POSTECH/ONNXim/tree/a1e86296e080fa1c82f8ad3f1b6de1079c192afc), inspected master HEAD | Root LICENSE is MIT. Current source pin is not asserted to be the paper artifact revision. |
| PyTorchSim (second) | [`5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3`](https://github.com/PSAL-POSTECH/PyTorchSim/tree/5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3), v1.0.0 | Paper declares MIT; no root LICENSE at this pin. Exact grant/coverage unresolved; no green licence conclusion. Choose artifact release for traceability, not moving main. |
| BookSim, both gitlinks | `1d69c9d9db190d130087471b373d12ed4605bf6e` | Stanford BSD-2-Clause notices in `src/allocators/allocator.cpp` and `src/routers/iq_router.cpp`; no top-level licence. Audit wrapper and all compiled files, not just those two. |
| Ramulator2, ONNXim | `0d063011281a112da29e67cbd708308dd05e7e64` | MIT LICENSE inspected; its CMake fetches yaml-cpp 0.7.0, spdlog 1.11.0, argparse 2.9. Resolve these tags to commits and audit bundled dependencies before build. |
| Ramulator2, PyTorchSim | `748cd7099778d7196326aeb6384da92efb0c34c9` | MIT LICENSE inspected; distinct fork revision, not interchangeable with ONNXim's. Transitive build closure still required. |
| ONNX, both | `f7ee1ac60d06abe8e26c9b6bbe1e3db5286b614b` | Apache-2.0 LICENSE inspected. |
| protobuf, both | `0dab03ba7bc438d7ba3eac2b2c1eb39ed520f928` | BSD-3-Clause notice inspected; linked/generated code included in scan. |
| torch2timeloop gitlinks | ONNXim `1e36aa55072a7762579146aea19443ac5d782398`; PyTorchSim `62aa175421165cc9cd7dfb182a02fc3e26c01e3a` | Build/use and grant unresolved; do not claim excluded merely because we do not select mapping search. |
| STONNE core, PyTorchSim | `97804185f00e98e56f74638e4282b9aecab8cfce` | CMake links `sstStonne`; no top-level licence located. Embedded cpptoml has MIT notice, which does not license the whole core. |

Pin evidence: each candidate's `.gitmodules` plus Git gitlink objects. Licence sources for
[BookSim](https://github.com/PSAL-POSTECH/booksim/blob/1d69c9d9db190d130087471b373d12ed4605bf6e/src/allocators/allocator.cpp),
[ONNXim Ramulator2](https://github.com/PSAL-POSTECH/ramulator2/blob/0d063011281a112da29e67cbd708308dd05e7e64/LICENSE),
[PyTorchSim Ramulator2](https://github.com/PSAL-POSTECH/ramulator2/blob/748cd7099778d7196326aeb6384da92efb0c34c9/LICENSE),
[ONNX](https://github.com/onnx/onnx/blob/f7ee1ac60d06abe8e26c9b6bbe1e3db5286b614b/LICENSE),
[protobuf](https://github.com/protocolbuffers/protobuf/blob/0dab03ba7bc438d7ba3eac2b2c1eb39ed520f928/LICENSE).

Both `conanfile.txt` files require boost/1.79.0, robin-hood-hashing/3.11.5,
spdlog/1.11.0 and nlohmann_json/3.11.2. Their full package revisions/transitive licences
are not yet frozen. Boost's BSL-1.0 is outside this repository's literal allow-list;
it needs a human ADR disposition if incorporated, not an agent's “permissive enough” waiver.
MIT expectations for the other three still require exact package notice verification, including
fmt bundled with spdlog. ONNXim also builds/links vendored `extern/ramulator_custom` (Ramulator1);
its licence coverage needs checking even when selecting Ramulator2 at runtime.

PyTorchSim's pinned Dockerfile consumes a mutable `torchsim_base:latest`, Gem5/LLVM release
asset IDs supplied externally, a moving Spike `TorchSim` branch, and riscv-pk at
`4f3debe4d04f56d31089c1c716a27e2d5245e9a1`. Its base uses a CUDA/PyTorch image plus
unlocked Python packages. Exact Gem5/LLVM/MLIR/Spike revisions, compiler runtimes, Python,
PyTorch, ONNX/ONNXRuntime, system libraries and image-layer licences remain unresolved.
ONNXim's Dockerfile also has mutable base/package inputs. Neither upstream recipe is a
finished reproducible, allow-listed image for us. CPU-only packaging is proposed; removing
unused CUDA/build components requires demonstrated dependency closure, not assumed exclusion.
Separate build tools from linked/runtime libraries, retain notices, record base image digest
and lock all downloads. Out-of-list system/runtime licences also need explicit human scope
resolution; do not silently reinterpret G2(e). No licence register or dependency was changed.

## 4. Static feasibility and proposed fidelity (not runtime evidence)

All source locations below refer to the pins in §3. ONNXim paths are under `src/`;
PyTorchSim backend paths are under `PyTorchSimBackend/src/` at v1.0.0.

| Finding | Source and consequence |
| --- | --- |
| ONNXim LLM input reconstructs TP | [`models/LanguageModel.cc:34–69`](https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/models/LanguageModel.cc#L34) divides heads, KV heads, FFN and projection widths. Its decoder builder (159 onward) is not a generic immutable prepared-operator importer. Do not feed already sharded shapes into this path and divide again. The declared `LmHead` string is not evidence that the generated graph executes the tail. |
| Unsupported ONNX work can disappear | [`operations/OperationFactory.cc:24–61`](https://github.com/PSAL-POSTECH/ONNXim/blob/a1e86296e080fa1c82f8ad3f1b6de1079c192afc/src/operations/OperationFactory.cc#L24) supports a bounded operator set and returns Dummy for unknown types. Adapter admission must refuse unsupported operations before launch. RoPE, RMS normalization, SiLU/gating, paged KV and fused attention need explicit correspondence. No engine patch to make parity pass. |
| Precision is not just bytes | ONNXim `Common.cc:135` loads a global integer precision, and `LanguageModel.cc:106–110` uses it for tensors. PyTorchSim `PyTorchSimFrontend/mlir/mlir_common.py:38–66` names BF16/FP16/FP32 but does not establish exact execution/accumulation coverage. Per-operand semantics need independent tests. |
| Counts/attribution are not proven observable | ONNXim `Stat.h:7–25` gives cycles/stalls/SRAM fields, not exact matrix operation counts; `SystolicWS.cc:170–175` prints instruction issues, not scalar MACs. PyTorchSim `TileGraphParser.cc:563–573` consumes precomputed compute cycles. Neither justifies deriving actual matrix counts from time or echoing the bundle. Identify complete executed-op evidence or fail G2(c). Critical-path attribution also needs real dependency evidence; busy-time sums are insufficient. |

Propose the BookSim + Ramulator2 configuration as the primary candidate mode for both;
no automatic downgrade after seeing time. Source-level ladder below is conservative and
provisional until configuration and hardware correspondence are reviewed. Simple modes are
catalogued, not alternate ways to rescue the primary gate retrospectively.

| Candidate configuration | Compute / SRAM banks | NoC | DRAM | Shared SRAM / sync | Proposed composite |
| --- | --- | --- | --- | --- | --- |
| ONNXim WS + BookSim + Ramulator2 | 1; `SystolicWS.cc:20–110` tile timing; `Sram.cc:18–84` readiness/capacity, empty cycle(), no demonstrated placement bank conflicts | 2, `Interconnect.cc:83–127` | 2 only with exact spec configuration, `Dram.cc:136–197` | H1 absent; serial loop sync must be verified exact | C1, not C2 |
| ONNXim simple NoC + Ramulator2 | 1, same bank limit | Candidate 1+ts: timestamped port arbitration, `Interconnect.cc:30–65`; unbounded buffers disclosed | As above | As above | C1 |
| ONNXim simple DRAM (either NoC) | 1 | As selected above | No admitted ≥1 claim: `Dram.cc:15–59` explicitly warns of bugs; lacks required row policy/queues | As above | No accepted configuration; cannot earn C2 |
| PyTorchSim TLS + BookSim + Ramulator2 | At most 1 pending offline latency/placement audit; `Core.cc:1–35,347–371`, `TileGraphParser.cc:563–573`; offline latency is not proof of mapped SRAM bank conflicts | 2 provisionally, `Interconnect.cc` BookSim calls | 2 provisionally, `Dram.cc:52–87`, exact config required | H1 absent; exact serial sync to verify | At most C1 on present evidence |
| PyTorchSim simple NoC and/or simple DRAM | Same compute ceiling | Simple mode needs port/queue audit before 1+ts | `Dram.cc:133–205` delay queues do not establish required row-buffer/page-policy model | As above | No higher than C1; not selected for gate |

BookSim and Ramulator2 comparisons against these same embedded implementations are not
independent L2 evidence for U-P8. No fidelity or validation badge follows from their names.
H1 `timing_source=direct`, `timing_preset=null`: translate its explicit organisation/timing,
not the fork's HBM preset. Required fields absent from H1 but demanded by Ramulator2 must
be named as unresolved stipulations for B/Javid; no default insertion. Audit dataflow,
array geometry, SRAM capacity/banks, DMA outstanding/request limits, per-job overhead,
DRAM refresh/queues/page policy and clocks, NoC topology/link width and initial state field
by field against the full HardwareSpec. Every unsupported field needs a warning; refusal
is required when the claimed workload/configuration cannot be represented faithfully.

## 5. Runtime, resource and measurement procedure — proposal only

Host status supplied by Javid: `javid@152.53.209.203`, native Debian12; Python 3.12.14,
uv 0.12.13, Rust/cargo 1.99 and tmux available. Podman/Docker and newuidmap/newgidmap absent;
subordinate ID ranges assigned. Reza is unavailable. Runner is unverified and nightly paused.
This session neither contacted nor modified the host; CPU topology/RAM/disk/cgroups and
available shared-host capacity remain unknown.

Propose rootless **Podman**, installed/configured by the administrator, under Javid's account;
no privileged container, rootful daemon or alternate host. Rootless user namespaces need the
UID/GID helpers as well as subordinate ranges; those ranges alone are insufficient.
See [Podman rootless documentation](https://docs.podman.io/en/latest/markdown/podman.1.html#rootless-mode).
Verify native architecture, working user namespaces, OCI runtime, local storage and cgroup-v2
resource delegation before accepting a runner. No installation or privilege workaround here.

Proposed measurement allocation: one candidate process tree at a time across both lanes,
one pinned physical CPU core (no SMT sibling work), one simulator/compiler thread, one table
worker; set OMP/BLAS/compiler parallelism explicitly. Reserve 24 GiB RAM and 100 GiB local
scratch for either candidate, no swap reliance. These are requested reservations, not available
host facts. Build concurrency at most two jobs in a separate agreed window; no build or B
nightly/mutant suite concurrent with timed runs. Confirm at least one additional host core
and adequate remaining RAM for other users; if unavailable, stop and revise prospectively.
Record CPU model/affinity, kernel, runtime, cgroup limits, load/steal and memory pressure,
compiler/thread variables, locale and seed with results. Do not “fix” slow runs by adding cores.

For each point: validate exact captured bytes/configuration; run three fresh output directories
in fixed B/S/tp/rank order; clear per-point compilation caches for each invocation; use
identical in-container paths. OS page cache is not forcibly dropped. Capture all raw files,
exit status, signal, maximum RSS, elapsed monotonic time and configured limits. Designate
native stats file paths and their complete field inventory **before** the first run, by a
prospective pre-registration supplement if the source cannot establish them now. These paths
are currently unresolved; no measurements may precede that supplement. Nondeterministic
logs can be preserved outside the stats set only with a source-based, predeclared separation.
If native stats themselves contain timestamps, G2(b) fails; do not repair results afterward.

At 200 s send termination to the entire run/container process tree; allow at most 5 s cleanup,
then kill the remaining tree. Record timeout as failure, preserve partial evidence, never
parse partial counts as success. Clean up only this run's processes. OOM, crash, missing work,
missing stats or semantic refusal have distinct failure outcomes. No automatic rerun to erase
a slow/failing attempt. Infrastructure interruption is recorded and reviewed by Javid before
a labelled repeat; retain the original. Disallow scheduling overlap before timing; externally
observed interference remains visible, never silently excluded. Deterministic simulated values
carry no confidence intervals, and host runtime metrics stay outside canonical table identity.

## 6. A/B interfaces and concrete human decisions

Existing implemented interfaces, not the older protocol sketch:

| Surface | Actual U2 API / proposed ownership |
| --- | --- |
| Preparation | A: `workload.prepare.prepare(intent, hardware, *, rank_index, embedding_hits, synthetic_assignment, attention_mask, lm_head, fused_attention) -> PreparedBundle`; `load_prepared_input(path)` / `validate_execution_bundle(value)` validate replay. Protected `contract/uarch_contract/prepared.py` admits only `mapping_scope='analytic_ops'`, `uarch-prepared/1`; request Grid requires both phases. `validate_execution_bundle` also enforces analytic-ops@1 and C0 hardware detail. |
| Job/result | A: `workload.prepared.prepare_engine_job(bundle, point_hash, *, assumptions)` and `execute_prepared_point(...)` are analytic-specific. `engines/protocol.py` has `EngineIdentity.name='analytic'`, `state_model='stateless_roofline'`, only aggregate/per_op modes; result validator enforces roofline arithmetic and null diagnostics/busy times. `ResolvedHardware` is a small numeric projection, not full fork configuration. |
| Table transport | A: `table.build.capture(bundle, *, assumptions, workers=1, subprocess_engine=False) -> CapturedWork`; no engine injection point. `build_table(captured, *, context, model_card, artifacts) -> TablePackage`; CLI currently accepts only analytic. Do not remove these checks to sneak in a fork. |
| Evidence/report | B owns provenance/report and independent L0/L0m work; consume existing `ReportContext`, `ModelCard`, comparison/recipe/registry carriers and A's `load_verified_report_inputs(path)`. A supplies real captured jobs/results and complete provenance; B supplies honest badge/warning/display behavior and actual independent review closure. No private schema, invented reviews or second ledger. |
| Hardware/runner/CI | B owns `hw/`, `scripts/`, validation and workflows. A proposes config capability gaps and image/adapter changes; B/Javid resolves missing sourced/stipulated fields and runtime/runner evidence. No editing B files in this session. |

**Proposed boundary decision for human elaboration/commit:** add an explicitly versioned
fork-delegated preparation/execution variant that reuses immutable resolved operators and
rank/precision metadata, binds original bundle/point plus selected pinned mapping and image,
and discriminates fork result validation from analytic roofline validation. Preserve old U2
acceptance/replay bytes. Do not merely rename an analytic bundle or pass a detailed TaskGraph
through an analytic validator. The exact version, fields, migration fixtures, image/assumption
identity, observability, critical-path result representation and steady-state behavior need
an exact protected schema proposal/human commit before implementation; **none is specified
as an accepted runtime schema here**. This is a concrete gap, not a reopening of U0019.

Decisions still needed from Javid: accept/revise this exact pre-registration (including
synthetic one-layer/BF16/cold coverage, 200 s limit and resource reservation); licence scope
and out-of-list dispositions; new boundary/schema proposal acceptance; complete native-stats
inventory and capability disposition. These are not requests to reapprove already accepted
physical-versus-nominal accounting, mapping honesty, rank conservation, STUB visibility or
hardware stipulations. No bound support file may change without U0002's human freeze,
twice-generation, review and complete adoption lifecycle. Strict currentness remains strict.

Before later runtime edits, A writes discriminating tests from the expectation specification:
no double sharding; missing tail/gate/QK/AV fails even with equal total counters; correct
2/MAC; preserved padding/replication/embedding asymmetry; exact replay with producers trapped;
precision/fusion/preset/mapping refusals; timeout kills descendants; stats byte differences
fail; old analytic public capture/table/report still passes. B authors independent invariant
and metamorphic mutants and evidence closure/warning/report tests. Coordinate specific shared
API/test files through Javid before edits, with commit IDs/diffs; this document proposes the
partition and does not claim B accepted it. This session edits only its three named planning
files; no shared implementation, plan/status, prompt or protected file.

## 7. Remaining effort and stop conditions

Re-estimate the historical A=53 h / B=27 h U3 baseline as conditional engineering effort:

| Work | Hours |
| --- | ---: |
| A: schema/interface proposal and discriminating test design | 12–20 |
| A: dependency/licence closure and reproducible ONNXim build | 12–24 |
| A: prepared translation, config refusals, result/stats/replay and CLI integration | 28–48 |
| A: G2 evidence, integration and review responses | 12–20 |
| **A remaining, ONNXim path** | **64–112** |
| A: PyTorchSim fallback, only if needed | **+32–64** |
| B: U-P6 invariants/mutants plus fork provenance/report integration | **32–52** |
| Independent reviewer effort (not this author) | **12–20** |
| Administrator setup effort once available | **2–6**, provisional |

ONNXim path totals 108–184 engineering/reviewer hours (administrator setup separate);
second candidate adds 32–64. Candidate run envelope is separate from active engineering
hours; build elapsed time remains unknown. Administrator availability wait, Javid's exact
ADR/schema/licence decision wait, independent-review queue, runner/manual-nightly scheduling
and shared-host reservation waits are **unbounded/unestimated calendar dependencies**.
No actual effort claim or delivery date follows. Source incompatibility could terminate the
candidate rather than justify unbounded porting or engine patches.

Next dependency is human/administrator readiness: provision approved rootless runtime,
verify online self-hosted runner labelled `uarch`, B re-enables nightly schedule and records
a green manual run on the designated host (including what actually ran versus empty-suite
no-ops); Javid accepts exact pre-registration and a human commits U0005. Resolve schema,
licence and stats blockers before their dependent work. Both candidates failing eventually
requires a human-recorded U-C1 fallback and “C2 via fork: unbuilt”; this session neither
implements that fallback nor begins U-P7. Stop after publishing the planning handoff.
