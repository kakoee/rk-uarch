# rk-uarch vs *Performance Modeling of Computer Systems*: coverage and execution-readiness review

**Status, 2026-10-01:** F1–F17 and E2 are applied in build-spec Rev 2, the execution plan, the prompts, the READMEs and the rk-sim-side drafts. E1 is done: the protected files were added, CI is green on GitHub, and U0 is tagged `u00-end`. E3 is done: the superseded prompt pack was deleted from the Project.

*2026-09-28. Compared against: `book-toc-performance-modeling.md` (18 chapters, full TOC). The Project docs: `rk-uarch-build-spec.md` (Rev 1), `rk-uarch-execution-plan.md`, `rk-uarch-BOOTSTRAP-PROMPT.md`, `rk-uarch-rk-sim-side-integration.md`, `rk-uarch-track-verdict-and-plan.md`, `rk-uarch-build-plan-and-prompt-pack.md`. The local repo `~/Github/rk-uarch` at `0868dd3`, the only commit. rk-sim at `45bb696`, for the serving loop's KV and prefill behaviour.*

**Status labels.** Covered · Partial · Gap · N/A (a CPU/GPU mechanism with no counterpart on a scratchpad NPU) · Out of scope (excluded on purpose by build-spec §1.3). Finding IDs (F1…, E1…) point to §2.

---

## 1 · Verdict

**The methodology is well structured and, in places, goes further than the book.** It covers:
- the fidelity ladder and the composite rule (book Ch 1.2–1.3);
- claims vs stipulations and applicability (Ch 3.1);
- the L0 → L3 validation ladder with predictions frozen before measurement (Ch 7.7);
- the reporting discipline (Ch 7.6.3);
- the per-level "did detail help?" table, which makes the book's *fit for purpose* (1.3.4) testable.

The book has no counterpart for pre-registration enforced by git history, metamorphic testing, or a badge ceiling for chips that don't exist.

**The weak side is the hardware description and the microarchitectural model**: book Parts III and VI and the NPU counterparts of Parts IV–V. It also shows in the **outputs an architect would read** (Ch 7) and in **energy** (Ch 18). Of the concepts that apply to an NPU, the model runs without:
- memory-level parallelism;
- a defined starting (warm) state;
- DRAM organization and timing;
- per-job issue overhead;
- matrix-engine dataflow;
- KV-cache layout.

Each one makes the numbers **optimistic in a specific, predictable direction**. The validation ladder would then report that bias as "method error" without being able to name it.

**Timing is good.** The repo is at U0 (bootstrap, not yet tagged), and U-P1 (the contract) is the next session. Eight of the findings below are **contract fields**. They cost one line each now. After G1 each needs a MINOR bump plus an ADR. After U5's predictions are frozen, they need a new prediction set.

**Execution readiness.** U0's exit criterion is not met yet: there is no CI, no Makefile and no remote (E1). The plan's effort is about 1,274 h realistic, with Lane A (about 778 h) on the critical path, so about 39 weeks at 20 h/week. It runs alongside rk-sim, which is the committed priority.

### Coverage count (concept rows in §3)

| Status | Rows |
|---|---|
| Covered | 69 |
| Partial | 43 |
| Gap | 22 |
| N/A (no NPU counterpart) | 27 |
| Out of scope (by design) | 3 |
| **Total** | **164** |

Of the 134 rows that apply to an NPU, 69 are covered, 43 partial and 22 gaps. About half of the partial and gap rows (34 of 65) trace back to F1–F8, which are contract fields. F14, the output statistics, accounts for 12 more.

---

## 2 · Findings, ranked

### 2a · Fix before U-P1: these are contract fields

**F1 · Memory-level parallelism and transfer granularity are missing.** *Book 2.2.2, 11.4.2, 12.3, 14.2.3, 14.3.3, 14.5.2, 15.3, 15.5.*

**What's missing.** The bandwidth a requester actually gets is capped by outstanding requests × request size ÷ round-trip latency (Little's law). rk-uarch's DMA is `{engines, bytes_per_cycle}`. It has no limit on outstanding transfers and no request or burst size. L0m checks that "bandwidth ×2 is never slower", but has no latency relation.

**Why it matters.** A core many hops from its memory controller still streams at full link rate. So mesh designs look optimistic in exactly the regime the native engine exists for. Decode, which issues small transfers, looks better than it is.

**Fix.**
- U-P1: add `dma.max_outstanding` and `dma.request_bytes` (and the NIU equivalents) as SourcedValues.
- U-P8: an L1 closed form, `bw = min(peak, outstanding × request_bytes / rtt)`.
- U-P6: an L0m relation, "raising any latency never shortens duration".
- U-P15: a Blackhole benchmark that sweeps transfer size × hop distance.

**F2 · The simulated starting state is undefined, while silicon is measured warm.** *Book 6.3, 6.4.1.*

**What's missing.** U-P10's kits run warm-up repetitions before measuring. The simulator's starting state is not defined: SRAM contents, open DRAM rows, and whether the next iteration's first-layer weights are already in flight. The verdict's "steady state, weights in HBM" (§D.2 item 6) never made it into the build-spec or the contract.

**Why it matters.** Every L3 comparison sets a warm measurement against a prediction from an unspecified state. The difference lands in "method error".

**Fix.**
- Add a request field `initial_state: cold | steady`, a stipulation carried on every row. `steady` means simulate one priming iteration and report the second.
- Each prediction file states which state it used.
- Each table reports the cold-vs-steady delta once.

