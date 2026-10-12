# U3 fork feasibility after RoPE — Lane A decision proposal

**2026-10-12 · Author investigation; proposed, not independently accepted.**

Neither pinned candidate currently offers a defensible adapter-only route for the complete
one-chip diagnostic. A chip must gather its local embedding hits, execute the projections,
normalizations, residuals and gated FFN, rotate Q and new K, append K/V, attend to exactly
the valid paged context without spilling scores, and execute the final norm and vocabulary
head. It must do this for the already resolved rank, with BF16 operands and the required
FP32 arithmetic. Merely getting its matrix dimensions through a simulator is insufficient.

ONNXim executes matrix tiles and models transfers through a network and DRAM, but its native
LLM builder omits required work and its ONNX factory skips unsupported operations. Its tp8
GQA path also encounters an assertion inconsistent with this diagnostic. These are execution
and timing problems that an adapter cannot repair. PyTorchSim offers a more general compiler,
but the supplied model uses dummy RoPE and contiguous cache concatenation. More decisively,
the inspected matrix templates hard-code FP32; naming BF16 in a dtype dictionary does not
supply BF16 matrix execution. Fused paged attention remains unestablished.

RoPE completion fixes **our declaration and analytic accounting**: coefficients, absolute
positions, Q/new-K placement, casts, traffic and cache profile are now authenticated inputs.
It does not add those capabilities to either simulator. Nor does it turn our analytic result
validator into a validator of simulator observations. Both tools still lack demonstrated
completed scalar matrix counts by prepared operator. Device latency, expressed in simulated
cycles/time, is separate from the host time spent compiling and simulating it.

I recommend **deferring fork implementation and requesting a bounded U-C1 plan amendment
design**, with no engine implementation authorized yet. This avoids paying for a build that
cannot resolve known workload and evidence gaps. The principal cost is losing the planned
published-fork reference for native validation; U-C1 would be a weaker, internally developed
reference and would itself need design, implementation and independent verification.
Source infeasibility is not an empirical finding that both tools failed G2.

The next authorization is concrete: A/B prepare a contention-aware U-C1 design, acceptance
matrix and exact U3–U6/G5 plan edits for Javid, capped at **16–28 combined active engineering
hours**, plus **4–8 reviewer/decision hours**, then stop. Do not build it, start U-P7 or relax
workload semantics. An alternative is separately funded PyTorchSim compiler/engine extension
research; that is a substantial policy and maintenance choice, not ordinary wrapping.
No candidate was built or run; speed, determinism, image inventory and G2 remain unmeasured.

[Exact next action](next-decision.md) · [draft U0005](proposed-U0005.md) ·
[immutable source evidence and coverage](source-evidence.md).

## Investigation basis and delta

The independent A clone was clean on main, with empty index/worktree and origin
`https://github.com/kakoee/rk-uarch.git`. Fetch/integration found no incoming change at
investigation start. Baseline and investigation revision:
`456215cdf9ec4ec383ce2604a483ee4bfa7f5991`, tree
`2570682d1af20a0860b70b9bbd79a0ec75ad1a4b`; baseline ancestry verified.
The task authorizes source inspection and publication of this directory only.

| Earlier statement | Current disposition and reason |
| --- | --- |
| RoPE has no prepared representation | Superseded for v2 by [accepted U0022](../../decisions/U0022-explicit-rope-semantics.md) and the live producer/admission/runtime. Historical v1 remains unchanged and excludes RoPE. |
| RoPE runtime/adoption/activation is pending | Historical wording in the [runtime handoff](../U3-RoPE-runtime-v1/README.md) is superseded by baseline publication, adoption and all 28 active admission checks. The [final local receipt](../U3-final-local-validation-v1/README.md) predates publication. |
| PyTorchSim precision is merely unresolved because templates mix dtype names | Strengthened: MLIR GEMM render options fix `DATA_STYPE="f32"` at line 211; BMM at line 261. The alternative LLVM GEMM fixes float/f32/4 bytes. The inspected normal matrix route contradicts faithful BF16 storage/compute translation; arbitrary alternate programs remain unproven. |
| Backend-only logging might suffice | It cannot reconstruct absent kernel extents/masks. `TileGraphParser` consumes cycles/type; `TOGGenerator.generate_tile_graph` even substitutes 10 cycles when its latency list runs out. Require complete authentic kernel/latency correspondence before a TOG can be evidence. |
| Native cache starting at S−1 necessarily changes the input | Clarify after U0022: declaring **incoming C−1**, appending one, and attending C is correct if the route can express it faithfully. The error is silently treating attended C as incoming C. This clarification does not fix ONNXim's skipped append, paging or GQA problems. |
| Both CMake recipes link vendored Ramulator1 | Correct the prior supplement's overstatement: ONNXim explicitly adds/links `ramulator_custom`/`ramulator1`. PyTorchSim vendors it, but its inspected top-level recipe adds Ramulator2 and links `ramulator`; direct Ramulator1 linkage is not established. Actual image closure is still unknown. |
| Podman absent | Outdated. Javid reports working rootless Podman 4.3.1/user namespaces after Reza's installation. Account-specific runner, enforced allocation and manual nightly remain unverified. |
| Generic PyTorch compatibility establishes a complete route | Still false. CPU fallback registration is a possibility, not proof every compiled operator falls back. Each required operator needs actual compiler/latency/backend correspondence. |

