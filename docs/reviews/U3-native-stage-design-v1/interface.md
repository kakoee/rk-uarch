# Proposed mapped-input / job / result boundary

**Design only. No live schema is changed; examples are readable field projections,
not generated, authenticated or currently executable artifacts.** Version names below
are proposed reservations and must be checked for collision at schema review.

## Additive carriers and identity

Reuse [OpSpec](../../../contract/uarch_contract/operators.py), PreparedOp/PreparedOpV2,
Producer, RankScope, Padding, Replication, KvAccess and RotaryCoefficients. Do not create
a second operator language or a Rust sharder. The missing TaskGraph is a mapping of
those operators, with explicit job IDs and coverage, not a replacement model graph.

| Proposed carrier | Required fields and semantics |
| --- | --- |
| `MappedBundle`, `format=uarch-prepared/3` | `bundle_hash`, `producer`, full `hardware_spec`, `hardware_spec_hash`, `assumptions_hash`, `rank`, `mapping_scope=task_graph`, `mapping_policy`, `scope`, `source`, `points`. No default fields. |
| `scope` tagged union | `component`: 1–16 PreparedOp objects, exact ordered op IDs, `repeat=1`, no layer/model claim; `prepared_model`: immutable original v1/v2 bundle and selected point hashes, complete graph coverage, never a sliced model relabeled complete; `kernel_fixture`: test-only fixed delays. B admits component only; K admits kernel_fixture only. |
| `source` tagged union | Component: null, since explicit OpSpecs are the authoritative work. Model: original format, bundle_hash and entire original authenticated bundle (including coefficients for v2); no rewriting analytic mapping/assumption fields. New mapping assumptions are separate. Rust uses resolved content; model intent is provenance/validation, not instructions to rebuild it. |
| Mapped point | `payload_hash`, `point_id`, exact component or original query identity, `frequency_ratio`, `initial_state`, `priming_iterations`, `task_graph`. Component `initial_state=cold`, priming=0. `fixture_resident` allowed only with test admission. Model steady later requires 1 or 2 priming iterations; no inherited stateless interpretation. |
| `TaskGraph`, `format=uarch-taskgraph/1` | `graph_hash`, `buffers`, `jobs`, `dependencies`, `coverage`, `arbitration`. Ordered arrays sorted by unique ID; edges sorted by (before,after), no duplicates/cycles/dangling IDs. `coverage` partitions operator extents and group/repeat instances, with no dropped or duplicate region. |
| `MappedEngineJob`, `protocol=uarch-engine/3` | `job_hash`, `bundle_hash`, `point_hash`, `request_hash` (null for component), `assumptions_hash`, `engine`, full `mapped_point`, full `workload_closure`, numeric `hardware`, `hardware_spec_hash`, `rank`, `precision`, `fidelity_detail`, `frequency_ratio`, integer domain `freq_hz`, `initial_state`, `priming_iterations`, `seed`, `state_model=resource_intervals/1`. K uses `state_model=fixed_delay/1` and `fidelity_detail=null` in its strict fixture-only variant. |
| `MappedEngineResult`, same protocol | `result_hash`, `job_hash`, exact engine identity, `scope`, `completion=complete`, `duration_ps` (u64), ordered `completed_jobs`, `counts`, `ext_counts`, ordered `per_op`, `busy_time_ps` by resource, `attribution_ps`, `diagnostics`, `fidelity_detail`, sorted `unrepresented`, deterministic `simulator_metrics`, `trace_hash` or null, and `u_c0_duration_ps` (null for components/K; separately bound same-work analytic baseline for future model results). No success object on incomplete execution. |

Full numeric hardware includes every resource/clock/topology/capacity and the relevant
SourcedValue leaf path bindings, not merely analytic peaks. Sender and Python admission
resolve it from the authenticated HardwareSpec; Rust validates the join and rejects
unknown/unsupported fields. Use integer/rational service values rather than lossy float
periods. Eight channel IDs 0…7 bind to controller `channel_id//2`; 256-byte HBM stripes
use `(address_bytes//256)%8`, with local channel addresses derived by stripping that
interleave. This proposed mapping law belongs in assumptions; it is not an inferred preset.

Engine identity is proposed as `name=native`, `version=native-stage/1`, with model
`name=native-intervals`, `version=1` and separate implementation hashes for engine and
model. K uses model `fixed-delay/1` and null fidelity_detail; its results cannot carry subsystem fidelity or be
accepted as B results. Full-array throughput is not used to backfill completed counts.
Fixture admission requires an explicit `--fixture-mode` invocation and scope binding;
the normal production runner rejects that flag/scope combination for tables.

