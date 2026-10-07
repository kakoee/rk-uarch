# rk-uarch — Build Spec

**What this is:** the implementation contract for `rk-uarch`, a microarchitecture-level simulator
of one AI accelerator (a custom NPU SoC or a real reference chip). It produces characterization
tables that rk-sim consumes as the C2 compute answer for a `compute_resource`. This document
holds the architecture, repo layout, interfaces, conventions and the prompt pack that drives a
coding agent through the build.

**Team:** Ray (kakoee), Lane A, Engine · Javid (jjaffari), Lane B, Evidence & Product ·
one shared GitHub repo · the shared Linux box · Apple Silicon laptops for the Python harness.
**Rev 2, 2026-09-28.** Rev 2 closes the gaps the book-coverage review found (F1–F17 in
`docs/reviews/rk-uarch-book-coverage-review.md`): memory-level parallelism, the initial
state, layer-reuse error, DRAM organisation and timing, per-job and barrier overheads,
matrix-engine dataflow, the KV page layout, the full applicability scope, an optional shared
SRAM level, SRAM placement, energy evidence, mapping match at L3, workload fidelity, architect
diagnostics, workload suites, the derated DRAM limit, and the mixed-iteration limit.
**Rev 2.1, 2026-10-01.** Applies the fixes in `docs/reviews/rev2-plan-review.md` (its Findings
1–12): the tensor-parallel shard and a ninth integration rule, durations in the parity
fixtures, unit and preset rules the contract can satisfy, counts as SourcedValues, six more
U0001 decisions, fidelity keys and the fork's levels, a fused attention operator, an
end-to-end mesh class, accumulator and controller-queue state, structural study variants,
split native-engine prompts, and deferred scope (shared-SRAM engine support, the energy rung,
a gate on U9).
**Rev 2.2, 2026-10-01.** The native engine is written in **Rust**, not C++20: most of it is
written by coding agents, and safe Rust turns their likeliest bugs (undefined behaviour, data
races) into compile errors. `unsafe` lives only in the crate that bridges to Ramulator 2. The
seam with rk-sim is unchanged and language-neutral (§7.1).
**Rev 2.3, 2026-10-01.** Two native-engine time decisions, recorded here instead of in an ADR.
(1) **Edges are rounded, periods are not.** An integer `period_ps` cannot represent a 1.2 GHz
clock (833.33… ps): rounding down makes the engine faster than its own U-C0 roofline
(invariant 6), and rounding up biases every row. Each domain's frequency is now resolved
once to integer hertz, used by every engine and U-C0 alike, and edge k of a domain sits at
⌈k·10¹²/f⌉ ps. Time stays `u64` picoseconds; an edge is never early and is less than 1 ps
late, so no drift accumulates (§2.3.2, §2.5, §2.8). (2) **How the cycle-ticked Ramulator 2
runs inside the event-driven kernel.** Batched ticks up to a conservative horizon while a
controller is busy, exact catch-up ticks over idle gaps (so refresh still happens), one new
event kind `MEM_TICK`, and a tick-every-cycle debug mode that the batched mode must match byte
for byte (§2.8, §2.9, U-P13b, U-P17).

**Companion documents.** `docs/execution-plan.md` is *when and who*: sprints, gates and effort.
`rk-uarch-track-verdict-and-plan.md` (in the Project) holds the research and the reasoning
behind every choice here: prior art, licences, the badge answer, and the validation ladder.
Nothing in that document needs to be fed to a coding agent. Everything in *this* one does.
`docs/reviews/rk-uarch-book-coverage-review.md` checks this plan against a performance-modeling
textbook's full table of contents (`docs/reviews/book-toc-performance-modeling.md`); the
F-numbers in Rev 2 point to it. Both are also in the Project.
The verdict's advice to wait was overtaken by the founders' decision to open this track; its
research still stands. An earlier prompt pack (U-P0…U-P17, eight sprints) was superseded by
this document and the execution plan, and deleted from the Project on 2026-10-01. Its numbering
does not match this one; if an old copy turns up, never hand it to an agent.

**Relationship to rk-sim.** rk-uarch is a **separate repository**. It never imports rk-sim, and
rk-sim never imports it. rk-sim reads its output files. Two prompts in this pack (U-P19 and
U-P20) run *inside* rk-sim, after an rk-sim boundary ADR admits characterized C2 tables. The
draft ADR and the rk-sim-side prompt files ship in this kit under `rk-sim-side/`.

---

**Preparation-boundary amendment, 2026-10-06 (Javid approved the direction).**
Rationale, alternatives and rollout: [ADR U0019](decisions/U0019-standalone-preparation-and-prepared-input-replay.md).
Preserve standalone operation and the existing EngineJob/TaskGraph boundary. Make local
preparation a separately versioned producer, and admit validated file-based import/replay of
prepared inputs without requiring a compiler or a live rk-sim installation. §2.5.1 defines
ownership and staged delivery. U0001 remains subject to its U1 acceptance process; U0003
must settle concrete prepared-input schemas and any public contract revision before U2
implementation. This amendment implements no simulator or upstream integration.

## §0 · HOW TO USE THIS DOCUMENT WITH A CODING AGENT

| Step | Do this |
|---|---|
| **Once, at repo creation** | Put this kit's `docs/` in an empty directory, attach **`BOOTSTRAP-PROMPT.md`** to a fresh session and say "follow this file." It creates the skeleton, `CLAUDE.md`, 23 READMEs, CI and the lane plumbing. U-P0 in §8 is the same task in short form |
| **Every sprint** | Open the sprint in `docs/execution-plan.md` §3. It names the prompt per lane and the joint exit criterion. Run each prompt in its **own fresh session** using `docs/prompts/TEMPLATE-implementation-session.md` |
| **Every prompt** | The prompt assumes `CLAUDE.md` is loaded and names the files to read. Where it says *stop* or *ask*, the agent stopping is the correct outcome |
| **Every sprint end** | Run **U-REVIEW** in a fresh session per lane: the session that wrote the code never reviews it. Then run `STANDING-how-it-works-refresh.md`. Humans tag `uNN-end` after the adjudication is ACCEPTED |
| **Never** | Feed an agent the whole document; let it edit `contract/`, `tests/golden/expected/`, `CLAUDE.md` or `docs/decisions/` mid-task; or let it edit a committed prediction under `validation/L3_silicon/*/predictions/` |

**The rule that outranks everything in this repo:** *detail is not accuracy.* A cycle-level
number reaches a human only with its fidelity, its evidence, and the stipulations it is
conditional on. A confident number with no right to confidence is the highest-severity bug, and
at cycle resolution it looks more confident, not less.

---

## §1 · WHAT WE ARE BUILDING

### 1.1 One paragraph

A simulator of the **inside of one chip**: cores with matrix and vector engines, SRAM, DMA, one
or more on-chip networks, an optional shared on-chip SRAM, memory controllers and DRAM. It is
driven by the same model description rk-sim uses. It answers one question: *what does one
iteration of LLM inference (one tensor-parallel shard, all layers, at a given batch and context)
cost on this chip?* It answers at a stated fidelity per subsystem, with its own error measured
and stated, and with a badge earned only from comparisons against real silicon. It runs a
published open-source NPU simulator (the fork) and its own event-driven engine (native) behind
one protocol. The fork stays forever as the reference for the native engine. It is validated
against two real chips, one per architecture class: Google Cloud TPU v5e (few large systolic
cores) and Tenstorrent Blackhole p100a (a mesh of many small cores). Its output is a hashed
characterization table that rk-sim reads to price a custom ASIC at C2 inside a whole-rack run.

### 1.2 The acceptance test: the design-study demo

This is the **definition of done**. The final sprint (U11) is "perform this cold, twice." Build
toward it from U1.

| Min | Action | Output | What it proves |
|---|---|---|---|
| 0:00 | `uarch validate hw/designs/npu-m256.yaml`, then the same on a copy of `hw/references/blackhole-p100a.yaml` with one value turned into a stipulation | Counts of claims (each with a URL), stipulations (each with a rationale) and stubs; then a refusal naming the parameter path | Claims and design choices are different things, and the loader knows it |
| 1:00 | `uarch table hw/designs/npu-m256.yaml --model llama-3.1-70b --precision fp8 --tp 8 --engine native --workers 10` | A table built in parallel across grid points, for one rank of an 8-way tensor-parallel split. It prints composite **C2** with the per-subsystem detail, the model-card badge, the measured interpolation, composition, layer-reuse and cold-vs-steady errors, and the FLOP-parity deviations | A cycle-level answer that says how it was computed and how well it knows itself |
| 2:30 | `uarch report tables/<hash>` | An HTML report where every number is badged, marked "conditional · N stipulations", and shows its error band or "unknown", never "±0"; each C2 row sits beside its own U-C0 roofline; architect diagnostics (utilisation, critical-path attribution, NoC and DRAM statistics) render "not modelled" where a level does not model them | Honesty rendered, not asserted |
| 4:00 | `uarch study hw/studies/npu-m256-sram-and-noc.yaml` | A two-variant diff over the versioned workload suite: which regime moved, with attribution, per workload and as a geometric-mean speedup; a one-at-a-time tornado labelled *local sensitivity*; energy per token with its own conditions, marked unverified until energy evidence exists | What a chip architect actually does with the tool |
| 5:30 | `uarch ledger` | L3 rows for TPU v5e and Blackhole, predicted vs measured by class, with predictions provably committed first; model cards promoted only within their scope; error by fidelity level, answering *did more detail help?* | The method is graded against silicon, including where it lost |
| 6:30 | rk-sim: a rack of 8 × `npu-m256` at **C2**, tp = 8, against 8 × H100 at C0 → Run → Compare | The Fidelity Map row shows `C2 · uarch@x · <table hash>`; badges are conditional; Compare warns that the comparison is biased *against* the detailed part and shows its roofline beside it | The two products meet at a seam neither had to rewrite |
| 8:00 | `uarch diff` of `npu-l4` at native vs fork, matched levels | Agreement fraction and speedup; disagreements attributed per subsystem | The native engine is checked against something that isn't itself |
| 9:00 | Close | "N stipulations; validated band X% for {classes, shape regimes, precision} on {family}; everything else says unknown." If the evidence covers none of the 1:00 table's own rows (family, precision, end-to-end class), the close says so | — |

### 1.3 Scope boundaries: the agent's guardrails

**In scope:**