**F3 · Layer reuse is sampling, and its error is never measured.** *Book 6.2, 6.2.5, 6.4.2.*

**What's missing.** `layer_reuse` (simulate one decoder layer, multiply by `n_layers`) is the SimPoint move: pick a representative interval and weight it. It is declared, but `measured_error` only holds `interpolation_loo` and `composition_reduction`.

**Why it matters.** Anything that crosses a layer boundary is dropped silently: the next layer's weight DMA overlapping this layer's compute, and NoC and DRAM state carrying over.

**Fix.** Add `measured_error.layer_reuse` to `table.py`. For a seeded sample of grid points, simulate all layers and report the deviation. Like the composition error, it is reported and never corrected.

**F4 · DRAM organization, timing, controller policy and address interleaving are absent.** *Book 8.2, 8.3, 10.1.*

**What's missing.** The spec's DRAM is `{standard, channels, bw_bytes_per_s, capacity_bytes}`, and a controller is only `{attach}`.

**Why it matters.**
- At level 2, Ramulator 2 runs on its own preset timings and organization. Dozens of numbers that decide the answer never become SourcedValues, which breaks invariant 2 without anyone noticing.
- On a mesh, the interleaving scheme decides which cores talk to which controller, and so decides the NoC traffic pattern.

**Fix.**
- Add `dram.organization` and `dram.timing`. A timing preset can be recorded as a claim whose source is the preset file plus its hash.
- Add `memory.interleave {granularity_bytes, scheme}` and `controller {scheduler, page_policy}`.
- Each engine lists the fields it cannot represent.

**F5 · There is no per-job issue or synchronization overhead, and the device/host line isn't drawn.** *Book 5.7.1, 11.2.1, 11.5.4, 13.5, 14.2.2.*

**What's missing.**
- Tile jobs start the moment their dependencies resolve. There is no per-job cost for instruction issue, descriptor setup or semaphores.
- There is no barrier mechanism or barrier latency parameter.
- No L3 suite has a synchronization class.
- Host and runtime are correctly out of scope, but SUITE.md never says to compare device-side time only.

**Why it matters.** Decode at small batch is many small jobs, where fixed costs can dominate, so decode rows will be optimistic. And L3 end-to-end numbers may include runtime gaps that no uarch model could ever predict.

**Fix.**
- Add `core_type.job_overhead` and `sync.barrier_latency` (claims or stipulations).
- Add an L3 class for barrier and semaphore latency on Blackhole, and per-op launch overhead on both chips.
- Add a SUITE.md rule to compare device-side time only.
- Declare "host/runtime" as an omission on every row; rk-sim's R-axis owns it.

**F6 · The matrix engine has no dataflow field.** *Book 16.3, 17.3.*

**What's missing.** `matrix_engine` is `{array, macs_per_cycle}`. Dataflow (weight-, output- or input-stationary) appears only implicitly, in the name of the mapping policy `ws-rowsplit@1`.

**Why it matters.**
- The level-1 fill/drain formula and the SRAM operand bandwidth both depend on dataflow.
- SCALE-Sim, U-P8's L2 reference, takes dataflow as a config input, so the comparison is underspecified.
- A design study can't compare dataflows, which is the book's canonical accelerator experiment.

**Fix.**
- Add `matrix_engine.dataflow` (the supported set) to the spec.
- Each mapping policy declares the dataflow it requires.
- Add an example study: dataflow on npu-l4.

**F7 · The KV-cache layout is not in the request, and DRAM validation covers streaming only.** *Book 3.2.4, 8.3.3, 10.3–10.4.*

**What's missing.**
- rk-sim pages KV in `block_size` blocks (`rk/engine/f1/serving.py`), but the request carries no layout.
- Both L3 suites test only DRAM streaming: the TPU suite's read/write/copy, and Blackhole's per-channel and all-channel streaming.

**Why it matters.** In decode, attention reads are a gather over pages, not a stream. Row-buffer hit rate and descriptor count both differ. The DRAM model is validated only on its easiest pattern.

**Fix.**
- Add a request field `kv_layout {block_size_tokens}`, taken from rk-sim's plan, and have the op graph emit page-sized KV DMA.
- Add a strided/gather benchmark at page granularity to both SUITE.md files.

**F8 · The evidence scope can't express what applicability checks, and the demo claim may never be reachable.** *Book 3.1.1–3.1.5, 3.2.3, 3.2.5.*

**What's missing.**
- U-P4's applicability checks five dimensions: family, op class, precision, shape regime and load regime. The contract's `validated_error_band.scope` carries only `{family, op_classes}`.
- "Shape regime" and "load regime" are never defined.
- TPU operator benchmarks are 8B-class shapes in bf16/int8. Blackhole shapes are not pinned, and its headline 8-bit format is BLOCKFP8, which is not the same thing as fp8.
- Neither suite is worked backward from the demo request: npu-m256 with a 70B model in fp8.

**Why it matters.** The §1.2 demo ends on "validated band X% for {classes} on {family}". By construction, its request may fall outside every scope and stay `stub`.

**Fix.**
- The contract carries the full applicability vector in its scope.
- Define shape-regime bins, for example per-op M/N/K ranges or operational-intensity ranges.
- Add a `uarch characterize` command that reports op mix, bytes and operational intensity per op across the grid, and use it to choose L3 shapes that cover the demo's per-op regimes.
- Decide in U0001 whether BLOCKFP8 evidence applies to an fp8 request.