Every buffer names `id`, `space=hbm|sram|accumulator`, `size_bytes`, `alignment_bytes`,
`core_id`/`channel_id` where applicable, `offset_bytes`, `bank` for SRAM, operand binding,
initial residency and lifetime (producer through final consumers). Cold SRAM begins
uninitialized; compute requires all bound inputs to have completed producing transfers.
Resident fixtures declare preloaded ranges explicitly, never implicit cache hits. HBM page/segment
ranges stay explicit when paged work is later admitted. B uses 256-byte-aligned slot
bases and exact byte lengths; nonoverlapping double-buffer slots, no in-place operands.
Accumulator footprint is `4*m*n`; no K spill at B. SRAM allocations include both input
slots and output lifetime; offsets cannot alias a live buffer. Capacity violations refuse
with resource ID, requested bytes and available bytes. Banks are validated coordinates,
not modeled bank conflicts at compute 1.

Jobs are a strict tagged union, never an unconstrained parameter dictionary:

- `compute`: `id`, `op_id`, group/repeat instance, `core_id`, `engine=matrix|vector`,
  tile origin/extents, physical padded extents, operand-buffer bindings,
  per-operand dtypes, accumulator dtype and `dataflow`. B permits only matrix WS
  q_projection; K refuses compute. Padding is internal issued capacity, distinct from
  any authoritative PreparedOp physical padding. Imported workload padding at B refuses.
- `dma`: `id`, `op_id` or null for transport fixtures, `dma_engine_id`, direction,
  source/destination ranges, ordered fragments with `request_id`, offsets,
  `payload_bytes`, `transaction_bytes`, channel and route references. Recompute fragment
  count; never trust supplied count alone. Each ≤256-byte request occupies one credit;
  short final requests carry exact payload and reserve one 256-byte transaction. A transfer
  crossing a stripe splits there; no request crosses a channel boundary. SRAM bus traffic
  uses payload; DRAM channel service uses transaction bytes. Counts distinguish both.
- `noc_transfer`: transport-only SRAM-to-SRAM unicast job, exact payload, NoC index,
  endpoint cores, dimension-order route. DMA fragments reference a route too: they do
  not schedule a second independent transfer that double-counts the same packet. B
  rejects multicast. Independent unicast jobs pay hop delay only at NoC 0.
- `barrier`: exact participant job IDs and owner; releases after the final arrival plus
  the specified NoC-domain overhead. All consumers depend on release.
- `fixed_delay`: `duration_ps`, owner/resource and dependencies, permitted only for K
  fixtures. A clock-edge fixture additionally carries `domain`, `start_ps`, `n_cycles`
  **inside the engine job**, never the outer prepared/table carriers. Test-only setup
  cannot enter the production model/table path.

`arbitration` is `fifo-ready/1`: oldest ready timestamp, then canonical job ID; channel
admission uses ready timestamp then (DMA engine ID, request ID). Completion events precede
new admissions at the same time. Event phases: 0 completion/release, 1 readiness/arrival,
2 issue, 3 statistics/end. Owner IDs are a canonical resource enumeration; schedule-time
seq breaks remaining ties. Handlers may not schedule into an earlier phase at the same
time. Newly enabled work is processed in canonical ID order. Memory requests have no
cancellation/retry at level 0; unsupported cancellation is rejected rather than invented.

Canonical JSON and hashes reuse [hashing.py](../../../contract/uarch_contract/hashing.py):
normalized validated defaults, sorted keys, compact UTF-8, finite numbers, exact ordered
arrays; hash excluding only the object's own hash. Reject duplicate JSON keys, unknown
fields, invalid integers/booleans, stale or cross-version hashes, invalid closure and
out-of-range u64 times before events. Retain coefficient bit strings exactly. Native's
float spelling must reproduce the accepted canonical vectors, not just serde defaults;
integer/rational resolved hardware minimizes this surface. Golden canonicalization vectors
are a protected proposal, not edits to existing goldens.

Hash graph → point → bundle → selected job → result; original model bundle and assumptions
are leaves. Result has no backward inclusion in its job. The request references the mapped
bundle; the bundle hashes intent rather than a request containing its own hash, avoiding
cycles. Component jobs have null request_hash and cannot become UarchCostTable rows.
Mapping names/versions and placements participate in identity, not just paths. Changing
an engine dependency with unchanged version changes implementation_hash and refuses old
execution bindings. Preserve the normal U0002 support inventory; no new exclusion.

## B hardware representation ledger