| Class | Fidelity range | Note |
|---|---|---|
| Hardware description | — | Proposed designs (stipulations allowed) and reference chips (claims only). Includes matrix-engine dataflow, accumulator and operand-buffer capacity, DMA outstanding limits and request size, per-job and barrier overheads, DRAM organisation and timing, address interleaving, controller policy, queue depths and credits, and an optional shared SRAM |
| Workload | — | Dense decoder with GQA, prefill and decode, from rk-sim `ModelSpec` + a `ModelShape` sidecar, as one rank of a tp-way tensor-parallel split. MoE as active-parameter dense-equivalent only, as in rk-sim. KV in pages of rk-sim's block size. Attention as one fused operator. A stipulated initial state (`steady` or `cold`) |
| Mapping | — | Named, versioned, stipulated policies. No search |
| Compute (core) | levels 0–2 | Roofline → tile-job intervals (dataflow-specific fill/drain, per-job overhead) → + SRAM banks (from the mapping's buffer placement) and DMA interleave |
| NoC | levels 0–2 | Hop latency → reservation calendars with cycle timestamps → flit-level (BookSim2, reference) |
| DRAM | levels 0–2 | Latency + bandwidth cap derated for refresh → per-channel queue with row buffer and the spec's page policy → Ramulator 2 (library), configured from the spec's organisation and timing |
| Shared SRAM (optional) | levels 0–1 | Capacity + bandwidth cap → per-port queue, attached to the NoC like a memory controller. In the contract from 0.1; engine support is deferred until after U8, and until then a spec with a shared SRAM lists it as unrepresented, so its composite is never C2 |
| Engines | — | Analytic (U-C0), fork (ONNXim or PyTorchSim, pinned), native (Rust) |
| Parallelism | — | Across grid points from U4; inside a simulation from U9: exact conservative mode, plus a lax mode labelled approximate |
| Evidence | — | L0 invariants, L0m metamorphic, L1 analytical limits, L2 differential, L3 two reference chips, ledger, model cards; workload fidelity against compiler-reported counts; diagnostic fidelity against device counters where a chip exposes them; L0 energy conservation (the energy L2 rung is deferred until after U8) |
| Product | — | Tables, CLI, static reports with architect diagnostics, `uarch characterize`, design studies over a versioned workload suite, rk-sim integration (U-P19, U-P20) |

**Out of scope.** If an agent proposes any of these, the answer is no:

- mapping search or autotuning;
- simulating actual tensor values (functional execution);
- sparsity;
- data-dependent MoE routing and imbalance;
- host CPU, PCIe, OS, and runtime or launch time outside the device (L3 compares device-side
  time only; rk-sim's runtime axis owns the rest);
- address translation (TLBs, IOMMU) and cache coherence: declared as omissions on every row;
- mixed prefill/decode (chunked-prefill) iterations: a known limit of contract 0.x (F17);
- multi-chip inside uarch (rk-sim owns tensor-parallel collectives);
- power or thermal feedback inside the simulation (uarch emits activity counts; energy is computed from them);
- area models (a study that grows SRAM says area is not modelled);
- training workloads;
- a third NoC backend, or a router microarchitecture of our own;
- optimistic synchronisation or rollback;
- SIMD, GPU or MPI execution backends;
- a simulation compiler;
- a workload IR of our own, or ONNX as a source of truth;
- a web UI (rk-sim's UI is the UI);
- a database.

---

## §2 · ARCHITECTURE

### 2.1 System diagram

```
  rk-sim (reads files; never imports uarch)                    rk-uarch
 ┌───────────────────────────────────────┐  CharacterizationRequest  ┌──────────────────────────────────────────────┐
 │ ModelSpec · Precision · tp · reachable ├──────────────────────────▶│ contract/     the only shared vocabulary      │
 │ (B,T,Q) envelope                       │                           │ hw/           designs (stipulated) · refs     │
 │                                        │                           │ workload/     ModelSpec+ModelShape → op graph │
 │ R1 DES ── IterationCost protocol ──┐   │                           │ mapping/      named policies → TaskGraph      │
 │                                    │   │                           │ engines/ analytic(U-C0) │ fork │ native(Rust) │
 │   rk/engine/characterized/  ◀──────┘   │◀─────── UarchCostTable ───┤ table/        grid · pool · interp · errors   │
 │   (table-backed cost, P18)             │     (JSON, hashed)        │ provenance/   badges · cards · applicability  │
 │   <Badged> conditional · chip panel    │                           │ report/ study/  what a human reads            │
 └───────────────────────────────────────┘                           │ validation/   L0 L0m L1 L2 L3 · ledger · sync │
                                                                     └──────────────────────────────────────────────┘
```

### 2.2 Module map

| Path | Lane | Owns | Notes |
|---|---|---|---|
| `contract/` | both | Carriers, hardware spec, operators, model shape, request, table, model card, hashing, errors | Human-owned. Agents propose and stop |
| `hw/` | B | Designs, references, studies (YAML) | References are claims only |
| `src/rkuarch/hw/` | A | `derive_rk_params` | One chip, one set of facts |
| `src/rkuarch/workload/` | A | Standalone workload preparation and validated prepared-graph loading; `uarch characterize` | Existing OpSpec vocabulary; explicit rank scope, producer identity, omissions and KV pages |
| `src/rkuarch/mapping/` | A | Standalone policies → `TaskGraph`; validation of supplied mappings | Runs before simulation; `name@version`; dataflow, placement and content identity are explicit |
| `src/rkuarch/engines/` | A | Prepared-input protocol; analytic, fork, native adapters | Execute validated inputs; fork-delegated mapping is explicitly qualified (§2.5.1) |
| `native/` | A | The Rust engine (a Cargo workspace) | Built in the engine container; `unsafe` only in the Ramulator 2 bridge crate |
| `src/rkuarch/table/` | A | Grid, pool, interpolation, measured errors (LOO, composition, layer reuse, cold vs steady) | Refuses extrapolation |
| `src/rkuarch/provenance/` | B | Badges, model cards, applicability | Never raises a badge |
| `src/rkuarch/report/`, `study/` | B | Reports, diagnostics, studies over workload suites, diffs | Every number through `badged()`; unmodelled renders "not modelled" |
| `validation/` | B | L0–L3 suites, ledger, perf, sync | Predictions frozen before results |
| `measure/` | B | Silicon measurement kits | Dry-run before real hardware |
| `third_party/`, `containers/` | A | Pinned forks, patches, engine image | Licence allow-list |

### 2.3 The contract

#### 2.3.1 The carriers

- `SourcedValue` is rk-sim's, verbatim: `{value, unit, provenance, source, date}`. It adds
  **`kind: claim | stipulation`**.
  - A **claim** follows rk-sim's rules: `stub` requires `source=None`; anything else requires a
    source.
  - A **stipulation** requires `provenance=None`, `source=None`, `date=None` and a non-empty
    `rationale`. Stipulations are allowed only in `design_status: proposed` specs.
- Outputs are rk-sim-`Metric`-compatible, plus `conditional_on`.

#### 2.3.2 HardwareSpec (shape)

```yaml
id: npu-m256
design_status: proposed            # proposed | reference
clock_domains:
  core: {freq_hz: {value: 1.2e9, unit: Hz, kind: stipulation, rationale: "target node"}}
  noc:  {freq_hz: {...}, scales_with_core: false}   # frequency_ratio scales core and every
  dram: {freq_hz: {...}, scales_with_core: false}   #   domain with scales_with_core: true
cores:                             # *_cycles leaves under cores: core clock domain
  grid: {rows: {...}, cols: {...}} # counts are SourcedValues with integral values
  core_type:
    matrix_engine: {array: {rows: {...}, cols: {...}}, dataflows: [weight_stationary],  # F6
                    macs_per_cycle: {bf16: {...}, fp8: {...}},
                    accumulator_bytes: {...},                    # output-tile / partial-sum capacity
                    operand_buffer_bytes: {...}, operand_bytes_per_cycle: {...}}  # SRAM -> array staging
    vector_engine: {ops_per_cycle: {...}}
    sram: {bytes: {...}, banks: {...}, bytes_per_cycle_per_bank: {...}}
    dma:  {engines: {...}, bytes_per_cycle: {...},
           max_outstanding: {...}, request_bytes: {...}}               # F1: memory-level parallelism
    job_overhead_cycles: {...}                                          # F5: issue + descriptor + semaphore, per tile job
sync: {mechanism: noc_semaphore, barrier_latency_cycles: {...}}         # F5; noc clock domain
shared_sram: null                  # F9, optional: {bytes, banks, bytes_per_cycle_per_bank,
                                   #   latency_cycles (noc domain), attach: [[r, c], ...]}
nocs:                              # *_cycles leaves: noc clock domain
  - {topology: torus, direction: positive, link_bytes_per_cycle: {...},
     router_latency_cycles: {...}, virtual_channels: {...}, buffer_flits: {...}}
memory:
  interleave: {granularity_bytes: {...}, scheme: channel_hash}          # F4: address -> channel -> controller
  controllers: [{attach: [0, 0], scheduler: fr_fcfs, page_policy: open,
                 read_queue_depth: {...}, write_queue_depth: {...},     # a full queue withholds
                 noc_credits: {...}},                                   #   NoC credits (back-pressure)
                {attach: [0, 15], ...}, ...]
  dram: {standard: gddr6, channels: {...}, bw_bytes_per_s: {...}, capacity_bytes: {...},
         organization: {ranks: {...}, bank_groups: {...}, banks_per_group: {...}, row_bytes: {...}},
         timing_preset: null,      # or {file: <path in the simulator repo>, sha: <pinned commit>}
         timing: {t_rcd_cycles: {...}, t_rp_cycles: {...}, t_cl_cycles: {...},
                  t_rfc_cycles: {...}, t_refi_cycles: {...}}}         # F4: in the dram clock domain
formats: {fp8: {bytes: 1, accumulate_bytes: {...}, block_scale_bytes: {...}}}
energy: {pj_per_mac: {fp8: {...}}, pj_per_byte: {sram: {...}, noc_hop: {...}, dram: {...}},
         voltage_ratio: {0.6: {...}}}  # F11: V(f)/V(1) per frequency ratio; absent => energy at f≠1 is unknown
static_power_w: {...}
tdp_w: {...}
```

**Rules for the fields (Rev 2, amended in Rev 2.1).**
- Categorical fields (`topology`, `direction`, `dataflows`, `scheme`, `scheduler`,
  `page_policy`, `sync.mechanism`) are plain enums. Structure is plain too: the lists of NoCs
  and controllers, and every `attach` coordinate. Every numeric leaf is a SourcedValue, counts
  included (grid, array, banks, DMA engines, virtual channels, DRAM channels and organisation,
  queue depths, credits), and a count's value must be integral. So a reference marks an
  unpublished count as a stub, and a study may vary a count of a proposed design. A format's
  `bytes` is the format's definition and stays plain.
- **Clock domains.** Every `*_cycles` and `*_per_cycle` leaf counts cycles of the domain that
  owns its block: `cores` → core; `nocs`, `sync`, `shared_sram` and controller `noc_credits`
  → noc; `memory.dram` → dram. A frequency ratio scales `clock_domains.core` and every domain
  whose `scales_with_core` is true, and nothing else.
- **Resolved frequencies (Rev 2.3).** For each grid point the harness resolves every domain's
  frequency once to a whole number of hertz: `round(freq_hz × ratio)` for a domain the ratio
  scales, `round(freq_hz)` otherwise. Every engine, U-C0 included, uses those integers and
  nothing else, so a roofline and the cycle-level run it bounds share one clock. Clocks are
  never stored as a rounded period (§2.8).
- **Presets.** A simulator preset (Ramulator's GDDR6 or HBM tables, say) may supply DRAM timing
  only through `memory.dram.timing_preset: {file, sha}`, and every timing leaf it supplies is a
  claim whose `source` is `<file>@<sha>`. A timing claim that cites any other preset file, or a
  `timing_preset` without a pinned sha, is refused (`UnnamedPreset`). No engine reads any
  simulator configuration (timing, controller queues, scheduler parameters) from a preset or a
  default the spec does not name; what the spec lacks is listed as unrepresented (F4).
- `sram.bytes` and `energy.pj_per_byte.sram` travel together: a variant that changes one
  re-stipulates the other (F11).
- A field an engine cannot represent goes into that engine's `unrepresented` list and becomes a
  table warning, as for every other field.

#### 2.3.3 Request and table

rk-sim → uarch: **`CharacterizationRequest`**

```yaml
contract: uarch-contract/0.1
rk_schema_snapshot: <rk-sim sha>
component_id: compute.asic.npu-m256
hardware_spec_hash: "sha256:…"
model: {name, total_params, active_params, n_experts, experts_per_token,
        n_layers, d_model, n_heads, kv_heads}           # rk-sim ModelSpec, verbatim
model_shape: {d_ff, gated_mlp, vocab_size, attention: gqa, tie_embeddings, expert_d_ff}
precision: {compute: fp8, kv_cache: fp8}                 # rk-sim PrecisionFormat
tp: 8                                                    # the shard: rows cost ONE rank of a tp-way split
envelope:
  decode:  {batch_max: 128, context_per_seq_max: 32768}
  prefill: {prompt_tokens_max: 32768, prompts_per_iteration_max: 8}
grid:
  decode:  {batch: [1,2,4,8,16,32,64,128],
            context_per_seq: [128,512,1024,2048,4096,8192,16384,32768]}   # 64 × 2 f = 128 rows
  prefill: {n: [1,2,4,8], L: [128,512,2048,8192,32768]}                   # 20 × 2 f = 40 rows
  frequency_ratio: [1.0, 0.6]
mapping_policy: summa-2d@1                               # stipulated
uarch_fidelity: {compute: 2, noc: "1+ts", dram: 2}           # values as fidelity_detail (§2.4)
initial_state: steady                                    # F2: steady | cold; a stipulation on every row
kv_layout: {block_size_tokens: 16}                       # F7: rk-sim's KV block size
visit_weights: null                                      # F15, optional: rk-sim's density over (B, T) and
                                                         #   (n, L) from its timeline export (ADR 0046)
seed: 7                                                  # sampled errors only
```

uarch → rk-sim: **`UarchCostTable`**

```yaml
contract: uarch-contract/0.1
uarch_version: 0.3.0+g1a2b3c4
request_hash: "sha256:…"
table_hash:   "sha256:…"
tp: 8                                  # the request's tp; rk-sim refuses it for any other tp (rule 9)
composite_fidelity: C2
fidelity_detail: {compute: 2, noc: "1+ts", dram: 2, sync: exact, layer_reuse: true}
rows:                                  # seconds and bytes; never cycles
  - {phase: decode, batch: 8, total_context_tokens: 32768, frequency_ratio: 1.0,
     duration_s: 3.1e-3, u_c0_duration_s: 2.2e-3,
     attribution_s: {compute: …, memory: …, noc: …, sync: …, overhead: …},   # critical path; sums to duration_s
     counts: {matrix_ops: …, vector_ops: …, memory_read_bytes: …, memory_write_bytes: …},
     ext_counts: {sram_read_bytes: …, sram_write_bytes: …, noc_flit_hop_count: …},
     peak_resident_bytes: {hbm: …, sram: …},
     diagnostics: {matrix_util_ratio: …, vector_util_ratio: …, dma_compute_overlap_ratio: …,
                   sram_bank_conflict_stall_ratio: …, noc_latency_p50_s: …, noc_latency_p99_s: …,
                   noc_max_link_util_ratio: …, dram_bw_util_ratio: …, dram_row_hit_ratio: …}}
                                       # F14: null where the level does not model it, never 0;
                                       #   uarch-internal (rk-sim ignores it)
  - {phase: prefill, n_prompts: 2, prompt_tokens: 2048, frequency_ratio: 1.0, …}
                                       # same fields as a decode row; keys (n_prompts, prompt_tokens)
interpolation: {decode: "bilinear in (log B, log T); linear in 1/f",
                prefill: "bilinear in (log n, log L); linear in 1/f", outside_grid: refuse}
initial_state: steady
kv_layout: {block_size_tokens: 16}
measured_error: {interpolation_loo: {median_rel: …, max_rel: …, weighted_median_rel: … | null},
                 composition_reduction: {decode: {…}, prefill: {…}, n_samples: …},
                 layer_reuse: {median_rel: …, max_rel: …, n_samples: …},            # F3
                 cold_vs_steady: {median_rel: …, max_rel: …, n_samples: …,
                                  priming_2_vs_1_max_rel: …}}                         # F2; warm-up length
flop_parity: {max_rel: …, declared_deviations: [{id, deviation_rel, reason}]}
provenance: {params: [...], model_card: {hash, badge, evidence, validated_error_band,
                                         energy_verification},
             conditional_on: [...]}
warnings: [...]                        # includes the declared omissions (§2.3.4)
```

`validated_error_band` is `None` or `{low_rel, high_rel, scope}`, and `scope` is the full
applicability vector: `{family, op_classes, precisions, shape_regimes, load_regimes,
mapping_match}` (F8). `energy_verification` is `None` ("unverified") until every coefficient
family the energy figure uses (per MAC, SRAM, NoC hop, DRAM, static) has an L2 reference; the
energy rung is deferred until after U8 (§2.7). The table embeds the model card's hash, badge,
evidence, band and energy verification, so rk-sim reads the badge without the card file.

#### 2.3.4 Canonical batches, and the reduction error

rk-sim reduces a batch to three sufficient statistics: batch size B, total context T, and
Q = Σ Sᵢ². Its own docstring says this is exact only while cost is linear. A cycle-level model
is not linear, because of padding and tile quantization. So the table evaluates canonical batches:

- **decode:** B sequences of T/B tokens;
- **prefill:** n prompts of L tokens, so n = T²/Q and L = Q/T.

For a seeded sample of points the table then **measures** how far unequal batches with the same
(B, T, Q) deviate, and reports that number. It never corrects it.

**A row is one rank of a tp-way split (rule 1, rule 9).** The standalone preparation
frontend builds the split; a supplied prepared workload already carries its authoritative
rank scope and is validated without re-sharding (§2.5.1). The initial supported policy, for
`tp = N`, produces one rank of a Megatron-style split: attention heads divided by N
(KV heads too, replicated when `kv_heads < N`), FFN up and gate columns and down rows divided by
N, embedding and lm_head split over the vocabulary. It has no collective operations: rk-sim
prices those. A request whose heads or FFN width do not divide by N is refused, naming the
dimension. A table is built for exactly one tp, carries it, and rk-sim uses it only for a plan
with the same tp.

**Layer reuse is sampling, so its error is measured too (F3).** With `layer_reuse: true` the
engine simulates one decoder layer and scales it by `n_layers`: a representative interval with a
weight, as SimPoint does. Anything that crosses a layer boundary is lost: the next layer's
weight DMA overlapping this layer's compute, and NoC and DRAM state carried over. For a seeded
sample of grid points the table simulates every layer and reports the deviation as
`measured_error.layer_reuse`. It never corrects it.

**The initial state is stipulated (F2).** A row depends on what is on the chip when the
iteration starts. `steady` (the default) simulates one priming iteration at the same point and
reports the second; `cold` starts from empty SRAM, closed DRAM rows and no DMA in flight. The
state is a stipulation on every row. L3 predictions use the state that matches the measurement
kit's warm-up. Each table reports the cold-vs-steady deviation over a seeded sample of points,
and on the same sample how far one priming iteration is from two (`priming_2_vs_1_max_rel`), so
the warm-up length is measured rather than assumed.

**KV lives in pages (F7).** KV is stored in pages of `kv_layout.block_size_tokens`, which is
rk-sim's block size. The workload graph emits KV reads as page-granular gathers, not one
contiguous stream.

**Declared omissions on every row.** Host and runtime time outside the device; address
translation; cache coherence; mixed prefill/decode iterations (F17); and for MoE, routing,
imbalance and all-to-all. They become table warnings, and the report's "what this table does
not claim" lists them.

#### 2.3.5 Operator vocabulary

`contract/uarch_contract/operators.py` starts from rk-sim P16's baseline list (QKV projection,
QK score, softmax, AV, output projection, normalization, residual, FFN projections, activation)
and adds only what tiling needs (e.g. `kv_write`, `embedding`, `lm_head`, `attention_fused`).
**Attention is one fused operator.** `attention_fused` is QK score → softmax → AV over KV tiles
with the scores kept on chip, as real attention kernels do: its operation count is the sum of
its three parts, and its DRAM traffic is Q, K, V and O only. The workload graph emits it for
prefill and decode; the three unfused operators stay in the vocabulary, and a policy that
materialises scores in DRAM says so in its name. Without this, a prefill row at L = 32768 would
either be refused or charged an L × L score matrix per head. Each operator carries
named dimensions, per-operand dtypes, per-operand layout (contiguous, or paged with a page size,
as KV is) and its reduction axis. **A multiply-add is two operations**
(rk-sim P7b). If rk-sim takes P16, the two lists are reconciled in P16's boundary ADR.

### 2.4 The fidelity ladder inside uarch, and the composite rule

| Subsystem | 0 · analytic | 1 · contention-aware | 2 · cycle-approximate | 3 · reference only |
|---|---|---|---|---|
| Compute | Roofline of the core | Tile-job intervals: fill/drain for the declared dataflow, quantization, double-buffering, per-job overhead | + SRAM bank conflicts (from the mapping's buffer placement) and DMA interleave at cycle timestamps | Gemmini RTL on Verilator |
| NoC | Hop latency, infinite bandwidth | Reservation calendars per link and port. **"1+ts"** when cycle-timestamped | Flit-level (BookSim2) | tt-npe; silicon |
| DRAM | Latency + bandwidth cap, derated for refresh | Per-channel queue + row buffer with the spec's page policy and queue depths. **"1+ts"** when cycle-timestamped | Ramulator 2, configured from the spec's organisation, timing and queues | Silicon |
| Shared SRAM (optional) | Capacity + bandwidth cap | Per-port queue; **"1+ts"** when cycle-timestamped (engine support after U8) | — | Silicon |
| Sync | exact | — | — | — |

**Memory-level parallelism holds at every level (F1).** Every DMA engine honours
`dma.max_outstanding` and `dma.request_bytes`. A requester's bandwidth is at most
`max_outstanding × request_bytes / round trip`, even at level 0, where the round trip is hop
latency plus memory latency. In the native engine, barriers cost
`sync.barrier_latency_cycles` at every level; U-C0 does not model them.
The Sync row above is about the parallel simulation (§2.9), not about barriers in the workload.

**`fidelity_detail`, the per-subsystem vector.** Keys and legal values are fixed:
`compute` 0 | 1 | 2; `noc` 0 | 1 | "1+ts" | 2; `dram` 0 | 1 | "1+ts" | 2; `shared_sram`
(present only when the spec has one) 0 | 1 | "1+ts" | "unrepresented"; `sync` "exact" |
"approx(Q=<ps>)"; `layer_reuse` true | false. A request's `uarch_fidelity` uses the same keys
and values. SRAM banks are modelled inside compute level 2, so they have no key of their own:
below compute level 2 they are unmodelled.

**The composite level reported to rk-sim:**

- **C2** only if compute is at level 2 (which is where SRAM bank conflicts live), NoC and DRAM
  are at level 2 or "1+ts", a shared SRAM (when present) is at "1+ts",
  **and** synchronisation is exact, or `approx(Q)` covered by a measured curve (§2.9).
- **C1** otherwise, if any subsystem is at level 1.
- **C0-equivalent** if every subsystem is at level 0.

Every engine's levels come from this table, never from its name. The fork's sub-models are
placed on the ladder once, per configuration, from its source, in ADR U0005 (U-P5), and its
tables get the composite this rule gives them: C1 if the fork models no SRAM bank conflicts.

A request for C2 that cannot be honoured degrades or raises as §7.4 says.

### 2.5 The engine protocol and the TaskGraph

Every engine runs as a subprocess: **`EngineJob` JSON in, `EngineResult` JSON out.** There is no
foreign-function interface between the harness and any engine. `engines/protocol.py` defines
both messages, `make gen` exports their JSON Schema to `src/rkuarch/engines/schema/`, and the
native engine's Rust types are tested against that schema, so the two sides cannot drift.

**`EngineJob` contains:**
- the resolved HardwareSpec (numbers only, with a hash back to the spec);
- the validated prepared workload and mapping identity (§2.5.1): U2 analytic jobs carry
  resolved operators/dependencies and an explicit analytic mapping scope; detailed jobs carry
  the resolved `TaskGraph`. Payload kind and unsupported mapping detail are explicit;
- the per-subsystem levels;
- the frequency ratio, and each domain's resolved integer `freq_hz` (§2.3.2);
- the initial state;
- the seed.

**`TaskGraph`** is the output of mapping. It holds:
- per-core compute jobs (operator, tile shape, dtype, engine, dataflow);
- buffer placements for every SRAM-resident operand (core, offset_bytes, bank). A mapping that
  cannot place a tile refuses it with `SramCapacityExceeded` (F10);
- DMA jobs (source, destination, bytes, request count; KV reads are page-granular);
- NoC transfers (unicast or multicast set, bytes, NoC index);
- barriers;
- dependency edges.

The fork is an explicit delegated-mapping mode: the adapter translates the prepared
workload to its format and the fork tiles internally. Record policy
`fork:<name>-default@<sha>` and the input scope actually represented. It must refuse supplied
placements it cannot honor; it cannot silently replace them with its own mapping. The policy
`onnxim-compat@1` reproduces the fork's tiling, with evidence of correspondence, so native can
be compared on the same work. A common policy name alone does not establish equivalence.

**`EngineResult` contains:**
- `duration_ps`;
- per-resource busy time;
- attribution by critical path: each interval on the critical path is charged to the resource
  that bounded it, and the parts sum to the duration;
- activity counts in contract channel names;
- `diagnostics` (§2.3.3), `null` wherever the level does not model a quantity, never 0;
- `fidelity_detail`;
- the list of unrepresented spec fields;
- simulator metrics;
- optionally (`--trace`), a per-resource timeline as Chrome-trace JSON, for debugging (F14).

Cycles stay inside `engines/` and `native/`; `table/` converts `duration_ps` to seconds with a
named function.

### 2.5.1 Standalone preparation and externally supplied inputs

**Two entry paths, one execution boundary.** Standalone operation is a requirement: a user
can run rk-uarch from ModelSpec + a sourced ModelShape + precision + tp + query/grid + hardware
and a selected versioned mapping policy, with no compiler or live rk-sim. The workload and
mapping modules prepare engine inputs before simulation. An optional file-based prepared
input follows the same validation and engine boundary without invoking those producers.
The existing EngineJob/TaskGraph boundary remains; this exposes its preparation step.

**Ownership.** The upstream execution plan chooses inter-chip partitioning. The local
frontend is a bootstrap producer implementing the explicitly selected supported split when
no external producer exists. Supplied rank-local operators must already identify their split,
rank/equivalence scope, shapes, dtypes, layouts, dependency edges, fusion, padding/replication,
KV layout and omissions. Imported inputs are never silently re-sharded, divided by tp again,
or given an inferred fusion policy. Initially accept only the declared balanced TP and
representative-rank cases; unsupported heterogeneous/unequal-rank or other parallelism must
fail explicitly. This does not introduce PP/EP/CP support or a second operator language.

Within a chip, the selected mapping producer resolves tile shapes, cores/resources, dataflow,
buffer placement, transfers, barriers and scheduling policies. At the mapped execution
boundary these choices are inputs. Actual issue/completion timestamps, contention, stalls,
and critical-path attribution are simulator outputs. Engines may apply declared resource
arbitration, but cannot search, re-tile or substitute a different mapping to make a job fit.
If an external producer supplies only operators, a caller may explicitly select a local
mapping policy; that is recorded local preparation, not exact replay of a supplied mapping.

**Small file contract.** Reuse contract/operators.py and the existing TaskGraph. U0003 fixes
one versioned prepared-input envelope and fixture set, rather than a generic workload IR,
compiler frontend or ONNX input path. Include producer name/version, supported scope,
canonical workload/mapping content identities, hardware binding, and the run conditions
required for replay. A bundle manifest maps exact queries to payloads and declares coverage;
it never substitutes one point for another. Level-0 analytic input declares aggregate/per-op
scope; it must not fabricate tile placement or claim to model an imported detailed schedule.
Validate schema/version, hashes, rank/tp, precision, dimensions, dependency references and
hardware/layout compatibility before executing. A mapping for different hardware is refused.

**Identity and replay.** High-level intent, resolved contents and actual execution have
separate roles: content hashes of imported files and versioned local preparation choices must
participate in request/cache identity; path names alone never identify inputs. Each result
and table must trace the prepared inputs it used. Replaying the same captured bundle with the
same engine/version/run conditions is byte-identical regardless of path or local producer
availability. Equivalent externally produced payloads have equivalent numerical results;
different producer metadata remains honestly distinct provenance. Changing a shape, placement
or mapping version invalidates the corresponding identity/cache entry. Do not mutate a frozen
mapping when changing hardware; explicitly prepare a new compatible mapping or refuse it.

U0003 specifies exact field names, canonicalization and validation cases before coding. Any
new request/table field follows the normal human-owned contract revision procedure; include
its schema/fixtures and advance the contract version as required. U1 records this ownership
decision without speculatively adding U2 payload fields. U2's report lane starts against the
accepted revised boundary, so it never invents its own preparation metadata.

**Delivery.** U-P3 (U2) implements the local producer, `uarch prepare <request> --out <bundle>`,
and `uarch table --prepared-input <bundle> --engine analytic`, alongside the existing high-level
CLI. Save/load/replay works without invoking the producer; U2 includes no detailed mapper.
U-P5 preserves prepared workload semantics through the fork's declared mapping mode. U-P7
(U4) adds serialized TaskGraph mapping artifacts and mapped import/replay; preparation includes
the additional query/state cases requested by error experiments. Imported bundles with missing
coverage fail instead of invoking hidden preparation. U-P11a/b consume the established boundary
in Rust; U-P12 checks resolved mapping correspondence before comparing engines. U-P14 explicitly
separates re-preparation for design variants from replay of a fixed external mapping.

The external-producer capability is exercised with standalone file fixtures; no running
compiler, rk-sim P16, live service or production rk-sim change is a prerequisite. Later upstream
adapters require their own accepted boundary and must use this format rather than create a
second sharding implementation inside the engine. U-P19 remains a table-file consumer at run
time; it does not start a compiler or rk-uarch during an rk-sim simulation.

### 2.6 Badges

1. **Worst of contributors, over claims only.** Stipulations are excluded and recorded in
   `conditional_on`.
2. **The model is a contributor.** Its rung comes only from the ledger:
   - L0–L2 evidence → `stub`;
   - L3 in scope → `estimated`, scoped to the family, operator classes, precisions, shape
     regimes, load regimes and mapping match its entries cover;
   - L4 on the target chip → `measured`;
   - `spec_derived` never applies to a model.
3. **Applicability** (rk-sim ADR 0021). Evidence that does not apply to this request (wrong
   family, class, precision, shape regime, load regime or mapping match) contributes `stub` for
   this request. ADR U0001 fixes the bins (F8) and where applicability is judged (proposal: per
   row, with every operator in the row covered). The proposal for the bins:
   - **shape regime**, per operator: operational intensity relative to the chip's ridge point
     (below 0.5×, 0.5–2×, above 2×) × array fill (the smaller of M and N below the array
     dimension, or not);
   - **load regime**, for NoC and DRAM classes: offered load relative to saturation (below 30%,
     30–70%, above 70%);
   - **precision**: formats match by name. BLOCKFP8 evidence does not cover an fp8 request unless
     U0001 records why it should.
4. **The ceiling.** A `proposed` design is never better than `estimated`.
5. **Error is "unknown", never zero.** `validated_error_band` comes only from in-scope ledger
   entries. A deterministic run never fills `ci95`.
6. **Nothing may raise a badge**: no display code, fixture or spec file.
7. **Energy has its own evidence (F11).** Duration evidence never validates energy. Until every
   coefficient family an energy figure uses has an L2 reference (§2.7; deferred until after
   U8), energy renders "unverified" and its model contributes `stub`. A reference for one
   family (SRAM pJ, say) never lifts the label for the others.
8. **Unmodelled is `null`, never 0.** A diagnostic or energy figure that a level does not model
   is `null` in every output and renders "not modelled".

### 2.7 The validation ladder

| Rung | Establishes | Examples | Badge it supports |
|---|---|---|---|
| L0 invariants | No self-contradiction | MAC and byte conservation; utilisation ≤ 1; Little's law ≤ 1%; causality; byte-identical reruns; per-core SRAM occupancy ≤ capacity; attribution sums to duration; energy = Σ counts × coefficients + static × duration | none |
| L0m metamorphic | Relations without an answer key | Bandwidth ×2 never slower; any latency ×2 never faster; fewer outstanding requests never faster; `cold` never faster than `steady`; clock ×k → compute-bound ÷k; monotone in batch and context; symmetry; idle-core invariance | none |
| L1 analytical limits | Closed forms where exact | Transfer = hops × latency + serialisation; streaming = peak derated for refresh ±5% (levels 0–1; level 2 ≤ derated peak, efficiency recorded); latency-bound stream = outstanding × request size ÷ round trip ±5%; resident GEMM pipeline formula for the declared dataflow; **C2 ≥ own U-C0 roofline**; two hand-computed fixtures | none |
| L2 differential | Same abstraction as independent models | BookSim2, Ramulator 2, SCALE-Sim v3 (per declared dataflow), Gemmini RTL (optional), tt-npe; native vs fork; Timeloop mapping reference (optional, recorded, never used to change a policy); per-access energy references, one per coefficient family (deferred until after U8). A comparison of a sub-model with the same code (a fork whose NoC is BookSim 2, against BookSim 2) is refused as not independent | none: "verified", not "validated" |
| L3 same-class silicon | How far the method misses on a real chip | TPU v5e (large-core), Blackhole p100a (mesh); predictions committed before results, with ordering enforced by git; device-side time only; each benchmark tagged `matched` or `compiler-chosen` mapping; compiler-reported FLOPs and bytes checked against the workload graph (workload fidelity); device counters, where the chip exposes them, checked against the row diagnostics (diagnostic fidelity) | `estimated`, scoped |
| L4 target silicon | The actual chip | A design partner's silicon | `measured`, via the ledger |

**Four rules the harness enforces:**
- Subsystem evidence does not compose into system evidence.
- Agreement between two simulators is L2 and nothing more.
- Mapping error is not model error. `matched` and `compiler-chosen` benchmarks are separate
  ledger classes, and every gate verdict states which group it read (F12).
- Duration evidence never validates energy (F11).

### 2.8 The native engine

- **Time:** a `u64` count of picoseconds. Each clock domain has a resolved integer `freq_hz`
  (§2.3.2), never a rounded period. **Edges are rounded, periods are not:** edge k of a
  domain sits at `t_k = ⌈k · 10¹² / freq_hz⌉` ps, computed exactly in `u128`, so
  `0 ≤ t_k − k·10¹²/freq_hz < 1 ps` for every k. An edge is never early, and rounding never
  accumulates: 10⁹ cycles at 1.2 GHz end at 833,333,333,334 ps, not 833,000,000,000. Cycle
  lengths therefore differ by up to 1 ps from one cycle to the next (833 or 834 ps at
  1.2 GHz), deterministically. `next_edge(domain, t_ps, n_cycles)` returns `t_{k+n}`, where
  `t_k` is the first edge at or after `t_ps`. It is the only conversion between time and
  cycles, and `n_cycles = 0` is the plain next edge. DVFS is a per-domain frequency ratio,
  fixed when the simulation is constructed through the resolved `freq_hz`.
- **Language:** Rust (stable, pinned in `native/rust-toolchain.toml`), a Cargo workspace with a
  committed `Cargo.lock`. Every crate carries `#![forbid(unsafe_code)]` except
  `uarch-ramulator-sys`, the bridge to Ramulator 2, where each `unsafe` block has a `SAFETY:`
  comment. `cargo clippy -- -D warnings` and `cargo fmt --check` gate every change.
- **Event:** a 32-byte `#[repr(C)]` `Copy` struct, `{t_ps: u64, seq: u64, target: u32,
  kind: u16, phase: u8, flags: u8, payload: u32, pad: u32}`, with a compile-time assertion
  on its size.
  - Total order: `(t_ps, phase, target, seq)`.
  - Kinds: `TASK_READY`, `COMPUTE_DONE`, `DMA_ISSUE`, `DMA_DONE`, `NOC_HEAD`, `NOC_TAIL`,
    `MEM_REQ`, `MEM_RESP`, `MEM_TICK`, `SYNC_ARRIVE`, `BARRIER_RELEASE`, `STAT_SAMPLE`, `END`.
    `MEM_TICK` exists only for cycle-ticked memory models (below).
  - Dispatch is a `match` on kind, with no trait objects (`dyn`) on the hot path.
- **Ownership:** one owner id per resource. State is structure-of-arrays indexed by owner.
  Only the handler of an event targeted at an owner gets `&mut` access to that owner's state,
  and debug builds assert the target. From U9 each partition owns its slice of that state, so
  a cross-partition mutation does not compile.
- **Data structures:**
  - an event arena with a free list;
  - a two-level timing wheel (4,096 slots, each `⌊10¹² / max freq_hz⌋` ps wide, at least 1)
    with heap overflow;
  - CSR topology;
  - precomputed dimension-order routes;
  - `busy_until_ps[]` per link and port;
  - outstanding-request counters per DMA engine (F1);
  - ring buffers for memory queues;
  - sorted vectors or `BTreeMap` wherever iteration order could reach output; `HashMap` and
    `HashSet` are banned in the engine crate by clippy's `disallowed-types`, because Rust
    randomises their iteration order.
- **Cycle-ticked models inside the event kernel (Ramulator 2, DRAM level 2).** Ramulator 2
  advances by `tick()`, one DRAM cycle at a time. The engine drives it so that the result is
  exactly what ticking every cycle would give, without an event per cycle:
  - *Clock.* One instance per memory controller, owned by that controller's owner id.
    Ramulator cycle c is DRAM-domain edge `next_edge(dram, 0, c)`. The bridge configures
    Ramulator's clock from `clock_domains.dram`. A Ramulator configuration whose clock
    disagrees with that domain, including a data-to-command clock ratio the spec does not
    give, is refused with both values named. It is never silently aligned.
  - *Requests.* A `MEM_REQ` arriving at `t_ps` enters at the first DRAM edge at or after
    `t_ps`. The instance is first ticked up to that edge, and requests that enter at the same
    edge are sent in event total order. A DMA request larger than Ramulator's transaction
    splits by `memory.interleave`, and its `MEM_RESP` fires when the last part completes.
    Request ids come from a per-controller counter in arrival order. If Ramulator refuses a
    request because its queue is full, the request waits in the controller, NoC credits are
    withheld (back-pressure), and waiting requests are retried oldest first on later ticks.
  - *Busy* (anything queued, waiting or in flight): a `MEM_TICK` targeted at the controller
    ticks the instance, in one bridge call, through every cycle whose edge is before a
    horizon `H`. It stops early after the first cycle that completes a request or admits a
    waiting one, because both produce events (a `MEM_RESP`, or released NoC credits). `H` is
    the earliest of: the next pending event's `t_ps` plus `L_in`; the earliest `MEM_REQ`
    already scheduled for this controller, which the controller tracks in a sorted
    structure; and the window end (U9). `L_in` is the minimum delay with which any handler
    can schedule a `MEM_REQ` for this controller. It is computed from the spec (the final
    router and link at the controller's attach point), not configured. Debug builds assert,
    on every `MEM_REQ`, that the instance has not ticked past the arrival edge. `L_in = 0` is
    legal: it costs speed, not correctness. Completions come back as a vector sorted by
    (cycle, request id), and each becomes a `MEM_RESP` at its cycle's edge. The next
    `MEM_TICK` is scheduled at the first edge not yet ticked.
  - *Idle* (nothing queued, waiting or in flight): no events. The next `MEM_REQ` first
    advances the instance through the idle cycles in one bridge call, with no requests, so
    nothing can complete. Refresh and every other internal timer therefore run exactly as if
    the instance had ticked throughout. Catch-up costs host time in proportion to idle DRAM
    cycles, but no events. A faster skip (jumping whole `t_REFI` periods, say) is allowed only
    if it is byte-identical to catch-up on the golden requests. Otherwise it is an
    approximation, and the composite rule treats it like lax sync.
  - *Reference mode.* A debug flag ticks every cycle with one `MEM_TICK` per DRAM cycle. The
    batched mode must match it byte for byte, which is how batching is proven exact.
  - DRAM levels 0 and 1 are event-driven and never tick. Simulator metrics report busy ticks
    and catch-up ticks per simulated DRAM cycle separately.
- **Dependencies:** `serde` and `serde_json` (MIT/Apache-2.0), `proptest` (dev, MIT/Apache-2.0),
  and from U7 Ramulator 2 (MIT) behind `cxx` (MIT/Apache-2.0) in `uarch-ramulator-sys`; from
  U9, `loom` (dev, MIT) to check the mailboxes. Nothing else without an ADR. `cargo-deny`
  checks every crate's licence against the allow-list.

**Departures from the vision note (`elements_of_parallel_DES.md`), and why:**

| Vision note | Here | Why |
|---|---|---|
| Build an engine first | Fork first; native from U6 | The fork is the reference that makes the native engine checkable |
| "Lookahead collapse, L = 1" | L = minimum cross-partition latency, computed from the spec | Real routers take several cycles per hop (Tenstorrent documents ~9 router-to-router on Blackhole) |
| No conservative PDES | Exact conservative mode first; lax mode labelled and curve-gated | Determinism and honesty before speed |
| Three NoC backends | Reservation (native) + BookSim2 (reference) | A third backend adds cost and no evidence |
| Simulation compiler | Named mapping policies | No compiler engineer; honesty over optimality |
| CPU SIMD → GPU → MPI | None | No measured need; out of scope |
| M1 validates against RTL/SystemC | The five-rung ladder, with two real chips at L3 | No RTL exists for our designs; real chips exist for the method |

### 2.9 Parallel execution (U9)

**Partitions.** Row bands of the core grid (blocks behind a flag); memory controllers may be
their own partition. Every owner id belongs to exactly one partition.

**Exact mode.** Windowed conservative synchronisation.
- Lookahead L is the minimum cross-partition latency.
- Within a window, cross-partition events travel through single-producer/single-consumer
  mailboxes. `loom` checks the mailbox protocol over every thread interleaving it explores.
- At each window barrier, mailboxes merge in the global total order. Cross-partition `seq`
  values are derived deterministically.
- Output is byte-identical to the single-threaded engine at any thread count.
- A Ramulator 2 instance (§2.8) never ticks past its partition's window end. A memory
  controller in its own partition contributes its `L_in` to the lookahead like any other
  cross-partition link.

**Lax mode** (off by default). A quantum Q > L; crossing events are delivered at the window
boundary (temporal decoupling).
- The result reports `sync: approx(Q)`.
- The composite is C1 unless a measured error-vs-Q curve (U-P18) covers this Q, boundary type
  and family.

### 2.10 Tech stack

| Layer | Choice |
|---|---|
| Harness | Python 3.12, uv, Pydantic v2, NumPy, PyYAML, Typer, Jinja2 for reports |
| Development | pytest, hypothesis, mypy (strict), ruff, import-linter |
| Engine | Rust (stable, pinned), Cargo with a committed lockfile, serde_json, proptest; clippy `-D warnings`, rustfmt, cargo-deny for licences; in the nightly job, the debug build (overflow checks on) runs the golden requests, AddressSanitizer covers the Ramulator 2 bridge, and loom plus ThreadSanitizer cover the U9 mailboxes |
| Container | Docker, built on the Linux box only |
| References | BookSim 2 (BSD-2), Ramulator 2 (MIT), SCALE-Sim v3 (MIT), Gemmini (BSD-3) with Verilator (LGPL-3.0/Artistic-2.0), tt-npe and ttsim (Apache-2.0); Accelergy and Timeloop, each only after its licence passes the allow-list |
| Measurement | JAX on Cloud TPU v5e (plus XLA's compiled cost analysis for workload fidelity); TT-Metalium with the device profiler on Blackhole p100a |

No database.

---

## §3 · REPO LAYOUT

Paths marked *(later)* get a `.keep` file, or a one-line docstring module, plus their README at
bootstrap. Their contents arrive in the prompt named in parentheses.

```
rk-uarch/
├── README.md
├── CLAUDE.md
├── Makefile
├── pyproject.toml
├── .python-version         3.12 (one interpreter everywhere, for byte-identical tables)
├── .importlinter
├── .gitignore
├── .pre-commit-config.yaml
├── .github/
│   ├── CODEOWNERS
│   ├── pull_request_template.md
│   └── workflows/ci.yml, nightly.yml
├── contract/
│   ├── README.md
│   ├── uarch_contract/        __init__.py + sourced, hardware, operators, model_shape, precision,
│   │                          request, table, model_card, hashing, errors .py   (later: U-P1)
│   ├── schema/                generated JSON Schema                             (later: U-P1)
│   ├── fixtures/model_shapes/                                                    (later: U-P2)
│   ├── vendor/README.md       rk-sim snapshot lands here                        (later: U-P2)
│   └── tests/                 fixtures/  (no __init__.py: pytest runs in importlib mode)  (later: U-P1, U-P2)
├── hw/
│   ├── README.md
│   ├── designs/  references/  studies/  (studies/ also holds workload-suite@N.yaml)  (later: U-P3, U-P14)
├── src/rkuarch/
│   ├── __init__.py            ENGINE_VERSION = "0.0.0"
│   ├── README.md
│   ├── cli.py                                                                    (later: U-P3)
│   ├── hw/                    __init__.py, derive.py                             (later: U-P3)
│   ├── workload/              README.md, __init__.py                             (later: U-P3)
│   ├── mapping/               README.md, __init__.py, policies/__init__.py       (later: U-P7)
│   ├── engines/               README.md, __init__.py, protocol.py, schema/ (U-P3/U-P7),
│   │                          analytic/, fork/, native/  (each __init__.py)      (later: U-P3, U-P5, U-P11a)
│   ├── table/                 README.md, __init__.py                             (later: U-P3, U-P7)
│   ├── provenance/            README.md, __init__.py                             (later: U-P4)
│   ├── report/                README.md, __init__.py, templates/                 (later: U-P4)
│   └── study/                 README.md, __init__.py                             (later: U-P14)
├── native/
│   ├── README.md
│   ├── Cargo.toml             empty workspace at bootstrap
│   ├── rust-toolchain.toml  deny.toml                                           (later: U-P11a)
│   ├── crates/uarch-engine/                                                     (later: U-P11a)
│   ├── crates/uarch-ramulator-sys/                                              (later: U-P13b)
├── third_party/
│   ├── README.md
│   ├── LICENSES.md            allow-list + empty register
│   └── patches/                                                                  (later: U-P5)
├── containers/
│   ├── README.md
│   └── Dockerfile.engine      base image only                                    (later: U-P5)
├── validation/
│   ├── README.md
│   ├── L0_invariants/  L0m_metamorphic/  mutants/                                (later: U-P6)
│   ├── L1_limits/hand/                                                           (later: U-P8)
│   ├── L2_differential/README.md                                                 (later: U-P8, U-P12)
│   ├── L3_silicon/README.md, tpu-v5e/, blackhole/                                (later: U-P9, U-P15)
│   ├── ledger/README.md                                                          (later: U-P10)
│   ├── perf/  sync/                                                              (later: U-P12, U-P18)
├── measure/
│   ├── README.md
│   └── tpu-v5e/  blackhole/                                                      (later: U-P10, U-P16)
├── scripts/hooks/         human_owned.sh, frozen_predictions.sh (bootstrap); vendor_rk.py (later: U-P2)
├── rk-sim-side/            drafts for adoption INSIDE rk-sim; nothing here runs in rk-uarch
│   ├── decisions/DRAFT-admit-characterized-c2-tables.md
│   └── prompts/P18-characterized-c2-cost.md, P19-stipulations-and-chip-views.md
├── docs/
│   ├── README.md
│   ├── build-spec.md  execution-plan.md  how-it-works.md  glossary.md
│   ├── decisions/     U0000-record-architecture-decisions.md
│   ├── prompts/       every U-P*, U-REVIEW, STANDING, TEMPLATE (from the kit)
│   ├── reviews/  results/
│   ├── server/        setup-dev.sh and RUNBOOK-server.md for the shared Linux box
└── tests/
    ├── README.md
    ├── __init__.py
    ├── unit/test_prompt_sync.py, test_third_party.py
    ├── property/
    └── golden/README.md, scenarios/, expected/
```

---

## §4 · THE README SET, AND CLAUDE.md

These texts are written **verbatim** at bootstrap. They are how each agent session learns the
local rules, so a stale one actively misleads the next session: keep them true (U-REVIEW
check 11).

### 4.0 · `/CLAUDE.md`

```markdown
# rk-uarch — a microarchitecture-level simulator of one chip, feeding rk-sim

## What this is
A harness around simulation engines (analytic, a pinned published fork, and our own native
Rust engine) that produces characterization tables rk-sim reads as the C2 compute answer.
The product is the honesty: every row carries its fidelity, its evidence, and the
stipulations it is conditional on. Detail is not accuracy.

## Commands
- test: `uv run pytest -q` · fast: `make test-fast` (excludes nightly, silicon, native)
- typecheck: `uv run mypy src contract` · lint: `uv run ruff check`
- native: `make native` · `make native-test` (Linux box / engine container)
- table: `uv run uarch table <spec> --model <name> --precision <fmt> --engine analytic|fork|native`
- report: `uv run uarch report <table>` · study: `uv run uarch study <studyspec>`
- vendor rk-sim: `make vendor-rk SHA=<sha> RK=<path>` (humans only)

## Invariants (violating these = stop and ask)
1. Never import `rk`. rk-sim is read only through contract/vendor/, and only in tests.
2. Every hardware number is a SourcedValue with kind claim|stipulation. A claim needs a source
   (or is provenance: stub with source: null). A stipulation needs a rationale and is allowed
   only in hw/designs/ (design_status: proposed). Never invent a claim. DRAM timing from a
   simulator preset is a claim citing the preset file at a pinned SHA; no engine may fall back
   to a preset the spec does not name.
3. Units live in names (_s, _ps, _bytes, _hz, _ratio, _w, _pj). Cycles never leave engines/
   or native/. next_edge() is the only time↔cycle conversion.
4. A table is a pure function of (request, uarch version). Same inputs → same bytes, at any
   worker or thread count. New randomness takes the request seed.
5. A row is one chip's shard, one iteration, all layers, without inter-chip collectives.
6. A C2 result faster than its own U-C0 roofline is a bug, not a finding.
7. Verified is not validated. L0–L2 evidence never lifts a model above stub. Nothing may
   raise a badge. A proposed design is never above estimated.
8. Error is "unknown", never zero. Never fill ci95 from a deterministic run. A quantity a
   level does not model is null, never 0. Energy is "unverified" until its own rung exists.
9. C2 only when every shared resource is at level 2 or 1+ts and sync is exact (or approx(Q)
   covered by a measured curve). Otherwise report the lower composite.
10. Files under validation/L3_silicon/*/predictions/ are committed before any result exists
    and are never edited. check_ordering enforces it.
11. tests/golden/expected/ changes only via `make golden-update` + a docs/decisions/U*.md.
12. third_party/ changes only as numbered patches; licences only from the allow-list.

## Don't
- Don't add a new workload IR or an ONNX import path. Keep standalone ModelSpec + ModelShape
  preparation and support versioned prepared-input replay using OpSpec/TaskGraph (build-spec
  §2.5.1). Engines consume resolved inputs; imported mappings are never silently rebuilt.
- Don't add mapping search, SIMD, GPU, MPI, optimistic sync, a simulation compiler, or a web UI.
- Don't tune any model parameter to pass an L2 or L3 comparison. Record the gap.
- Don't add dependencies beyond pyproject.toml / native/Cargo.toml without asking.
- Don't write `unsafe` Rust outside native/crates/uarch-ramulator-sys/.
- Don't read rk-sim's docs/vision/ unless a prompt names a section; never edit rk-sim, except
  in U-P19 and U-P20, which run inside rk-sim under its own rules.

## Vocabulary
kind: claim | stipulation · design_status: proposed | reference
initial_state: steady | cold · mapping match: matched | compiler-chosen
per-subsystem levels 0 | 1 | 1+ts | 2 (3 = reference only) → composite C0/C1/C2 for rk-sim
calibration: measured > spec_derived > estimated > stub (rk-sim's), worst of claims
L0 invariants · L0m metamorphic · L1 limits · L2 differential · L3 same-class silicon · L4 target
Never call this codebase or its engine "DES" (that is rk-sim's R1), "F2" or "C2".

## Workflow
- Prompts live in docs/prompts/. One task per session. Write the acceptance tests first.
- Lanes (CODEOWNERS is authoritative): A = src/rkuarch/{hw,workload,mapping,engines,table},
  native/, third_party/, containers/, cli.py. B = hw/, src/rkuarch/{provenance,report,study},
  validation/, measure/, scripts/, .github/workflows/.
  Both humans: contract/, tests/golden/expected/, CLAUDE.md, docs/decisions/.
- Agents propose and stop on contract/, tests/golden/expected/, CLAUDE.md, docs/decisions/.
```

### 4.1 · `/README.md`

```markdown
# rk-uarch

A microarchitecture-level simulator of one AI accelerator. It turns a hardware spec and an
LLM model description into a characterization table — the cost of one inference iteration
per (batch, context) point — at a stated fidelity, with its own errors measured and a badge
earned only against real silicon. rk-sim reads those tables to price a custom ASIC at C2.

## Quickstart
    uv sync --extra dev
    make test-fast
    uv run uarch table hw/designs/npu-l4.yaml --model llama-3.1-8b --precision bf16 --engine analytic
    uv run uarch report tables/<hash>.json

## Repo map
contract/ the shared vocabulary · hw/ designs and references · src/rkuarch/ the harness ·
native/ the Rust engine · validation/ the evidence · measure/ silicon kits · docs/ everything else

## Working here
Read CLAUDE.md, then docs/build-spec.md §0. Sprints and prompts: docs/execution-plan.md.

## Status
See docs/execution-plan.md STATUS and docs/how-it-works.md.
```

### 4.2 · `/contract/README.md`

```markdown
# contract — THE shared vocabulary (human-owned)

Everything rk-sim and uarch exchange is defined here, and nowhere else: SourcedValue (with
kind claim|stipulation), HardwareSpec, the operator vocabulary, ModelShape, the
CharacterizationRequest, the UarchCostTable, the ModelCard, hashing and the error taxonomy.

## Rules
- Agents propose changes and stop. Both founders approve; every change has an ADR.
- Additive change = MINOR bump of uarch-contract; breaking change = MAJOR bump.
- Names copy rk-sim's where rk-sim has the concept. The vendored round-trip test proves it.
- Units live in names; no field carries cycles.
- After changing anything: `make gen`, commit contract/schema/, update fixtures.

## After integration
rk-sim adopts this contract into rk/schema/characterization.py (rk-sim P18's boundary ADR).
From then on rk-sim is the source of truth and this directory vendors it back.
```

### 4.3 · `/contract/vendor/README.md`

```markdown
# vendor — a read-only snapshot of rk-sim

Written only by `make vendor-rk SHA=<sha> RK=<path>`, run by a human. Holds rk-sim's generated
schema bundle, the source of the modules the contract mirrors, parity fixtures generated by
executing rk-sim's own iteration_cost(), and a MANIFEST of sha256s. Never edit by hand.
Production code never imports from here; tests read it by path.
```

### 4.4 · `/hw/README.md`

```markdown
# hw — hardware specs

designs/     chips that do not exist (design_status: proposed). Design choices are
             STIPULATIONS, each with a rationale. They define the question; they are not claims.
references/  real chips (design_status: reference). CLAIMS ONLY, each with a URL to a vendor
             page or document. What the vendor does not publish is provenance: stub with
             source: null — never a stipulation. The loader refuses a stipulation here.
studies/     StudySpecs: variants of a proposed design that change only what the design is
             free to choose (stipulated values, counts included, and categorical fields).

derive_rk_params() turns a spec into the params rk-sim's component entry must carry. If they
disagree, the spec is right and the component is wrong. Stipulations propagate as
stipulations; a derived claim is only as good as its worst input.

Every numeric leaf is a SourcedValue, counts and DRAM organisation and timing included. A
simulator preset supplies DRAM timing only through memory.dram.timing_preset {file, sha}, as
claims citing that file@sha. Each *_cycles leaf is in its block's clock domain (build-spec
§2.3.2). SRAM size and SRAM pJ/byte travel together: a
variant that changes one re-stipulates the other. studies/ also holds the versioned workload
suite (workload-suite@N.yaml) that studies and L3 shape selection read.
```

### 4.5 · `/src/rkuarch/README.md`

```markdown
# rkuarch — the harness

request → workload (op graph) → mapping (TaskGraph) → engine (EngineJob → EngineResult)
→ table (rows, interpolation, measured errors) → provenance (badges, conditional_on)
→ report / study. Never imports rk. The engines live behind one protocol; the table
does not know which engine ran except through EngineResult.fidelity_detail.
```

### 4.6 · `/src/rkuarch/workload/README.md`

```markdown
# workload — one iteration's operator graph

Input: rk-sim ModelSpec + ModelShape (parity ≤ 1% or loading fails) + precision + tp + a
canonical query (decode: B sequences of T/B; prefill: n prompts of L). Output: the operator
graph of ONE rank of a tp-way tensor-parallel split (heads, KV heads, FFN and vocabulary
divided by tp; no collectives), using contract/operators.py only. Attention is one
attention_fused operator: scores stay on chip and never reach DRAM. A multiply-add is two
operations. Layer reuse must be declared in
the graph, and its error is measured by table/. KV is read in pages of the request's
block_size_tokens. MoE is active-parameter dense-equivalent only. `omissions` lists routing,
imbalance, all-to-all, host/runtime time, address translation, coherence and mixed
prefill/decode iterations; they become table warnings. FLOP parity against rk-sim's own counts
runs on every change; every deviation above 0.5% has a name and a reason in deviations.py.
`uarch characterize` reports FLOPs, bytes, operational intensity and shape regime per op
across the grid; L3 suites and workload suites pick shapes from it.

Preparation boundary (build-spec §2.5.1): this module is the standalone, versioned producer
and loader of prepared OpSpec graphs. Engines receive its resolved output. A supplied
rank-local graph bypasses model expansion and sharding; validate its identity, supported
scope, precision, dependencies and omissions. Keep the high-level convenience path usable
without rk-sim or a compiler. U-P3 adds export/import/replay; no second workload IR is added.
```

### 4.7 · `/src/rkuarch/mapping/README.md`

```markdown
# mapping — named, versioned policies

A policy is a pure function (op graph, HardwareSpec) → TaskGraph, and a STIPULATION about how
a compiler would lay the work out. Its name@version travels to every row. There is no search
and no autotuning. A better policy is a new version, never an edit. A policy declares the
matrix dataflow it needs and its buffer depth, and places every SRAM-resident buffer (core,
offset, bank); a tile that does not fit is refused, never spilled silently. onnxim-compat@N
exists only so the native engine can be compared with the fork on the same work.

Policies execute in preparation, before simulation. U-P7 serializes their complete TaskGraph
output for inspection and replay. An externally supplied mapping follows the same validated
format and bypasses these policies. Engines never silently remap an input. Record producer
versions, hardware binding and content hashes; moving a file is not a mapping change, while
changing placements under the same policy label is. Keep local preparation as the default.
```

### 4.8 · `/src/rkuarch/engines/README.md`

```markdown
# engines — one protocol, three engines

Every engine: EngineJob JSON in, EngineResult JSON out, as a subprocess or in-process pure
function. No foreign-function interface.
- analytic/  U-C0: our roofline of the spec. aggregate mode reproduces rk-sim C0 to ±0.1%;
             per_op mode is always ≥ aggregate. Anchors every L1 test.
- fork/      the pinned published simulator in the engine container. Its mapping is its own,
             recorded as fork:<name>-default@<sha>. Fields it cannot represent are listed.
- native/    the Python side of our Rust engine (native/ at the repo root).
Cycles live here and in native/, and nowhere else. EngineResult carries duration_ps, a
critical-path attribution that sums to it, and diagnostics that are null wherever the level
does not model them, never 0.

Prepared-input ownership (build-spec §2.5.1): engines consume validated resolved work,
not high-level model recipes that invoke a builder. U2 analytic jobs carry resolved OpSpecs
and an explicit analytic scope; U4 detailed jobs carry mapped TaskGraphs. U2 establishes
versioned protocol fixtures for later fork/Rust consumers. Replay requires neither local
producer execution nor a compiler. Fork-delegated mapping is explicit and supplied mappings
that it cannot honor are refused. Resource timing and contention remain simulation outputs.
```

### 4.9 · `/src/rkuarch/table/README.md`

```markdown
# table — request in, hashed UarchCostTable out

Builds the grid from the request's envelope (and refuses a request whose grid does not cover
it), runs points in a process pool (parallel across points only; byte-identical at any worker
count), interpolates exactly as declared, and measures its own errors: leave-one-out
interpolation (also weighted by rk-sim's visit density when the request supplies it),
batch-composition reduction, layer reuse, and cold vs steady. It reports them; it never
corrects them. Outside the grid is an error, never a clamp or an extrapolation.
```

### 4.10 · `/src/rkuarch/provenance/README.md`

```markdown
# provenance — what a number may claim

Worst-of over claims only; stipulations go to conditional_on. The model is a contributor whose
rung comes from validation/ledger only, scoped by applicability: family, op class, precision,
shape regime, load regime and mapping match. A proposed design is capped at estimated.
validated_error_band is None ("unknown") unless in-scope ledger entries supply it. Energy is
"unverified" until its own rung exists. Nothing in this directory may raise a badge — a fuzz
test asserts it.
```

### 4.11 · `/src/rkuarch/report/README.md`

```markdown
# report — the only way a number reaches a human

Static HTML (plus a Markdown twin), no framework, no network. Every number renders through
badged(value, unit, badge, conditional_on, error_band); a template lint fails on any raw value.
"conditional · N stipulations" is a scope statement, not a warning. An absent error band
renders "unknown", never "±0"; a null diagnostic renders "not modelled", never 0. Reports carry
the architect diagnostics and a per-op roofline (static SVG). Each report ends with what the
table does not claim, including the declared omissions.
```

### 4.12 · `/src/rkuarch/study/README.md`

```markdown
# study — comparing designs

A StudySpec names a base design, the parameters to vary, a versioned workload suite (or one
request template), one engine and fidelity. Variants may change only what a proposed design
is free to choose: stipulated values (counts included), categorical fields, and the mapping
policy; each change is recorded in conditional_on. A reference is never varied.
Tables are cached by request hash. The diff report shows which regime moved and why, per
workload and as a geometric mean of normalised speedup (never an arithmetic mean of ratios), a
one-at-a-time tornado labelled "local sensitivity at these points, not a ranking", energy with
its own conditions (unverified until its rung exists), and each variant's detail delta against
its own U-C0. No optimiser, no fitted surrogate, no area model.
```

### 4.13 · `/native/README.md`

```markdown
# native — our event-driven engine (Rust)

Spec: docs/build-spec.md §2.8 (and §2.9 for parallel execution). A Cargo workspace, built in
the engine container; `make native`, `make native-test`. Binary: uarch-engine
(EngineJob → EngineResult), behind the same subprocess protocol as every engine.

## Rules
- Time is u64 picoseconds; next_edge() is the only time↔cycle conversion. Clocks are
  integer freq_hz; edges are rounded up to the picosecond, periods never are.
- Ramulator 2 ticks in batches to a conservative horizon, catches up over idle gaps, and
  must match the tick-every-cycle debug mode byte for byte (build-spec §2.8).
- Events are 32-byte `#[repr(C)]` `Copy` structs, totally ordered by (t_ps, phase, target,
  seq). Dispatch is a `match` on kind; no `dyn` on the hot path.
- One owner per resource; only events targeted at it mutate it (asserted in debug builds).
- No HashMap or HashSet on any path that reaches output (clippy disallowed-types).
- `unsafe` only in crates/uarch-ramulator-sys, the C++ bridge to Ramulator 2; every other
  crate has #![forbid(unsafe_code)].
- Dependencies: serde, serde_json, proptest (dev); cxx and Ramulator 2 (from U7); loom (dev,
  from U9). Nothing else without an ADR; cargo-deny checks every licence.
- The engine protocol's JSON Schema (src/rkuarch/engines/schema/) is the contract with the
  harness; a Rust test holds the serde types to it.
- Determinism before speed. A speed-up that changes bytes is a bug.
```

### 4.14 · `/third_party/README.md`

```markdown
# third_party — pinned engines and references

Every component is pinned by SHA and registered in LICENSES.md with its licence and where it
is used. Allow-list: MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0 (with or without the LLVM
exception). LGPL tools (Verilator) may be run, not shipped modified. Local changes only as
patches/NNNN-<slug>.patch, each with a one-line reason; CI checks they still apply. The fork
stays here for the life of the project as the native engine's L2 reference.
```

### 4.15 · `/containers/README.md`

```markdown
# containers — the engine image

Dockerfile.engine builds the pinned fork, BookSim 2 and Ramulator 2 at pinned SHAs, and the
native engine, unattended, from a script. Build and run on the Linux box only; never on a
laptop. The image digest is recorded in every EngineResult produced inside it.
```

### 4.16 · `/validation/README.md`

```markdown
# validation — the evidence

L0_invariants/    conservation, bounds, Little's law, causality, determinism, SRAM capacity,
                  attribution sums, energy conservation
L0m_metamorphic/  relations that must hold without an answer key (property tests)
mutants/          deliberately broken engines each suite must catch (nightly)
L1_limits/        closed forms where exact, the U-C0 floor, and hand/ fixtures worked on paper
L2_differential/  BookSim 2, Ramulator 2, SCALE-Sim v3, Gemmini/Verilator, tt-npe, native↔fork,
                  Timeloop (mapping reference, optional); energy references after U8
L3_silicon/       frozen predictions and immutable results per reference chip
ledger/           one entry per comparison; the only source of a model card's rung
perf/ sync/       simulator metrics; the error-vs-quantum curve

Verified (L0–L2) is not validated (L3+). Suites run through the engine protocol against every
engine; never relax a suite because an engine fails it — that is a finding.
```

### 4.17 · `/validation/L2_differential/README.md`

```markdown
# L2 differential — agreement with independent models

Each comparison records deviations as data, attributes each one it can to a named mechanism,
and reports the fraction of >5% deviations that carry a mechanism. Only the NoC bound
(within 10% of BookSim 2 below 70% of saturation) is enforced. native↔fork comparisons run only
on matched mapping and matched levels. A comparison of a sub-model with the same code (a fork
whose NoC is BookSim 2, against BookSim 2) is refused as not independent. Agreement here is
never called validation.
```

### 4.18 · `/validation/L3_silicon/README.md`

```markdown
# L3 silicon — predictions first, then measurements

Per reference chip: SUITE.md (signed by both lanes before predictions exist), predictions/
(committed in one "FROZEN PREDICTIONS:" commit, never edited), UNKNOWNS.md (every stub the
engine read), results/ (raw and immutable). check_ordering.py fails CI if any result appears in
a commit at or before its prediction's. A new prediction is a new file in a new commit. Every
benchmark states device-side timing, its mapping match (matched | compiler-chosen), its initial
state, and the compiler-reported FLOPs and bytes the workload graph is checked against.
```

### 4.19 · `/validation/ledger/README.md`

```markdown
# ledger — the only thing that can promote a model card

One entry per (benchmark × prediction source): question, granularity, applicability
dimensions (family, op class, precision, shape regime, load regime, mapping match), predicted,
measured, signed relative error, engine and spec versions. A duplicate key with a different
prediction is refused. Promotion is scoped to exactly what the entries cover; never by hand;
never by averaging across classes. Workload-fidelity entries (FLOPs and bytes vs the
compiler's counts) and diagnostic-fidelity entries (row diagnostics vs device counters) never
promote a duration card. Failing verdicts are published like passing ones.
```

### 4.20 · `/measure/README.md`

```markdown
# measure — silicon measurement kits

Written and dry-run before any paid hour or real card run: CPU JAX for tpu-v5e/, ttsim
(functional only) for blackhole/. Dry-run outputs are labelled SYNTHETIC and the ledger refuses
them. Real runs happen only after check_ordering passes. Every result captures its environment.
Timing is device-side only; kits also record the compiler-reported FLOPs and bytes, and the
device counters the chip exposes.
```

### 4.21 · `/tests/README.md`

```markdown
# tests

unit/ property/ golden/ plus contract/tests/ and validation/ (collected by pytest).
Markers: golden, nightly, silicon, native. `make test-fast` excludes nightly, silicon, native.
Write the acceptance tests first. A skipped test states its reason and id; it never passes.
```

### 4.22 · `/tests/golden/README.md`

```markdown
# golden — full-request regressions

scenarios/ are lane-writable requests; expected/ is human-owned and changes only via
`make golden-update` plus a docs/decisions/U*.md saying why. Until an expected file exists its
test skips with a reason. Golden tables are small on purpose (2-core and 4×4 designs, 12-point
grids) so CI stays fast.
```

### 4.23 · `/docs/README.md`

```markdown
# docs

build-spec.md (what and how) · execution-plan.md (when and who) · how-it-works.md (the
system today, with real numbers) · glossary.md · decisions/ (U-numbered ADRs) · prompts/ (one
task per session) · reviews/ (handoffs and U-REVIEW records) · results/ (published findings) ·
server/ (setup-dev.sh and the runbook for the shared Linux box).
```

---

## §5 · INTERFACES BETWEEN THE TWO LANES

| Interface | Producer → consumer | Defined in | Rule |
|---|---|---|---|
| The contract | both → everyone | `contract/` | Human-owned; ADR per change |
| EngineJob / EngineResult | Lane A engines → Lane B suites | §2.5, `engines/protocol.py` | Every suite runs through it, so suites never depend on one engine |
| UarchCostTable | A `table/` → B `provenance/`, `report/`, `study/` | contract | B never recomputes a physical number |
| Model card and ledger | B → A (via table provenance) | contract, `validation/ledger/` | A never sets a badge |
| SUITE.md per reference | both, signed | `validation/L3_silicon/*/` | Signed before predictions exist |
| Predictions → results | A commits, B measures | L3 README | Ordering enforced by git |
| Workload suite | B → both | `hw/studies/workload-suite@N.yaml` | Versioned; studies and L3 shape selection read it; chosen from `uarch characterize` |

---

## §6 · CONVENTIONS

**6.1 Units live in names.** Allowed suffixes: `_s`, `_ps`, `_bytes`, `_hz`, `_ratio`, `_rel`
(a relative error), `_w`, `_j`, `_pj`, `_per_s`, `_per_cycle`, `_flits`. Counts are `n_*` or
`*_count`. A mapping field carries the unit in its own name and its keys name resources
(`attribution_s: {compute: …}`, `peak_resident_bytes: {hbm: …}`); every value inherits the
unit. rk-sim Channel names (`matrix_ops`, `vector_ops`) are copied verbatim, and U-P2's
round-trip pins them. HardwareSpec leaves may also end in `_cycles`, in the clock domain
§2.3.2 assigns, and may name counts plainly (`banks`, `engines`); cycles never appear in a
request or a table. Converting is a named function, never an inline multiply.

**6.2 Decimal units.** 1 GB = 1e9 bytes, as datasheets quote them. Bandwidth is per direction.

**6.3 Human-owned paths.** `contract/`, `tests/golden/expected/`, `CLAUDE.md`,
`docs/decisions/`. Committed predictions are frozen for everyone.

**6.4 The dependency is one-way and test-only.** uarch → vendored rk-sim snapshot, in tests.
rk-sim → uarch output files, from U10. Enforced by import-linter.

**6.5 Hashing.** Canonical JSON (sorted keys, repr-round-trip floats, no NaN) → sha256.
Every table carries the spec, request and table hashes.

**6.6 Determinism.** Pure function of (inputs, version, seed). Byte-identical across runs,
worker counts and, from U9, thread counts in exact mode. Nothing that reaches output may
depend on iteration order, wall-clock time or thread interleaving.

**6.7 CI.** Jobs: lint, types, import-linter, tests (unit + contract + validation), contract
(the contract tests, the vendored-snapshot manifest and the schema-staleness check), golden,
determinism, licences, patches, native, ordering, perf. A job may report "nothing yet" and pass
**only while the thing it checks does not exist yet**:
- contract: no tests under `contract/tests/`;
- golden: no expected files;
- determinism: no golden scenarios;
- patches: no files under `third_party/patches/`;
- native: no Rust sources under `native/crates/`;
- ordering: no `predictions/`;
- perf: no baselines.

The tests job fails on an empty suite. Nightly (on the Linux box as a self-hosted runner) runs
the mutants, the L2 suite, the native debug build over the golden requests, AddressSanitizer on
the Ramulator 2 bridge, and (from U9) loom and ThreadSanitizer on the mailboxes.

**6.8 Patches.** `third_party/patches/NNNN-<slug>.patch`, one reason line each.

**6.9 ADRs.** `docs/decisions/UNNNN-slug.md`. U0000 records the practice. Numbers follow the
prompt that writes them where possible.

**6.10 Goldens.** Small by design. `make golden-update` regenerates `expected/` and refuses if
numbers move while `ENGINE_VERSION` is unchanged.

**6.11 Unmodelled is null.** A quantity a level does not model is `null` in every output and
renders "not modelled". A zero means the model computed zero.

---

## §7 · INTEGRATION WITH rk-sim

### 7.1 Files, not calls

rk-sim never invokes uarch during a run. It reads a hashed table. That keeps rk-sim's engine
pure (its invariant 4). Neither codebase imports the other at any point.

**The seam is language-neutral.** rk-sim sees only `UarchCostTable` JSON, validated by the
contract's JSON Schema, which the Python harness assembles from `EngineResult` JSON. The
native engine's language (Rust) never reaches rk-sim, which needs no Rust toolchain, no
binary, no bindings. rk-sim's `IterationCost` anticipates a future native-code DES that
evaluates costs locally with no per-event calls back into Python; a table-backed cost stays
compatible with that, because the table's interpolation is declared in closed form and
`contract/fixtures/interpolation_vectors.json` pins expected values, so any implementation,
in any language, can prove it reproduces them (U-P7).

### 7.2 The seam, and the nine rules

The seam is rk-sim's `rk/engine/f0/compute.py::IterationCost`. Its comment already calls it
*the seam*, and says a later term makes the struct *"gain a field, not get replaced."* A
table-backed cost satisfies the same interface the R1 DES already calls:

1. **A row is one shard; the tp divisor is 1.** Collectives stay rk-sim's. `_time_s` divides
   by tp today, so carrying that into the table path silently double-counts tensor parallelism.
2. **Canonical batch compositions** are used, and the measured interpolation, reduction and
   layer-reuse errors are surfaced as run warnings.
3. **The envelope is checked at build time.** Extrapolation is refused.
4. **DVFS uses the table's frequency axis.** DVFS without one is a hard error.
5. **Counts use rk-sim's channel names.** Extension channels are carried as "unmodelled".
6. **One chip, one set of facts.** The component's params equal `derive_rk_params` of the
   cited spec: the spec hash matches, and the table's `provenance.params` (which are
   `derive_rk_params` of that spec) equal the component's params field by field.
7. **Steady state for back-to-back iterations.** R1 prices back-to-back iterations, so it reads
   `initial_state: steady` tables. A `cold` table in an R1 run is refused at build time.
8. **The KV layout matches.** The table's `kv_layout.block_size_tokens` equals the plan's block
   size, checked at build time.
9. **The tp matches.** A table is one rank of a tp-way split that uarch's workload graph built
   (§2.3.4). Its `tp` equals the plan's tp for that component, checked at build time; a table
   built for another tp is refused, never rescaled.

### 7.3 What lands in rk-sim

| Order | What | Who | Where |
|---|---|---|---|
| 1 | Boundary ADR admitting characterized C2 tables, and its schema PR | both founders | Draft: `rk-sim-side/decisions/DRAFT-admit-characterized-c2-tables.md` |
| 2 | P18: characterized C2 cost | rk-sim Lane A | `rk-sim-side/prompts/P18-characterized-c2-cost.md` (= U-P19) |
| 3 | P19: stipulations through the product, and the chip views | rk-sim Lane B | `rk-sim-side/prompts/P19-stipulations-and-chip-views.md` (= U-P20) |

Why a boundary ADR is needed: build-spec §1.3 of rk-sim rules out C1+ fidelity and
memoization surrogates for the prototype. A characterization table is both, so admitting it is
a scope decision for both founders, made at an rk-sim sprint boundary.

### 7.4 Errors and degradation

This follows rk-sim's own rule: *a system default degrades; an explicit per-instance override
raises; nothing degrades silently.*

| Situation | C2 by system default | C2 by per-instance override |
|---|---|---|
| No table for this component | STUB for that component, with a warning naming the missing table | `NoTableForComponent` |
| Workload envelope exceeds the grid | Degrade, with a warning naming the region | `EnvelopeExceedsGrid` at build time |
| Table spec hash ≠ component's | `SpecHashMismatch` | same |
| Table `provenance.params` ≠ component's params | `ParamsMismatch` | same |
| Table tp ≠ plan's tp | `TpMismatch` | same |
| Contract major-version mismatch | `ContractMajorMismatch` | same |
| Contract minor-version mismatch | Warning | Warning |
| Peak resident HBM > declared capacity | `ResidencyExceedsCapacity` for weights; warning for KV (rk-sim's M0 rule) | same |
| Non-finite or negative row | `NonFiniteRow` | same |
| DVFS declared, no frequency axis | `MissingFrequencyAxis` | same |
| `cold` table in an R1 run | `InitialStateMismatch` | same |
| Table KV block size ≠ plan's | `KvLayoutMismatch` | same |
| C2 not built for this component | UI shows C2 disabled, with the reason (ADR 0016) | — |

### 7.5 What rk-sim bakes in meanwhile

Two things, both small and both linear:

- Every new TypeScript `switch` over badges will need the conditional state. Keep the switches
  exhaustive so the compiler finds them.
- Every new `IterationCost` method is one more the table-backed variant must implement.

Neither requires changing rk-sim now.

---

## §8 · THE PROMPT PACK

Ready-to-paste prompts for a coding agent. The same texts live one per file in `docs/prompts/`, and `tests/unit/test_prompt_sync.py` fails if the two ever differ.

**Conventions.** The native engine's two largest steps are split so that each fits one
session: U-P11a–c (sprint U6) and U-P13a–d (sprint U7); "U-P11" and "U-P13" name those groups.
One prompt = one fresh session, started with `docs/prompts/TEMPLATE-implementation-session.md`. Each prompt assumes `CLAUDE.md` is loaded and names the files to read, so it does not repeat the standing rules. **Every prompt carries acceptance tests the agent writes first and must show passing.** That check is the entire productivity mechanism. Where a prompt says *stop*, the agent stopping is the correct outcome. The sprint and lane of each prompt are in `docs/execution-plan.md` §6.


### U-P0 · U0 · either, run once — Repo bootstrap

```text
CONTEXT TO LOAD: docs/build-spec.md §1 through §6 (scope, architecture, repo layout, the
README set, interfaces, conventions). docs/execution-plan.md §1 (the sprint loop).

TASK: create the rk-uarch skeleton. Structure and documentation only: no schema, no engine,
no test logic. When you are done, someone should be able to clone the repository and
understand the whole system before a single model exists.

1. The tree in build-spec §3, exactly. Python packages get __init__.py with a one-line
   docstring. Directories filled by later prompts get a .keep plus their README now.
2. Every README in build-spec §4 and CLAUDE.md, verbatim. These are the point of the task —
   do not summarise, merge or improve them.
3. Tooling: pyproject.toml (uv, Python 3.12, hatchling with
   [tool.hatch.build.targets.wheel] packages = ["src/rkuarch", "contract/uarch_contract"]),
   .python-version (3.12), Makefile, .importlinter, .pre-commit-config.yaml, .gitignore,
   .github/CODEOWNERS,
   .github/workflows/{ci.yml,nightly.yml}, native/Cargo.toml (an empty workspace that
   builds nothing yet), containers/Dockerfile.engine (base image only), and
   third_party/LICENSES.md with the allow-list and an empty register.
4. tests/unit/test_prompt_sync.py: asserts every ```text block in build-spec §8 equals the
   text block in the matching docs/prompts/ file. It passes on day one because the kit
   ships both.

ACCEPTANCE TESTS:
1. uv sync --extra dev succeeds on a clean checkout.
2. make test runs and passes; make lint and make typecheck are clean.
3. Every CI job exists. A job that has nothing to test yet reports "nothing yet" and exits 0
   ONLY where build-spec §6.7 says it may. Every other job fails on an empty suite.
4. python -c "import rkuarch, uarch_contract" succeeds, and import-linter forbids
   rkuarch -> rk.
5. git status is clean after committing.

GUARDRAILS: Do not create any file that is not in build-spec §3. Do not write model,
schema, engine or test logic — later prompts own all of it. Do not edit anything under
docs/ except to add docs/decisions/U0000-record-architecture-decisions.md, adapted from
rk-sim's ADR 0001.
```


### U-P1 · U1 · joint → Lane A — The contract

```text
CONTEXT TO LOAD: CLAUDE.md, docs/build-spec.md §2.3 (the contract), §2.4 (fidelity), §2.6
(applicability bins) and §7 (integration), contract/README.md. From rk-sim, READ-ONLY, from
a local clone at the SHA you record in ADR U0001: rk/provenance.py, rk/engine/f0/compute.py
(IterationCost,
iteration_cost, IterationCounts), rk/engine/f0/power.py (operating_point), rk/schema/
{fidelity,channels,execution,workloads}.py, docs/decisions/0011, 0016, 0021, 0026, 0027, and
docs/prompts/P16-symbolic-operators-and-parallelism.md for its baseline operator list.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Record the ownership decision in U0001: retain the standalone model-to-workload and
policy-to-mapping frontend; engines consume resolved inputs. Supplied prepared workloads
carry authoritative rank shapes, and supplied mappings are not silently replaced. U-P3's
U0003 owns the concrete prepared-input schemas and public-field revision before U2 coding.
Do not add those future payload fields in U1. Keep final U0001 acceptance explicit.

TASK: contract/uarch_contract/, the only vocabulary uarch shares with rk-sim. Pydantic v2,
frozen=True, extra="forbid" on every model.

AUTHORITY: CLAUDE.md says agents propose and stop on contract/ and docs/decisions/. This
prompt is that proposal. Write contract/ and docs/decisions/U0001 in full, leave them
uncommitted, and stop; both founders review them and commit with UARCH_HUMAN=1.

1. sourced.py — SourcedValue. rk-sim's five fields VERBATIM (value, unit, provenance, source,
   date) with rk-sim's validator semantics: provenance=stub requires source=None, anything
   else requires a non-empty source, non-finite values refused. PLUS one field:
   kind: Literal["claim","stipulation"] = "claim".
   A STIPULATION IS NOT A WEAK CLAIM, IT IS A DIFFERENT THING. It is a design choice for a
   chip that does not exist ("tile SRAM = 2 MB") and it defines the question the way n_layers
   does in rk-sim's ModelSpec. So: kind="stipulation" requires provenance=None, source=None,
   date=None, and a non-empty `rationale: str`. kind="claim" forbids rationale. Write the
   validator so both halves fail loudly with a sentence that says which rule was broken.
2. hardware.py — HardwareSpec, design_status: Literal["proposed","reference"].
   - A "reference" describes a real chip and may contain ONLY claims.
   - A "proposed" design may contain stipulations.
   - The loader refuses a stipulation anywhere in a reference, naming the parameter path.
   Structure, per build-spec §2.3.2 (Rev 2.1): clock_domains (each with scales_with_core);
   cores (grid rows and cols; core_type with a matrix engine, its array, supported dataflows,
   accumulator_bytes, operand_buffer_bytes and operand_bytes_per_cycle, a vector engine, SRAM
   with banks, DMA engines with max_outstanding and request_bytes, and job_overhead_cycles);
   sync (mechanism, barrier_latency_cycles); an optional shared_sram; one or more NoCs
   (topology mesh|torus, link_bytes_per_cycle, router_latency_cycles, virtual_channels,
   buffer_flits, direction for multi-NoC designs); memory (interleave granularity and scheme;
   controllers with attachment coordinates, scheduler, page_policy, read and write queue
   depths and noc_credits; DRAM standard, channels, bandwidth, capacity, organization,
   timing_preset and timing); numeric formats (byte width, accumulation width, block-scale
   bytes); energy coefficients per activity, with voltage_ratio per frequency ratio; static
   power; tdp. EVERY NUMERIC LEAF IS A SourcedValue, counts included (grid, array, banks, DMA
   engines, virtual channels, DRAM channels and organisation, queue depths, credits), with an
   integral value for counts; a reference marks an unpublished count as a stub. Only these
   stay plain: categorical enums (topology, direction, dataflows, scheme, scheduler,
   page_policy, sync mechanism), list structure (how many NoCs and controllers), attach
   coordinates, and a format's byte width. A preset supplies DRAM timing only through
   memory.dram.timing_preset {file, sha}; each timing claim it supplies has source
   "<file>@<sha>". Each *_cycles leaf is in its block's clock domain (build-spec §2.3.2).
3. operators.py — THE OPERATOR VOCABULARY. uarch holds the pen here because it has the
   harder requirement: a roofline needs a name and a FLOP count; a tiled model needs
   shapes, layouts, reduction axes and per-operand precision. Start from rk-sim P16's baseline
   list and use its names where they exist: Q/K/V projection, QK score, softmax, AV
   application, output projection, normalization, residual addition, FFN projections,
   activation. Add only what tiling needs (e.g. kv_write, embedding, lm_head) and
   attention_fused (QK score -> softmax -> AV over KV tiles, scores on chip; its operation
   count is the sum of its three parts, and its DRAM operands are Q, K, V and O only; build-spec
   §2.3.5). Each OpSpec
   carries its M/N/K (or equivalent) as named dimensions, operand dtypes and the reduction
   axis. COUNTING FOLLOWS rk-sim P7b: A MULTIPLY-ADD IS TWO OPERATIONS. Restate it in the
   module docstring; do not re-decide it.
4. model_shape.py — ModelShape, the sidecar ModelSpec lacks: d_ff, gated_mlp, vocab_size,
   attention: Literal["mha","gqa"], tie_embeddings, expert_d_ff (MoE only). Plus a copy of
   rk-sim's ModelSpec with IDENTICAL field names and validators, and
   implied_params(spec, shape) -> (total, active). check_parity() raises unless both are
   within 1% of ModelSpec's total_params and active_params. Two sources describing
   different models is the failure this exists to make impossible.
5. precision.py — rk-sim's PrecisionFormat, all eight members, same string values.
6. request.py — CharacterizationRequest, field for field as build-spec §2.3.3 lays it out:
   contract version, rk_schema_snapshot, component_id, hardware_spec_hash, model, model_shape,
   precision {compute, kv_cache}, tp, envelope, grid (decode B × context_per_seq, prefill
   n × L, frequency_ratio), mapping_policy, uarch_fidelity (the fidelity_detail keys and
   values of build-spec §2.4), initial_state (steady | cold), kv_layout {block_size_tokens},
   visit_weights (optional), seed. tp is the shard: the table is ONE rank of a tp-way split
   (build-spec §2.3.4).
7. table.py — UarchCostTable and Row. A ROW IS ONE CHIP'S SHARD, ONE ITERATION, ALL LAYERS,
   WITHOUT INTER-CHIP COLLECTIVES. Write that sentence in the class docstring. Row keys:
   decode {phase, batch, total_context_tokens, frequency_ratio}; prefill {phase, n_prompts,
   prompt_tokens, frequency_ratio}. Fields per build-spec §2.3.3: duration_s, u_c0_duration_s (uarch's own aggregate roofline for the
   same point, which is the floor every C2 row must respect and the "detail delta" rk-sim's
   Compare shows), attribution_s {compute, memory, noc, sync, overhead} (a critical-path
   split whose parts sum to duration_s), counts {matrix_ops, vector_ops, memory_read_bytes,
   memory_write_bytes} (rk-sim Channel names), ext_counts {sram_read_bytes, sram_write_bytes,
   noc_flit_hop_count}, peak_resident_bytes {hbm, sram}, and diagnostics (build-spec §2.3.3):
   every diagnostic is Optional with NO default of 0, because null means "not modelled".
   Table-level: contract, uarch_version, request_hash, table_hash, tp, initial_state,
   kv_layout, interpolation spec, measured_error {interpolation_loo (with
   weighted_median_rel), composition_reduction, layer_reuse, cold_vs_steady (with
   priming_2_vs_1_max_rel); each sampled error with n_samples}, flop_parity {max_rel,
   declared_deviations[{id, deviation_rel, reason}]}, composite_fidelity, fidelity_detail
   (build-spec §2.4's keys and values), provenance {params (derive_rk_params of the spec),
   model_card {hash, badge, evidence, validated_error_band, energy_verification},
   conditional_on}, warnings (the declared omissions of build-spec §2.3.4 among them).
8. model_card.py — ModelCard: model_id (engine, engine version, fidelity_detail, mapping
   policy), badge, evidence (ledger ids), verification {L0, L0m, L1, L2: report hash or
   None}, validated_error_band: None | {low_rel, high_rel, scope {family, op_classes,
   precisions, shape_regimes, load_regimes, mapping_match}}, energy_verification: None |
   {L0, L2: report hash per coefficient family}. None means "unknown" (for energy, "unverified"). THERE IS NO ZERO
   DEFAULT ANYWHERE IN THIS FILE.
9. hashing.py — canonical_json (sorted keys, floats via repr round-trip, no NaN), sha256,
   spec_hash / request_hash / table_hash. CONTRACT_VERSION = "uarch-contract/0.1".
10. errors.py — one exception class per raising row of build-spec §7.4's error table:
    NoTableForComponent, EnvelopeExceedsGrid, SpecHashMismatch, ParamsMismatch, TpMismatch,
    ContractMajorMismatch, ContractMinorMismatch (a warning), ResidencyExceedsCapacity,
    NonFiniteRow, MissingFrequencyAxis, InitialStateMismatch, KvLayoutMismatch; plus the
    uarch-side errors StipulationOnReference, ClaimWithoutSource, SramCapacityExceeded,
    UnnamedPreset (a DRAM timing claim citing a preset other than
    memory.dram.timing_preset, or a timing_preset without a pinned sha) and ShardIndivisible
    (heads or FFN width not divisible by tp). Each carries the sentence the user will read.
11. make gen writes contract/schema/*.json from the models; CI fails if it is stale.

ACCEPTANCE TESTS (write first):
1. Round-trip: every model survives model_validate(model_dump(mode="json")) unchanged.
2. Hash stability: table_hash of the toy table is identical across two fresh interpreter
   processes (subprocess, not the same process twice) and invariant to input key order.
3. One test per error class. Where contract code raises it (StipulationOnReference,
   ClaimWithoutSource, UnnamedPreset, ShardIndivisible), build it from a minimal failing
   input; for errors raised later or in rk-sim, assert the class exists, carries its
   sentence, and round-trips through the schema.
4. SourcedValue: a stipulation with a source is refused; a claim with a rationale is
   refused; a non-stub claim without a source is refused; a stub with a source is refused.
5. A reference HardwareSpec holding one stipulation deep in the tree is refused, and the
   message names the full parameter path.
6. UNITS LIVE IN NAMES. A test walks every float field of request.py and table.py and fails
   on any name without a unit suffix from the allow-list in build-spec §6.1, applying §6.1's
   two exceptions exactly (keys of a mapping field inherit its unit; rk-sim Channel names
   are verbatim). The real field names of build-spec §2.3.3 pass.
7. CYCLES NEVER CROSS. A test fails if any field in request.py or table.py is named *_cycles
   or carries unit "cycle". Cycles are an engine-internal quantity.
8. ModelShape parity: a Llama-3.1-70B-shaped sidecar passes against its ModelSpec; the same
   sidecar with d_ff off by 10% fails with both numbers in the message.
9. contract/tests/fixtures/toy_table.json (hand-written by you, two decode rows and one
   prefill row) validates, and the contract CI job is green against it.
10. Rev-2 fields: a reference spec whose timing_preset has no sha, or one timing claim of
    which cites a preset file other than timing_preset, is refused (UnnamedPreset); a design
    with sram.bytes but no energy.pj_per_byte.sram is refused, naming both paths; a reference
    with a stub bank count loads.
11. NULL, NOT ZERO: a test fails if any diagnostics field in table.py, or any field in
    model_card.py, has a numeric default.
12. The toy table carries tp, initial_state, kv_layout, all four measured errors, the
    embedded model card, and a diagnostics block with at least one null.
13. A fidelity_detail value outside build-spec §2.4's legal set (dram: "2+ts", say) is
    refused, naming the key.

GUARDRAILS: Import nothing from rk: copy rk-sim names by reading its source, and let U-P2's
vendored round-trip prove the copy is exact. Do not add a workload IR or an ONNX path. Do not
add fields for later sprints (mapping search, parallel sync, multi-chip): the contract grows
by MINOR bumps with an ADR each. The Rev-2 fields are not later-sprint fields: an engine that
cannot use one lists it as unrepresented. If P16's baseline names and tiling's needs genuinely
conflict, write both options into ADR U0001 and STOP. That is a founders' decision.

ADR: docs/decisions/U0001-the-integration-contract.md, written with both founders. It must
state build-spec §7.2's nine semantic rules in your own words and record the rk-sim SHA the
contract was read against. Rules 1 and 9 matter most: a row is one rank of a tp-way split
that uarch built, the rk-sim side uses a tp divisor of 1, and it refuses a table built for
another tp. Getting this wrong is the likeliest silent bug in the project. U0001 also records
these decisions, each with its proposed default:
- the shape-regime and load-regime bins (build-spec §2.6's proposal);
- whether BLOCKFP8 evidence can cover an fp8 request (proposal: no);
- whether shared_sram is in contract 0.1 (proposal: yes, optional; engines list it as
  unrepresented until after U8);
- the initial_state default (proposal: steady);
- the declared omissions, mixed prefill/decode iterations among them;
- the shard (proposal: build-spec §2.3.4's Megatron-style split; one tp per table);
- where applicability is judged (proposal: per row; a row's evidence applies only if every
  operator in it has its op class and shape regime covered, and its load regime for NoC and
  DRAM classes);
- clock domains (proposal: build-spec §2.3.2's assignment; a frequency ratio scales the core
  domain and every domain with scales_with_core: true; each domain's frequency is resolved
  once per grid point to integer hertz, and every engine, U-C0 included, uses that integer);
- fidelity values (proposal: build-spec §2.4's keys and legal values, the same in requests
  and tables);
- row keys (proposal: decode {batch, total_context_tokens}, prefill {n_prompts,
  prompt_tokens});
- the model card in the table (proposal: embedded, as build-spec §2.3.3 shows);
- attention (proposal: one attention_fused operator; scores never in DRAM).
```


### U-P2 · U1 · Lane B — The vendored rk-sim snapshot and FLOP parity

```text
CONTEXT TO LOAD: CLAUDE.md, contract/README.md, contract/vendor/README.md, ADR U0001 (the SHA
it names), build-spec §6.4 (the one-way dependency). From rk-sim, READ-ONLY at that SHA:
rk/engine/f0/compute.py, rk/schema/ (and the schema bundle `make gen` writes), Makefile.

TASK: prove, mechanically and on every CI run, that uarch's copy of rk-sim's vocabulary is
exact and that uarch counts work the way rk-sim does, without CI ever touching rk-sim.

1. scripts/vendor_rk.py and `make vendor-rk SHA=<sha> RK=<path-to-rk-sim-clone>
   [PARAMS=<component.yaml> ...]`. A HUMAN RUNS IT; CI never does. It:
   a. checks the clone is at <sha> with a clean tree and refuses otherwise;
   b. copies rk-sim's generated schema bundle plus the source of rk/provenance.py,
      rk/schema/{fidelity,channels,execution,workloads}.py into
      contract/vendor/rk-sim@<sha>/, read-only (chmod a-w), with a MANIFEST listing sha256s;
   c. GENERATES PARITY FIXTURES BY EXECUTING rk-sim's OWN iteration_cost(), in rk-sim's own
      environment (subprocess `uv run --project <rk>`), never by reimplementing the formula.
      Fixtures cover at least 3 ModelSpecs (one dense GQA ~8B, one dense ~70B, one MoE) ×
      2 precisions × tp ∈ {1, 8} × at least 24 queries spanning decode (B, T) and prefill
      (T, Q); the decode queries include B ∈ {1, 8, 32} × context per sequence ∈ {512, 4096}
      (gate G2(c)'s points). Each fixture records IterationCounts.matrix_ops,
      memory_read_bytes, memory_write_bytes, the query, the tp, and rk-sim's own durations
      (decode_s or prefill_s from IterationCost) for each component params file it was run
      with: rk-sim's library entries asic_placeholder.yaml and nvidia_h100_sxm.yaml always,
      plus every PARAMS file the human passes (in U2, `uarch rk-component` output for the
      designs). A duration is rk-sim's output, never ours: these are the oracle for U-P3's
      U-C0 parity test.
   A REIMPLEMENTED FORMULA IS A MIRROR, NOT AN ORACLE. If you find yourself writing
   2*P_active anywhere under contract/, stop: the point is that rk-sim's code produced it.
2. contract/tests/test_vendored_round_trip.py. Load the vendored classes by path, not by
   import name, so nothing named `rk` is ever importable from production code:
   - a uarch claim SourcedValue round-trips through rk-sim's SourcedValue exactly (dropping
     `kind`);
   - A uarch STIPULATION IS REFUSED BY rk-sim's CLASS. Assert the refusal. This pins the gap
     honestly: the day rk-sim adopts the stipulation kind (rk-sim P19), this test fails
     loudly and is updated in the same ADR, never quietly deleted;
   - ModelSpec and PrecisionFormat: every field and member name and value identical;
   - uarch Row.counts keys are a subset of rk-sim's Channel literal values.
3. contract/tests/test_flop_parity.py, the harness later prompts plug into. Given a
   callable (ModelSpec, ModelShape, precision, query) -> counts, compare against every
   fixture: pass if within 0.5%, or if the difference is fully attributed to named declared
   deviations with no single deviation above 5%. U-P3's workload graph is the first callable.
   Until then the test runs against a stub callable that returns the fixture itself, and is
   marked so the report says it is a harness self-test, not a parity result.
4. ModelShape sidecars for the three fixture models under contract/fixtures/model_shapes/,
   each sourced (URL to the model card or config.json) and passing check_parity.
5. CI: the contract job reads the committed snapshot. It needs no rk-sim credentials. It fails
   if MANIFEST sha256s do not match the files, naming the stale file.

ACCEPTANCE TESTS (write first):
1. Tamper test: flip one byte in a vendored file in a temp copy, and the manifest check fails
   naming it.
2. Round-trip suite green; the stipulation-refusal test passes because rk-sim refuses.
3. Parity harness self-test green; a deliberately wrong callable (matrix_ops × 1.1) fails
   with the fixture id and both numbers.
4. import-linter: nothing under src/ or contract/uarch_contract/ imports from
   contract/vendor/.
5. `make vendor-rk` run twice at the same SHA produces byte-identical output.
6. Every fixture carries a tp, a component params file name and rk-sim's duration for it,
   and the fixture set contains G2(c)'s six decode points.

GUARDRAILS: Never hand-edit anything under contract/vendor/; regenerate it. Never give CI
access to rk-sim. Do not "fix" a parity failure by widening the tolerance. Declare the
deviation with a name and a reason, or report it. Changing rk-sim is out of scope for every
uarch prompt except U-P19 and U-P20, which run inside rk-sim.

ADR: docs/decisions/U0002-the-vendored-snapshot-and-parity-discipline.md.
```


### U-P3 · U2 · Lane A — Hardware specs, the workload graph, and the analytic engine

```text
CONTEXT TO LOAD: CLAUDE.md, hw/README.md, src/rkuarch/{workload,engines,table}/README.md,
contract/uarch_contract/, ADR U0001, contract/tests/test_flop_parity.py, build-spec §2.2–§2.4.
From rk-sim READ-ONLY: rk/components/library/compute/asic_placeholder.yaml and
nvidia_h100_sxm.yaml (the param names derive_rk_params must produce).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Keep the high-level standalone CLI and add file-based prepare/replay without requiring
rk-sim or a compiler. First propose and obtain acceptance of U0003's prepared-input schema,
hashing/provenance and any public request/table schema revision; coordinate it with U-P4.
Use the existing OpSpec vocabulary and engine protocol. Workload construction belongs to
preparation; analytic engines consume resolved operators. No detailed mapper lands in U2.

TASK: the first honest number end to end. Analytic only; the fork and the native engine come
later.

1. hw/ — four specs:
   - hw/designs/npu-l4.yaml — a PROPOSED large-core design (2×2 grid of big systolic cores,
     HBM). The class the forks model.
   - hw/designs/npu-m256.yaml — a PROPOSED mesh design (16×16 grid of small cores, SRAM per
     core, one or two 2-D NoCs, GDDR or HBM). The class the native engine will model.
   - hw/references/tpu-v5e.yaml and hw/references/blackhole-p100a.yaml — REFERENCE specs,
     claims only, every number with a URL to a vendor page or document. WHAT THE VENDOR DOES
     NOT PUBLISH IS provenance: stub WITH source: null. It is NOT a stipulation: a reference
     may not contain one, and the loader will refuse it. Record every stub in the spec's
     header comment as "unknown for this chip", because U-P9/U-P15 measure against these
     specs and the model card must say how many unknowns the method carried.
   Every stipulation in designs/ carries a rationale. Do not invent a number you would
   have to call a claim. All four specs fill the Rev-2 fields: dataflows, DMA
   max_outstanding and request_bytes, job_overhead_cycles, sync, DRAM organisation and timing
   (a reference cites JEDEC, the vendor, or a preset file at a pinned SHA), interleave and
   controller policy, and a pj_per_byte.sram consistent with sram.bytes. Unknown for a
   reference means stub.
2. src/rkuarch/hw/derive.py — derive_rk_params(spec) -> the rk-sim component params
   (fp16_tflops and the other per-format peaks that apply, hbm_bw, hbm_capacity, tdp) as
   SourcedValues whose provenance is the WORST of the spec leaves each was computed from.
   STIPULATIONS STAY STIPULATIONS. A peak computed from stipulated MACs/cycle and a
   stipulated clock is a stipulation, never a claim. Plus `uarch rk-component <spec>`, which
   emits the rk-sim library YAML for the chip (kind: compute_resource, role: asic,
   design_status carried in a comment until rk-sim's schema has the field; uarch's proposed
   maps to rk-sim's proposed and reference to shipping).
3. src/rkuarch/workload/ — the standalone, separately versioned preparation producer:
   (ModelSpec, ModelShape, precision, tp, query) -> the operator
   graph of ONE RANK of a tp-way tensor-parallel split, for one iteration, at decoder-layer
   granularity, using contract/operators.py only. The split is build-spec §2.3.4's: heads
   and KV heads (replicated when kv_heads < tp), FFN columns and rows, and the vocabulary
   divided by tp; no collective ops, because rk-sim prices them; ShardIndivisible if a
   dimension does not divide. Attention is one attention_fused operator per layer (scores on
   chip, DRAM operands Q, K, V, O). A query is
   a canonical batch (build-spec §2.3.4): decode = B sequences of context T/B; prefill =
   n prompts of L. layer_reuse=True means "one decoder layer instantiated n_layers times
   plus the non-repeated head and tail ops", and the graph says so in a field. MoE is
   active-parameter dense-equivalent ONLY, exactly as rk-sim: routing, imbalance and
   all-to-all are declared absent in a graph-level `omissions` list, together with
   host/runtime time, address translation, coherence and mixed prefill/decode iterations
   (build-spec §2.3.4). KV operands are paged: the graph carries page-granular KV reads for
   the request's kv_layout.block_size_tokens.
4. Plug the graph into the parity harness (contract/tests/test_flop_parity.py) as its first
   real callable. Every difference from rk-sim's closed form above 0.5% gets a named
   declared deviation in src/rkuarch/workload/deviations.py with a one-line reason: embedding
   or lm_head accounting, norm parameters, and whatever else you actually find. Report them;
   do not tune the graph to hide them.
5. src/rkuarch/engines/analytic/ — U-C0, consuming a validated prepared operator graph and
   resolved HardwareSpec without importing/calling the workload builder or mapping policies.
   Record the explicit analytic mapping scope and preparation identity. Two modes:
   - aggregate: max(compute_time, memory_time) over the whole iteration, the same shape as
     rk-sim's IterationCost._time_s. This is the parity anchor.
   - per_op: the sum over ops of each op's own roofline. Always >= aggregate. It is the first
     place the chip's structure shows up.
   Both return a Row (the contract's row, via table/) with attribution_s split by which roof
   bound, its parts summing to duration_s. Units in names. Seconds at the boundary. U-C0
   uses peak DRAM bandwidth with no refresh derating, because it is the parity anchor for
   rk-sim C0; derating starts at native level 0. U-C0 leaves every diagnostic null.
6. src/rkuarch/table/ — the minimal path: high-level request -> grid-point preparation
   OR validated prepared bundle -> engine -> rows -> UarchCostTable. Both paths share engine
   execution and hashing; imported payloads bypass local preparation. Single process, no
   interpolation (U-P7 owns that). Include input content and producer versions in identity.
7. src/rkuarch/cli.py (typer): `uarch validate <spec>` (lists claims / stipulations / stubs
   with counts; refuses a bad spec with the path) and `uarch table <spec> --model <name>
   --precision <fmt> [--tp N] --engine analytic` (tp defaults to 1).
8. `uarch characterize <spec> --model <name> --precision <fmt>`: for every op across the
   request's grid, its FLOPs, bytes, operational intensity, op class and shape regime (the
   bins ADR U0001 fixed), as hashed JSON plus a Markdown twin. U-P9 and U-P15 pick their
   benchmark shapes from it, and U-P14 picks its workload suite from it.

9. Add `uarch prepare <request> --out <bundle>` and
   `uarch table --prepared-input <bundle> --engine analytic`. The bundle explicitly covers
   its grid/query points, their resolved OpSpecs/dependencies, precision, shard scope,
   hardware binding, producer identity and analytic mapping scope. Reject ambiguous mixed
   high-level/prepared overrides. Round-trip the actual prepared payload, not a recipe that
   calls the builder again. Preserve model-based table/characterize convenience commands.
10. Implement the U0003-approved protocol/schema fixtures and a read-only freshness check.
    Reuse these fixtures in the fork adapter and Rust protocol work; do not create another IR.

ACCEPTANCE TESTS (write first):
1. U-C0 AGGREGATE REPRODUCES rk-sim C0: fed each fixture's own component params (U-P2
   records the file and rk-sim's duration for it), aggregate-mode duration equals that rk-sim
   duration within ±0.1% on every fixture (decode and prefill, both precisions, tp 1 and 8).
   A test, not a claim. Then a human runs `make vendor-rk ... PARAMS=<uarch rk-component
   output for npu-l4>` and the same test covers derive_rk_params(npu-l4). Never compute an
   expected duration yourself.
2. per_op >= aggregate on every fixture query (a property test over random queries too).
3. FLOP parity: the workload graph passes the harness with every deviation named.
4. derive_rk_params: a stipulated-clock design yields stipulation-kind peaks. A reference
   yields claims whose provenance is the worst of their inputs. Test both.
5. `uarch table hw/designs/npu-l4.yaml --model llama-3.1-8b --precision bf16 --engine
   analytic` writes a table whose hash is identical across two runs, whose rows validate
   against the contract, and whose composite_fidelity is "C0" with engine "analytic".
6. `uarch validate` on a reference spec with a stipulation injected fails and names the path.
7. Omissions: an MoE ModelSpec's graph lists routing/imbalance/all-to-all as omitted, and
   the table's warnings carry that sentence, alongside the other declared omissions.
8. `uarch characterize` on the demo request (npu-m256 × Llama-3.1-70B × fp8) writes a
   hash-stable report in which every op has a shape regime.
9. KV reads are page-granular: the number of KV page reads per sequence per layer equals
   ceil(context / block_size_tokens).
10. The shard: at tp = 8 the graph's matrix_ops equals the tp = 1 graph's divided by 8, except
    for named deviations (replicated KV heads, vocabulary padding), and a model whose heads do
    not divide by tp raises ShardIndivisible.
11. Attention: a prefill at L = 32768 yields an attention_fused operator whose DRAM bytes are
    Q, K, V and O only, and the graph contains no L × L tensor.

ADDITIONAL ACCEPTANCE — prepared inputs:
- Export locally prepared inputs and replay them with the local builder unavailable:
  engine results and table bytes match under identical engine/version/run conditions.
- A hand-authored supported prepared fixture executes with no rk-sim clone or compiler.
  Independent expected operator dimensions/dependencies pin the local producer's output.
- A changed operator shape or declared preparation/mapping version changes request/cache
  identity; moving unchanged files does not. Tampering with a declared hash is refused.
- Wrong tp/rank scope, precision, hardware binding, unknown schema version, missing query
  coverage and unsupported detailed mapping fail before engine execution.
- Architecture checks prove the analytic execution path does not invoke preparation.
  Public schemas, prompt-sync and the protocol fixtures are fresh.

GUARDRAILS: Do not touch the fork or the native engine; they are U-P5 and U-P11a–c. Do not add
interpolation or a process pool; that is U-P7. Do not tune the operator graph to hit rk-sim's
numbers, because the deviations are findings. Never write a number you cannot source as a claim:
stipulate it in designs/ with a rationale, or stub it in references/.

ADR: docs/decisions/U0003-one-chip-one-set-of-facts.md, covering derive_rk_params,
stipulation propagation, the standalone/prepared-input boundary, payload/schema ownership,
content identity, import refusals, and any public contract-version revision. Settle its
boundary and share the schema with Lane B before implementation; record validation after.
```


### U-P4 · U2 · Lane B — The honesty layer, and the report every number renders through

```text
CONTEXT TO LOAD: CLAUDE.md, src/rkuarch/{provenance,report}/README.md, build-spec §2.6 (badges)
and §2.7 (the validation ladder), contract/uarch_contract/{sourced,model_card,table}.py.
From rk-sim READ-ONLY: rk/provenance.py (combine), docs/decisions/0009, 0011 §5.4, 0021,
0027, docs/glossary.md §2, web/src/components/Badged.tsx (the rule you are porting).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Use U0003's accepted preparation/provenance fields from U-P3. Reports distinguish the
standalone producer, an imported mapping and fork-delegated mapping when interpreting a
result; they must not claim compiler-matched execution from a policy name alone. Existing
toy tables suffice after the schema prerequisite; do not implement a producer in this lane.

TASK: provenance/ decides what a number may claim. report/ is the only way a number reaches
a human. Develop both against contract/tests/fixtures/toy_table.json; you do not need
U-P3 to have landed.

1. provenance/badge.py — badge_for(row_or_metric, spec, model_card) -> (Calibration,
   conditional_on[]). The rules, exactly as build-spec §2.6 states them:
   a. WORST OF CONTRIBUTORS, over claims only. Stipulations are EXCLUDED from the
      calculation and RECORDED in conditional_on. A stipulation neither lowers nor raises a
      badge; it scopes the question.
   b. THE MODEL IS A CONTRIBUTOR. Its rung comes from the model card, which comes from the
      ledger. L0–L2 evidence -> stub. L3 -> estimated, scoped. L4 -> measured.
      spec_derived never applies to a model.
   c. THE CEILING: anything computed for a design_status: proposed spec is capped at
      estimated, whatever its evidence. Enforced in code, with a test.
   d. combine([]) is stub, as in rk-sim: a number that cannot name what fed it has no
      evidence behind it.
   e. NOTHING HERE MAY RAISE A BADGE. Write a test that fuzzes inputs and asserts the output
      badge is never better than the worst claim contributor and never better than the model
      card's rung.
2. provenance/model_card.py — build a ModelCard from (engine id, engine version,
   fidelity_detail, mapping policy, ledger entries). validated_error_band is None unless
   ledger entries whose scope covers this request (family, op class, precision, shape regime,
   load regime, mapping match) supply it. None renders as "unknown". energy_verification is
   None until every coefficient family an energy figure uses has an L2 reference (deferred
   until after U8), and None renders energy as "unverified".
3. provenance/applicability.py — rk-sim ADR 0021's shape for uarch: for a request, which
   evidence dimensions MATCH, MISMATCH or are UNKNOWN (architecture family, op class,
   precision, shape regime, load regime, mapping match), using the bins ADR U0001 fixed, and
   judged where U0001 says (proposal: per row, with every operator in the row covered).
   Precision matches by format name: BLOCKFP8 evidence does not cover fp8 unless U0001 says
   why it should. A model card whose evidence does not apply to this
   request contributes stub for this request, whatever its best rung elsewhere.
4. report/ — `uarch report <table>` writes a self-contained static HTML file (plus a
   Markdown twin for agents), with no JavaScript framework and no network fetches:
   - every number renders through report/badged.py::badged(value, unit, badge,
     conditional_on, error_band). A raw float in a template is a build failure: add a
     template lint that fails on any {{ x }} whose x is not a Badged object;
   - "conditional: if built as specified (N stipulations)" with the list expandable;
   - error band shown as the band, or "unknown", NEVER "±0";
   - the fidelity chip (composite plus the per-subsystem detail), the model card, the
     measured interpolation and composition errors, and the flop-parity deviations;
   - a diagnostics section: a null diagnostic renders "not modelled", never 0 and never a
     blank that reads as zero;
   - a per-op roofline as static inline SVG (operational intensity against achieved
     throughput, from the table's counts; no JavaScript);
   - all four measured errors (interpolation, composition, layer reuse, cold vs steady), the
     initial state and the KV layout;
   - energy marked "unverified" while the model card's energy_verification is None;
   - a one-paragraph "what this table does not claim" generated from omissions (the declared
     ones included), warnings, stubs and the badge ceiling.

ACCEPTANCE TESTS (write first):
1. A stipulation does not lower a badge; a stub claim does; both appear in the right list.
2. L0–L2-only card -> the model contributes stub; L3 in-scope -> estimated; L3 out-of-scope
   for this request -> stub, with the mismatched dimension named.
3. Ceiling: a proposed design with an L4 card is capped at estimated, and the report says why.
4. Error unknown: a card with validated_error_band=None renders "unknown", and the rendered
   HTML contains no "±0" anywhere (grep test).
5. Template lint catches an injected raw {{ row.duration_s }}.
6. The report for the toy table is byte-identical across two runs (no timestamps in the
   body; the generation time goes in a comment block excluded from the hash).
7. A null diagnostic renders "not modelled": no diagnostic that is null in the toy table
   appears as 0 in the rendered report.
8. Precision scope: an fp8 request against BLOCKFP8-only evidence gets stub, naming precision.
9. Energy renders "unverified" when energy_verification is None, and stays "unverified" when
   only one coefficient family has a reference.
10. Applicability per row: a row with one operator whose shape regime the evidence does not
    cover gets stub, naming that operator.

GUARDRAILS: Do not read from an engine or compute a physical number here. Do not compute
error bars from a deterministic run; a deterministic simulator has no replication variance,
and a zero-width interval is the most confident error bar you could draw on the least-
validated number. No web app: the rk-sim UI is the interactive surface (U-P20).

ADR: docs/decisions/U0004-stipulated-values-and-the-estimated-ceiling.md. Say in plain words
that a chip which does not exist is never badged better than ESTIMATED, and that this will be
commercially uncomfortable, and that it is the thesis applied without exceptions.
```


### U-P5 · U3 · Lane A — Fork selection, the engine container, and the adapter

```text
CONTEXT TO LOAD: CLAUDE.md, src/rkuarch/engines/README.md, third_party/README.md,
containers/README.md, build-spec §2.5 (the engine protocol) and §4 gate G2 in
docs/execution-plan.md. Read BOTH PAPERS IN FULL, not their abstracts. The planning documents
only had the abstracts and say so:
- PyTorchSim, MICRO 2025, doi 10.1145/3725843.3756045 (MIT; github.com/PSAL-POSTECH/PyTorchSim);
- ONNXim, IEEE CAL 2024, arXiv 2406.08051 (MIT; github.com/PSAL-POSTECH/ONNXim).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Consume the U2 prepared workload and preserve its already resolved rank shapes. The
adapter translates supported prepared operators to fork input; it does not independently
rebuild/shard the model. Keep the high-level CLI through the standalone producer. The fork's
internal tiling is a declared delegated-mapping mode, not proof it honored a supplied mapping.

TASK: get a published cycle-level NPU simulator driven by a uarch request, reproducibly, and
choose between the two candidates on pre-registered numbers.

1. BEFORE RUNNING ANYTHING, write docs/decisions/U0005-fork-selection.md's "pre-registered
   criteria" section and commit it. It holds G2's five criteria with the per-point wall-clock
   budget made concrete: derive it from the grid you intend (build-spec §2.3.3's default grid
   size) and a table build budget you state. A threshold chosen after seeing the number is a
   retrospective, not a gate.
2. containers/Dockerfile.engine — builds the candidate from a PINNED SHA, unattended, from a
   script. The image carries BookSim2 and Ramulator2 at the SHAs the fork's submodules pin.
   Build and run only on the Linux box, never on a laptop.
3. third_party/<fork>/: pinned SHA in third_party/LICENSES.md, with the licence of every
   component the image links (the fork, BookSim2, Ramulator2, and their dependencies). Local
   changes ONLY as numbered patches third_party/patches/NNNN-<slug>.patch, each with a
   one-line reason, applied at image build. CI job `patches` verifies they still apply.
4. src/rkuarch/engines/fork/ — the adapter. FILES IN, FILES OUT, NO FOREIGN-FUNCTION
   INTERFACE:
   - config_writer.py: HardwareSpec (a large-core design) -> the fork's config JSON. Every
     spec field the fork cannot represent is listed in the adapter's `unrepresented` output,
     which becomes a table warning. Never silently dropped. That includes the Rev-2 fields:
     the fork's dataflow, DRAM organisation and timing (its Ramulator config comes from the
     spec, never from the fork's default preset unless the spec names that preset),
     outstanding-request limits and per-job overhead are mapped where the fork has them and
     listed as unrepresented where it does not.
   - workload_writer.py: validated prepared workload -> the fork's LLM input format.
     Preserve its declared shapes, tp/rank scope, precision, fusion and omissions. Use
     provenance model metadata only when it faithfully represents those resolved operators;
     refuse inputs the fork format cannot express. ONNX or PyTorch graphs remain adapter
     outputs, never a new source-of-truth input language. No duplicate sharding logic.
   - runner.py: runs the container as a subprocess with a timeout, captures stdout/stderr
     and stats files, and records the image digest in the result.
   - stats_parser.py: fork stats -> EngineResult (build-spec §2.5): duration_ps, per-resource
     busy time, activity counts in contract channel names. MACs are converted to ops at
     2 per MAC (P7b) by a named function. Diagnostics are filled from the fork's stats where
     they exist and null otherwise; attribution follows the critical path and sums to the
     duration.
   - THE FORK'S MAPPING IS THE FORK'S. It tiles and schedules internally. Record it as
     mapping_policy "fork:<name>-default@<sha>", a stipulation on every row. Do not pretend
     uarch's mapping policies drove it.
   - initial_state: steady runs the query twice in one simulation where the fork allows it
     and reports the second; where it does not, initial_state is listed as unrepresented and
     the table warns. Never report a cold run as steady.
   - FIDELITY: place each of the fork's sub-models (compute, SRAM banks, NoC, DRAM) on
     build-spec §2.4's ladder, per configuration you run (its default, and any simpler NoC or
     DRAM mode it offers), from its source, cited by file and line. The table goes into ADR
     U0005. stats_parser emits that fidelity_detail, and the composite comes from §2.4's rule,
     never from the fork's name: if the fork models no SRAM bank conflicts, its compute is
     level 1 and its tables are C1. Record which sub-models ARE BookSim 2 or Ramulator 2, so
     U-P8 never compares them with themselves.
5. Evaluate ONNXim first (it is lighter). If it passes G2, you may skip PyTorchSim. Record
   that you skipped it and why. If it fails, evaluate PyTorchSim with the same criteria.
6. `uarch table ... --engine fork` for one-layer decode queries on npu-l4, driven from a
   ModelSpec end to end.

ACCEPTANCE TESTS (write first where they can be written first):
1. G2(a): `make image` from a clean clone builds the engine image unattended.
2. G2(b): three consecutive runs of the same query produce byte-identical stats files.
3. G2(c): decode matrix-op counts at B ∈ {1,8,32}, context/seq ∈ {512,4096} match rk-sim's
   parity fixtures within 0.5% after named deviations, no single deviation above 5%.
4. G2(d): wall-clock per one-layer decode query at or under the pre-registered budget.
5. G2(e): licence scan of the image green against the allow-list.
6. The adapter's `unrepresented` list is non-empty for npu-l4 if anything is unrepresented,
   and each entry appears as a table warning.
7. The fork's own default DRAM preset is never used silently: a spec whose timing_preset the
   fork cannot load is refused (UnnamedPreset) or listed as unrepresented.
8. ADR U0005 holds the fork's per-configuration ladder table with citations, and a table
   built by the fork reports exactly the composite §2.4's rule gives for those levels.

ADDITIONAL ACCEPTANCE — prepared inputs:
- Model-based preparation and replay of its saved bundle preserve identical workload
  semantics through the adapter, with independent shape/count checks at the fork boundary.
- A caller supplying an exact mapped TaskGraph that the fork cannot honor receives an
  explicit refusal. Selecting fork-delegated preparation is a separate declared choice.
- Result provenance identifies prepared content and pinned fork mapping/version; no claim
  of mapping equivalence is made without evidence of resolved correspondence.

GUARDRAILS: Do not patch the engine to make parity pass. Declare the deviation. Do not touch
anything under src/rkuarch/engines/native/. Do not start U-P7 until a fork has passed G2. If
BOTH fail, do not improvise a workaround: record the U-C1 fallback decision in ADR U0005
(build a Python contention-aware model, ship it labelled C1, record "C2 via fork:
unbuilt") and stop for the founders.

ADR: docs/decisions/U0005-fork-selection.md, with pre-registered criteria, every measured
number, the rejected candidate's numbers, the image digest, and the fork's ladder table.
```


### U-P6 · U3 · Lane B — L0 invariants and L0m metamorphic relations

```text
CONTEXT TO LOAD: CLAUDE.md, validation/README.md, build-spec §2.7 (the ladder), tests/README.md,
src/rkuarch/engines/README.md (the engine protocol every suite runs through). From rk-sim
READ-ONLY: tests/properties/ (the house style for property tests).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Exercise saved prepared jobs as well as the standalone frontend. Keep tests of the
producer's counts/shape resolution separate from engine invariants on fixed inputs. Apply
metamorphic graph/mapping changes explicitly, update their content identity, and never let
an engine repair a deliberately invalid mapping through hidden re-preparation.

TASK: the rungs that establish that the simulator does not contradict itself, and relations
that must hold even though nobody knows the right answer. They run against ANY engine through
the engine protocol: today U-C0, the fork when U-P5 lands, the native engine later. Write
them once.

1. validation/L0_invariants/ — per engine run:
   - MACs executed == MACs in the operator graph (from the workload graph, not re-derived);
   - DMA bytes moved in == bytes consumed by compute plus bytes written back;
   - no resource utilisation > 1 over any window;
   - Little's law within 1% on every queue the engine reports (mean occupancy vs arrival
     rate × mean residence);
   - causality: no event or interval begins before the one it depends on (for engines that
     emit traces);
   - byte-identical reruns;
   - per-core SRAM occupancy ≤ sram.bytes at every event (engines that report placement);
   - attribution_s parts sum to duration_s within 1e-9 relative;
   - energy = Σ counts × coefficients + static power × duration, on every row that reports
     energy;
   - null, not zero: a diagnostic of a subsystem running at a level that does not model it is
     null.
2. validation/L0m_metamorphic/ — relations over PAIRS of runs:
   - doubling any bandwidth (DRAM, NoC link, SRAM port) never increases duration;
   - scaling every core-domain clock by k scales a compute-bound query's duration by 1/k
     within 1%, and changes a DRAM-bound one by less than k;
   - decode duration is non-decreasing in batch and in context;
   - permuting core ids on a symmetric topology (torus, or mesh with a symmetric mapping)
     leaves duration unchanged;
   - adding an idle core (one the mapping does not use) changes nothing;
   - a stipulated-parameter change that the mapping does not touch changes nothing;
   - raising any latency (router, DRAM timing, job overhead, barrier) never shortens duration;
   - lowering dma.max_outstanding never shortens duration;
   - a cold run is never faster than the steady run at the same point.
3. Write them as HYPOTHESIS PROPERTY TESTS over generated HardwareSpecs and queries, with
   strategies in validation/strategies.py that only generate valid specs. Examples alone
   prove only the examples. A relation an engine cannot express (U-C0 models no latency and
   no initial state, for example) SKIPS for that engine with its reason; it never passes.
4. Each suite writes a machine-readable report (JSON, hashed) that the model card cites under
   verification.L0 / verification.L0m. A card may cite only a report produced by the same
   engine version.
5. POWER, DEMONSTRATED NOT ASSERTED: for at least five relations, commit a deliberately
   injected bug under validation/mutants/ (a bandwidth read from the wrong field; an
   off-by-one tile count; a queue that drops requests; an attribution that double-counts
   overlap; an allocator that ignores SRAM capacity), and a test that runs the suite
   against the mutant and asserts it FAILS. Mark these tests so they run nightly.

ACCEPTANCE TESTS:
1. Every L0 and L0m suite passes against U-C0 (aggregate and per_op).
2. Every committed mutant is caught, by name.
3. Reports are hash-stable across runs.
4. When the fork lands (U-P5), the same suites run against it with no code change. Add the
   fork to the engine matrix and record the result; a failure there is a finding for Lane A,
   not a test to relax.

GUARDRAILS: These rungs are about RELATIONS. Do not assert a numerical value that someone
would have to believe. Do not downgrade a failing invariant to a warning. Ever. Do not make
L0/L0m depend on the fork: they must run on the analytic engine alone.

ADR: docs/decisions/U0006-what-verification-can-and-cannot-establish.md. State plainly that
L0–L2 evidence never lifts a model above stub, and why: agreement with yourself, or with
another simulator, is not agreement with silicon.
```


### U-P7 · U4 · Lane A — Mapping policies, the grid, interpolation, and the first full table

```text
CONTEXT TO LOAD: CLAUDE.md, src/rkuarch/{mapping,table,workload}/README.md, build-spec §2.3.3
and §2.3.4 (canonical batches and the reduction error), §7.2 (the nine rules), ADR U0005,
contract/uarch_contract/{request,table}.py. From rk-sim READ-ONLY: rk/engine/f0/compute.py's
comment block above IterationCounts, which says why (B, T, Q) is sufficient for a
roofline and warns that it is exact only while cost is linear.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Extend U2's saved-input path with the existing TaskGraph; policies are versioned
preparation producers outside engines. Imported mapped inputs bypass policy execution and
are validated unchanged. The fork's declared internal-mapping exception remains explicit;
a supplied native mapping cannot silently turn into a fork default.

TASK: turn a CharacterizationRequest into a complete, hashed, honestly-errored table, driven
by the fork, at the composite build-spec §2.4's rule gives for the fork's levels as ADR U0005
records them: C2 only if they qualify, and C1, said so, if they do not.

1. mapping/ — standalone preparation: named, versioned policies, each a pure function
   (validated prepared op graph, HardwareSpec) ->
   TaskGraph (build-spec §2.5): per-core compute jobs, DMA jobs, NoC transfers (unicast and
   multicast), barriers, dependencies.
   - ws-rowsplit@1 for the large-core class (weight-stationary, output rows split across
     cores).
   - os-tiled@1 for the large-core class (output-stationary, output tiles split across
     cores), so a dataflow study has a second policy to compare (U-P14).
   - onnxim-compat@1: reproduces the chosen fork's own tiling decisions, read from its source
     and cited by file and line in the policy's docstring. It exists so a native engine can
     later be compared with the fork ON THE SAME WORK. Without it every future disagreement
     is ambiguous between "different engine" and "different mapping".
   A policy's name@version is a stipulation on every row. A better policy is a new version,
   never an edit. No search, no autotuning. Every policy declares the matrix dataflow it
   needs (refused on a spec whose dataflows lack it) and its buffer depth (double or triple
   buffering, part of name@version). It places every SRAM-resident buffer (core,
   offset_bytes, bank) and refuses a tile that does not fit with SramCapacityExceeded,
   naming the core and the bytes. KV reads are page-granular DMA jobs. attention_fused is
   tiled so its score tile (query block × KV page block) fits in SRAM: scores never become
   DMA jobs.
2. table/grid.py — the grid from the request's envelope. Refuse a request whose grid does not
   cover its envelope, naming the uncovered region, at REQUEST time.
3. table/pool.py — one process per grid point, parallel ACROSS POINTS only. Results are
   reassembled in grid order, so the table is byte-identical at 1 worker and at N.
4. table/interpolate.py — exactly the declared scheme: decode bilinear in (log B, log T),
   prefill bilinear in (log n, log L), linear in 1/f across the frequency axis. OUTSIDE THE
   GRID IS AN ERROR (EnvelopeExceedsGrid), never a clamp and never an extrapolation. It also
   writes contract/fixtures/interpolation_vectors.json (proposed to both founders, since
   contract/ is theirs): query points inside and on the edges of the toy table's grid, with
   the expected interpolated value of every row field. rk-sim's table-backed cost (U-P19)
   and any later native-code reader must reproduce them within 1e-12 relative; that is what
   keeps the table usable from any language.
5. table/errors.py — the table measures its own errors and reports them. It never
   corrects them.
   a. interpolation_loo: leave each interior point out, predict it from the rest, report the
      median and max relative error.
   b. composition_reduction: rk-sim reduces a batch to (B, T, Q) sufficient statistics. A
      cycle-level model is not linear (padding, tile quantisation), so for a seeded sample of
      points evaluate UNEQUAL batches with the same (B, T, Q) as the canonical equal-length
      one, and report how far they deviate. This number is a finding. It tells rk-sim how much
      its own sufficient-statistic reduction costs at C2.
   c. layer_reuse: for a seeded sample of grid points, simulate every layer (no reuse) and
      report how far the reused result deviates (build-spec §2.3.4).
   d. cold_vs_steady: for a seeded sample, run both initial states and report the deviation;
      on the same sample, run steady with two priming iterations and report how far one is
      from two (priming_2_vs_1_max_rel), so the warm-up length is measured.
   Each sampled error reports n_samples. interpolation_loo also reports
   weighted_median_rel, weighted by the request's visit_weights, or null when there are
   none.
6. Frequency axis: for each frequency ratio in the grid, scale the stipulated core-domain
   clock (and whatever the spec declares scales with it), rerun, and record the row.
   attribution_s is diagnostic only; it is never fed back into a max() form.
7. Rows carry peak_resident_bytes. If HBM residency exceeds the spec's capacity, raise
   ResidencyExceedsCapacity for weights, and warn for KV, mirroring rk-sim's M0 rule.
8. `uarch table ... --engine fork --workers N` builds the full default grid for npu-l4 ×
   Llama-3.1-70B-class × fp8 and bf16, tp = 8, and also tp = 1 where the weights fit the
   spec's capacity (a weight-residency refusal at tp = 1 is recorded, never worked around).
9. initial_state travels in every EngineJob; steady primes one iteration at the same point
   and reports the second.

10. Extend prepare/export and prepared-input loading with complete TaskGraph payloads and
    their hashes: placements, tiles, DMA/NoC transfers, dependencies, barriers and policies.
    Schema and producer versions are explicit. Validate hardware/resource references, SRAM
    capacity, dimensions and dependency consistency before launching an engine. Reject a
    hardware-incompatible imported mapping rather than re-running a local policy.
    Materialize all requested grid and seeded error-experiment jobs during preparation;
    imported bundles must declare sufficient query/state coverage or refuse the experiment.

ACCEPTANCE TESTS (write first):
1. Determinism: two builds byte-identical; --workers 1 vs --workers 8 byte-identical.
2. An out-of-envelope query raises EnvelopeExceedsGrid at request time, naming the region.
3. Interpolating at a grid point returns the grid value exactly.
4. LOO and composition errors are present, finite, and reported. The composition sample is
   seeded and reproducible.
5. G3 (execution-plan §4): the npu-l4 table passes L0, L0m and L1 (U-P6 and U-P8) as run by
   Lane B, and its model card says stub.
6. onnxim-compat@1 reproduces the fork's tile counts per op on three shapes, cited to source.
7. layer_reuse and cold_vs_steady errors are present, finite, seeded and reproducible.
8. A tile larger than a core's SRAM is refused with SramCapacityExceeded, naming the core and
   the bytes.
9. With uniform visit_weights, weighted_median_rel equals median_rel.
10. os-tiled@1 is refused on a spec whose dataflows lack output_stationary, and runs on one
    that has it.
11. A prefill row at L = 32768 builds with no SramCapacityExceeded, and its attention DRAM
    bytes equal Q, K, V and O within named deviations.
12. The table's composite equals what build-spec §2.4's rule gives for ADR U0005's levels.
13. interpolate.py reproduces interpolation_vectors.json, and a query outside the grid in
    that file is refused.

ADDITIONAL ACCEPTANCE — prepared inputs:
- A locally prepared mapped bundle replays with mapping policies disabled and yields
  identical EngineResults/tables for the same engine/version/run conditions.
- A supported external TaskGraph fixture executes without the local mapper. Changing its
  placement changes content/cache identity even if the model and policy label are unchanged.
- Unsupported supplied mapping, stale hardware binding, bad dependencies, and missing error
  sample coverage are refused; no implicit retiling or regeneration occurs.
- Fork/native correspondence compares the resolved work supported by the fork; a shared
  policy label alone cannot pass the mapping-match check.

GUARDRAILS: No mapping search. Never silently clamp an out-of-grid query. Do not correct the
composition or layer-reuse error, because disclosure is the deliverable. Do not let
attribution_s feed back into anything. Do not add parallelism inside a simulation:
parallelism is across points only.

ADR: docs/decisions/U0007-canonical-batches-and-the-reduction-error.md.
```


### U-P8 · U4 · Lane B — L1 analytical limits and L2 differential references

```text
CONTEXT TO LOAD: CLAUDE.md, validation/README.md, build-spec §2.7, third_party/README.md,
ADR U0005 (which fork sub-models are BookSim 2 or Ramulator 2). Documentation for BookSim 2 (BSD-2, Stanford), Ramulator 2 (MIT, CMU SAFARI), SCALE-Sim v3
(MIT). Optionally Gemmini (BSD-3, UC Berkeley) and Verilator (LGPL-3.0/Artistic-2.0).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Pin the prepared workload/mapping identity and represented scope for each reference
comparison. A difference caused by another mapping is not an engine discrepancy. References
that cannot consume equivalent resolved inputs must be reported as unmatched rather than
being compared solely by model name, tp or a policy label.

TASK: two rungs. L1: the model reduces to closed forms wherever those are exact. L2: it
implements the same abstraction as independent, published models. Both run through the
engine protocol against every engine in the matrix.

1. validation/L1_limits/:
   - uncontended point-to-point transfer = hops × router_latency + serialisation (bytes /
     link width), per NoC;
   - saturated DRAM streaming = peak bandwidth × (1 − t_rfc/t_refi) ± 5% at levels 0–1,
     the derating taken from the spec's timing; at level 2, at most that figure, with the
     efficiency recorded as data against Ramulator 2 in L2;
   - a latency-bound stream (one requester, dma.max_outstanding requests of request_bytes
     over a known round trip) achieves min(peak, max_outstanding × request_bytes / round
     trip) ± 5%;
   - a single GEMM with operands resident in SRAM follows the pipeline formula for the
     declared array and dataflow (fill + ceil-tiled steady state + drain);
   - A C2 RESULT IS NEVER BELOW ITS OWN U-C0 ROOFLINE. Assert it for every row of every
     table. A cycle-level result faster than the roofline of the same spec is a bug, not a
     finding;
   - at vanishing load, C2 converges to U-C0 plus the fixed latencies.
   AT LEAST TWO L1 FIXTURES ARE COMPUTED BY HAND, ON PAPER, BY A HUMAN, with the working
   committed as a scan or Markdown under validation/L1_limits/hand/. An unfilled hand
   fixture SKIPS with its id and is listed in the report. It never passes. rk-sim calls
   these the defence against plausible garbage; the same reason applies here.
2. validation/L2_differential/ (the nightly job):
   - NoC: the engine's NoC vs STANDALONE BookSim2 (built in the engine image) on
     uniform-random, transpose and hotspot traffic, over an injection-rate sweep. If the
     engine's NoC IS BookSim 2 (ADR U0005 says which fork sub-models are), the comparison is
     refused as not independent and the report says so; the bound then waits for the native
     NoC (U-P13a). ENFORCED:
     latency within 10% below 70% of BookSim's saturation throughput. Above that, record,
     don't assert;
   - DRAM: vs Ramulator 2 standalone on streaming, random and strided traces;
   - tile compute: vs SCALE-Sim v3 cycle counts for GEMM shapes on the matching array and
     dataflow, one run per dataflow the spec declares;
   - optional: one systolic tile vs Gemmini RTL under Verilator (a cycle-exact reference for
     THAT design);
   - Tenstorrent tt-npe (Apache-2.0) as a second NoC reference for mesh specs, once
     U-P13a lands the native mesh NoC;
   - energy references are DEFERRED until after U8: energy stays "unverified", and
     energy_verification stays None, until every coefficient family has a reference;
   - optional, a mapping reference: Timeloop's best mapping for representative GEMMs on the
     same array, recorded next to each named policy's efficiency. It never changes a policy:
     mapping search stays out of scope.
   Check each new tool's licence against third_party/LICENSES.md's allow-list before using
   it. If one fails, record that and skip it.
   Each comparison records its deviations as DATA (JSON, hashed), and attributes each
   deviation, where it can, to a named mechanism (e.g. "BookSim models VC allocation; the
   reservation NoC does not").
3. The L2 report computes ONE NUMBER THE FOUNDERS SHOULD WATCH: the fraction of deviations
   larger than 5% that carry a named mechanism. Below one half, the rungs above L2 will not
   mean what you want them to mean. Report it on the first page.

ACCEPTANCE TESTS:
1. All L1 pass for U-C0 and the fork; the roofline-floor assertion runs over every row of the
   npu-l4 table.
2. The two hand fixtures exist, pass, and have committed working.
3. The L2 nightly job runs end to end and publishes its report; the NoC bound is enforced.
4. A mutant (NoC with router latency read as 1 instead of the spec value) is caught by L1
   and shows up in L2.
5. The derated DRAM check and the latency-bound stream check run for every engine they apply
   to; a mutant DMA that ignores max_outstanding fails the latency-bound check.
6. At least one hand fixture covers the latency-bound stream.
7. The harness refuses to compare a sub-model with itself (a fork NoC that is BookSim 2,
   against BookSim 2), naming both.

GUARDRAILS: Do not tune engine parameters to close an L2 gap. Record it and attribute it.
Agreement between two simulators is L2 and NOTHING MORE. It never appears in a model card as
validation. BookSim, Ramulator, SCALE-Sim and Timeloop run as standalone references
here; they are not new dependencies of rkuarch.

ADR: docs/decisions/U0008-the-L2-reference-set-and-its-limits.md.
```


### U-P9 · U5 · Lane A — The large-core reference model, and predictions frozen before anyone measures

```text
CONTEXT TO LOAD: CLAUDE.md, validation/README.md, validation/L3_silicon/README.md, build-spec
§2.7 (rung L3), hw/references/tpu-v5e.yaml, ADR U0005, the chosen fork's paper (its TPU
validation section: what it measured, and how). From rk-sim READ-ONLY: docs/prompts/P11-*.md
and docs/execution-plan.md S7–S8 (the A100-fits, H100-held-out discipline this copies).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Freeze the exact prepared workload/mapping artifacts or a resolvable immutable manifest
alongside predictions, including producer versions, content hashes, hardware binding and run
conditions. Measurements use the declared mapping match; a compiler-chosen mapping is not
assumed equal to the local policy. Replaying predictions must not silently re-prepare inputs
with a newer producer.

TASK: produce, and COMMIT BEFORE ANY MEASUREMENT EXISTS, uarch's predictions for a suite of
microbenchmarks on Google Cloud TPU v5e, the large-core reference. This prompt never sees a
measurement. That is its whole design.

1. Agree the microbenchmark list with Lane B FIRST, in writing, in
   validation/L3_silicon/tpu-v5e/SUITE.md. Lane B's U-P10 builds the kit that runs it. At
   least 24 benchmarks, covering every one of these six classes:
   - matrix: isolated matmuls at ≥ 6 shapes spanning MXU-underfilled to saturated, bf16 and
     int8 where the chip supports them;
   - memory: HBM streaming read, write, and copy at ≥ 3 sizes;
   - operator: each decoder-layer operator in contract/operators.py at a decode and a prefill
     shape for an 8B-class model;
   - end-to-end: one full decoder layer, decode B ∈ {1, 8, 32} and one prefill;
   - DRAM gather: page-granular reads at rk-sim's block size (the KV access pattern), at ≥ 2
     page sizes;
   - launch overhead: the device-side time of a minimal kernel, so fixed per-op cost is
     measured rather than folded into other classes.
   Operator and matrix shapes are chosen with `uarch characterize` to cover the shape
   regimes (U0001's bins) of the requests this family's evidence should support, not only
   8B-class shapes. SUITE.md records the coverage.
   EACH BENCHMARK STATES WHAT IS MEASURED, AND AT WHAT GRANULARITY, in words both lanes sign:
   XLA fuses operators, so "the softmax" on silicon may not be a separable event. Where a
   uarch operator has no separable silicon counterpart, the benchmark measures the smallest
   fused unit that contains it, and the prediction is made for THAT unit. This is rk-sim's
   anchor-semantics problem one level down, and getting it wrong makes every comparison
   meaningless while looking fine. Every benchmark also states: device-side timing only
   (host and launch gaps excluded); its mapping match (XLA chooses the tiling on TPU, so
   benchmarks are `compiler-chosen` unless one pins the layout); its initial state (steady,
   matching the kit's warm-up); and the compiler-reported FLOPs and bytes the kit records.
2. Configure the engine for the reference: the fork via config_writer from
   hw/references/tpu-v5e.yaml. Every microarchitectural parameter the vendor does not publish
   is a STUB claim in that spec (never a stipulation). Count them, and list them in
   predictions/UNKNOWNS.md: the L3 error will be method error plus unknown-parameter error,
   and the card must say how many unknowns there were.
3. Predictions: for each benchmark, uarch's predicted duration, FLOPs and bytes, from the
   fork AND from U-C0 aggregate and per_op, written to
   validation/L3_silicon/tpu-v5e/predictions/<id>.json with engine versions, image digest,
   spec hash, mapping policy, mapping match, initial state, and the row diagnostics where the
   engine reports them (U-P10 compares them with device counters). Commit them in ONE commit
   whose message begins "FROZEN PREDICTIONS:".
4. validation/L3_silicon/check_ordering.py and a CI job: fails if any file under results/
   exists in a commit earlier than, or equal to, the commit that added its prediction file.
   The ordering is enforced by git history, not by a promise.

ACCEPTANCE TESTS:
1. SUITE.md signed off by both lanes (both names, in the file) before predictions are
   generated.
2. ≥ 24 prediction files covering all six classes, each with full provenance fields, mapping
   match, initial state, and predicted FLOPs and bytes.
3. The ordering check fails on a synthetic history where a result precedes its prediction.
4. UNKNOWNS.md lists every stub in the reference spec that the engine actually read.

GUARDRAILS: DO NOT LOOK AT, REQUEST OR ESTIMATE ANY MEASUREMENT IN THIS SESSION. Do not edit
a prediction after it is committed. A new prediction is a new file in a new commit, and the old
one stays. Do not tune the reference spec towards published TPU results. Do not change the
engine in this prompt; U-P10 and the G4 verdict decide what happens next.

ADR: docs/decisions/U0009-the-large-core-reference-and-what-it-can-support.md. Say which
architecture family this reference can support evidence for (few large systolic cores),
and which it cannot (anything mesh-shaped).
```


### U-P10 · U5 · Lane B — The large-core measurement kit, the ledger, and promotion

```text
CONTEXT TO LOAD: CLAUDE.md, measure/README.md, validation/L3_silicon/README.md,
validation/ledger/README.md, validation/L3_silicon/tpu-v5e/SUITE.md, build-spec §2.6–§2.7.
From rk-sim READ-ONLY: docs/prompts/P10-measurement-kit-write-before-renting-anything.md,
rk/calibration/ (the ledger's shape), docs/decisions/0021 and anchor-semantics.md.

TASK: measure the reference chip, compare against the frozen predictions, and let the ledger,
and only the ledger, decide what the model card may say.

1. measure/tpu-v5e/, the kit, WRITTEN AND DRY-RUN BEFORE ANY PAID HOUR. Code for every
   benchmark in SUITE.md, runnable end to end on CPU JAX as a dry run that produces
   correctly shaped (fake, labelled SYNTHETIC) result files. Warm-up and repetition counts
   stated per benchmark; device-side timing via the XLA/JAX profiler at the granularity SUITE.md
   fixes; XLA's compiled cost analysis (FLOPs and bytes accessed) per benchmark; whatever
   device counters the profiler exposes (HBM bytes, utilisation), recorded as data;
   environment capture (TPU type, runtime and library versions, VM image) into every result.
2. Run it on Cloud TPU v5e ONLY AFTER check_ordering passes for every prediction. Raw results
   go to validation/L3_silicon/tpu-v5e/results/, and are immutable once committed. These are
   records of spent money, like rk-sim's measure/results/.
3. validation/ledger/: one entry per comparison, recording the question it answers
   (benchmark id and granularity), its applicability dimensions (architecture family, op
   class, precision, shape regime, load regime, mapping match), predicted, measured, signed
   relative error, and the engine and spec versions. The ledger REFUSES a second entry with
   the same key and a different prediction, as rk-sim's does. Workload fidelity is its own
   entry type: predicted vs compiler-reported FLOPs and bytes, with declared deviations for
   fusions, layout copies and padding. It never promotes a duration card; a deviation above
   5% with no declared reason is published as a finding. Diagnostic fidelity is another
   entry type: each predicted diagnostic against the device counter that measures it, where
   one exists. It never promotes a duration card either.
4. Gate G4 (execution-plan §4), evaluated by script and written to the ledger either way:
   median |relative error| ≤ 25% across all benchmarks, and no class median above 50%. It is
   evaluated separately for matched and compiler-chosen benchmarks, and the verdict names the
   group; an empty group is reported as "no evidence", never as a pass. The same script
   computes G4's fail-branch attribution exactly as execution-plan §4 defines it.
5. Promotion: provenance/ reads the ledger. A model card moves from stub to estimated ONLY
   through ledger entries, ONLY for the family and op classes those entries cover, with
   validated_error_band set to the observed band for that scope. Never by hand, and never
   by averaging across classes to get under a threshold.
6. The two honesty rules, enforced in code:
   a. SUBSYSTEM EVIDENCE DOES NOT COMPOSE INTO SYSTEM EVIDENCE. Memory-class and
      matrix-class agreement do not validate end-to-end numbers; only end-to-end entries do.
   b. A COVERED COMPONENT WITH AN INAPPLICABLE ANCHOR CANNOT MAKE A RUN LOOK VALIDATED
      (rk-sim ADR 0021). A mesh-design request against large-core evidence gets stub.
7. `uarch ledger` prints the table; `uarch report` gains a ledger section.

ACCEPTANCE TESTS (write first):
1. Dry run: the full kit runs on CPU JAX and writes SYNTHETIC-labelled files that the ledger
   REFUSES to ingest.
2. The ledger refuses a duplicate key with a changed prediction.
3. Promotion: with fixture entries at 18% median error, a large-core design's card becomes
   estimated for {matrix, memory, operator, end-to-end}; npu-m256's card stays stub, and
   says the family mismatched.
4. Subsystem-only fixture evidence does not promote end-to-end rows.
5. G4 is evaluated and recorded, pass or fail, per mapping-match group.
6. Workload-fidelity entries exist for every benchmark that has compiler-reported counts.
7. A fixture where only the compiler-chosen group passes promotes only within that group's
   scope.

GUARDRAILS: Do not run paid hardware until predictions are frozen and ordering passes. If G4
fails, PUBLISH THE ERRORS ANYWAY. Then follow G4's fail branch (execution-plan §4), and do not
start adjusting the model in this session. Never average away a failing class.

ADR: docs/decisions/U0010-the-first-validation-verdict.md, whichever way it went, with the
table of errors by class.
```


### U-P11a · U6 · Lane A — Native engine kernel: time, events, the wheel, ownership, and the protocol

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/engines/README.md, build-spec §2.5
(the engine protocol and TaskGraph) and §2.8 (the native engine specification; it is the
spec, not background), ADR U0005, U0007. Javid's ../rk-sim/docs/vision/elements_of_parallel_DES.md
from rk-sim, READ-ONLY, for the parts §2.8 adopts, and build-spec §2.8's "departures" table
for the parts it rejects and why.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Reuse the U2/U4 versioned prepared-job protocol and fixtures. Rust receives resolved
shapes, resource assignments, dependencies and policies; no model builder or mapper runs
inside the engine. Timing/events are outputs of executing those inputs. Extend the accepted
protocol only through its versioned schema procedure, not a parallel Rust-only format.

TASK: the kernel of native/, uarch's own event-driven engine, in Rust, built in the engine
container, and the plumbing that puts it behind exactly the same engine protocol as the
fork: EngineJob JSON in, EngineResult JSON out, invoked as a subprocess binary
`uarch-engine`. Single-threaded. No subsystem models yet: U-P11b adds them.

1. BEFORE MEASURING ANYTHING, write in ADR U0011 (a) the speed factor over the fork that you
   expect on npu-l4 and on a 16×16 mesh, and why (G5 checks it), and (b) a single-point
   wall-clock budget for the npu-m256 and 32×32 grids, above which parallelism inside one
   simulation is needed (U9's gate reads it).
2. Build: native/Cargo.toml (workspace) with crates/uarch-engine (the `uarch-engine`
   binary); native/rust-toolchain.toml pinning the current stable Rust, recorded in U0011;
   a committed Cargo.lock. Dependencies ONLY serde and serde_json, plus proptest as a
   dev-dependency, each added to third_party/LICENSES.md. native/deny.toml makes cargo-deny
   check every crate's licence against the allow-list; if a core crate needs a licence
   outside it (serde_derive's unicode-ident carries Unicode-3.0, for example), stop and
   propose the allow-list change in an ADR. The crate has #![forbid(unsafe_code)];
   clippy runs with -D warnings and disallows HashMap and HashSet; rustfmt is enforced.
   Add the Rust toolchain to containers/Dockerfile.engine, and wire `make native` and
   `make native-test` to cargo.
3. Time: u64 picoseconds. Each clock domain has the resolved integer freq_hz from the
   EngineJob, NEVER A ROUNDED PERIOD (1.2 GHz is 833.33… ps, and rounding it either way
   biases every row or breaks the roofline floor). EDGES ARE ROUNDED, PERIODS ARE NOT: edge k
   sits at t_k = ceil(k · 10^12 / freq_hz) ps, computed exactly in u128.
   next_edge(domain, t_ps, n_cycles) returns t_{k+n}, where t_k is the first edge at or after
   t_ps. It is THE ONLY conversion between time and cycles; units in every name (_ps,
   _cycles, _hz). DVFS is a per-domain frequency ratio, applied through the resolved freq_hz
   when the Simulation is constructed.
4. Event: a 32-byte #[repr(C)] Copy struct {t_ps: u64, seq: u64, target: u32, kind: u16,
   phase: u8, flags: u8, payload: u32, pad: u32} with a compile-time assertion that its size
   is 32. The total order is (t_ps, phase, target, seq), and seq is assigned at schedule time
   from one counter.
   Kinds: TASK_READY, COMPUTE_DONE, DMA_ISSUE, DMA_DONE, NOC_HEAD, NOC_TAIL, MEM_REQ,
   MEM_RESP, MEM_TICK, SYNC_ARRIVE, BARRIER_RELEASE, STAT_SAMPLE, END (MEM_TICK is unused
   until U-P13b's Ramulator 2 path, build-spec §2.8). Dispatch is a match on kind,
   with no trait objects (dyn) on the hot path.
5. Scheduling: an event arena with a free list (no per-event heap allocation after warm-up);
   a two-level timing wheel (4,096 slots, each floor(10^12 / max freq_hz) ps wide, at least
   1) with a min-heap for
   overflow. Ties within a slot are resolved by the total order, never by insertion order.
6. State ownership: every resource (core matrix engine, core vector engine, SRAM bank group,
   DMA engine, router output port, link, memory channel) has exactly ONE owner id. State lives
   in structure-of-arrays indexed by owner id. Only events whose target is that id may mutate
   it: only that event's handler gets &mut access to the owner's state, and debug builds
   assert the target on every mutation. Single-threaded, this is discipline; in U-P17 it
   becomes the partition boundary, enforced by the compiler.
7. Topology: CSR adjacency; precomputed dimension-order routes (XY on mesh, shortest
   direction on torus); multiple NoCs, each with its own direction. Sorted vectors wherever
   iteration order could reach a result. NO HashMap OR HashSet ON ANY PATH THAT PRODUCES
   OUTPUT: Rust randomises their iteration order. Use BTreeMap or sorted Vecs.
8. A fixed-delay executor: a TaskGraph whose jobs are fixed delays (no models yet),
   dependencies resolved by events, so the kernel runs end to end before any model exists.
9. src/rkuarch/engines/native/: the Python side: job writer, subprocess runner, result
   parser, identical in shape to engines/fork/, so `uarch table ... --engine native` reaches
   the binary.
10. The protocol as a schema: reuse U2/U4's EngineJob/EngineResult schemas and fixture
    messages from engines/protocol.py in src/rkuarch/engines/schema/. `make gen` keeps exporting
    them; the freshness check remains read-only. Test Rust serde types against those fixtures,
    including prepared input versions/hashes and refusal cases, so neither side drifts alone.

ACCEPTANCE TESTS (write first):
1. cargo test: event ordering, wheel overflow into heap and back, arena reuse, next_edge at
   domain boundaries, owner assertion fires on a foreign mutation (debug build); proptest
   checks the wheel against a sorted reference over random schedules.
1a. Clock edges: at 1.2 GHz, next_edge(core, 0, 3) == 2500 and next_edge(core, 0, 10^9) ==
   833_333_333_334 (no drift); proptest over random freq_hz and k asserts
   0 <= t_k · freq_hz − k · 10^12 < freq_hz (never early, under 1 ps late); a fixed-delay job
   of N core cycles started at t = 0 never ends before N / freq_hz exactly.
2. cargo fmt --check, cargo clippy --all-targets -- -D warnings and cargo deny check
   licenses pass; the engine crate forbids unsafe.
3. A fixed-delay TaskGraph's duration equals its critical path worked by hand in the test,
   and its EngineResult is byte-identical across 3 runs and between debug and release
   builds.
4. The Python side round-trips an EngineJob through `uarch-engine`, and the EngineResult
   validates against the engine protocol.
5. Ties: events with equal t_ps resolve by (phase, target, seq), whatever order they were
   scheduled in.
6. Protocol drift: the Rust types parse and re-emit every schema fixture unchanged, and a
   fixture with an unknown field is refused, as Pydantic's extra="forbid" refuses it.

GUARDRAILS: No subsystem models; they are U-P11b. No unsafe. No threads, no SIMD intrinsics
(std::simd, core::arch), no GPU, no MPI; those are U-P17 at the earliest, and only what it
builds. Do not delete or bypass the
fork: it is the permanent L2 reference. Cycles never leave native/ and engines/. Do not
optimise before determinism holds.

ADR: docs/decisions/U0011-the-native-engine-core.md, started here: the expected speed factor
and the single-point budget (both written before any measurement), the pinned Rust version,
the time base as built (build-spec Rev 2.3: resolved integer freq_hz, rounded edges),
and each departure from the vision note. The lookahead-collapse premise in particular: real routers take several
cycles per hop (Tenstorrent documents ~9 router-to-router on Blackhole), so it is not L = 1.
```


### U-P11b · U6 · Lane A — Native engine models: compute level 1, NoC and DRAM level 0, and the TaskGraph executor

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/mapping/README.md, build-spec §2.4
(the ladder and fidelity_detail), §2.5 (the TaskGraph and EngineResult) and §2.8, ADR U0011
as U-P11a left it, and U-P11a's handoff.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Execute locally produced or imported validated TaskGraphs through the same path.
Mapping policy identifiers are provenance, not instructions for the native engine to invoke
Python mapping. Engine arbitration follows declared policies; it never changes tile shapes,
placement, fusion or buffer assignment to fit a job. Reject unsupported supplied decisions.

TASK: the models at the levels this sprint builds, and the executor that runs a real
TaskGraph through them, so the native engine produces real rows.

1. Models (build-spec §2.4):
   - compute level 1: tile-job intervals, meaning pipeline fill and drain for the job's
     declared dataflow, tile quantisation and padding, double-buffer overlap of DMA and
     compute, operand staging at operand_bytes_per_cycle, an output tile bounded by
     accumulator_bytes (partial sums beyond it go to SRAM where the policy placed them), and
     job_overhead_cycles on every tile job. A tensor job is O(1–10) events, not O(cycles);
   - NoC level 0: hop latency, infinite bandwidth;
   - DRAM level 0: fixed latency plus a bandwidth cap per channel, derated for refresh from
     the spec's timing;
   - at every level, each DMA engine honours dma.max_outstanding and request_bytes, so a
     distant core's bandwidth is latency-bound; barriers cost sync.barrier_latency_cycles.
   EngineResult reports fidelity_detail honestly: {compute: 1, noc: 0, dram: 0}. The
   composite for that is C1 at best, and the table must say so.
2. TaskGraph executor: runs the TaskGraph from mapping/ (ws-rowsplit@1, os-tiled@1 and
   onnxim-compat@1; npu-m256 uses ws-rowsplit@1 until the mesh policies land in U-P13d),
   resolving dependencies by events, attention_fused tiles included. initial_state steady
   primes one iteration inside the same simulation and reports the second (two priming
   iterations when the job asks for the warm-up check).
3. Critical-path attribution: each interval on the critical path is charged to the resource
   that bounded it, and the parts sum to duration_ps.

ACCEPTANCE TESTS (write first):
1. The FULL L0, L0m and L1 suites pass against the native engine through the engine
   protocol, with no suite code changed.
2. Determinism: same job → byte-identical EngineResult across 3 runs, and between debug and
   release builds.
3. `uarch table hw/designs/npu-m256.yaml ... --engine native` builds a full table: the mesh
   class, which the fork cannot represent.
4. The latency-bound stream fixture (U-P8) passes, and lowering max_outstanding lowers a
   distant core's achieved bandwidth.
5. Halving accumulator_bytes on a GEMM whose output tile then no longer fits never shortens
   it, and the extra SRAM traffic appears in ext_counts.
6. attribution_s sums to duration_s on every row.

ADDITIONAL ACCEPTANCE — prepared inputs:
- Replay a saved mapped job with local workload/mapping producers unavailable and compare
  its complete EngineResult with the original. Invalid placement is refused before events
  run. No hidden reconstruction from ModelSpec or tp is allowed.

GUARDRAILS: Only the levels above: NoC "1+ts", DRAM 1 and 2, and compute 2 are U-P13a–c. No
threads. Do not optimise before the determinism and L0–L1 suites pass. Do not tune a model
toward the fork; U-P11c measures agreement.

ADR: append to docs/decisions/U0011-the-native-engine-core.md the models built and every spec
field the native engine lists as unrepresented at these levels.
```


### U-P11c · U6 · Lane A — Native engine diagnostics, traces, G5 and the measured speed factor

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/engines/README.md, build-spec
§2.3.3 (diagnostics), §2.5 and §2.8, ADR U0005 (the fork's ladder table), U0011, U-P11b's
handoff, and U-P12's harness (validation/L2_differential/native_vs_fork/).

TASK: make the native engine's output complete and checked: diagnostics, traces, agreement
with the fork at matched levels, and the speed factor against the one written first.

1. Diagnostics: fill the row diagnostics the running levels model, and null for everything
   else (NoC contention statistics at NoC level 0, for example). Never 0 for unmodelled.
2. With --trace, a Chrome-trace JSON per-resource timeline from STAT_SAMPLE and job events.
3. G5 with U-P12's harness: onnxim-compat@1 driving both engines, the fork in the
   configuration ADR U0005 classifies as matching native's levels. If no fork configuration
   matches {compute: 1, noc: 0, dram: 0}, do not compare mismatched levels: record which
   subsystem mismatches, and G5 moves to U7, after U-P13a–c, at the closest matching
   configuration.
4. Measure the speed factor against the fork on npu-l4 and the 16×16 mesh, and the
   single-point wall-clock on the npu-m256 grid against U0011's budget.

ACCEPTANCE TESTS (write first):
1. G5: durations agree within 3% on ≥ 95% of the npu-l4 grid at matched levels, or the level
   mismatch is recorded and G5 rescheduled as item 3 says.
2. Diagnostics: at NoC level 0 every NoC statistic is null, and no null diagnostic renders as
   0 in `uarch report`.
3. The trace of a golden request loads as valid Chrome-trace JSON, and no two intervals on
   one resource overlap.
4. The speed factor and the single-point wall-clock are recorded next to the numbers written
   first.

GUARDRAILS: If the speed factor disappoints, record it; do not trade determinism for it. Do
not fix a disagreement with the fork by tuning: bisect it with U-P12's attribution and record
it. No threads.

ADR: complete docs/decisions/U0011-the-native-engine-core.md with the measured speed factor,
the single-point wall-clock against the budget, and G5's result or its rescheduling.
```


### U-P12 · U6 · Lane B — The differential harness, determinism gates, and simulator metrics

```text
CONTEXT TO LOAD: CLAUDE.md, validation/L2_differential/README.md, build-spec §2.5, §2.8, §6.6
(determinism), ADR U0011's expected speed factor. You do not need the native engine to be
finished: you need the engine protocol, which already exists.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Compare prepared workload content and resolved mapping correspondence before comparing
engine results. Preserve each producer/version and engine identity. Byte-identical shared
TaskGraphs are preferred; fork-specific encoding needs explicit audited equivalence evidence.
Matching policy names without matching shapes, placement, precision and run conditions fails.

TASK: make "native agrees with fork" a measured, attributable, continuously checked fact,
and make simulator performance a regression-tested quantity rather than an anecdote.

1. validation/L2_differential/native_vs_fork/: given a request and a list of
   (engine, level-config) pairs, build both tables through the table interface, then report
   per-point relative deviation, the fraction of points within 3%, and per-subsystem
   attribution. Attribution uses each engine's critical-path attribution_s, busy times and
   diagnostics (where both report them), so a
   disagreement can be bisected to compute, NoC, DRAM or sync. Only configurations where both
   engines run the SAME mapping (onnxim-compat@1) and MATCHING sub-model levels are
   comparable, and the harness refuses the rest with the mismatch named.
2. Determinism gates in CI, for every engine in the matrix:
   - table built twice → byte-identical;
   - --workers 1 vs --workers N → byte-identical;
   - nightly: the native engine's debug build (overflow checks on) runs the golden requests
     clean, and from U-P13b the Ramulator 2 bridge runs its tests under AddressSanitizer.
3. validation/perf/: simulator-performance metrics recorded per golden request, per engine
   version, as data:
   - HOST INSTRUCTIONS PER SIMULATED CYCLE, via `perf stat` where the box permits it.
     Otherwise host nanoseconds per simulated cycle, labelled as such and never mixed with
     instruction counts;
   - events per simulated cycle, and events per completed tensor job;
   - cross-thread messages per simulated cycle, and sync operations per million simulated
     cycles. Both are 0 by construction until U-P17, and the report says so rather than
     omitting them;
   - NOT events per second as a headline. The vision note is right about this.
   A regression gate fails a PR that worsens host-cost-per-simulated-cycle by more than a
   threshold you set in ADR U0012 (with its noise floor measured first).
4. POWER: commit a mutant native engine that adds one cycle to every router hop. Assert the
   harness catches it, and attributes the disagreement to the NoC, not to compute or DRAM.
5. `uarch diff <table-a> <table-b>` prints per-point deviation and attribution. The design
   study (U-P14) reuses it.

ACCEPTANCE TESTS:
1. G5's criterion (≥95% of shared points within 3%) is computed and recorded for the npu-l4
   grid at matched levels.
2. The one-cycle mutant is caught and attributed to the NoC.
3. The harness refuses a comparison with mismatched mapping or levels, naming the mismatch.
4. Performance baselines are recorded for every golden request, and the regression gate trips
   on a synthetic 2× slowdown.

ADDITIONAL ACCEPTANCE — prepared inputs:
- Two inputs with the same model/tp/policy label but different resolved tiles or placements
  are refused as an engine-equivalence comparison. A numerical gap must not be attributed
  to engine physics until input and mapping correspondence is established.

GUARDRAILS: Do not call agreement "validation" anywhere, in code, reports or ADRs. It is L2.
Do not fix a disagreement here. Report it with its attribution and hand it to Lane A.
Do not headline events per second.

ADR: docs/decisions/U0012-native-vs-fork-agreement.md, with the agreement fraction, the
per-subsystem attribution of what did not agree, and the performance noise floor.
```


### U-P13a · U7 · Lane A — Native NoC at "1+ts": reservation calendars and NoC barriers

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, build-spec §2.4 (the per-subsystem ladder and
fidelity_detail) and §2.8, ADR U0011, U0012 (what did not agree, and why), and U0008's NoC
L2 report.

TASK: the first contention-aware subsystem of the native engine: the NoC at level 1 with
cycle timestamps.

1. NoC level 1 WITH CYCLE TIMESTAMPS ("1+ts"): reservation calendars per link and per router
   output port (the vision note's "F2a"). A packet reserves [start, start + serialisation)
   at each resource along its precomputed route. Head and tail timing propagate wormhole
   dependencies; virtual-channel occupancy and credit backpressure are modelled at packet
   granularity; multicast along rows and columns. BookSim2 STAYS the L2 reference. Do not
   build a flit-level router of your own, and do not build a third NoC backend.
2. Barriers follow sync.mechanism: with noc_semaphore they are NoC messages and contend like
   any other traffic.
3. The NoC diagnostics that level models (latency p50 and p99, maximum link utilisation) are
   filled; the rest stay null.

ACCEPTANCE TESTS (write first):
1. L0, L0m and L1 pass at the new level; L2 NoC (vs standalone BookSim2) passes U-P8's bound
   against the native engine.
2. Contention actually bites: a hotspot mapping on npu-m256 is measurably slower than a
   uniform one at equal MACs and bytes. At NoC level 0 the two are identical, and the test
   asserts both halves.
3. A barrier across 64 cores takes longer under background NoC traffic than on an idle NoC.
4. Determinism: byte-identical at 1 and N workers; the debug build runs clean.

GUARDRAILS: No threads yet. Do not remove the level-0 path: it is a fast mode. Do not tune
reservation parameters to match BookSim. Record the gap and its mechanism in the L2 report.

ADR: none here; U-P13d's U0013 records this level and its BookSim gap.
```


### U-P13b · U7 · Lane A — Native DRAM: queues with back-pressure, Ramulator 2, and interleaving

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, build-spec §2.3.2 (memory, presets, queues and
credits), §2.4 and §2.8, ADR U0011, U0012, and U0008's DRAM L2 report. Ramulator 2
documentation (its External frontend, for use as a library).

TASK: DRAM at levels 1 and 2, with the controller back-pressure the spec now describes, and
the address interleaving that decides which cores talk to which controller.

1. DRAM level 1 with cycle timestamps ("1+ts"): a per-channel queue with a row-buffer
   approximation, the spec's page policy, and the spec's read and write queue depths. It
   stays the fast path.
2. DRAM level 2: Ramulator 2 linked as a library through its External frontend, at the SHA the
   engine image pins, one instance per memory controller, configured from the spec's DRAM
   organisation, timing, timing_preset and queue depths, and never from a preset or default
   the spec does not name; what Ramulator needs and the spec lacks is listed as
   unrepresented. The bridge is its own crate, crates/uarch-ramulator-sys: a thin C++ shim over
   the External frontend, compiled by build.rs, bound with cxx, and the ONLY crate allowed
   unsafe, every unsafe block with a SAFETY comment. The engine crate calls it through a safe
   API and stays #![forbid(unsafe_code)]. Register Ramulator 2 and cxx in
   third_party/LICENSES.md.
2a. Driving a cycle-ticked library from the event kernel, EXACTLY AS build-spec §2.8
   ("Cycle-ticked models inside the event kernel") SAYS:
   - Ramulator cycle c is edge next_edge(dram, 0, c); its clock comes from
     clock_domains.dram, and a configuration whose clock disagrees (including a
     data-to-command clock ratio the spec does not give) is refused with both values named;
   - busy: one MEM_TICK ticks the instance in one bridge call through every cycle before the
     horizon H = min(next pending event's t_ps + L_in, earliest MEM_REQ already scheduled
     for this controller, window end), stopping early after the first cycle that completes a
     request or admits a waiting one. L_in is computed from the spec (the final router and
     link at the attach point), never configured;
   - idle: no events; the next MEM_REQ first catches the instance up through the idle cycles
     in one bridge call, so refresh happens exactly as if it had ticked throughout. No
     shortcut that is not byte-identical to catch-up;
   - completions are returned sorted by (cycle, request id); request ids come from a
     per-controller counter in arrival order; same-edge requests are sent in event total
     order;
   - a debug flag ticks every DRAM cycle with one MEM_TICK each: the REFERENCE MODE.
   Simulator metrics report busy ticks and catch-up ticks per simulated DRAM cycle
   separately.
3. Back-pressure: a controller whose queue is full withholds NoC credits (noc_credits), so
   requests wait in the network rather than vanishing into an unbounded queue.
4. Addresses map to channels and controllers by memory.interleave, so the NoC sees the
   traffic pattern the interleaving creates. The job chooses the DRAM level; EngineResult
   reports which ran, and fills dram_bw_util_ratio and dram_row_hit_ratio where the level
   models them.

ACCEPTANCE TESTS (write first):
1. L0, L0m and L1 pass at both new levels; L2 DRAM (vs standalone Ramulator 2) is recorded
   against the native engine, with each >5% deviation attributed where it can be.
2. Interleaving bites: changing memory.interleave's granularity changes the per-controller
   traffic split and the NoC diagnostics, at equal bytes.
3. Back-pressure bites: halving a controller's queue depth under saturating traffic never
   shortens duration, and raises NoC latency at that controller's attach point.
4. No preset fallback: a spec without timing and without timing_preset is refused at DRAM
   level 2, naming the missing fields.
5. Determinism: byte-identical at 1 and N workers; the bridge's tests run clean under
   AddressSanitizer in the nightly job.
6. unsafe appears nowhere outside crates/uarch-ramulator-sys (a test greps the workspace).
7. Batching is exact: at DRAM level 2, every golden request and a saturating-stream fixture
   produce byte-identical EngineResults in batched mode and in the tick-every-cycle
   reference mode (simulator metrics excluded).
8. Idle refresh: a request arriving after an idle gap longer than t_REFI sees the same
   latency in batched and reference modes, and a different latency from a run with refresh
   disabled in Ramulator, which proves catch-up is not skipping refresh.
9. Causality: the debug build's assertion (no MEM_REQ arrives at an edge the instance has
   already ticked past) holds on every golden request, and a test that forces L_in too
   large makes it fire.
10. Clock agreement: a spec whose Ramulator configuration implies a clock different from
   clock_domains.dram is refused, naming both values.

GUARDRAILS: No threads yet. Keep DRAM level 0 and level 1: they are the fast modes. Do not
tune DRAM parameters toward Ramulator's defaults; record the gap.

ADR: none here; U-P13d's U0013 records these levels, the fields Ramulator could not take,
the measured cost of busy and catch-up ticking, and each controller's L_in.
```


### U-P13c · U7 · Lane A — Native compute level 2: SRAM bank conflicts and DMA interleave

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/mapping/README.md, build-spec §2.4
and §2.8, ADR U0011, U0012.

TASK: compute at level 2, the last piece the composite rule needs for C2.

1. Compute level 2: SRAM bank conflicts, from the mapping's buffer placement (core,
   offset_bytes, bank), and DMA/compute interleaving at cycle timestamps, still O(1–10)
   events per tensor job wherever no conflict occurs. sram_bank_conflict_stall_ratio and
   dma_compute_overlap_ratio are filled at this level.
2. Shared SRAM: engine support is deferred until after U8. A spec with a shared_sram is run
   with that field listed as unrepresented, fidelity_detail.shared_sram = "unrepresented",
   and the table warns.

ACCEPTANCE TESTS (write first):
1. L0, L0m and L1 pass at compute level 2.
2. Conflicts bite: a placement that puts two concurrently read operands in one bank is
   slower than one that spreads them, at equal bytes; at compute level 1 the two are
   identical, and the test asserts both halves.
3. A spec with a shared_sram reports it as unrepresented and is refused C2, with the reason.
4. Determinism: byte-identical at 1 and N workers; the debug build runs clean.

GUARDRAILS: No threads yet. Keep compute level 1: it is the fast mode. Do not model the
shared SRAM in this prompt.

ADR: none here; U-P13d's U0013 records this level.
```


### U-P13d · U7 · Lane A — Mesh mapping policies, the composite rule, and C2 at mesh scale

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/mapping/README.md, build-spec §2.4
(the per-subsystem ladder and the composite rule), §2.8, ADR U0011, U0012, and the handoffs
of U-P13a, U-P13b and U-P13c.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Mesh mapping policies extend the standalone preparation frontend and emit the same
versioned TaskGraph format that external producers can supply. The native engine consumes
resolved mapped inputs, never chooses SUMMA/head placement itself. Export/import preserves
policy version, hardware binding and content identity; no search or compiler integration.

TASK: make the mesh class a first-class target and the composite honest: mesh policies, the
composite rule in code, and full C2 tables at mesh scale.

1. Mesh-class mapping policies in src/rkuarch/mapping/ (Python, shared by every engine):
   - summa-2d@1: GEMM outputs blocked over the core grid, operands multicast along rows
     and columns;
   - head-parallel@1: attention heads distributed over cores, attention_fused tiled per head
     group, KV resident per head group and read in pages of the request's block size.
   Each carries its own docstring derivation of per-core bytes and MACs. L0 checks those
   against the graph.
2. THE COMPOSITE RULE (build-spec §2.4), enforced in native/ and re-checked in Python:
   - report C2 ONLY IF compute is at level 2, NoC and DRAM are at level 2 or "1+ts", a
     shared SRAM (when present) is at "1+ts", AND synchronisation is exact;
   - otherwise C1, if any subsystem is at level 1;
   - otherwise C0-equivalent.
   Emit the full per-subsystem vector as fidelity_detail, with build-spec §2.4's keys and
   values only. A request that asks for C2 and cannot get it degrades or raises exactly as
   build-spec §7.4 says for default vs override.
3. Scale: build full tables for npu-m256 (16×16) and a 32×32 variant. Record the simulator
   metrics from U-P12 for both, and the single-point wall-clock against ADR U0011's budget.
4. If G5 was rescheduled from U6 (U-P11c item 3), run it now at the closest matching
   configuration.

ACCEPTANCE TESTS (write first):
1. G6: the npu-m256 table reports composite C2 with detail {compute: 2, noc: "1+ts",
   dram: 2 or "1+ts", sync: "exact"}. A job with any subsystem below the rule is refused C2,
   with the reason.
2. Roofline floor: no row of any native table is faster than its U-C0 roofline.
3. summa-2d@1 and head-parallel@1 pass L0's per-core bytes and MACs check against the graph.
4. Determinism: byte-identical at 1 and N workers; the debug build runs clean.
5. The 32×32 table builds, and its metrics and wall-clock are recorded.

GUARDRAILS: Do not claim C2 below the rule. No threads yet. Do not remove the level-0 and
level-1 paths: they are the fast modes, and the ladder is a feature.

ADR: docs/decisions/U0013-the-composite-fidelity-rule.md, covering the rule as built, each
level U-P13a–c added, and their L2 gaps with mechanisms.
```


### U-P14 · U7 · Lane B — Design studies: variants, sweeps, and the diff report

```text
CONTEXT TO LOAD: CLAUDE.md, src/rkuarch/{report,study}/README.md, build-spec §1.2 (the
acceptance demo: the study is minutes 4–5 of it) and §2.6. From rk-sim READ-ONLY:
docs/prompts/P9a-sweep-engine.md and P9b-*.md (its sweep and tornado conventions, and why a
one-at-a-time tornado is labelled local sensitivity rather than a ranking).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Declare whether a study re-prepares each variant with a named local policy or replays
an externally supplied mapping. Local preparation records a new hardware/mapping identity
per variant. Fixed imported mappings are validated against each variant and refused when
incompatible; re-mapping requires an explicit study choice and recorded producer. Cache
identity includes prepared content and its bindings, not just model/tp or policy label.

TASK: the thing a chip architect actually does with this tool, which is to compare designs. A
study is a set of tables over stipulated variants, and a report that says what moved and why.

1. src/rkuarch/study/: a StudySpec (YAML) names a base design, a list of parameter paths with
   values (one-at-a-time, or a small full grid), a versioned workload
   suite (or one request template), and one engine and fidelity. `uarch study <studyspec>`
   builds each variant's table through the existing pipeline. Tables are cached by request
   hash, so a rerun rebuilds nothing.
2. VARIANTS MAY ONLY CHANGE WHAT A PROPOSED DESIGN IS FREE TO CHOOSE: its stipulated values
   (counts included: array, grid, banks, channels, queue depths), its categorical fields
   (dataflows, topology, interleave scheme, scheduler, page policy, sync mechanism) and the
   request's mapping policy. Every change is recorded in conditional_on as path=value.
   In local-preparation mode the mapping is re-run per variant; fixed imported mappings
   follow the validation/refusal rule above. A study that edits a reference spec, or any claim, is
   refused: it would be a counterfactual about a real chip wearing that chip's evidence. A
   variant that changes sram.bytes without re-stipulating energy.pj_per_byte.sram is refused,
   naming both paths.
3. The diff report (uarch diff from U-P12, extended):
   - per grid point, the relative change in duration, with its attribution split, showing
     which regime moved (compute-, memory-, NoC- or sync-bound) and which did not move at all;
   - per workload in the suite, each variant's normalised speedup over the base, and their
     geometric mean. Never an arithmetic mean of ratios;
   - a one-at-a-time tornado over the study's parameters at the operating points the
     StudySpec names, LABELLED "local sensitivity at these points, not a ranking";
   - energy per token from activity counts × per-activity coefficients, which are claims
     or stipulations from the spec, so the energy number carries its own conditional_on. It
     renders "unverified" while energy_verification is None (the energy rung is deferred
     until after U8), and uses voltage_ratio at frequency ratios ≠ 1 ("unknown" without it);
   - "detail delta": each variant's C2 duration next to its own U-C0 roofline, so the study
     shows how much of each change the roofline would have predicted anyway.
4. Every number renders through report/badged.py. A study over a proposed design says, at
   the top, "every number here is conditional on N stipulations" plus the model card's scope,
   and whether the evidence applies to this design's family at all.
5. hw/studies/: three example studies. hw/studies/npu-m256-sram-and-noc.yaml: SRAM per core
   1.5 MB → 3 MB (pj_per_byte.sram re-stipulated per size), and NoC link width 32 → 64
   B/cycle. hw/studies/npu-l4-hbm.yaml: HBM bandwidth ±25%. hw/studies/npu-l4-dataflow.yaml:
   weight- vs output-stationary (dataflows and mapping policy together: ws-rowsplit@1 vs
   os-tiled@1).
6. hw/studies/workload-suite@1.yaml: models × precisions × phases × named operating points,
   chosen from `uarch characterize` coverage, with a one-line reason per entry. A new suite
   is a new version, never an edit.

ACCEPTANCE TESTS (write first):
1. A study over two variants rebuilds nothing on rerun (cache hit, by request hash).
2. A variant that edits a claim, or any field of a reference spec, is refused, and names the
   path.
3. The tornado is labelled local sensitivity, and a test greps the rendered report for it.
4. Energy per token carries conditional_on and renders "unknown" error when there is no band.
5. A variant that changes nothing the mapping touches produces a diff of exactly zero at every
   point (reuses the L0m relation).
6. Geometric mean: a two-workload fixture where one speeds up 2× and the other slows 2×
   reports a geometric-mean speedup of exactly 1.0.
7. A variant that changes sram.bytes without pj_per_byte.sram is refused, naming both paths.
8. Energy renders "unverified" with no energy_verification, and "unknown" at frequency ratio
   0.6 when voltage_ratio is absent.
9. The dataflow study runs: each variant's conditional_on names its dataflows and mapping
   policy, and a variant whose dataflows lack its policy's dataflow is refused.
10. A count variant (npu-m256 SRAM banks 16 → 32) runs, and its change is in conditional_on.

ADDITIONAL ACCEPTANCE — prepared inputs:
- A variant invalidating a supplied mapping is refused without calling a local mapper.
  An explicitly re-prepared variant records the new mapping identity. Changing prepared
  content under the same input filename causes a cache miss.

GUARDRAILS: No optimiser and no design search. A study is a set of runs a human chose. No
fitted surrogate; rk-sim deliberately refuses fitted Sobol indices, and so does this.
No area model: area is not modelled, and the report says so.

ADR: docs/decisions/U0014-what-a-design-study-may-claim.md.
```


### U-P15 · U8 · Lane A — The mesh reference model, and predictions frozen before anyone measures

```text
CONTEXT TO LOAD: CLAUDE.md, validation/L3_silicon/README.md, hw/references/blackhole-p100a.yaml,
ADR U0009, U0010, U0013. Tenstorrent's public documentation: the Blackhole product page, and
tt-isa-documentation/BlackholeA0/NoC/README.md (two opposite-direction 2-D torus NoCs,
64-byte flits, about 9 cycles router-to-router, about 5 cycles NIU↔router), the TT-Metalium
device program profiler page, and tt-npe (Apache-2.0).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Freeze the exact prepared workload/mapping artifacts or a resolvable immutable manifest
alongside predictions, including producer versions, content hashes, hardware binding and run
conditions. Measurements use the declared mapping match; a compiler-chosen mapping is not
assumed equal to the local policy. Replaying predictions must not silently re-prepare inputs
with a newer producer.

TASK: the same discipline as U-P9, for the class the native engine exists for: a mesh of many
small cores. Predictions are committed before any measurement exists, and this prompt never
sees one.

1. Complete hw/references/blackhole-p100a.yaml as a REFERENCE: claims only, every number with
   a URL, unknowns as stub claims. Model what the docs describe: two NoCs in opposite
   directions on a torus, the per-hop latencies, flit width, SRAM per core, the GDDR6
   channels and bandwidth, the numeric formats including BLOCKFP8 with its scale bytes. List
   every stub the engine reads in predictions/UNKNOWNS.md. Fill the Rev-2 fields from the docs
   where they exist (GDDR6 organisation and timing, interleaving, DMA/NIU outstanding
   requests, barrier mechanism, accumulator and operand-buffer capacity, controller queues
   and credits); otherwise stub them, counts included.
2. Agree validation/L3_silicon/blackhole/SUITE.md with Lane B FIRST, signed by both, with
   at least 36 benchmarks covering every one of these eight classes:
   - NoC: point-to-point latency vs hop count on each NoC; k-to-1 contention at k ∈ {2,4,8};
     row multicast;
   - DRAM: streaming read and write per channel, and all channels at once;
   - core compute: single-core matmul at ≥ 4 shapes in at least two formats;
   - multi-core: summa-2d@1-style matmul across 1, 4, 16, 64 cores;
   - end-to-end: one full decoder layer (summa-2d@1 and head-parallel@1 style) across ≥ 64
     cores, at decode B ∈ {1, 8, 32} and at one prefill shape. Only this class can validate
     whole-iteration rows (U-P10's rule), so it is what the demo's table needs;
   - latency-bound transfer: achieved bandwidth against transfer size × hop distance
     (memory-level parallelism);
   - DRAM gather: page-granular reads at rk-sim's block size;
   - synchronisation: barrier and semaphore latency across k ∈ {2, 4, 16, 64} cores, and the
     device-side cost of launching an empty program.
   Shapes are chosen with `uarch characterize` to cover the demo request's per-op shape
   regimes (npu-m256 × Llama-3.1-70B × fp8) where the card can express them. Precision
   follows U0001's rule: BLOCKFP8 benchmarks are BLOCKFP8 evidence. Core-compute and
   end-to-end benchmarks run in the demo request's precision (fp8) if the card runs it, and
   in bf16 and BLOCKFP8; if the card cannot run fp8, SUITE.md and ADR U0015 say so, and say
   that the demo table's rows stay stub on precision. Kernels programmed to a
   uarch policy (summa-2d@1-style) are `matched`; anything else is `compiler-chosen`.
   Each benchmark states its GRANULARITY IN PROFILER ZONES: which zone start/end on which
   RISC-V core. The profiler timestamps in cycles since reset and holds 125 zones per core
   buffer. Inter-core clocks are "closely synced but may have minor skews", so a
   cross-core latency benchmark states how skew is bounded or cancelled.
3. Predictions from the native engine at every level it has (the level-1 fast path
   {compute: 1, noc: "1+ts", dram: "1+ts"} and composite C2) AND from U-C0 (aggregate, and per_op,
   which stands for level 0), written to
   validation/L3_silicon/blackhole/predictions/<id>.json with full provenance, mapping match,
   initial state, predicted FLOPs and bytes, and the row diagnostics. Also run
   tt-npe on the NoC benchmarks and commit its outputs as a SECOND prediction set, labelled
   as the vendor's estimator. It is an L2 reference, and its own error against silicon is
   information too.
4. One commit, message beginning "FROZEN PREDICTIONS:". check_ordering already enforces the
   rest.

ACCEPTANCE TESTS:
1. SUITE.md signed by both lanes before prediction generation.
2. ≥ 36 prediction files covering all eight classes; each has a native prediction per
   available level and U-C0 predictions; NoC benchmarks also have tt-npe predictions.
3. The reference spec loads as design_status: reference, with zero stipulations.
4. UNKNOWNS.md is complete: a test cross-checks it against the stubs the engine read.

GUARDRAILS: DO NOT LOOK AT, REQUEST OR ESTIMATE ANY MEASUREMENT. Do not edit a prediction once
it is committed. Do not tune the reference spec toward published Tenstorrent numbers. If a
documented behaviour cannot be represented at a given level (e.g. a NoC feature the
reservation model lacks), record it in the prediction file's `unrepresented` field. Do not
drop it.

ADR: docs/decisions/U0015-the-mesh-reference-and-what-it-can-support.md.
```


### U-P16 · U8 · Lane B — The mesh measurement kit, the second validation verdict, and fidelity-level evidence

```text
CONTEXT TO LOAD: CLAUDE.md, measure/README.md, validation/L3_silicon/blackhole/SUITE.md,
validation/ledger/README.md, ADR U0010 (how the first verdict was reached; reuse it). Tenstorrent
tt-metal documentation: TT-Metalium kernels, the device program profiler, tt-smi. PREREQUISITE:
a host with the Blackhole p100a installed, Ubuntu 22.04 as the card's docs require, and tt-smi
reporting the card. If any of that is not true, stop and say so.

TASK: measure the mesh reference, compare against every frozen prediction set, and let the
ledger say what the native engine, per fidelity level, is entitled to claim.

1. measure/blackhole/: the kit, written and dry-run BEFORE the card is used for real. One
   TT-Metalium program per benchmark in SUITE.md, with profiler zones exactly where SUITE.md
   puts them. The dry run executes on Tenstorrent's functional simulator (ttsim, Apache-2.0)
   where it supports the kernel. ttsim does not model timing, so dry-run outputs are labelled
   SYNTHETIC and are refused by the ledger. Environment capture per result: firmware, tt-metal
   version, clocks as reported, card serial. Timing is device-side only. Where TT-Metalium
   reports op counts, record them for the workload-fidelity check; record whatever device
   counters the card exposes (NoC, DRAM) for diagnostic-fidelity entries; where tt-smi
   exposes board power, record it as coarse energy context, labelled so.
2. Run on the card only after check_ordering passes. Raw results (profiler CSVs as emitted,
   plus the derived durations and the derivation script's hash) are committed immutable under
   validation/L3_silicon/blackhole/results/.
3. Ledger entries, one per (benchmark × prediction source): native at each fidelity level,
   U-C0, and tt-npe. The same key discipline as U-P10, and classes split by mapping match.
4. THE NEW THING THIS VERDICT CAN SAY, which the first could not: whether MORE DETAIL IS
   MORE ACCURATE for this class. Report the error by class for each native fidelity level
   side by side. "Closer" means a lower median |error| in that class; it is reported per
   class and as the median across classes, never pooled. If composite C2 is not closer to
   silicon than level-1, the report says so on its first page. Detail is fidelity, not evidence; this is the one place you can test
   whether it is also accuracy.
5. Gate G7 (execution-plan §4): the same thresholds as G4, applied to native composite C2 on
   the mesh family. Promotion is scoped to the mesh family and the passing classes only.
6. tt-npe vs silicon on NoC benchmarks goes in the report as context, labelled as an L2
   reference's own error. It is not our evidence.

ACCEPTANCE TESTS (write first):
1. The dry run completes and the ledger refuses its SYNTHETIC outputs.
2. Every result file postdates its prediction file (the ordering check is green).
3. The per-level error table exists, with ≥ 3 levels (U-C0 per_op, level-1 fast path,
   composite C2) × all eight classes.
4. G7 is evaluated and recorded either way; promotion, if any, is scoped to the mesh family.
5. A large-core design's request still gets stub from mesh evidence (applicability).

GUARDRAILS: If G7 fails, publish the errors anyway and follow its fail branch. Do not average
across classes or levels to pass. Do not change the engine in this session. Do not let
tt-npe agreement stand in for silicon agreement.

ADR: docs/decisions/U0016-the-mesh-validation-verdict-and-whether-detail-helped.md.
```


### U-P17 · U9 · Lane A — The parallel engine: exact conservative synchronisation, then a labelled lax mode

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, build-spec §2.8 (ownership and partitioning) and
§2.9 (parallel execution), ADR U0011, U0012 (the performance baselines), U0013. From rk-sim
READ-ONLY: ../rk-sim/docs/vision/elements_of_parallel_DES.md §§6–15 and 30–38 (partitioning, mailboxes,
epochs, determinism) and docs/vision/rack-to-kernel-24-month-execution-plan.md (E6 and the funded plan's G1).
SST's documentation on conservative synchronisation with link-latency lookahead.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Compare worker/thread/synchronization configurations using the same saved prepared
workload and mapped TaskGraph. Partitioning simulator ownership must not repartition model
tensors or change the declared chip mapping. Record prepared input identity with every run
so timing differences cannot hide a change in the workload producer.

TASK: parallelism INSIDE one simulation, built so that the exact mode is byte-identical to the
single-threaded engine. Only then comes a lax mode, and it is labelled as approximate everywhere it
appears.

1. Partitioning: logical processes are rectangular sub-meshes (row bands first; blocks behind
   a flag). Every owner id belongs to exactly one partition, so the ownership discipline from
   U-P11a becomes the partition boundary, and the owner assertion now also fails a
   cross-partition mutation. Memory controllers, and the shared SRAM when present, may be
   their own partition. A Ramulator 2 instance never ticks past its partition's window end
   (build-spec §2.8), and a controller in its own partition contributes its L_in to the
   lookahead like any other cross-partition link.
2. EXACT MODE: windowed conservative synchronisation. Lookahead L = the minimum latency of any
   cross-partition link, which is router pipeline plus link, and SEVERAL CYCLES on any real
   design. It is not 1, and this is where the vision note's lookahead-collapse premise gets
   corrected in code. Each window [T, T+L): partitions execute independently; cross-partition
   events go into single-producer/single-consumer mailboxes; at the barrier, mailboxes are
   drained and merged in the global total order (t_ps, phase, target, seq). seq for a
   cross-partition event is derived deterministically, NOT from a shared atomic counter
   whose value depends on thread interleaving.
3. Threads: a fixed pool (std::thread::scope), static partition affinity, no work stealing in
   this prompt. Each partition owns its state slice, handed to exactly one thread as &mut, so
   the compiler forbids a cross-partition mutation. No mutex on the hot path; the only
   synchronisation is the window barrier. Mailboxes use std's synchronisation primitives;
   core pinning, or a lock-free crate (crossbeam, MIT/Apache-2.0), only with an ADR. Still no
   unsafe.
4. LAX MODE (a flag, off by default): a synchronisation quantum Q > L. Events that cross a
   partition boundary within a window are delivered at the next window boundary (temporal
   decoupling, as in a TLM-2.0 quantum keeper). EngineResult then reports sync: approx(Q),
   and the composite rule (U-P13d) DROPS THE COMPOSITE TO C1 unless the model card cites a
   measured error-vs-Q curve that covers this Q (U-P18 produces it).
5. The U-P12 metrics become live: cross-thread messages per simulated cycle and sync
   operations per million simulated cycles, recorded for npu-m256 and the 32×32 variant at
   1, 2, 4, 8 and N threads.

ACCEPTANCE TESTS (write first):
1. EXACT MODE IS BYTE-IDENTICAL to single-threaded for every golden request, at 1, 2, 4 and
   8 threads, and under ThreadSanitizer in the nightly job.
2. A loom model of the mailbox protocol (two producers' windows, one merge) yields the same
   merged order in every interleaving loom explores; and a fuzz test with randomised thread
   sleeps produces identical output across 50 runs.
3. The lookahead is computed from the spec, not configured. A test changes a router latency
   and asserts L changes with it.
4. Lax mode at Q = L is byte-identical to exact mode. At Q > L, EngineResult says
   approx(Q) and the composite is C1 without a covering curve.
5. Scaling is recorded, not asserted: the speedup curve at 1..N threads, next to the vision
   note's expectation, whatever it turns out to be.

GUARDRAILS: No optimistic synchronisation and no rollback: the design says so, and adding
it is a new ADR, not a detail. No SIMD, GPU or MPI in this prompt. Never let lax mode be the
default. Never let a result computed in lax mode carry exact mode's composite.

ADR: docs/decisions/U0017-the-parallel-engine.md, with the measured scaling and the
lookahead values for each golden design.
```


### U-P18 · U9 · Lane B — The synchronisation experiment: error vs quantum at a backpressured boundary

```text
CONTEXT TO LOAD: CLAUDE.md, validation/README.md, build-spec §2.9, ADR U0017. From rk-sim
READ-ONLY: docs/vision/rack-to-kernel-24-month-execution-plan.md: E6, the FUNDED PLAN's gate G1 (not this plan's G1) and its
criterion. That is the company's central technical bet, and this prompt is where it gets
measured. docs/context-and-decisions.md §2.3 (why the prototype deferred it).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Compare worker/thread/synchronization configurations using the same saved prepared
workload and mapped TaskGraph. Partitioning simulator ownership must not repartition model
tensors or change the declared chip mapping. Record prepared input identity with every run
so timing differences cannot hide a change in the workload producer.

TASK: measure whether lax synchronisation survives a BACKPRESSURED boundary, publish the curve
whatever its shape, and wire the result into what the composite fidelity may claim.

1. PRE-REGISTER FIRST, in docs/decisions/U0018-the-error-vs-quantum-curve.md, committed
   before any run:
   - the boundary: core partitions ↔ memory-controller partition with closed-loop credit
     backpressure. It is deliberately the hard one: an uncontended boundary passes and proves
     nothing;
   - the operator mixes: at least one real decoder-layer mix, decode and prefill;
   - the quantum values: at least 5, from Q = L to Q = 64 L;
   - the metrics: wall-clock speedup over exact mode, and the deviation of the escalated
     component's latency DISTRIBUTION (p50 and p99 of memory-request latency, and per-query
     duration), not only the mean;
   - the pass criterion, copied from the funded plan's G1 (its E6) and labelled there as that plan's
     own assumption: ≥ 5× over conservative at ≤ 10% latency-distribution deviation.
2. validation/sync/: the harness runs exact and lax modes on the same jobs, reports
   error-vs-speedup over Q with exact mode on the same axes, and writes a hashed curve file the
   model card can cite, scoped by boundary type, design family and operator mix.
3. Enforcement: provenance/ accepts a lax-mode composite C2 ONLY when the job's Q, boundary type
   and family fall inside a cited curve's measured range AND that curve's deviation at Q is
   within the pre-registered bound. Otherwise C1, with the reason in the fidelity detail.
4. Publication: docs/results/sync-error-vs-quantum.md, with method, data, the curve, and the
   verdict against the pre-registered criterion, written the same day the curve exists,
   pass or fail. The funded plan calls a dated result "the cheapest fundraising asset", and
   says to publish it "regardless of outcome".

ACCEPTANCE TESTS:
1. The pre-registration commit precedes every curve file (git-ordering check, reusing
   check_ordering).
2. The curve exists over ≥ 5 values of Q on ≥ 1 real operator mix, with exact mode on the
   same axes.
3. A lax job inside a covering curve's range keeps C2; one outside drops to C1; both are
   asserted in one test so neither half can pass alone.
4. The publication file exists and states pass or fail against the pre-registered criterion
   in its first sentence.

GUARDRAILS: Do not choose the boundary, mixes or threshold after seeing data. Do not report
only the mean deviation, because tails are where decoupling breaks. Do not tune Q per
workload to make the curve look better. This prompt MEASURES whether lax parallelism is
justified; it does not make lax mode the default.

ADR: docs/decisions/U0018-the-error-vs-quantum-curve.md (the pre-registration, then the
verdict appended).
```


### U-P19 · U10 · Lane A · RUNS IN rk-sim — Characterized C2 cost (rk-sim P18)

```text
CONTEXT TO LOAD: rk-sim's CLAUDE.md, rk/engine/README.md, rk/engine/f0/compute.py (IterationCost
and iteration_cost, the seam this prompt substitutes behind), rk/engine/f0/power.py
(operating_point), rk/engine/registry.py, rk/engine/orchestrator.py (dispatch, _collectives,
_fidelity_map), rk/engine/f1/serving.py (how R1 consumes IterationCost), rk/schema/, ADRs 0011,
0015, 0016, 0018, 0021, and THE rk-sim BOUNDARY ADR ADMITTING CHARACTERIZED C2 TABLES. The
draft is in the uarch kit at rk-sim-side/decisions/DRAFT-admit-characterized-c2-tables.md.
It must be ACCEPTED, and its schema PR MERGED, before this prompt starts: build-spec §1.3 rules
out memoization surrogates for the prototype, and a characterization table is one. From
rk-uarch, READ-ONLY: docs/decisions/U0001 (the nine rules), contract/schema/*.json at the
contract version the boundary ADR names, contract/fixtures/interpolation_vectors.json, and one
committed table.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR (in rk-uarch, READ-ONLY): docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Read the accepted U0003 and later public contract revisions as well as U0001. Preserve
and validate the table's declared preparation identity/scope through the adopted boundary.
This prompt remains table consumption at runtime: no live rk-uarch, compiler or preparation
invocation, and no new tensor sharding in the reader. A future rk-sim prepared-input exporter
is a separately approved integration; it is not a prerequisite or an implicit part of P18.

TASK: a component whose effective compute fidelity is C2 is priced, every iteration, from a
uarch cost table instead of the C0 roofline, with the R1 DES unchanged.

1. rk/engine/characterized/ (new; engine layer; Lane A): loader.py reads a table file, verifies
   table_hash by recomputing it, checks the contract MAJOR version, checks the table's
   spec_hash against the component's characterization.spec_hash and the table's tp against
   the plan's tp for that component, and returns a frozen object.
   cost.py: CharacterizedIterationCost, satisfying EXACTLY the interface f1 already calls on
   IterationCost (decode_s, prefill_s, decode_counts, prefill_counts, collective_s, spill_s,
   power_point, kv_byte_per_context_token, tp, and whatever else f1 reads). If f1 annotates
   the concrete class, introduce a Protocol in f0/compute.py that both satisfy, and change
   ONLY the annotation in f1. The DES's behaviour does not change.
2. THE NINE RULES, each with its own test:
   a. A ROW IS ONE SHARD. THE TP DIVISOR IS 1. `_time_s` divides by tp today; carrying that
      into the table path double-counts tensor parallelism silently. Collectives still come
      from the orchestrator's _collective_coefficients, exactly as for C0.
   b. Canonical compositions: decode (B, T) maps to the table directly; prefill (T, Q) maps to
      n = T²/Q, L = Q/T. The table's measured interpolation_loo, composition_reduction and
      layer_reuse errors are copied into run warnings, each stating its own provenance
      (ADR 0027).
   c. The envelope is checked at BUILD time, where UnsupportedPrecision is raised today, from
      the workload's reachable (B, T, Q) region. Never discovered mid-run; never extrapolated.
   d. DVFS: duration_at(f) interpolates the table's frequency axis. A plan that declares DVFS
      on a component whose table lacks a frequency axis is a HARD ERROR. Never evaluate at
      f = 1 silently.
   e. Counts map onto rk-sim's Channel names; ext_counts are carried through to channel
      diagnostics as coverage "unmodelled" until rk-sim adopts SRAM/NoC channels.
   f. One chip, one set of facts: the component's top-level params must equal
      derive_rk_params of the spec the table cites. Check the spec hash, and compare the
      table's provenance.params with the component's params field by field
      (ParamsMismatch).
   g. Steady state: an R1 run reads initial_state: steady tables. A cold table in an R1 run
      is InitialStateMismatch at build time.
   h. KV layout: the table's kv_layout.block_size_tokens equals the plan's block size, or
      KvLayoutMismatch at build time.
   i. tp: the table's tp equals the plan's tp for that component, or TpMismatch at build
      time. A table is never rescaled to another tp.
3. Registry: a C2 row for (compute_resource, compute, C2) naming
   rk.engine.characterized.cost, with requires=("characterization",). ADR 0016's three sets:
   C2 joins the ADMISSIBLE set via the schema PR; it is BUILT for a component only if that
   component carries a characterization. The orchestrator applies ADR 0011's asymmetry:
   system default C2 on an uncharacterized component → STUB with a warning naming the missing
   table; per-instance override C2 on it → NoTableForComponent, a hard error.
4. Badges: the uarch model is a named contributor whose badge is the table's model_card
   badge. Stipulated params are excluded from combine() and recorded in conditional_on (the
   schema PR landed the types; you wire them). A proposed design is capped at estimated. A run
   that mixes a C2 compute component with a C0 one emits a warning that says the comparison is
   biased AGAINST the detailed part, and why.
5. Fidelity map: the C2 row reports compute "C2", model_origin "uarch@<version>",
   fidelity_detail and table_hash (fields from the schema PR). config_hash includes the table
   hash through the component descriptor.
6. Golden: tests/golden/scenarios/asic_c2.yaml (lane-writable): 8 × a proposed ASIC at C2 from
   a committed fixture table under tests/fixtures/characterization/, R1 runtime. The expected
   file is human-owned; the test SKIPS WITH A REASON until `make golden-update` is run and
   committed with an ADR. Bump ENGINE_VERSION.

ACCEPTANCE TESTS (write first):
1. TP, HAND-COMPUTED: a two-row fixture table built for tp = 8, in a plan with tp = 8.
   decode_s equals the row's duration plus the collective, NOT duration/8 plus collective.
   The expected value is worked on paper and committed.
2. PLUMBING WITHOUT UARCH: generate a table from rk-sim's own C0 closed form on a grid. At grid
   points the characterized cost reproduces IterationCost exactly (==), and between points
   within the declared interpolation error. This proves the path independently of uarch's
   physics. The characterized cost also reproduces rk-uarch's
   contract/fixtures/interpolation_vectors.json within 1e-12 relative.
3. Envelope refusal at build time; spec-hash mismatch; params mismatch; tp mismatch;
   contract-major mismatch; non-finite row; DVFS without a frequency axis; a cold table in
   R1; a KV block-size mismatch: one test each, each raising the named error.
4. Default-degrades / override-raises asserted as a pair in one test.
5. Every existing golden is byte-identical. The C0 and R0/R1 paths are untouched.
6. R1 with a C2 component: determinism, Little's law and conservation (P5's tests) still hold.

GUARDRAILS: Never import rk-uarch; rk-sim reads files. Do not change f1's scheduling
semantics. Do not extrapolate, clamp, or refit a table. Do not edit tests/golden/expected/ or
CLAUDE.md. Do not touch web/: that is P19.
```


### U-P20 · U10 · Lane B · RUNS IN rk-sim — Stipulations through the product, and the chip views (rk-sim P19)

```text
CONTEXT TO LOAD: rk-sim's CLAUDE.md (invariants 2, 3 and 10), web/README.md,
web/src/components/Badged.tsx, FidelityPicker.tsx, CoverageBanner.tsx, web/src/lib/fidelity.ts,
web/src/screens/{Builder,Results}.tsx and the Compare and Assumptions screens from P9b,
rk/api/README.md, tests/api/test_contract.py (canonical routes), ADRs 0009, 0011 §5, 0016,
0021, 0027, the accepted boundary ADR, and P18's handoff.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR (in rk-uarch, READ-ONLY): docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Use the accepted table/preparation provenance from the boundary schema. Where mapping
assumptions affect interpretation, disclose whether preparation was local, externally
supplied or delegated to a fork. Do not imply a compiler mapping was reproduced solely from
a policy name, and do not build a compiler or prepared-input exporter in this UI prompt.

TASK: a stipulation reaches a human as what it is — a scoped question, not a weak claim — and
a C2 component shows its evidence where the user is looking.

1. make gen after the schema PR, so web/src/types.ts carries SourcedValue.kind/rationale,
   Metric.conditional_on, the fidelity map's model_origin, fidelity_detail and table_hash,
   and ComponentDescriptor's design_status and characterization.
2. <Badged> gains the conditional state: when conditional_on is non-empty, it renders
   "conditional · N stipulations" next to the badge, and its popover lists each stipulation
   with its rationale. CONDITIONAL IS A SCOPE STATEMENT, NOT A WARNING. It is not amber, not an
   alert and not dismissable. The error band renders as the band or as "unknown", NEVER "±0".
   Keep every switch over Calibration exhaustive (a `never` default), so the compiler finds
   every place a new state must render.
3. Builder and inspector: a design_status: proposed component is labelled "proposed design".
   The inspector lists claims and stipulations under separate headings. The fidelity picker
   offers C2 ENABLED only for components whose fidelity_available includes it (ADR 0016:
   selectable = built). For any other component C2 renders disabled, with the reason, not absent.
   Update web/src/lib/fidelity.ts's three sets and tests/unit/test_fidelity_ts_sync.py
   together.
4. A chip panel in the inspector and Results for a C2 component: composite fidelity plus the
   per-subsystem detail vector; the model card (badge, evidence scope, validated band or
   "unknown"); uarch version and table hash; tp; measured interpolation, composition,
   layer-reuse and cold-vs-steady errors; the initial state and KV block size; energy marked "unverified" while
   the card has no energy evidence; flop-parity deviations; the conditional_on list. EMBED
   IT IN THE EXISTING COMPONENT/RUN RESPONSES. Do not add a route: test_contract.py freezes the
   canonical route list, and the
   boundary ADR does not amend it.
5. Compare: when the two sides differ in compute fidelity (C2 vs C0), a banner states that the
   comparison is biased AGAINST the detailed part, because it charges stalls the roofline cannot
   see, and shows the C2 part's own u_c0 duration beside it, so the detail delta is visible.
6. Assumptions page: stipulations of proposed components under their own heading, "Design
   stipulations — these define the question; they are not claims." Never listed as STUB or
   ESTIMATED.
7. Tell uarch: its vendored round-trip test asserts rk-sim refuses a stipulation. After this
   lands, that assertion is false by design. Record it in your handoff so uarch updates the
   test and its ADR together.

ACCEPTANCE TESTS (write first):
1. vitest: <Badged> with conditional_on renders the marker and count; with none it renders
   exactly as before (the existing tests are unchanged and still pass).
2. No rendered text anywhere in the app contains "±0" for a C2 component: a DOM text scan in
   the Results and chip panel tests.
3. The C2 picker is enabled only for a characterized component; it renders disabled, with the
   reason, for an uncharacterized ASIC and for the H100.
4. The Compare banner appears for C2 vs C0 and is absent for C0 vs C0: asserted as a pair.
5. Assumptions: stipulations appear under their own heading and never under STUB or ESTIMATED.
6. test_contract.py's route list is unchanged.

GUARDRAILS: Numbers render only through <Badged>. Never improve a badge in display code.
Do not add routes. Do not fill ci95 from a deterministic run. No new UI dependencies:
Tailwind defaults, as web/README.md says.
```


### U-P21 · U11 · both — Demo hardening

```text
CONTEXT TO LOAD: CLAUDE.md, README.md, build-spec §1.2 (the acceptance demo: the definition of
done), docs/execution-plan.md U11, docs/how-it-works.md, every docs/reviews/*-closeout.md.
From rk-sim READ-ONLY: docs/prompts/P13-demo-hardening.md (same discipline).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Demonstrate both the standalone model-based path and replay of a saved prepared bundle
on the cold setup. Neither path requires a live rk-sim clone or a compiler to produce uarch
results. Verify replay with local producers disabled, including input-content/cache identity;
keep the later rk-sim table-consumption demo independent of preparation services.

TASK: a stranger can run it, and either founder can perform the build-spec §1.2 demo cold,
including the other lane's parts.

1. docs/demo-script.md: build-spec §1.2 turned into exact commands and clicks, with the
   expected output of each step pasted from a real run and the hashes of every table it
   touches. When a step's output legitimately changes, the script changes in the same commit.
2. Seed data: every design, reference, study and fixture table the demo needs, committed, with
   hashes; `make demo-data` rebuilds and verifies them.
3. Error states: every error in contract/errors.py has a CLI message a stranger can act on.
   Test each by invoking the CLI and matching the message.
4. README: a stranger reaches a built table from a clean clone following only the README,
   engine image included, and the README says how long each step takes on the reference box.
5. docs/what-this-is.md: what a uarch number is, what it is not, the two validation verdicts
   with their scopes and bands, the sync curve's verdict (or that U9 was deferred, and why),
   the stipulation ceiling, the
   declared omissions, and the state of energy evidence, in one page.
6. A fresh session runs STANDING-how-it-works-refresh.md afterwards; not this one.

ACCEPTANCE TESTS:
1. Each founder performs the demo cold, twice, with no crashes, and the log is committed.
2. A person who has not seen the repo reaches a built table from the README; their notes are
   committed.
3. Every contract error has a CLI message test.
4. `make demo-data` verifies every hash.

GUARDRAILS: Change no model, threshold or badge rule in this prompt. A demo that needs one
changed has found a bug: file it and stop.
```


### U-REVIEW · standing — Adversarial review (review → response → adjudication, per lane, every sprint end)

```text
U-REVIEW IS A THREE-STAGE LOOP AND NO STAGE IS A HUMAN. Read the stage that is yours.
Stage 1 REVIEW (a cold agent) -> Stage 2 RESPONSE (the authoring session) ->
Stage 3 ADJUDICATION (the reviewer again).

=== STAGE 1 · REVIEW — you are a fresh session that did not write this code ===

You are reviewing rk-uarch's Sprint U<N> diff against docs/execution-plan.md §3 (that sprint's
block) and its prompts in docs/prompts/. Do not trust commit messages or the author's review
records; they are claims to verify.

YOU MUST NOT HAVE WRITTEN THE CODE YOU ARE REVIEWING. If you find you already know it because
you wrote it earlier in this conversation, SAY SO AND STOP. A clean verdict from the author is
worse than no review, because it will be believed.

CHECK, in order:
1. Does the sprint's joint exit criterion actually run, on the Linux box, from a cold clone?
   Execute it. Paste the output.
2. Does any number reach a human without its badge? Grep report templates for raw values;
   run `uarch report` on the sprint's tables and scan for "±0"; check CLI output paths.
3. Did any golden change? If so, is there a docs/decisions/U*.md for it, and does it match the
   diff?
4. Numerical smells: units missing from names; cycles crossing out of engines/ or native/;
   time converted anywhere but next_edge(); MACs counted as one op; the tp rules (divisor 1,
   table tp equals plan tp); seeds not
   plumbed into a new randomness source; unordered iteration reaching output; a diagnostic
   or energy figure rendered as 0 where the level does not model it; an engine reading a
   DRAM preset the spec does not name; `unsafe` Rust outside crates/uarch-ramulator-sys, or a
   HashMap or HashSet on a path that reaches output. Re-derive the
   three most-touched formulas from their docstrings and say whether the code matches.
5. Provenance: any stipulation outside hw/designs/? Any claim without a source? Any reference
   spec that loads with a stipulation? Any derived value whose kind or provenance is better
   than its worst input?
6. Evidence: any model card promoted without ledger entries? Any promotion wider than its
   entries' scope? Any error band of zero? Any prediction file edited after its freeze commit?
   Any L3 prediction without its mapping match and initial state? Run check_ordering yourself.
7. Fidelity: any composite C2 that breaks build-spec §2.4's rule (compute below 2, NoC or DRAM
   below "1+ts"), any engine whose levels were not derived from §2.4's table, or any lax sync
   result without a covering curve? Any C2 row faster than its u_c0_duration_s?
8. Determinism: build one golden table at --workers 1 and --workers N yourself and diff the
   bytes. From U9, also at 1 and 4 threads in exact mode.
9. From U6: run the native-vs-fork harness on one matched configuration yourself.
10. Scope: anything built that build-spec §1.3 lists as out? Name it.
11. READMEs: does any directory's README now describe something that is no longer true?

WRITE THE REPORT TO docs/reviews/U<N>-lane-<A|B>-review.md, incrementally, as you finish each
check. Number findings F1, F2… and label each BLOCKING or NON-BLOCKING with evidence:
file:line, pasted output, or a reproducing command. Do NOT fix anything. Style is out of scope.
You are producing evidence, not a verdict.

=== STAGE 2 · RESPONSE — you are the session that wrote the code ===

Read the report. Verify each finding yourself first: a reviewer can be wrong. Then write
docs/reviews/U<N>-lane-<A|B>-response.md answering EVERY numbered finding:

  APPLIED   what changed, and the test that now covers it. No regression test, not applied.
  REJECTED  why, in a sentence a stranger can evaluate. Reproducing the finding and showing
            it does not hold is a reason; "disagree" is not.
  DEFERRED  what it waits on, and where that is recorded. "Later" is not a plan.

Put every BLOCKING finding you rejected or deferred at the top, under a heading that says so.
You may not close a finding by editing the report.

=== STAGE 3 · ADJUDICATION — the reviewing session reads the response ===

Check three things and nothing else: (a) every numbered finding has a row; (b) each REJECTED
reason addresses the finding rather than restating intent; (c) each APPLIED change has a test
that fails without it. Check one at random by reverting it in a scratch copy. No new findings.
Append ACCEPTED, or NOT ACCEPTED with the rows at fault.

=== WHAT NO STAGE MAY DO ===

No stage tags the sprint. Humans tag u<NN>-end after the adjudication verdict is ACCEPTED.
```


### STANDING · every sprint end — Refresh docs/how-it-works.md

```text
CONTEXT TO LOAD: CLAUDE.md, docs/how-it-works.md, docs/execution-plan.md (STATUS and the sprint
just closed), the sprint's docs/reviews/ closeout and handoffs, and the code the sprint touched.

TASK: amend docs/how-it-works.md so it is true of main at the tag you are given, and is
readable by someone returning to the other lane after a month.

1. Amend it; do not append. Every section earns its place. A subsystem that grew earns the
   lines that explain it; a section describing something that no longer exists is deleted.
2. Real numbers: quote at least one real table row, with its hash, for every engine the
   sprint touched, and the current composite fidelity and badge of each golden design.
3. Say what the numbers do not claim: the stipulation count, the evidence scope, "unknown"
   error bands.
4. Link every claim about behaviour to the test that pins it.

ACCEPTANCE: every file path and command in the document exists and runs at the tag; every
quoted number is reproduced by the command next to it.

GUARDRAILS: Documentation only. Change no code, fixture or ADR.
```