### 2b · Fix in the prompt that owns it

**F9 · No shared on-chip memory level exists.** *Book 2.1.4, 8.1, 14.3.2, 16.4.1.*

**What's missing.** The hierarchy is fixed at per-core SRAM plus DRAM. There is no global buffer, last-level cache (LLC) or TPU v4-style CMEM.

**Why it matters.** A study can't ask "per-core SRAM or shared SRAM?", and KV held in shared SRAM can't be expressed.

**Fix.** Decide in U0001. Adding it later is an additive MINOR bump. If it is deferred, add "no shared on-chip level" to what each table does not claim.

**F10 · SRAM capacity isn't enforced, and data layout has no source.** *Book 14.4, 16.4.2, 17.1.4.*

**What's missing.** HBM residency is checked (U-P7 item 7) but per-core SRAM is not. Compute level 2 models bank conflicts, but no stage produces buffer addresses or bank assignments.

**Fix.**
- TaskGraph buffers carry `{core, offset_bytes, bank}` from the mapping policy (U-P7, U-P13).
- Add an L0 invariant, "per-core SRAM occupancy ≤ capacity at every event", with a mutant (U-P6).
- The mapping refuses a tile that doesn't fit.

**F11 · Energy is reported but no rung checks it.** *Book Ch 18.*

**What's missing.**
- Energy per token is counts × pJ coefficients plus static power, and nothing verifies it.
- Timeloop and Accelergy were in the verdict's L2 list and were dropped from build-spec §2.7.
- The flagship demo study doubles SRAM per core (1.5 → 3 MB) with a fixed pJ/byte, although energy per SRAM access grows with capacity.
- The frequency axis has no voltage scaling of energy.

**Fix.**
- Add an L0 energy-conservation invariant.
- Tie SRAM pJ/byte to capacity through an Accelergy/CACTI estimate (L2), or make studies re-stipulate it for each variant.
- Label energy "unverified" until a rung exists.
- Optionally, use Blackhole board-power telemetry as a coarse L3 check, if the card exposes it.

**F12 · At L3, mapping error is mixed with model error.** *Book 16.5, 3.1.2.*

**What's missing.** TPU v5e benchmarks run XLA's own tiling while the predictions use uarch's policy. The Blackhole kit programs kernels in the style of `summa-2d@1`. The ledger doesn't tell these two cases apart.

**Fix.** SUITE.md tags each benchmark `mapping: matched | compiler-chosen`. Ledger classes split on that tag, and G4 is read on the matched classes first.

**F13 · The workload is only checked against a mirror.** *Book 5.5.3, 3.2.2.*

**What's missing.** The operator graph is checked against rk-sim's closed form, which is an analytic model with the same assumptions. Parity proves consistency, not correctness. Nothing compares it with what a compiler actually runs: fusions, layout copies, KV gathers, padding.

**Fix.** In U-P9 and U-P10, record the compiler-reported FLOPs and bytes per benchmark (XLA compiled cost analysis, and TT-Metalium's counts where available). Add them to the ledger as a workload-fidelity check, with declared deviations.

**F14 · Outputs are too coarse for an architect, and attribution is undefined.** *Book 2.1.2, 4.2, 7.1–7.5, 13.1.4, 17.4.*

**What's there.** Rows carry duration, `u_c0`, a four-way `attribution_s`, counts, `ext_counts` and residency. `EngineResult` adds busy time and "simulator metrics".

**What's missing.**
- Utilisation (achieved vs peak).
- SRAM bank-conflict stalls.
- DMA/compute overlap.
- NoC mean and p99 latency, and the hottest link's utilisation.
- DRAM bandwidth utilisation and row-hit rate.
- Queue occupancy.
- A per-op roofline plot.
- A defined attribution method: how overlapping stalls are attributed, for example by critical path.
- An invariant that `attribution_s` sums to `duration_s`.
- A per-resource timeline for debugging.

**Fix.**
- `EngineResult.diagnostics`, internal to uarch and not in the rk-sim contract (U-P5, U-P11).
- A report section (U-P4).
- The attribution invariant (U-P6).
- `STAT_SAMPLE` events exported as Chrome-trace JSON.

**F15 · A study covers one workload, and errors are unweighted.** *Book 3.3–3.4, 6.2.5, 6.4.4, 7.6.2, 9.2.1.*

**What's missing.** A StudySpec takes one request template. The LOO interpolation error is an unweighted median/max over grid points, even though rk-sim runs visit a narrow region of the grid.

**Fix.**
- A versioned workload suite: models × precision × phase × named operating points.
- StudySpec runs over a suite and reports each workload plus the geometric mean of normalised speedup, never the arithmetic mean of ratios.
- Report LOO error weighted by rk-sim's visit distribution (ADR 0046's timeline export) as well as unweighted.

**F16 · The L1 DRAM streaming check conflicts with level 2.** *Book 8.2.3.*

**What's missing.** U-P8's check is "saturated streaming = configured bandwidth ±5%". Ramulator 2 charges refresh, row switches and bank-group timing, so sustained bandwidth sits below peak. The check will either fail, or be met by quietly setting "bandwidth" to the sustained figure.

**Fix.** Derive the expected efficiency from the spec's timing parameters (F4). Or apply the check at levels 0–1 only, and bound level 2 between the derated figure and peak.