Capacity/placement and aggregate operand/DMA service are represented; SRAM bank indices
are validated without bank contention. Return unrepresented paths for
`cores.core_type.sram.banks` and `bytes_per_cycle_per_bank` as **timing** controls,
`nocs[0].link_bytes_per_cycle`, `virtual_channels`, `buffer_flits`, and each
`memory.controllers[i].scheduler`, `page_policy`, `read_queue_depth`,
`write_queue_depth`, `noc_credits`. DRAM organization ranks/bank_groups/banks_per_group/
row_bytes have no row-level timing effect; list their full paths too. `vector_engine`
rate is unavailable for execution at B; nonzero vector workloads refuse. Energy leaves,
static_power_w and tdp_w are unmodeled for energy/thermal prediction. NoC flit/link
utilization, SRAM conflict and DRAM row-hit diagnostics are null, not zero. List exact
resolved leaf paths in emitted results (expand i); do not use broad warnings to conceal
an unsupported required operator. Hardware hash joins still validate every supplied field.
No shared_sram key is omitted unless the actual hardware has none, as this spec does.

## Literal component and mapped example

C1 uses TP1/rank0, excluded collectives, BF16 compute/storage. The semantic payload reuses
PreparedOp with id `g0`, empty dependencies/padding/replication, fusion `none`, kv_access
null, weight_copies=work_repeat=1, embedding_local_tokens=null and this existing OpSpec:

```json
{"operator":"q_projection","dimensions":{"M":16,"K":256,"N":256},"operands":{"X":{"dtype":"bf16","dimensions":["M","K"],"layout":"contiguous","block_size_tokens":null},"W":{"dtype":"bf16","dimensions":["K","N"],"layout":"contiguous","block_size_tokens":null},"Y":{"dtype":"bf16","dimensions":["M","N"],"layout":"contiguous","block_size_tokens":null}},"reduction_axes":["K"]}
```

Operand access: X/W read, Y write. One mapped tile uses core 0, origin M=K=N=0,
extents 16/256/256, WS, FP32 accumulator. SRAM: X offset 0 size 8192 bank 0;
W offset 8192 size 131072 bank 0; Y offset 139264 size 8192 bank 0. Accumulator
is a separate 16384-byte allocation. Slot 1 reserves an identical 147456-byte SRAM
region at offset 147456. Total reservation 294912 bytes fits 16777216. Reserving
an unused slot is capacity, not transferred bytes. Resident fixture preloads X/W
only; cold component creates explicit HBM→X/W jobs, then compute, then Y→HBM.
No HBM transfer is synthesized by Rust.

Resident result projection (future expected answer, not an observation):

```json
{"completion":"complete","duration_ps":702000,"completed_jobs":["g0.t0"],"counts":{"matrix_ops":2097152,"vector_ops":0,"memory_read_bytes":0,"memory_write_bytes":0},"ext_counts":{"sram_read_bytes":139264,"sram_write_bytes":8192,"issued_matrix_ops":2097152},"attribution_ps":{"compute":670000,"memory":0,"noc":0,"sync":0,"overhead":32000}}
```

This projection omits required identity/diagnostic/resource fields for readability.
All final fields must be present in the schema fixture; it is not valid protocol JSON.
Zero means modeled absence for this case, not a substitute for unavailable observation.
C2 changes dimensions to M=3,K=5,N=7: 210 useful ops; 393216 issued padded ops;
100 SRAM read bytes, 42 SRAM write bytes and 547000 ps under the proposed interval law.
C3 uses M=257,K=N=256: rows [0,256) on core0 and [256,257) on core1, with W copied to
both; useful matrix ops=33685504, read bytes=393728, write bytes=131584. No tp division.

## Literal admission/refusal catalogue

Apply mutations to valid controls, recomputing affected hashes when testing semantics;
a stale hash is only an identity test. Each row is a future public-boundary case.