Baseline model `physical-resolved/2`, engine `resolved-ops/2`, execution identity
`sha256:c5420668fb3db8781168f4b8b9495a28474f001356cff10f1df9915158f8cdf6`;
adopted manifest `1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a`;
frozen input `27c6238d42e57dc4f2b1baf0c8846c11f1eec2968176dcefcdc463beb64bc80f`.
All 97 support-bound files are outside this change set.

Inherited baseline CI: [run 38198912991](https://github.com/kakoee/rk-uarch/actions/runs/38198912991),
1,691 Python passes, 29 existing skips, 10 deselected; 681 contract passes. The preceding
local suite had 1,701 passes/29 skips. These overlap; none was rerun here or establishes
simulator capability. Conditional no-op jobs are not evidence. [B's recheck](../U3-B-SR-C1-coordinator-recheck.md)
remains model-v1 partial/not_run, including L0m aggregate-clock 22/24 distinct cases.
No positive v2/fork verification, card attachment, independent review or U3 closure follows.
The execution plan's top-level “not started” wording is historical, not a denial of this work.

## Routes and chip behavior

The exact source citations are collected in [source-evidence.md](source-evidence.md).
Existing disposable O/P checkouts were verified clean at the two required immutable pins;
no candidate fetch/update, submodule initialization, module import or script execution was
needed. No newer revision was nominated: no specific evidenced fix in this investigation
justifies changing the comparison baseline. The earlier author's full-paper reading is an
inherited claim. This author consulted relevant sections of both original papers and the
source sites cited here, not both entire papers anew.

**ONNXim native LLM:** model JSON → `LanguageModel` divides global widths/heads by TP →
native operations → tiles/instructions → core scheduling with SRAM readiness and simulated
NoC/DRAM → core and simulation logs. It starts from hidden activations, builds a biased,
differently normalized decoder and allocates an lm_head weight without executing that tail.
Feeding resolved rank extents to its TP division shards twice. Feeding global metadata to
reconstruct a nominally matching graph loses authoritative prepared work. Stop this route.

**ONNXim ONNX graph:** prepared operators could become adapter-produced ONNX, then
`Model::initialize_model` → `OperationFactory` → tiling → the same scheduler. GEMMs are real
supported operations. Unknown Add/Gather/RoPE/RMS-style decompositions become skipped Dummy
work; Cast is explicitly Dummy. A factory-recognized fused Attention is not a generic
paged-GQA kernel. Public C++ operation/tile classes are implementation seams, not a documented
faithful files-in/files-out importer for our graph. Adding operations there is category 4.
Stop adapter design once these contradictions are established.

ONNXim device latency comes from matrix/vector timing formulas, instruction dependencies,
double buffering, DMA, NoC and DRAM responses. It does not numerically multiply BF16 tensors.
[ONNXim §§II–III](https://arxiv.org/html/2406.08051v1) explains this execution model and its
Gemmini core comparison; those experiments do not validate our workload or host budget.

**PyTorchSim supplied model:** hidden activations → example transformer → dummy RoPE,
`torch.cat` cache and repeated KV → scaled-dot-product attention. It is not the complete
paged diagnostic. Stop this example route; selecting the nearby unused rotation function
would still leave pairing/partial-R/casts/coefficient traffic and all other blockers.

**PyTorchSim generic compiler:** a rank-local adapter program could use existing Aten
operations → Inductor/custom MLIR lowering → templates/loops → LLVM/RISC-V → offline Gem5
latencies (and Spike when needed) → TOG → parser → tile/core scheduler → DMA/NoC/DRAM.
The setup selects MLIR scheduling. The inspected GEMM/BMM templates force f32; changing
render options, memory widths or accumulator semantics is compiler behavior work, not
configuration. The [paper §§3.6.4–3.8](https://jongse-park.github.io/files/paper/2025-micro-pytorchsim.pdf)
explicitly lacks FlashAttention support and describes offline tile latency generation.
This does not prove every possible fused decode program impossible, but supplies no bounded
faithful BF16/fused/paged route. Do not build the full adapter to discover that distinction.

**Lower-level TOG:** the backend accepts graph files in an ONNX container, including loops,
loads/stores/barriers and COMPUTE nodes carrying cycles/type. This is not ONNX neural-network
operator support. An externally authored TOG can describe transfers/scheduling, but someone
must supply correct kernels, masks and compute latencies. Inserting our analytic counts or
latencies would remove the independent execution claim. New fused paged templates or a new
latency model are category 4 (and require the no-parity-patching policy decision). Merely
serializing a graph faithfully produced by existing supported tools would be category 1;
that producer has not been established for this workload.

## Observations and stable statistics

| Producer | Actual output / units | What it cannot establish |
| --- | --- | --- |
| O `Simulator.cc`, `Core::print_stats`, `SystolicWS::print_stats` | Overall cycles/us, matrix/vector active cycles, idle/bubble cycles, utilization %, GEMM/PRELOAD **instruction** issues, stdout | No complete per-prepared-op integer scalar MAC completion counter. `finish_compute_pipeline` adds tile m×k×n divided by array area to a cycle-like statistic. Attention's GFLOP/theoretical-time printouts are input arithmetic, not independent execution. |
| O `DramRamulator2::print_stat` | Per-channel `print(stdout)` | Not the Ramulator1 `ramulator.stats` file. R1's request/DRAM-cycle/capacity fields are DRAM-only; requests are not valid payload bytes or matrix operations. |
| P `Core::print_stats`, `Simulator.cc` | Issued/skipped opcode counts, COMP GEMM/vector instruction split, active/idle cycles, memory response count, GB/s, NUMA hits/misses; total execution cycles | No scalar extents/masks or complete prepared-op attribution. Instruction issue is not completed mathematical work. Overlapped busy sums are not elapsed duration or a critical path. |
| P `Simulator/simulator.py` | Captured backend stdout under `backendsim_result/<directory-entry-count>`; Gem5 `m5out/stats.txt` and `sto.log` | Gem5 consumer selects `system.clk_domain.clock` and `system.cpu.numCycles`, drops the final cycle-list item; external asset identity/output closure unresolved. Frontend's older utilization parser is not a complete statistics record. |

The current complete-statistics three-run proposal is **not ready to execute**. Both main
programs print elapsed host time; standard spdlog output mixes timestamps and simulation
statistics. Paths, progress and P's directory-dependent filenames are operational telemetry.
No complete stable native simulation-statistics product has been established. Comparing only
Ramulator output or stripping/sorting/rounding mixed logs does not satisfy G2(b).

A separately accepted category-3 alternative could emit a versioned complete statistics
stream directly from execution, excluding host fields by design before any trial; keep all
raw logs alongside it. Declare file set, ordering, units, completion/refusal semantics and
schema before runs; compare its entire bytes and parsed results for all three repetitions.
This is a **prospective statistics-protocol decision**, not evidence of determinism today.

Candidate observation sites: O `Core::finish_compute_pipeline`, `finish_vector_pipeline`,
load/store issue/response and tile/layer completion retain instruction/tile identity and
some extents; propagate actual masks and prepared IDs through fused QKV/up-gate boundaries.
P `Core::finish_instruction`, response sites and parser have lifecycle identity but COMP has
no scalar extents. Compiler/kernel and offline execution provenance must be joined to dynamic
TOG iterations; logging expected `2MNK` at the backend would not suffice. If required metadata
is unavailable, stop; obtaining it may exceed observation-only work. Retain logical declared
work, physical input padding, extra issued capacity, eliminated work and completed work
separately. Two ops/MAC applies only to independently observed MACs with known scope.

Logging has host CPU/I/O/storage cost that must remain in the timed invocation; cost is
unknown. It must not affect simulated scheduling, latency, masks, addresses or precision.
Required future controls: instrumented/uninstrumented same modeled event schedule/duration
and memory requests; missing/duplicate/swapped op attribution, dropped tail/gate, skipped
instructions, partial completion, padded tile and repeated-group discriminators; deterministic
emission across three fresh processes; no expected-count backfill. An altered schedule is a
category-4 change even if called instrumentation. True critical-path attribution also needs
causal issue/completion/dependency records, not allocation of busy cycles until totals fit.

## Work categories and integration consequences

Categories apply to **each change**, not the directory where it is implemented:

| Necessary work | Category and disposition |
| --- | --- |
| Preserve resolved operands/rank/repeats and explicit coefficients in a supported input language; map existing hardware knobs; reject unsupported inputs | **1 adapter/configuration**, only after faithful capabilities exist. Not currently sufficient for either candidate. |
| Immutable source/base/compiler pins, locks, build recipes, retained notices and clean build | **2 packaging**; no permission to change simulated behavior or waive licences. |
| Completed op/byte telemetry, stable complete stats emission and causal attribution | **3 observation**, separate approval and noninterference tests. Does not repair missing work. |
| O missing operations/GQA/cache/precision/SWISH timing; P BF16 templates, fused paged kernels, changed rounding or invented TOG latency | **4 semantic/compiler/timing**, separate decision changing U-P5's prohibition on engine patches to obtain parity. No such changes authorized or recommended as a small adapter. |
| Omit embedding/norm/RoPE, allow spill, substitute FP32, shrink mandatory ranks, change 200 s or G2 evidence/fidelity; select source-based fallback | **5 workload/gate/plan**, human ADR before dependent work. No missing model operation may become an ordinary hardware warning. |

No route qualifies, so there is no proposed complete fork schema. The actual v2 seam leaves
these precise questions for A/B/Javid if a route is later accepted:

- [producer_v2.prepare](../../../src/rkuarch/workload/producer_v2.py) requires supplied
  coefficients; [prepared_v2](../../../src/rkuarch/workload/prepared_v2.py) validates graph,
  rank, hardware and coefficient closure, but admits only analytic-ops@2/C0. Its
  `prepare_engine_job(bundle, point_hash, *, assumptions)` binds the analytic engine.
  Separate semantic input validation from new execution admission by an accepted design;
  do not weaken this validator or mutate a saved bundle into a fork bundle.
- [protocol_v2](../../../src/rkuarch/engines/protocol_v2.py) fixes engine name `analytic`,
  `state_model=stateless_roofline`, null simulator metrics/trace, and validates a result by
  exact analytic recomputation. A future simulator result needs separate identity and
  validation for observed counts, completion, time and absent capabilities. Never attach
  those observations to analytic evidence or substitute them for analytic results.
- [capture_v2](../../../src/rkuarch/table/capture_v2.py) executes every point with workers=1;
  replay requires complete ordered point/job/result coverage. A future diagnostic selector
  must bind chosen point hashes without claiming prepared-only prefill was executed.
  Replay must work with model/mapping/coefficient producers disabled. Preserve bundle,
  intent/hardware/assumptions, point, coefficient/profile/positions, rank/hits/equivalence,
  op/group IDs, repeats and physical padding/replication in the execution closure.
  Projection Y[b*S+s,h*D+d] to rotary X[b,h,s,d] is logical correspondence; any physical
  reorder/transpose needs an explicit supported transfer, not an assumed free layout change.
- A owns translation, engine/config/source/patch/image identities and runner/parser design;
  B owns hardware/provenance/report/verification/workflow reconciliation. Protected carriers
  and ADRs need Javid's human commit; shared table/evidence paths need an exact coordinated
  diff. Public v2 tables/reports remain future work, with A's table and B's report ownership.
- Bind source/patch/compiler/latency provenance, image digest, exact config/DRAM bytes,
  seed, clocks, state and delegated mapping to observations. Exact imported mapping must
  be refused if unsupported. Preserve honest nulls and all hardware/state warnings.
  Capacity_v2's known weights/KV/coefficients do not establish peak activation residency.
- B must reconcile [U0006 report §7](../U3-U0006-report-supplement.md#7-future-dma-queue-and-clock-premises-reconciliation-with-a):
  payload vs bus bytes, request/fragment IDs, accepted/completed/cancelled and endpoint
  inventories; queue membership/service boundaries and censored intervals; clock-domain
  premises; actual critical path; v2 relation corpus and contributor/evidence eligibility.
  The analytic clock law cannot be imposed on a contention simulator unchanged. Identity,
  actual execution, accepted independent review and accuracy remain distinct obligations.

## Diagnostic after RoPE and hardware fidelity

The [old proposal](../U3-U0005-proposal.md) still offers a useful **prospective** full-work
capability/count/reproducibility/cost test; it is not currently runnable and **200 seconds
remains unaccepted**. Preserve 12 B/context/tp combinations ({1,8,32}×{512,4096}×{1,8}),
plus tp8/B1/rank1 at both contexts: 14 decode cases × 3 fresh runs = 42/candidate.
Seven bundles each also contain n=1/L=8 prepared-only prefill. This earns no prefill execution,
full 32-layer performance, FP8 support or full-table cost claim. B1/tp8 rank0 hit vector
[1,0,0,0,0,0,0,0] and rank1's zero hits remain distinct even with equal matrix counts.

The unchanged synthetic one-layer shape has 1,268,789,248 parameters; the source 32-layer
shape has 8,030,261,248. The [12 matrix rows and tiny 928/1024 discriminators](../U3-G2-physical-expectations.md)
are unchanged by RoPE. New-version inputs need **prospectively accepted exact coefficient
bytes/producer/hash, R and pairing**; these values are UNRESOLVED for G2, not model-name
defaults. Preserve full-square fused attention, cold state, seed 7, block 16, BF16/BF16,
frequency 1, all groups and once-only head/tail. Add rotary admission/execution discriminators
for both pairings, partial rotation, casts/tails, profile mismatches, C=17 page boundary and
replicated K; they are capability/refusal controls, not silent replacements for timing cases.

For scale only, full R=128 at B=1 adds 25,600 vector operations, 11,264 read bytes and 10,240
write bytes per layer at tp1; at tp8 it adds 3,200 vectors, 2,304 reads and 1,280 writes.
These include explicit casts and Q/K coefficient reads; multiply by B and decoder repeats
once, never by expert count. Full coefficient allocation with 4096 positions/R128 is
2,097,152 bytes, shared rather than multiplied by layers. These are independently checked
U0022 arithmetic examples, **not chosen coefficients, simulator observations or throughput**.

The old budget arithmetic is still (64 decode+20 prefill)×2 frequencies=168 points/precision,
336 for two precisions; 86,400×0.8/336=205.714… seconds, rounded down to 200. Then 336×200=
67,200 seconds; diagnostic 42×200=8,400 seconds/candidate. The 20% reserve and remaining
1,920 seconds are allocations, not evidence that full-model/error/prefill work fits.
RoPE introduces work but no measured justification to increase or decrease the limit.
Compile/latency preparation, startup, validation and statistics collection/parse stay in
host wall time; image build time is separate. No inherited cache makes that preparation free.

H1 [npu-l4](../../../hw/designs/npu-l4.yaml) specifies **direct** DRAM timings and null
`timing_preset`; no named vendor preset is currently selected. Any future image must realize
those values through a pinned exact Ramulator configuration or refuse/name missing fields
for B/Javid; it cannot silently use the fork's HBM default. Field coverage includes array
geometry/dataflow, SRAM/banks/placement, clocks/vector rates, DMA request size/outstanding
limits, job/barrier overhead, NoC topology/queues/credits, DRAM organisation/timing/queues,
initial state and optional shared SRAM. A capability warning is permitted for an unrepresented
hardware field, not for omitting required workload work. Cold SRAM/closed DRAM/inflight state
must be defined while preserving the existing decode cache. Steady needs priming/reporting
iteration two or explicit unsupported-state handling; cold trials prove no steady behavior.

No new ladder acceptance: prior source supports O compute at level 1 (no established SRAM
bank conflicts), BookSim provisionally 2 and exact-config Ramulator2 provisionally 2; composite
C1. P TLS compute remains at most 1 pending core/placement/config correspondence, so no C2
claim. Simple modes cannot rescue runtime retrospectively. Shared SRAM when present cannot
be omitted. Exact sync and each configuration need review. Embedded BookSim/Ramulator
self-comparisons are not independent L2. STUB, unknown error and unverified energy persist.

## Dependencies, licences and native host

No actual built-image inventory exists. This is source inspection, not a legal-compliance
verdict. The [earlier exact dependency table](../U3-U0005-proposal.md#3-candidate-pins-full-paper-reading-and-licence-dependencies)
remains useful with the Ramulator1 correction above. Rechecked candidate gitlinks and recipes:
BookSim `1d69c9d9db190d130087471b373d12ed4605bf6e`, ONNX
`f7ee1ac60d06abe8e26c9b6bbe1e3db5286b614b`, protobuf
`0dab03ba7bc438d7ba3eac2b2c1eb39ed520f928`; O Ramulator2
`0d063011281a112da29e67cbd708308dd05e7e64`, P Ramulator2
`748cd7099778d7196326aeb6384da92efb0c34c9`; P STONNE
`97804185f00e98e56f74638e4282b9aecab8cfce`. Distinct pins are not interchangeable.

O has root MIT; P has no root licence at this pin. Neither P's paper nor BSD notices in
its Dockerfiles license the entire repository. STONNE grant and complete BookSim wrapper
coverage remain unresolved; one cpptoml MIT header is insufficient. Both torch2timeloop
usage/grants and incorporated/generated code need closure. Both Conan recipes name
Boost 1.79.0, robin-hood-hashing 3.11.5, spdlog 1.11.0, nlohmann_json 3.11.2 without full
recipe/package/transitive locks; O Ramulator2 FetchContent tags also need immutable resolution.
Boost BSL-1.0 is outside the literal [allow-list](../../../third_party/LICENSES.md).
Unknown grants cannot be fixed by declaring an exception; no exception is proposed as accepted.

O's Ubuntu/apt/Python recipe has mutable inputs. P uses `torchsim_base:latest`, a CUDA/cuDNN
PyTorch base, externally supplied GEM5_ASSET_ID/LLVM_ASSET_ID and moving Spike TorchSim branch;
riscv-pk alone is pinned at `4f3debe4d04f56d31089c1c716a27e2d5245e9a1`. Missing compiler/
Gem5/Spike source revisions, build recipes, checksums, runtime and base-image closure are
material blockers. GNU/GPL tools, LGPL runtimes and vendor CUDA terms need exact incorporation
and human scope disposition; the narrow existing LGPL tool exception is not a blanket waiver.
CPU-only packaging remains a dependency question, not assumed permission to remove components.
All serious simulator options inherit these costs. No pins/allow-list/register changed.

Reported designated host: Debian 12 `v2202507191245365394`, `javid@152.53.209.203`, 12 logical
CPUs, about 31.3 GiB RAM; working rootless Podman 4.3.1/user namespaces reported by Javid.
This is not an exclusive reservation or a check under the eventual runner account. No server
contact occurred. Future prerequisites: runner identity and account-specific environment,
current topology/load/free scratch, cgroup CPU/memory/process-tree enforcement, an approved
reservation, online `uarch` runner, B's schedule enablement and successful manual nightly
with actual/no-op jobs distinguished. No WSL2 simulator-performance run or waiver.

Previously proposed envelope remains **ungranted**: one physical core without sibling
contention, one process tree/thread/table worker across lanes, 24 GiB RAM, 100 GiB scratch;
separate build window with at most two jobs. Compiler threading needs enforcement too.
The paper's artifact minimum is 20 GB RAM/50 GB disk; it is no build-resource guarantee.
At a later approved G2 run, timeout at 200 s plus at most 5 s process-tree cleanup retains
raw/partial evidence and distinct timeout/crash/OOM/refusal outcomes. Host/admin/calendar
waits are separate from engineering and simulated device duration.

## Options and active effort

These are planning ranges in person-hours, not commitments, recorded effort or measured
runtime. They **supersede** the suspended A 64–112 h ONNXim/+32–64 h PyTorchSim estimates
and the old A53/B27 allocation for this direction decision. B's completed v1 work is not
subtracted from future fork effort. Assumptions: existing skilled A/B contributors, no
upstream response needed, coherent review rounds; unavailable grants/assets can stop work.

| Option | Adapter / packaging / observation or engine work | Evidence and review | Decision and cost confidence |
| --- | --- | --- | --- |
| Keep exact G2 and pins; defer external engine | Adapter/build/instrumentation **0 authorized**. A source record is sufficient to stop known routes. | 4–8 h coordinator review of this package; no measurements. | Lowest immediate cost; U4/U5 and fork-based U6 dependency stay blocked. High confidence in bounded scope, no delivery date. |
| **Recommended: U-C1 amendment design, then new decision** | A 8–14 h model/boundary/acceptance design; B 8–14 h evidence/gate/plan reconciliation; packaging/instrumentation/engine implementation **0** in this tranche. | Additional 4–8 h independent reviewer/human decision effort. | **16–28 engineering + 4–8 review hours**, medium confidence. Deliver exact proposal and stop. No build/host prerequisite for design. |
| Conditional later U-C1 implementation, only after design acceptance | Adapter/replay 16–32; reproducibility packaging 4–8; observations 12–24; new contention model 48–96 (category 4 for a new engine, category 5 plan change). | Independent fixtures/verification/integration 24–48; review 12–24. | **116–232 total**, low confidence; assumes compute 1, NoC/DRAM 0 and a bounded mapping/state model prove sufficient for a truthful C1. Design may reject that assumption. Public full-grid/report expansion and U4 error campaigns require a new estimate. |
| P compiler/engine extension research at fixed pin | Source/extension design 16–32 first, packaging closure 24–48 if approved/resolvable. Future adapter 24–48 and observation 24–48 only if semantics are established. BF16/fused-paged/rounding/timing extension effort **not credibly bounded yet**. | Initial controls/evidence 12–24; review 8–16. | Initial exploration/design/package/control/review allowance **60–120**, low confidence, excludes engine implementation and production adapter/observation. No honest total-to-G2 estimate. Separate category 3/4/5 decisions; long-lived compiler/ISA/toolchain maintenance. |

For the last option, the small uncertainty-reducing experiment would be an **UNEXECUTED
BF16 matrix capability check**, conditional on explicit experiment/build/licence/host authority;
its exact scope and stopping criteria are in [next-decision.md](next-decision.md). It cannot
resolve fusion/paging/RoPE or pass G2. Source already argues against funding it at this pin.
No ONNXim repair program is costed as serious adapter work: it needs multiple missing
operators, cache/indexing and precision/timing changes, exceeding the released U-P5 policy.

A reduced GEMM-only/FP32 benchmark would change the claim to component characterization,
exclude required model work and change G2(c)/coverage/hardware scope. It could not select the
full-workload fork, unblock U-P7/G3 or stand in for G2. It is not recommended or authorized.

Choosing U-C1 **now** needs U0005 plus explicit plan/prompt amendments allowing source
infeasibility to select the fallback without claiming empirical “both failed.” U4/G3 must name
U-C1, its available precisions, mapping/replay and table/error obligations; U5 stays gated by
that revised G3 and freezes predictions against C1 before silicon. U6 may then use U-C1 at
matched levels, with G5 agreement within 3% on ≥95% of points, determinism and speed evidence
retained unless separately amended. Matched mapping/levels must exist; otherwise specify a
new dependency/deferral, never compare mismatched models. This also needs explicit resolution
of downstream G5 dependencies. A C0 analytic engine relabelled C1 is not the fallback.
“C2 via fork: unbuilt,” external fork reference, public v2 product/report path, detailed mapped
replay and native engine remain unbuilt. No current implementation or accepted policy changes.

## Executed checks and stop point

Executed: source/document inspection and Git identity/ancestry/cleanliness checks; relevant
primary-paper sections; Python3 checks of 27 local links, 34 immutable source citation
paths/line bounds, all 12 prior matrix rows, both parameter counts, tiny 928/1024 totals,
RoPE increments/coefficient allocation and grid/run-budget arithmetic. Candidate checkouts
remained clean. The initial unversioned `python` command was unavailable and ran no checks;
the corrected `python3` invocation passed. Final staged whitespace/path-scope checks and
normal hooks/publication are reported in the handoff. No new Python file,
dependency, source-bound artifact or generated evidence is part of the package. No full
runtime suite, mypy or Ruff rerun is needed for these prose-only additions; no baseline test
result is represented as this author's run. No candidate was built, imported or run; no
measurement or G2 verdict exists. Stop for coordinator reconciliation and Javid's exact
[next decision](next-decision.md), before implementation or experiments.