**F17 · Mixed prefill/decode iterations can't be priced (a forward-looking limit).** *Book 6.1.2.*

**What's missing.** rk-sim runs prefill-first, as separate iterations. Chunked prefill is a named extension point in `_next_phase`, deferred for now.

**Why it matters.** Once chunked prefill lands, a mixed iteration isn't a decode row plus a prefill row, because the weights stream only once.

**Fix.** Record this in U0001 as a known limit of the query space, and reserve a `mixed` phase for a later MINOR bump.

### 2c · Execution readiness

**E1 · U0 is not finished.**

**State.** The repo has one local commit (`0868dd3`), no remote and no tag. Missing files:
- `Makefile`
- `.pre-commit-config.yaml`
- `.github/CODEOWNERS`
- `.github/pull_request_template.md`
- `.github/workflows/ci.yml`
- `.github/workflows/nightly.yml`

The hook scripts aren't executable (mode `-rw-------`). The U0 handoff says the remote tools refused to write these files.

**Why it matters.** Every mechanical guarantee in the plan runs through these files: the golden ceremony, `check_ordering`, the determinism job, the human-owned-path hook.

**Fix.** Add them from BOOTSTRAP PART 3, `chmod +x scripts/hooks/*.sh`, push to a private remote, confirm CI is green, and tag `u00-end`. All of this before U-P1.

**E2 · The Python version isn't pinned.** `uv` resolved Python 3.14.7, while the spec says 3.12. There is no `.python-version`. Byte-identical tables across the laptop, the Linux box and CI (invariant 4) need a single interpreter. **Fix:** add `.python-version` set to `3.12`, plus a matching upper bound or a pin in CI.

**E3 · Superseded plans still sit in the Project with clashing numbering.** `rk-uarch-build-plan-and-prompt-pack.md` has U-P0…U-P17 over 8 sprints, where U-P14 is the error-vs-quantum work and U-P17 is the review. In the build-spec, U-P14 is design studies and U-P17 is the parallel engine. The verdict doc's "not now; don't write the engine" has also been overtaken by the decision to proceed. An agent handed either file would build the wrong thing. **Fix:** put a `SUPERSEDED by build-spec Rev 1 + execution-plan` header on both.

---

## 3 · Concept-by-concept coverage

### Part I · Foundations

| § | Concept | Status | Where in rk-uarch | Finding |
|---|---|---|---|---|
| 1.1–1.1.2 | Role and use cases of performance modeling | Covered | build-spec §1.1 (one question), §1.2 demo (design study, rk-sim integration) | |
| 1.1.3 | History | N/A | background | |
| 1.2.1 | Analytical models | Covered | U-C0 (aggregate + per_op); level 0 on every subsystem | |
| 1.2.2 | Transaction-level models (TLM) | Covered | Level 1 reservation calendars ≈ TLM approximately-timed; lax sync ≈ TLM-2.0 quantum keeper (U-P17) | |
| 1.2.3 | Cycle-accurate simulation | Covered | Level 2 (BookSim 2, Ramulator 2); level 3 reference (Gemmini RTL on Verilator) | |
| 1.3.1–1.3.3 | Accuracy / speed / flexibility trade-offs | Covered | Per-subsystem ladder and composite rule; per-point budget (G2d); simulator metrics (U-P12); error-vs-quantum curve (U-P18); fork (validated, rigid) vs native (flexible) | |
| 1.3.4 | Fit for purpose | Covered | G7's per-level error table ("did detail help?"); the level-1 fast path stays the default if not | |
| 1.3.5 | Case study: prefetcher evaluation | N/A | CPU-specific | |
| 1.4.2–1.4.4 | ChampSim, gem5, Accel-Sim | N/A | CPU and GPU simulators | |
| 1.4.5 | SCALE-Sim | Covered | L2 reference for tile compute (U-P8) | F6 |
| 1.4.6 | Supporting tools | Partial | BookSim 2, Ramulator 2, Gemmini/Verilator and tt-npe are in; Timeloop and Accelergy were dropped between the verdict and the build-spec | F11, F12 |
| 2.1.1–2.1.2 | Compute-memory balance; operational intensity | Partial | U-C0 roofline, with attribution by the bounding roof; no per-op operational-intensity output or roofline plot | F14 |
| 2.1.3 | Compute resources | Covered | Matrix and vector engines; `macs_per_cycle` per format; format accumulate width | |
| 2.1.4 | Memory resources | Partial | Per-core SRAM (banked) and DRAM only | F9 |
| 2.1.5, 2.3.4 | Cross-platform comparison | Covered | Two reference classes (TPU v5e, Blackhole); rk-sim Compare with the bias banner (U-P20) | |
| 2.2.1 | Bandwidth constraints | Covered | DRAM, NoC link, SRAM per bank and DMA bandwidths, all SourcedValues | |
| 2.2.2 | Latency constraints | Partial | Router and DRAM latency exist; latency never limits bandwidth | F1 |
| 2.3.1 | ILP | Covered | Counterpart: matrix, vector and DMA engines overlap within a core through TaskGraph dependencies | |
| 2.3.2–2.3.3 | TLP, DLP | Covered | Core grid and mapping across cores; systolic array and vector engine | |
| 3.1.1–3.1.2 | Sample → population; representativeness failures | Partial | Applicability dimensions exist; shape regime is undefined; L3 shapes aren't derived from the demo request | F8 |
| 3.1.3 | Claims and applicability | Covered | Claim vs stipulation; ADR 0021 applicability; `conditional_on` | |
| 3.1.4 | Evidence requirements by claim strength | Covered | Badge by rung (L0–L2 → stub, L3 → estimated, L4 → measured); proposed designs capped at estimated | |
| 3.1.5 | Working backward from claims | Partial | The demo's closing claim is defined; the L3 suites aren't built backward from it | F8 |
| 3.1.6 | Example: cache replacement study | N/A | CPU-specific | |
| 3.2.1 | Purpose of workload characterization | Gap | No characterization of the operator graph (op mix, bytes, operational intensity per op, per phase) | F8 |
| 3.2.2 | Hardware performance counters | Partial | Kits capture durations; counts only "where measurable" | F13 |
| 3.2.3 | Characterizing operational intensity | Partial | Computable from counts but never reported | F8, F14 |
| 3.2.4 | Characterizing memory access patterns | Gap | KV page gather not represented; DRAM evidence is streaming only | F7 |
| 3.2.5 | Clustering and visualization | Gap | L3 shapes and grid density are chosen by hand | F8 |
| 3.3.1 | CPU benchmark suites | N/A | CPU-specific | |
| 3.3.2 | GPU and accelerator workloads | Partial | Llama-class ModelSpecs from rk-sim fixtures; no named, versioned workload suite | F15 |
| 3.3.3 | Server and cloud workloads | N/A | Serving workloads belong to rk-sim | |
| 3.3.4 | Limitations of suites | Covered | `omissions` → table warnings; "what this table does not claim" | |
| 3.4.1–3.4.3 | Practical workload selection | Partial | Default grid plus three fixture models; no selection rationale | F15 |
| 4.1 | From trace to statistics | Covered | request → op graph → TaskGraph → engine → table → provenance → report (`src/rkuarch/README.md`) | |
| 4.2 | Path of a memory access | Partial | Event kinds cover DMA → NoC → memory; no walkthrough of one transfer and no timeline export | F14 |