| ID | Literal input/change | Expected disposition |
| --- | --- | --- |
| R01 | Submit `protocol=uarch-engine/1` or `/2` to native | `UnsupportedProtocol`; historical analytic path remains unchanged |
| R02 | Complete v1 model wrapped in mapped/3; native B selected | `UnsupportedWorkloadScope`; no upgrade or complete RoPE claim |
| R03 | Complete v2 with valid RoPE table/positions wrapped in mapped/3 | Same refusal at B, even though analytic v2 can run |
| R04 | C1 with fp16, fp32, fp8 or mixed operand/KV format | `UnsupportedPrecision`, named operand; no substitution |
| R05 | C1 TP8/rank1 or PP/EP/CP metadata | `UnsupportedRankScope` or strict unknown-field refusal |
| R06 | C1 operator normalization, rotary_embedding, kv_write or attention_fused | `UnsupportedOperator`; all other non-q_projection operators likewise |
| R07 | C1 `initial_state=steady`, priming=1 | `UnsupportedInitialState`; never report cold as steady |
| R08 | C1 K=257, M=1025, 17 ops, or imported padding | `UnsupportedShape`/`UnsupportedScope`; no retiling to fit |
| R09 | Tile dataflow output_stationary, multicast=true, or policy unknown@1 | `UnsupportedMapping`; same label on changed placement still changes hash |
| R10 | X at offset 16777216 size 8192; or W aliases live X | `SramCapacityExceeded` or `LiveBufferAlias`, names ranges |
| R11 | Compute references core4; route missing hop; DMA crosses stripe unsplit | `InvalidResource`/`InvalidRoute`/`InvalidTransfer` |
| R12 | g0 depends on missing g9 or on itself; duplicate g0.t0 coverage | `InvalidDependency`/`InvalidCoverage`, before scheduling |
| R13 | Wrong hardware hash, coefficients_hash tamper, changed dependency bytes | Hash/closure refusal; no fallback preparation |
| R14 | C1 frozen mapping retargeted to different hardware; missing requested point | `HardwareMismatch`/`MissingCoverage` |
| R15 | fixed_delay in a component job; resident fixture requested through table | `TestOnlyScope`; no fabricated table row |
| R16 | Incomplete native execution, malformed/nonfinite output or wrong job_hash | No successful result; retained error/diagnostic, not_run for execution error |

## V2 expansion: required before claiming decoder work

At T, preserve the original v2 closure and add a mapped representation of **every**
op/group/repeat, including once-only head/tail. Separate semantic validation from analytic
engine admission through a reviewed shared validator; never weaken `validate_engine_job`
for analytic/2 or strip RoPE and delegate the rest to v1. Full legacy replay remains on
its historical analytic implementation unless a later native legacy scope is accepted.

RoPE requires explicit Q and new-K bindings, both pairings, partial R, separate FP32 RNE
arithmetic, BF16/FP16 casts when admitted, full D tail transfers, coefficient row gathers
and no hidden table generation or cross-node/layer retention. Physical transpose/reorder
from projection layout is a named transfer unless validated as a zero-copy view. Coefficient
bytes are authoritative; mapping names are not proof of model equivalence. Counts/traffic
examples in verification.md are obligations; BF16 rates do not prove FP32 vector/cast rates.

Decode C includes the append. Positions C−1; cache K already rotated with the same profile.
Rotate each local KV head once, including replication; never rotate V, all C cached keys,
page-rounded new tokens or divide local work by tp again. Preserve `embedding_hits` and
selected/equivalent rank rules, including zero local hits, and group.repeat exactly once.
Fused attention is tiled QK→softmax→AV with scores in SRAM; explicit page-granular K/V
reads with last-page valid lengths, one append and no score DMA. Causal versus full-square
work, layouts, padding and precision remain declared. Ragged/offset/sliding-window work
remains refused under U0022 until a separate semantic amendment; this directly affects
composition-error experiments, not just the main grid.

## Result observations, receipts and protected work

Completed records bind op/group/repeat/tile IDs, useful versus issued padded operations,
request/fragment IDs and transferred payload/transaction bytes. Update counters on actual
completion, exactly once; abandoned or duplicated work cannot be backfilled from input.
Expected semantic coverage is checked separately by B against literal formulas. Resource
inventories retain accepted/completed/inflight counts; final inflight=0 is necessary for
complete. Busy time is per owner; its sum may exceed duration with overlap. Attribution
is a selected deterministic causal critical path, not normalized busy time. Equal longest
predecessors choose the lowest job ID. Unmodeled diagnostic fields are null.

Stable simulator metrics include event counts, completed jobs and maximum live events;
host ns, RSS, perf counters, stdout/stderr, executable/image digest and debug/release profile
belong in an operational receipt referencing result_hash. Source/model identity and pinned
compiler/lock identity define the comparable semantic build; debug/release receipts differ,
results must not. Optional trace has canonical ordering and no host timestamps. Trace-enabled
and disabled runs must agree on counts/timing; compare their numerical result projection
because trace_hash differs deliberately, and compare whole bytes within each trace setting.

Human patch inventory for M: additive `contract/uarch_contract/mapped.py` roots and dedicated
schema/fixture generator; new protected schema/fixture/admission tests, closure dispatch for
new roots only; no edits widening old schemas. A-owned protocol/3 and mirrors, mapper,
loader, subprocess/parser and native serde fixtures follow approval. B owns corresponding
report/provenance eligibility proposals; no automatic card attachment. U4b requires a
separately reviewed new request/table contract version (proposed 0.4), interpolation vectors
and public v2 product integration. No live protected file or source-bound artifact is changed
here. Exact installable schema review, version reservation and U0002 lifecycle are explicit
remaining dependencies, not completed by these field tables.