### Part II · The simulation pipeline

| § | Concept | Status | Where in rk-uarch | Finding |
|---|---|---|---|---|
| 5.1.1 | Trace contents | Covered | Counterpart: operator graph synthesized from ModelSpec + ModelShape | |
| 5.1.2 | What traces omit | Covered | The graph-level `omissions` list becomes table warnings | |
| 5.1.3 | Trace formats | Covered | EngineJob, TaskGraph and EngineResult JSON; the fork's `workload_writer` | |
| 5.2–5.2.1 | Choosing a collection approach | Covered | Decision recorded: synthesized graph, never ONNX or PyTorch as the source of truth (§1.3, U-P1 guardrail) | |
| 5.3 | Dynamic binary instrumentation (Pin) | N/A | Counterpart on silicon: JAX profiler and TT-Metalium profiler zones (U-P10, U-P16) | |
| 5.4 | Generating and compressing ChampSim traces | N/A | CPU-specific | |
| 5.5.1 | Trace sanity checks | Covered | ModelShape parity ≤ 1%; FLOP parity ≤ 0.5% with named deviations | |
| 5.5.2 | Instruction mix analysis | Covered | Counterpart: op, FLOP and byte counts per op class vs rk-sim's own fixtures | |
| 5.5.3 | Hardware counter validation | Gap | The workload is never checked against a real compiler or counters | F13 |
| 5.5.4 | End-to-end validation | Covered | L3 end-to-end class (decoder layer) on TPU v5e; multi-core on Blackhole | |
| 5.6.1–5.6.2 | Naming conventions; metadata | Covered | Content hashes (spec, request, table), image digest, engine version and mapping policy on every result | |
| 5.6.3 | Storage considerations | Partial | `tables/` is gitignored; no stated home for large artifacts (tables, profiler CSVs, fork stats) | — |
| 5.6.4 | Version control and artifact management | Covered | Vendored snapshot with MANIFEST; immutable results; golden ceremony; ledger | |
| 5.7.1 | The user-kernel gap | Partial | Host and runtime are out of scope, but the device-vs-host line isn't drawn in the L3 suites or row omissions | F5 |
| 5.7.2 | Missing wrong-path execution | Out of scope | No speculation in static dataflow; the closest counterpart, data-dependent MoE routing, is declared absent | |
| 6.1.1–6.1.2 | Application and phase behaviour | Covered | Separate prefill and decode grids; decode's evolution follows the T axis | F17 |
| 6.2.1–6.2.3 | SimPoint: BBVs, clustering, workflow | Partial | Counterparts: layer reuse (one representative layer × n_layers) and grid + interpolation; neither sampling error measured for layer reuse | F3 |
| 6.2.4 | From SimPoint to traces | N/A | CPU-specific | |
| 6.2.5 | Weighted results | Partial | Layer weight = n_layers is declared; interpolation error is unweighted | F3, F15 |
| 6.2.6 | Other sampling approaches | Partial | Composition error comes from a seeded sample whose size and uncertainty aren't specified | — |
| 6.3.1, 6.3.3 | Functional warming; warm-up length | Gap | Simulated starting state undefined | F2 |
| 6.3.2 | Checkpointing | N/A | Counterpart: tables cached by request hash | |
| 6.4.1 | Insufficient warming | Gap | as 6.3 | F2 |
| 6.4.2 | Short intervals | Gap | One-layer sampling error is unmeasured | F3 |
| 6.4.3 | Ignoring low-weight points | Covered | Out-of-grid queries refused; envelope checked at build time; max LOO reported | |
| 6.4.4 | Unweighted averaging | Partial | The gates forbid averaging across classes (good); LOO is unweighted | F15 |
| 7.1.1–7.1.2 | Output report; output and the pipeline | Covered | UarchCostTable, `fidelity_detail` and provenance; HTML and Markdown report | |
| 7.2.1 | IPC (throughput) | Partial | No achieved-vs-peak utilisation metric | F14 |
| 7.2.2 | CPI and the stall budget | Partial | `attribution_s` is the stall stack, but its method and its sum-to-duration rule are undefined | F14 |
| 7.3.1 | Cache statistics | Partial | Counterpart: SRAM bank conflicts modelled at level 2, but no statistics surfaced | F14 |
| 7.3.2 | Cross-level cache analysis | Partial | SRAM and DRAM bytes can be derived from `counts` and `ext_counts`, but reuse isn't reported | F14 |
| 7.3.3 | Prefetcher statistics | Partial | DMA/compute overlap not surfaced | F14 |
| 7.4 | Branch predictor metrics | N/A | No control speculation | |
| 7.5 | DRAM metrics | Partial | Bytes only; no row-hit rate, bandwidth utilisation or queueing latency | F14 |
| 7.6.1 | Normalized speedup | Covered | Study diff per point; each variant's detail delta vs its own U-C0 | |
| 7.6.2 | Geometric mean over workloads | Gap | One request template per study | F15 |
| 7.6.3 | Guidelines for reporting results | Covered | Stronger than the book: `badged()`, "unknown" error band, "conditional", "what this table does not claim", tornado labelled "local sensitivity" | |
| 7.7.1 | Internal consistency checks | Covered | L0 invariants | |
| 7.7.2 | Cross-metric plausibility checks | Covered | L0m metamorphic relations; L1 limits, including C2 ≥ its own U-C0 | |
| 7.7.3 | Reference data comparison | Covered | L2 differential; L3 silicon with frozen predictions | |

### Part III · Memory system modeling

| § | Concept | Status | Where in rk-uarch | Finding |
|---|---|---|---|---|
| 8.1.1–8.1.3, 8.1.5–8.1.6 | Set-associativity, miss classes, replacement, write and inclusion policies | Partial | These don't apply to per-core scratchpads, but the spec can't describe any cache or shared level | F9 |
| 8.1.4 | Prefetching | Covered | Counterpart: DMA double-buffering (compute level 1) | |
| 8.2.1 | DRAM organization | Gap | Only standard and channel count | F4 |
| 8.2.2 | DRAM timing parameters | Gap | Not in the spec; Ramulator presets stay hidden | F4 |
| 8.2.3 | Refresh overhead | Gap | Not in level 1; conflicts with the L1 streaming check | F4, F16 |
| 8.3.1 | Address mapping | Gap | No interleaving scheme | F4 |
| 8.3.2 | Controller scheduling policies | Gap | Not a spec field | F4 |
| 8.3.3 | Row-buffer management | Partial | Level 1 approximates the row buffer; page policy isn't a spec field; KV gather not modelled | F4, F7 |
| 8.4 | Address translation and TLBs | N/A | Not modelled; should be listed in the declared omissions | — |
| 9.1.1 | Cache hierarchy organization | Covered | HardwareSpec YAML (within the F9 limit) | F9 |
| 9.1.2 | Modifying parameters | Covered | StudySpec varies stipulations only; reference specs are locked to claims | |
| 9.2.1 | Workload selection | Partial | See 3.3–3.4 | F15 |
| 9.2.2 | Key metrics | Partial | Duration and energy per token; architect-level metrics missing | F14 |
| 9.2.3 | Experimental process | Covered | Pre-registration; one prompt per session; acceptance tests first | |
| 9.2.4 | Companion repository setup | Covered | Golden scenarios; `make demo-data`; demo script with hashes | |
| 9.3 | Replacement policies (interface, LRU, SRRIP) | N/A | Scratchpads; the analogous pattern, a policy interface, is the mapping-policy protocol | |
| 9.4 | Prefetchers (interface, next-line, filtering) | Covered | Counterpart: double-buffered DMA inside mapping policies; buffer depth should be a named policy parameter | F1 |
| 10.1.1–10.1.2 | DRAM configuration; modifying parameters | Gap | See 8.2 | F4 |
| 10.2 | DRAM experimental design | Covered | General study and L2/L3 machinery | |
| 10.3 | DRAM timing experiment | Partial | L2 vs Ramulator on streaming, random and strided traces; L3 is streaming only | F7 |
| 10.4 | Row-buffer management experiment | Partial | as 8.3.3 | F4, F7 |
| 10.5 | Adaptive row-buffer management | N/A | Controller design exploration isn't a v1 goal | |

### Part IV · CPU core modeling (NPU core counterparts)

| § | Concept | Status | Where in rk-uarch | Finding |
|---|---|---|---|---|
| 11.1.1 | Pipeline organization | Covered | Counterpart: systolic fill/drain pipeline formula (L1 fixture) | F6 |
| 11.1.2 | Depth vs frequency trade-off | Out of scope | Frequency is stipulated; no physical or area model (§1.3) | |
| 11.2.1 | Fetch and decode | Gap | Counterpart: no per-job issue or dispatch overhead | F5 |
| 11.2.2 | Branch prediction | N/A | Static dataflow | |
| 11.3.1 | Execution models | Covered | Counterpart: analytic, fork and native engines at several levels | |
| 11.3.2–11.3.5 | Rename, ROB, scheduling, retirement | N/A | Out-of-order CPU; counterpart: TaskGraph dependency-driven scheduling | |
| 11.4.1, 11.4.3 | Load/store queue; store buffer | N/A | CPU-specific | |
| 11.4.2 | MSHRs and memory-level parallelism | Gap | No outstanding-request limit | F1 |
| 11.5.1 | Shared resources and contention | Covered | NoC and DRAM contention at level ≥ 1; "contention visibly bites" test (U-P13) | |
| 11.5.2 | Cache coherence | N/A | Explicit data movement, no coherence; worth one glossary line | — |
| 11.5.3 | On-chip interconnect | Covered | NoC ladder; multiple NoCs; mesh/torus; virtual channels; multicast; BookSim 2 and tt-npe references | |
| 11.5.4 | Synchronization cost | Partial | Barriers exist in TaskGraph and "sync" in attribution; no cost parameters and no L3 class | F5 |
| 12.1.1 | CPU models (atomic → out-of-order) | Covered | Counterpart: fidelity levels 0 / 1 / 1+ts / 2 / 3 | |
| 12.1.2–12.1.3 | Configuration script; default parameters | Covered | HardwareSpec + request; reference specs with stubs in UNKNOWNS.md | |
| 12.1.4 | Pipeline in code | Covered | Native engine spec §2.8 | |
| 12.2 | CPU experimental design | Covered | General machinery | |
| 12.3 | ROB size and the instruction window | Partial | Counterpart: in-flight buffer depth; double-buffering is fixed, with no window study | F1 |
| 12.4 | Execution unit bandwidth | Covered | `macs_per_cycle` and `ops_per_cycle` stipulations; studies can vary them | |
| 12.5 | Squash recovery delay | N/A | No speculation | |
| 13.1.1 | Classic vs Ruby memory systems | Covered | Counterpart: DRAM level 1 vs Ramulator 2; reservation NoC vs BookSim 2 | |
| 13.1.2 | MESI two-level hierarchy | N/A | No coherence | |
| 13.1.3 | Configuration script | Covered | as 12.1.2 | |
| 13.1.4 | Ruby statistics output | Partial | Per-subsystem statistics aren't surfaced | F14 |
| 13.2 | Multicore experimental design | Covered | General machinery | |
| 13.3 | Multicore scaling | Covered | Blackhole summa on 1, 4, 16 and 64 cores; 16×16 and 32×32 tables; thread-scaling curve (U-P17) | |
| 13.4 | False sharing | N/A | Counterpart: hotspots and bank conflicts (U-P13 hotspot test) | |
| 13.5 | Synchronization cost experiment | Partial | No barrier benchmark | F5 |

### Part V · GPU modeling (NPU counterparts)

| § | Concept | Status | Where in rk-uarch | Finding |
|---|---|---|---|---|
| 14.1 | SIMT, warps, blocks, the compute unit | N/A | Counterpart: core grid + TaskGraph | |
| 14.2.1 | Warp scheduling mechanics | Covered | Counterpart: event-driven task scheduling per core | |
| 14.2.2 | Instruction and memory latencies | Partial | Engine and memory latencies exist; per-job fixed cost doesn't | F5 |
| 14.2.3 | Latency hiding | Partial | Double-buffering, but no outstanding-request limit | F1 |
| 14.3.1 | Shared memory and L1 | Covered | Per-core banked SRAM | |
| 14.3.2 | L2 cache and HBM | Partial | HBM/DRAM yes; no L2 or shared level | F9 |
| 14.3.3, 14.5.2 | Memory coalescing; uncoalesced access | Gap | Counterpart: no transfer or burst granularity | F1 |
| 14.3.4 | Asynchronous data movement | Covered | DMA engines; TaskGraph DMA jobs | |
| 14.4 | Occupancy and resource limits | Partial | SRAM capacity isn't enforced | F10 |
| 14.5.1 | Warp divergence | N/A | SIMT-specific | |
| 14.5.3 | Bank conflicts | Partial | Modelled at compute level 2, but nothing supplies the layout | F10 |
| 14.5.4 | Atomic contention | N/A | No atomics in scope | |
| 14.5.5 | Execution throughput bottlenecks | Covered | Attribution; per-op roofline mode | F14 |
| 15.1.1–15.1.2 | Simulator organization; configuration files | Covered | Counterpart: fork adapter (`config_writer`, `workload_writer`, `runner`, `stats_parser`) | |
| 15.1.3 | Trace format | Covered | Counterpart: EngineJob / TaskGraph JSON | |
| 15.2 | GPU experimental design | Covered | General machinery | |
| 15.3 | Memory coalescing experiment | Gap | Counterpart: a transfer-size sweep | F1 |
| 15.4 | Warp divergence experiment | N/A | SIMT-specific | |
| 15.5 | Latency tolerance experiment | Gap | No L0m latency relation and no latency-sweep study | F1 |

### Part VI · Accelerator modeling (the most directly relevant part)

| § | Concept | Status | Where in rk-uarch | Finding |
|---|---|---|---|---|
| 16.1 | The case for tensor accelerators | Covered | Context: build-spec §1.1 | |
| 16.2.1 | Array organization | Covered | `matrix_engine.array`; `macs_per_cycle` per format | |
| 16.2.2 | Data movement through the array | Covered | Fill/drain pipeline formula (compute level 1; L1 hand fixture) | F6 |
| 16.2.3 | The TPU example | Covered | TPU v5e reference spec and L3 suite | |
| 16.3 | Dataflow choices | Gap | No dataflow field; only implied by a policy name | F6 |
| 16.4.1 | Scratchpad hierarchy | Partial | One scratchpad level per core; no global buffer and no accumulator/operand split | F9 |
| 16.4.2 | Software-managed data movement | Covered | DMA jobs from named, versioned mapping policies | F10 |
| 16.5 | Mapping and performance bottlenecks | Partial | Named policies and tile quantisation; at L3 mapping error isn't separated from model error; Timeloop dropped | F12 |
| 17.1.1–17.1.2 | SCALE-Sim architecture model; config file | Covered | L2 reference for tile compute | F6 |
| 17.1.3 | Topology file (layer shapes) | Covered | Counterpart: operator vocabulary with named M/N/K dimensions | |
| 17.1.4 | Layout file | Gap | Data layout feeds neither bank conflicts nor row locality | F10 |
| 17.2 | Accelerator experimental design | Covered | General machinery | |
| 17.3 | Dataflow comparison | Gap | Can't be expressed | F6 |
| 17.4 | Array size and mapping efficiency | Partial | Studies can vary array size; utilisation isn't an output; no example study | F14 |
| 17.5 | Sparsity | Out of scope | Declared in §1.3 | |

### Part VII · Power modeling

| § | Concept | Status | Where in rk-uarch | Finding |
|---|---|---|---|---|
| 18.1 | Why model power | Partial | Activity counts × coefficients plus static power, with no rung | F11 |
| 18.2 | CPU power (McPAT) | N/A | Counterpart would be Accelergy/CACTI, which were dropped | F11 |
| 18.3 | GPU power (AccelWattch) | N/A | Counterpart would be measured board power | F11 |
| 18.4 | Looking further (thermal, DVFS power) | Partial | Thermal feedback is out of scope; energy doesn't scale with voltage along the frequency axis | F11 |

### Cross-cutting

| § | Concept | Status | Where in rk-uarch | Finding |
|---|---|---|---|---|
| Ch 9–17 | The experiment template: tool setup → configuration → experimental design → experiment → results and explanation | Covered | One prompt per session with acceptance tests; ADRs; pre-registered gates; L2 deviations attributed to a named mechanism; `docs/results/`; how-it-works refresh | |

---

## 4 · Proposed contract additions for U0001 (paste into the U-P1 session as a proposal)

The contract is human-owned, so these are proposals for both founders. Every numeric leaf is a SourcedValue: a claim on references, a stipulation on designs.

```yaml
# HardwareSpec
cores:
  core_type:
    matrix_engine: {array: [32, 32], dataflow: [weight_stationary],   # F6: supported set
                    macs_per_cycle: {...}}
    dma: {engines: 2, bytes_per_cycle: {...},
          max_outstanding: {...}, request_bytes: {...}}               # F1
    job_overhead_cycles: {...}                                         # F5: issue/descriptor/semaphore
sync: {mechanism: noc_semaphore, barrier_latency_cycles: {...}}        # F5
shared_sram: null                                                      # F9: decide now, or declare absent
memory:
  interleave: {granularity_bytes: {...}, scheme: channel_hash}         # F4
  controllers: [{attach: [0, 0], scheduler: fr_fcfs, page_policy: open}]
  dram: {standard: gddr6, channels: 8, bw_bytes_per_s: {...}, capacity_bytes: {...},
         organization: {...}, timing: {preset: <name>, source: <file@sha>}}   # F4

# CharacterizationRequest
initial_state: steady                  # F2: cold | steady; a stipulation on every row
kv_layout: {block_size_tokens: 16}     # F7: from rk-sim's plan

# UarchCostTable / ModelCard
measured_error: {interpolation_loo, composition_reduction, layer_reuse}              # F3
validated_error_band.scope: {family, op_classes, precision, shape_regime, load_regime} # F8
```

Also add to U0001's known limits: no mixed prefill/decode iterations (F17); no address translation; no coherence.

---

## 5 · What to do next, in order

1. **Finish U0 (E1, E2):** add the protected files, make the hooks executable, pin Python 3.12, push to a private remote, confirm CI is green, tag `u00-end`.
2. **Mark the superseded plans (E3)** in the Project.
3. **Fold §4 into the U-P1 session** as a founders' proposal. Decide F8's shape-regime bins and F9's shared level in U0001.
4. **Amend the prompt texts** that own F10–F16:
   - U-P6: SRAM capacity, attribution sum, energy conservation, latency monotonicity.
   - U-P8: DMA L1 closed form, derated DRAM check, Accelergy/CACTI reference.
   - U-P9/U-P15: matched vs compiler-chosen mapping, device-side timing, gather and barrier classes, compiler cost analysis.
   - U-P14: workload suite, geometric mean, SRAM energy per variant.
   - U-P5/U-P11: `EngineResult.diagnostics` and the timeline export.

   Keep `tests/unit/test_prompt_sync.py` green by editing each prompt text in build-spec §8 and in `docs/prompts/` in the same commit.
