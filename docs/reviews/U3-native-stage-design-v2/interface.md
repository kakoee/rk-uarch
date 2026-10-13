# Revised mapped-input / job / result proposal

**Design only. No live schema is changed; examples are readable field projections,
not generated, authenticated or currently executable artifacts.** Version names below
are proposed reservations and must be checked for collision at schema review.

## Revision boundary

Amendment baseline: `30812dfc322b742b81521e350d7d5b541221ca0d`.
Stage 2 corrects admission, clock crossings, zero-duration arbitration and carrier details
without installing them. E3 compute arithmetic is retained; revised E4 is normative here.
[Delivery](delivery.md) controls ordering and [verification](verification.md) controls
first-use deadlines. Field tables are a schema proposal, not an installed/tested patch.
M prepares the exact installable patch for human review; K1 can proceed independently
once its semantics and exact toolchain/license decisions are accepted.

## Additive carriers and identity

Reuse [OpSpec](../../../contract/uarch_contract/operators.py), PreparedOp/PreparedOpV2,
Producer, RankScope, Padding, Replication, KvAccess and RotaryCoefficients. Do not create
a second operator language or a Rust sharder. The missing TaskGraph is a mapping of
those operators, with explicit job IDs and coverage, not a replacement model graph.

| Proposed carrier | Required fields and semantics |
| --- | --- |
| `MappedBundle`, `format=uarch-prepared/3` | `bundle_hash`, `producer`, full `hardware_spec`, `hardware_spec_hash`, `assumptions_hash`, `rank`, `mapping_scope=task_graph`, `mapping_policy`, `scope`, `source`, `admission`, `points`. No default fields. |
| `scope` tagged union | `component`: `operator_version=prepared-op/1`, 1–16 existing v1 PreparedOp objects, exact ordered op IDs, `repeat=1`, no layer/model claim; `prepared_model`: immutable original v1/v2 bundle and selected point hashes, complete graph coverage, never a sliced model relabeled complete; `kernel_fixture`: test-only fixed delays; `transport_fixture`: test-only explicit DMA/unicast/barrier jobs without compute, with empty operator coverage. Production B admits component only; test B admits component, transport_fixture and kernel_fixture under the admission matrix below. K2 admits kernel_fixture only. K1 has private unit fixtures, no public carrier. |
| `source` tagged union | Component and transport/kernel fixtures: null; explicit ops/jobs are authoritative work. Model: original format, bundle_hash and entire original authenticated bundle (including coefficients for v2); no rewriting analytic mapping/assumption fields. New mapping assumptions are separate. Rust uses resolved content; model intent is provenance/validation, not instructions to rebuild it. |
| Mapped point | `payload_hash`, `point_id`, exact component or original query identity, `frequency_ratio`, `initial_state`, `priming_iterations`, `task_graph`. Component `initial_state=cold`, priming=0. `fixture_resident` allowed only with test admission. Model steady later requires 1 or 2 priming iterations; no inherited stateless interpretation. |
| `TaskGraph`, `format=uarch-taskgraph/1` | `graph_hash`, `buffers`, `jobs`, `dependencies`, `coverage`, `arbitration`. Ordered arrays sorted by unique ID; edges sorted by (before,after), no duplicates/cycles/dangling IDs. `coverage` partitions operator extents and group/repeat instances, with no dropped or duplicate region. |
| `MappedEngineJob`, `protocol=uarch-engine/3` | `job_hash`, `bundle_hash`, `point_hash`, `request_hash` (null for component), `assumptions_hash`, `engine`, full `mapped_point`, full `workload_closure`, numeric `hardware`, `hardware_spec_hash`, `rank`, `precision`, `fidelity_detail`, `frequency_ratio`, integer domain `freq_hz`, `initial_state`, `priming_iterations`, `seed`, `admission`, `state_model=resource_intervals/1`. Fixed-delay test admission at K2 or B uses `state_model=fixed_delay/1` and `fidelity_detail=null` in its strict fixture-only variant. |
| `MappedEngineResult`, same protocol | `result_hash`, `job_hash`, exact engine identity, `scope`, `completion=complete`, `duration_ps` (u64), ordered `completed_jobs`, `admission`, `counts`, `ext_counts`, `work_counts`, `traffic_counts`, ordered `per_op`, `busy_time_ps` by resource, `attribution_ps`, `diagnostics`, `fidelity_detail`, sorted `unrepresented`, deterministic `simulator_metrics`, `trace_hash` or null, and `u_c0_duration_ps` (null for components/K2; separately bound same-work analytic baseline for future model results). No success object on incomplete execution. |

Full numeric hardware includes every resource/clock/topology/capacity and the relevant
SourcedValue leaf path bindings, not merely analytic peaks. Sender and Python admission
resolve it from the authenticated HardwareSpec; Rust validates the join and rejects
unknown/unsupported fields. Use integer/rational service values rather than lossy float
periods. Eight channel IDs 0…7 bind to controller `channel_id//2`; 256-byte HBM stripes
use `(address_bytes//256)%8`, with local channel addresses derived by stripping that
interleave. This proposed mapping law belongs in assumptions; it is not an inferred preset.

Engine identity is proposed as `name=native`, `version=native-stage/1`, with model
`name=native-intervals`, `version=1` and separate implementation hashes for engine and
model. Fixed-delay test admission uses model `fixed-delay/1` and null fidelity_detail; its results cannot carry subsystem fidelity or be
credited as B subsystem evidence (they remain executable B regression results). Full-array throughput is not used to backfill completed counts.
Fixture admission uses the exact admission/profile binding below; normal prepare/table and
product report paths refuse verification-only inputs and results, regardless of filename.

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
  q_projection; K2 refuses compute. Padding is internal issued capacity, distinct from
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
- `fixed_delay`: `duration_ps`, owner/resource and dependencies, permitted only for kernel_fixture test admission at K2 and retained at B.
   A clock-edge fixture additionally carries `domain`, `start_ps`, `n_cycles`
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

The following is exhaustive for the frozen npu-l4's 59 SourcedValue leaves. T=timing,
C=capacity/admission, I=identity/coordinates only, U=unrepresented effect. All fields still
bind hardware identity; U does not allow a required unsupported operator. `i=0..3` expands
the twelve controller leaves. Structured/nonnumeric fields follow the table.

| Paths (prefixes expanded literally; braces enumerate suffixes) | Class / rule |
| --- | --- |
| clock_domains.{core,noc,dram}.freq_hz | T: resolved integer clocks and named-domain next_edge |
| cores.grid.{rows,cols} | C/I: core membership, coordinates/routes |
| cores.core_type.matrix_engine.array.{rows,cols} | T/C: E3 wave/issued lanes/tile bounds |
| cores.core_type.matrix_engine.macs_per_cycle.bf16 | C: require rows×cols=65536 for the B law; independent compute bound, not a second duration formula |
| cores.core_type.matrix_engine.{accumulator_bytes,operand_buffer_bytes} | C: live accumulator 4mn and staged X+W must fit; operand capacity is required, not unrepresented |
| cores.core_type.matrix_engine.operand_bytes_per_cycle | T: core-domain staging/drain |
| cores.core_type.vector_engine.ops_per_cycle | U: B vector work refuses |
| cores.core_type.sram.bytes | C: live allocation union/offset bounds |
| cores.core_type.sram.banks | I/U: bank coordinates validated as below; bank contention unrepresented |
| cores.core_type.sram.bytes_per_cycle_per_bank | U: no bank timing |
| cores.core_type.dma.{engines,max_outstanding,request_bytes} | C/T: IDs/credits/fragment cap, with bounded round-trip concurrency |
| cores.core_type.dma.bytes_per_cycle | T: shared core-port service |
| cores.core_type.job_overhead_cycles | T: compute jobs only in this proposed B law |
| sync.barrier_latency_cycles | T: NoC-domain barrier release |
| nocs[0].router_latency_cycles | T: hop arrival via next_edge |
| nocs[0].{link_bytes_per_cycle,virtual_channels,buffer_flits} | U: no bandwidth/VC/flow-control model |
| memory.interleave.granularity_bytes | C/T: stripes/request fragmentation |
| memory.controllers[i].{read_queue_depth,write_queue_depth,noc_credits} | U: physical queue/backpressure unrepresented |
| memory.dram.channels | C/T: channel IDs, total-bandwidth division |
| memory.dram.bw_bytes_per_s | T: rational service cap |
| memory.dram.capacity_bytes | C: allocated HBM ranges must fit; no out-of-capacity component execution |
| memory.dram.organization.{ranks,bank_groups,banks_per_group,row_bytes} | U: no DRAM row/bank timing |
| memory.dram.timing.{t_rp_cycles,t_rcd_cycles,t_cl_cycles,t_rfc_cycles,t_refi_cycles} | T: named-domain latency; refresh ratio derates bandwidth, no refresh event claim |
| formats.bf16.accumulate_bytes | C: require 4, accumulator footprint |
| formats.bf16.block_scale_bytes | C: require 0; block-scale payload not admitted |
| energy.pj_per_mac.bf16; energy.pj_per_byte.{sram,noc_hop,dram}; energy.voltage_ratio.1.0; static_power_w; tdp_w | U: energy/voltage/thermal unmodeled |

Metadata (id/design_status and every source/kind/rationale/unit/date/provenance) is identity/
provenance admission, not timing. `formats.bf16.bytes=2` and matrix `dataflows=[weight_stationary]`
are capability rules. `scales_with_core` resolves frequency ratios; the exact resolved
clock map binds admission. `shared_sram=null` is physical absence. NoC topology/direction,
controller attaches, interleave scheme and sync mechanism bind route/barrier admission;
controller scheduler/page_policy strings are unrepresented timing controls. Expand every
U path (and sram.banks as unrepresented timing) in `unrepresented`; null all corresponding
diagnostics. Unknown extra fields refuse schema admission.

Bank coordinates: B models contiguous equal bank regions, size=sram.bytes/banks (require
integer division), `bank=floor(offset_bytes/bank_region_bytes)`. Buffers may span banks;
validate every covered range against total SRAM. A bank tag names the starting bank, not
exclusive occupancy. Baseline bank region=524288 bytes, so all C1/slot1 starts are bank0;
an offset524288 must name bank1. This placement convention is an assumption, not bank-conflict
timing or physical-address evidence. An in-range wrong starting bank refuses InvalidBank.

Canonical owner enumeration: create tuples in the following fixed class order, then sort
numeric coordinate keys lexicographically and assign dense IDs starting at 0:
matrix(core), vector(core), sram(core), dma(core,engine), dma_port(core), channel(channel),
router(noc,row,col), link(noc,src_core,dst_core), barrier(barrier_job_id).
Cores are row-major `row*cols+col`; channels0..7 attach controller=floor(channel/2) in the
spec's controller order. DMA engine IDs flatten `core*engines+engine`. Links are legal
directed nearest-neighbor pairs; their owners are identity/dispatch only at NoC0, never
link reservations. Barrier IDs use canonical UTF-8 job ordering. Fixture-only owner lists
for fixed_delay are supplied unique numeric IDs sorted ascending; no arbitrary production
owner insertion. Include `owner_enumeration=native-owners/1` in assumptions and the complete
owner map in job/result observation identity; reordering source JSON cannot change it.

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
{"completion":"complete","duration_ps":702000,"completed_jobs":["g0.t0"],"counts":{"matrix_ops":2097152,"vector_ops":0,"memory_read_bytes":0,"memory_write_bytes":0},"ext_counts":{"sram_read_bytes":139264,"sram_write_bytes":8192,"noc_flit_hop_count":null},"work_counts":{"format":"uarch-native-work-counts/1","completed_mac_count":1048576,"issued_matrix_ops":2097152,"vector_arithmetic_ops":0,"cast_ops":0},"traffic_counts":{"format":"uarch-native-traffic-counts/1","read_payload_bytes":0,"write_payload_bytes":0,"read_transaction_bytes":0,"write_transaction_bytes":0,"unicast_payload_bytes":0},"attribution_ps":{"compute":670000,"memory":0,"noc":0,"sync":0,"overhead":32000}}
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
| R06 | C1 operator normalization, kv_write or attention_fused; separately rotary_embedding in v1 OpSpec | Schema-valid non-q_projection refuses `UnsupportedOperator`; rotary_embedding refuses v1 schema first (`InvalidOperatorSchema`), never weaken OpSpec |
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

At R for the required reference suite, and T for the declared product, preserve the original v2 closure and add a mapped representation of **every**
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
report/provenance eligibility proposals; no automatic card attachment. R requires a reviewed benchmark/point-result carrier where installed scopes cannot express
the signed suite; no table contract is required simply to execute benchmark points. T in
U7 requires a separately reviewed request/table version (proposed 0.4, reservation pending),
interpolation vectors and public v2 product integration. No live protected file or source-bound artifact is changed
here. Exact installable schema review, version reservation and U0002 lifecycle are explicit
remaining dependencies, not completed by these field tables.

## Mandatory observations reconciled with B

Add required `observations`, tagged `format=uarch-native-observations/1`, to the proposed
result. Each section has `status=observed|unrepresented` and a reason when unrepresented.
An observed empty list means no activity, not a nonempty qualifying test. K2 observes
jobs/events/resources; B resource_intervals also observes DMA, allocation and represented
service queues. Retained B fixed_delay regressions observe the same mechanisms as K2.
These deterministic records participate in result identity independently of optional
Chrome trace. Future compression cannot discard records needed by required checks.

| Section | Proposed record fields | Semantics |
| --- | --- | --- |
| events | event_seq, observation_ordinal, t_ps, phase, target_id, kind, job_id (nullable) | Actual dispatch order and ownership; K1 uses private equivalent observations |
| jobs | job_id, op_id, group_id, repeat_index, tile_origin, tile_extents, ready_ps, start_ps, end_ps, owner_id, blocking_predecessor_ids, useful_matrix_ops, issued_matrix_ops, vector_arithmetic_ops, cast_ops | Null nonapplicable op/group/tile fields for transport/kernel jobs; useful work increments on completion, exactly once, separately from input expectations |
| dma | request_id, job_id, dma_engine_id, direction=read\|write\|unicast, source_buffer_id, destination_buffer_id, payload_bytes, transaction_bytes, credit_acquire_ps, issue_ps, complete_ps, credit_release_ps, route_id | B supports whole-request completion, no retries/cancellation/multicast; credit acquired on issue, released at final commit/ack; unicast has null credit times when it consumes no DMA credit |
| transfers | request_id, boundary_id, direction, payload_bytes, transaction_bytes, enter_ps, leave_ps | Named control volumes: read issue→SRAM commit, write issue→HBM acknowledgement, SRAM unicast issue→destination commit; per-hop observations are never added as unique delivered payload |
| allocations | buffer_id, space, owner_id, offset_bytes, size_bytes, allocate_ps, free_ps, initially_live, last_consumer_ids | Half-open live ranges; null free_ps means resident at end; initial buffers count at t=0; no live aliases at B |
| queue_membership | queue_id, item_id, population=waiting\|service\|inflight, enter_ps, leave_ps, owner_id, clock_domain | B: bounded DMA inflight credits, channel bandwidth waiting/service, shared core-port waiting/service. Blocked submission differs from admitted occupancy. Physical DRAM queues/NoC VCs remain unrepresented |
| resource_intervals | owner_id, job_id, start_ps, end_ps, activity, limiting_resource_id; channel service additionally service_start_ps_ratio/service_end_ps_ratio | Utilization uses interval union/window/capacity, not overlapping sums; no NoC0 link-busy diagnostic |
| critical_path | start_ps, end_ps, cause_job_id, predecessor_id (nullable), limiting_resource_id, category=compute\|memory\|noc\|sync\|overhead | Causal partition of [0,duration_ps), including waits caused by resource predecessors; equal longest causes choose lowest job ID then resource ID |

Timestamp fields are integer picoseconds; exact channel service ratio pairs preserve
bandwidth time before quantization. Domains reference resolved clocks. Events retain
dispatch order; other sections sort by canonical ID/time. For window [a,b), initial
inventory is immediately before events at a; include a and exclude b events, then sample
final inventory. Per named boundary/direction, separately for payload/transaction units:
`final_inflight = initial_inflight + issued - completed`. B's 32+128−64=96-byte example
is a window identity, not a new request-size fixture. Compute consumption is not conserved
DMA inventory: reused inputs and newly produced outputs invalidate the old U-P6 shorthand
'DMA in = compute consumed + written back'. This explicit reconciliation requires B and
coordinator acceptance; it does not edit that prompt silently.

SRAM occupancy is the union of live allocation ranges, including initial/second-slot
reservations. Queue area equals the sum of clipped membership intervals, including
initial and terminal jobs. For arrivals 0/2000 ps and departures 4000/6000, area over
[0,8000) is 8000 request-ps; over [1000,5000) it is 6000. Dropping the initially present
job must fail. Finite-window identities and minimum observations are required at B.
Separately, stationary Little's law ≤1% is due at its first claim, normally U6/G5-correctness
or earlier if relied on, after freezing a nonempty stable window, population and boundary
treatment. Zero-flow mean residence is null. No completed-window identity passes the
stationary law, and required B observations cannot wait for U6 Chrome tracing.

### Zero duration, zero hops and phases (Stage 2 A-F4)

Every owned fixed_delay, including duration zero, joins its owner's FIFO-ready queue.
It may complete inline only **after owner grant**, never on dependency readiness alone.
At grant it consumes no positive service interval, records exactly one completion and
then enables dependents. Example: a(owner0,3000 ps) and p(owner1,1000 ps) start at 0;
z(owner0,0 ps) waits for p; c(owner1,2000 ps) waits for z. z is ready at 1000 but grants/
completes at 3000; c ends at **5000 ps**. Bypassing the owner makes 3000 and must fail.
The original two-zero-milestone→3000 case remains, but is not the discriminator.

Same-core zero-hop unicast is admitted at B in component/test transport scope only when
source/destination are distinct nonaliasing ranges on that core, with initialized source,
allocated destination, valid lengths,
and declared dependency/coverage joins hold. No NoC cycle or alignment is charged for
h=0. It is an instantaneous transfer, not an implicit view or an in-place alias exception;
record its payload commit and dependencies. It has no link reservation at NoC0. Actual
DMA port service still applies for DMA jobs regardless of route length.

At each timestamp drain phase0 completions, phase1 initial readiness, phase2 grants/issues,
then phase3 observations/end. Within each phase queued events use (target,seq); seq is
allocated at scheduling. Zero completion/dependent readiness induced by phase2 is processed
as a deterministic inline closure before the next grant: collect newly enabled jobs in
canonical ID order, enqueue on their owners, grant eligible owner queues in canonical
owner order. Repeat until no zero transition remains. Positive work schedules only future
phase0 events. Inline records carry the current phase and increasing observation ordinal;
they are not retroactive phase0 events. Bound zero transitions by DAG jobs; cycles refuse.

## Additional refusals and installation boundary

R01–R16 remain. R17: a B resource_intervals fidelity other than compute1/NoC0/DRAM0/exact/layer_reuse=false
refuses `UnsupportedFidelity`. R18: another production hardware hash, even correctly
rehashed, refuses `UnsupportedHardware`. R19: cancellation/retry, K spill, noncontiguous
layout, bias/sparsity or work_repeat=2 refuses its named unsupported capability before
events. R20: missing required observations refuses `IncompleteObservations`; do not
backfill input totals. R21: zero/negative dimension or frequency, negative delay or time
overflow refuses; zero fixed delay follows the milestone convention above.
K2 refuses subsystem compute/DMA jobs. Synthetic clock/credit/capacity cases use the profile below with proposed-design
stipulations and rationales; they do not expand production admission.

R needs an exact benchmark scope for each operator/fused unit/layer and its full closure;
an arbitrary OpSpec list cannot claim a full decoder. New benchmark/request carriers,
INT8 and TPU reference representation require separate decisions before execution.
T completes full layers/head/tail at its consumer envelope. No protected carrier changes
are applied here; M must propose the actual schema, fixtures, observation/admission tests
and canonicalization vectors before human installation. Old roots remain strict.

Before M installation, B completes the U0023 dependency audit and presents policy/migration
choices. If repair is not ready, Javid explicitly decides to retain current enforcement
and budgets M/K2/B adoption cycles. No narrowed support inventory, stale receipt acceptance
or automatic generation/adoption is included.

## Proposed-M dependencies for B's audit

Bounded A consultation against published main
`8867c0c86cddf17adafafe1717f57d8bc220a2d1`, B's
[audit](../U3-B-artifact-dependency-audit-v1/README.md),
[support delta](../U3-B-artifact-dependency-audit-v1/support-delta.json) and
[unaccepted migration](../U3-B-artifact-dependency-audit-v1/migration.md).
B's 97→52 inventory (39 retained, 58 removed, 13 added) is its audited baseline proposal,
not M's future count or an installed policy. Coordinator B-C1/B-C2 findings remain B's
separate correction task. No patch is applied, importer executed or artifact produced here.

**Observed current relationships.** `scripts/u2_inputs.py` imports
`uarch_contract.exports` and `rkuarch.hw.export`; the latter imports `hw.derive`, which
imports `rkuarch.engines.protocol.ResolvedHardware`. Importing these submodules executes
parent initializers. `uarch_contract/__init__.py` re-exports prepared, hardware, model,
request/table, export, evidence and report-context carriers. B therefore retains it and
those reached modules, including `common.py`, `hashing.py`, `exports.py`, `prepared.py`,
`operators.py`, `hardware.py`, `precision.py`, `request.py` and `table.py` as whole files.
`rkuarch`, `hw`, `engines` and `scripts` initializers are also retained; the inspected
initializers currently contain only docstrings, plus ENGINE_VERSION in `rkuarch`.
Changing a reached file matters even when its newly added function is not called.

**Planned source/edge inventory.** Names below make the existing M inventory concrete;
new filenames and placement remain proposed until the exact protected schema patch is
reviewed. This does not alter stage semantics or authorize these files to be installed.

| Planned file or relationship | Intended imports/use | Potential effect on B's proposed support closure |
| --- | --- | --- |
| `contract/uarch_contract/mapped.py` | Reuse common FrozenModel/strict scalar types, hashing, HardwareSpec, OpSpec, PreparedOp/Producer/RankScope/KvAccess; import `rotary_v2` carriers for the proposed immutable v2 model closure | M importing a retained carrier alone does not create a reverse edge from generator roots. But any reached initializer/carrier importing mapped brings mapped and its transitive imports into support; then currently removed `rotary_v2.py` may re-enter too |
| `contract/uarch_contract/__init__.py` | Prefer explicit mapped-submodule imports at callers; no new root re-export is needed merely for that access. Whether the human schema patch adds public root exports remains unresolved | A new `.mapped` re-export is a direct inclusion edge from an already retained file. Its bytes and full new closure bind; do not exempt it as convenience-only |
| Shared `common.py`, `hashing.py`, `prepared.py`, `operators.py`, `hardware.py`, `precision.py`, `request.py`, `table.py`, `exports.py` | Prefer reuse without widening old roots; any needed shared validator/type refactor must be listed in the exact patch | All are already retained. Byte changes trigger drift; imports of mapped/rotary/shared helpers add edges even inside functions or TYPE_CHECKING. Do not narrow support by saying only the new carrier uses a changed helper |
| Proposed `contract/uarch_contract/generate_mapped.py`, `contract/schema/mapped/`, `contract/fixtures/mapped/`, protected admission/canonicalization tests | Dedicated schema/fixture workflow imports mapped roots, reads/checks its own outputs; no registration in old analytic schema roots is proposed | A dedicated unimported generator is not automatically reached under the proposed policy, but is covered by current broad Python enumeration. Importing it from a reached initializer/common module would enter the audited closure; dynamic schema registration would need explicit policy review, not presumed support |
| Proposed `src/rkuarch/engines/protocol_mapped.py` and `schema/mapped/` | M boundary definitions/mirrors import mapped/common/fidelity/count carriers; K2 later consumes the same boundary | If existing retained `engines/protocol.py` or `engines/__init__.py` imports the new module for dispatch/re-export, it enters support. Prefer additive direct imports; final dispatch location is still a schema/wiring decision |
| Proposed `src/rkuarch/mapping/component.py`, `mapping/policies/ws_rowsplit.py`, `workload/mapped.py` | Component producer/mapper, export/import loader, strict closure validation; direct mapped/protocol imports plus sourced hardware resolution | Currently unimported mapping/workload initializers and their modules are outside B's proposed closure only while no reached root imports them. A shared initializer/loader/derive import can bring them in. Exact paths/helpers are not implemented |
| `src/rkuarch/hw/derive.py`, `hw/export.py`; possible additive mapped hardware resolver | M needs full resolved resource/topology data beyond existing analytic ResolvedHardware. Prefer a separately named resolver, with exact placement decided in M | Editing either retained file binds the changed whole file. Importing an additive resolver there brings its closure in even if oracle formulas stay unchanged. Moving ResolvedHardware or common validation can change the existing export→derive→protocol chain |
| K2 `src/rkuarch/engines/native/` runner/parser and later native serde fixtures | Consume M carriers/fixtures; no execution added to M | Follow actual imports through retained engines/derive/initializers. Pure Rust files are not Python import edges, but helper/build/data/lock dependencies require review; neither current nor proposed policy promises zero K2/B cycles |

Here **mapped export** means serializing prepared work; existing `hw.export` means
component truth/oracle projection. These are different functions, not proof of independent
dependencies. Shared canonicalization, source resolution, export carriers, initializers
and schema registration can connect them. M proposes no oracle formula or staging-root
change, but any such change discovered in implementation must return to B's audit.

**New non-import reads proposed for M.** Loader inputs include saved mapped bundle/point
JSON, explicit full hardware specification, assumptions, and referenced closure content;
model-scope validation reads supplied v1/v2/coefficient data only where that scope is
admitted. Component M has no RoPE execution or generated coefficient default. Local
mapping reads the selected explicit HardwareSpec and component OpSpecs. Canonical/schema
checks read mapped schema mirrors and hand-authored JSON/refusal/canonicalization fixtures.
An implementation-identity inventory may read producer/validator source and environment
or lock records; its exact scope still needs design review. No plugin search, implicit
home-directory configuration, network fetching or new environment-selected defaults are
proposed. That is an intended boundary, not an audit of code that does not yet exist.

These data are preparation/test inputs or outputs unless reached by nominal input staging,
generation or strict verification. B must classify each actual read and any glob/registry
that makes it reachable. A mapped schema mirror being an output does not make a later
validator read irrelevant. New runtime read paths are not discovered completely by the
proposed static import walker: register reviewed files/families explicitly if consumed
from a reached module, and add missing/changed/substituted-data controls. Existing B data
families already bind npu-l4 YAML, locks, component precision/execution inputs, retained
provenance, `a2-export` JSON/YAML/PIN and canonical model-shape mirrors. Adding/changing
files within those families affects inventory even without a Python import; placing a
mapped fixture there would not be unrelated. New proposed mapped schema/fixture locations
are outside those particular globs, which is not an exemption if a reached reader uses them.

**Uncertainties and handoff to B.** Exact root re-exports, shared-validator placement,
hardware resolution, dispatch location, generators/fixture paths and file-read inventory
are unresolved until M's concrete schema patch. A supplies that patch's imports (including
parent initializers, local/conditional/TYPE_CHECKING edges), data paths and environment
inputs; B then states the actual retained/added edges, rechecks static-analysis limits and
adds relevant/unrelated-change controls through the public support loader. No projected
closure count or zero-adoption promise is made here. Do not apply B's patch or treat its
unimported-native-file test as proof that these actual mapped relationships are unrelated.

Live U0002 still enumerates all Python files under src/rkuarch, contract/uarch_contract
and scripts, so planned additive Python files change current support even with no new
import edge. A narrower accepted policy plus real human migration would be needed to use
B's proposed reachability rule. Before protected M install, resolve exact repair/migration
or explicitly retain current enforcement and budget source-bound cycles. This prerequisite
does not become a new dependency for unrelated K1 design preparation.

## Stage 2 exact admission proposal (A-F1)

Add strict `admission` to bundle/job/result and hashing: `{checkpoint: K2|B,
invocation: production|test, profile_hash: Hash|null, case_id: string|null,
eligibility: component_only|verification_only}`. Host invocation must match these fields;
`--fixture-mode --test-profile <manifest>` is required for test. An ordinary path/flag or
a different hardware hash alone cannot confer test permission. K1 remains private only.

| Checkpoint | Invocation | Scope/state | Hardware/frequency | Result eligibility |
| --- | --- | --- | --- | --- |
| K1 | internal unit test | private delays, no public job | accepted private clock fixtures | no public result |
| K2 | test | kernel_fixture / fixture_cold, priming0 | exact frozen profile tuple | verification_only, fixed-delay/null fidelity |
| K2 | production | any | any | UnsupportedCheckpointScope |
| B | production | component / cold, priming0 | frozen npu-l4 hash, ratio1, all domains1GHz | component_only, no table/model row |
| B | test | component / cold or fixture_resident, priming0 | exact frozen profile tuple | verification_only, subsystem fidelity unchanged |
| B | test | transport_fixture / cold or fixture_resident, priming0 | exact frozen profile tuple | verification_only; no compute jobs |
| B | test | kernel_fixture / fixture_cold, priming0 | exact frozen profile tuple | verification_only; retained fixed-delay regressions, null fidelity |

A owns these semantics; B supplies requirements/catalogue and rationales. Proposed
`NativeTestProfile`, `format=uarch-native-test-profile/1`, fields: own `profile_hash`,
`semantics_revision`, `owner`, `entries`. Each sorted unique case entry binds exact
checkpoint/scope/state, hardware_spec_hash plus full HardwareSpec, frequency_ratio and
resolved integer frequency map, fixture graph_hash/point_hash, allowed job kinds,
expected_outcome (success or named refusal), seed and case-selection revision. Hash the
manifest without its own hash. The point does not embed admission/profile_hash; bundle
and job do, avoiding a profile↔point hash cycle. No '*' values, ranges or unhashed variants
are admitted by a frozen entry. Result echoes admission exactly and includes it in hash.
Negative cases bind the intended malformed mutation to a valid control via B's signed
case manifest; malformed input need not become a valid point to test refusal.

Allowed variant families for the future catalogue: max_outstanding1/2/32; accumulator
131072/262144; nonzero clock variants (core0.8/1/1.2/2GHz, NoC1/1.2GHz, DRAM0.9/1GHz)
and core frequency ratios {1,2} with resolved scales_with_core; DRAM bandwidth and operand/
DMA rates×1/×2; positive router/job/barrier/DRAM latency×1/×2; refresh omitted only as a
fault (not an accepted alternate expected answer); TDP100/200; symmetric core relabeling
and one unused column (2×3) for the idle-core test with explicit matching routes. B may
propose further values needed for 24 distinct cases, but they need review/freeze rather
than blanket arbitrary-hardware admission. Unsupported NoC bandwidth effects stay not_run.
Each actual hardware variant is a proposed-design stipulation with a rationale such as
'isolate outstanding-credit response' or 'exercise unequal-clock rounding', never a sourced
chip claim; eventual files belong under B-owned hw/designs/test-fixtures/ only after review.

Before public tests, freeze B's exact specs/rationales, profile bytes/hash, graphs, seeds,
expected records, A semantic revision and review decision. Bind their hashes in suite and
job identities before qualifying replay. Discovery needs its own approved finite catalogue
or prospectively bounded generation plan followed by exact concrete freeze; it cannot use
an execution-time mutable allowlist. This session installs no specs/profile or corpus.

Normal component prepare, characterize, table, report/card attachment must reject
verification_only manifests and all registered test-spec hashes, even if copied/renamed or
presented without the profile. This requires a reviewed admission registry of catalogue
spec hashes before fixture installation; registry changes bind loader identity. Only dedicated
synthetic fixture specs enter the test-only registry. Baseline npu-l4 may appear in a test
profile without becoming test-only hardware; its test invocation/result still binds
verification_only, while the exact cold production tuple remains admitted. Production
B still uses its single pinned hash. Verification records may cite test results as scoped
verification, but product reports, model predictions and table rows cannot consume them.
Refusals: missing/mismatched profile/case→TestProfileMismatch; unlisted tuple→TestVariantNotAdmitted;
wrong checkpoint/scope→UnsupportedCheckpointScope; state/priming mismatch→UnsupportedInitialState;
test spec sent to ordinary preparation→TestOnlyHardware; test result sent to product path→TestOnlyScope;
rehashed result relabeled production→AdmissionMismatch. R17/R18 govern production only;
test admission permits only the declared B fidelity or fixed-delay null fidelity, not C2.

## Stage 2 count carriers and validation order (A-F5)

Component `operator_version=prepared-op/1` selects existing PreparedOp/OpSpec; do not add
rotary_embedding to that root. Prepared_model carries its explicit immutable source v1/v2
and dispatches the appropriate validator. Syntax and version union checks happen first;
then validate all content hashes and nested closure (including v2 coefficients), followed
by invocation/profile/checkpoint/hardware/state admission, then graph/resource/count
semantics before events. Thus malformed v1 rotary fails schema; valid v1 normalization
reaches UnsupportedOperator at B; a valid complete v2 closure reaches UnsupportedWorkloadScope,
but tampered v2 coefficients first fail CoefficientHashMismatch. Fixtures must target the
intended layer, and semantic attacks rehash only the identities necessary to reach it.

Reuse current strict Counts and ExtCounts without adding keys: Counts memory_read/write_bytes
are completed HBM **payload**, vector_ops=arithmetic+casts. ExtCounts requires all three
fields including noc_flit_hop_count=null at NoC0. Numeric serialization follows those
carriers (finite nonnegative numbers); counters internally use checked integers. Add strict
`work_counts` (`uarch-native-work-counts/1`: completed_mac_count, issued_matrix_ops,
vector_arithmetic_ops, cast_ops, all nonnegative integers) and `traffic_counts`
(`uarch-native-traffic-counts/1`: read_payload_bytes, write_payload_bytes,
read_transaction_bytes, write_transaction_bytes, unicast_payload_bytes, all nonnegative
integers). Useful matrix_ops=2*completed_mac_count, never issued padded work. Duplicate or
incomplete completion inventories refuse. No native carrier validator recomputes duration
by calling analytic production code. Components retain u_c0_duration_ps=null.

For cold m3/k5/n7: Counts reads100/writes42, ExtCounts SRAM reads100/writes42 with null
NoC flits; work_counts completed_mac_count105/issued_matrix_ops393216/vector/casts0;
traffic payload100/42, transactions512/256, unicast0. For resident C1, the projection above
has traffic all zero and SRAM139264/8192. These are consistent **field projections**, not
full live jobs/results, authenticated files or permission to weaken old strict roots.

## Stage 2 observation envelope (A-F10)

Keep all required observations, deterministic record ordering and result binding. At maximum
B (16×4 tiles, m=k=n=256), X+W+Y=393216 bytes/tile and 1536 requests/tile: 98304 requests,
25165824 payload bytes. Four minimal records/request already mean393216 records, about79.7
MiB using the review's explicit string/number widths; actual output is larger. JSON trees,
parser copies, source closure and event storage add memory. This is an estimate, not a
measurement or proof that512MiB suffices. For the described read/write B lifecycle budget
up to32 observation records/request plus16/job and8/buffer as a planning allocation
(≤3145728 request records at maximum); implementation must enumerate event/interval kinds
and refine this estimate before full-size performance budgeting. No records may be dropped
to fit it. Exhaustion is incomplete/refusal, never success with missing evidence.

Narrow only the prospective 5s/512MiB **performance fixture**, not production B admission:
K2 up to256 fixed-delay jobs/1024 edges; B exactly one cold E3 C1 tile (576 requests), its
resident counterpart, and E4 transport bursts up to33 requests, each separately invoked.
The 576-request case has2304 minimum records (~0.47MiB with the same width assumptions),
planning ≤18432 request records plus jobs/buffers; profile cap65536 total records and16MiB
canonical observation bytes, enforced only for this performance fixture. Do not infer total
RSS from encoded bytes or call these proposed caps measured. Maximum-size B correctness
still needs complete observations and an authorized adequate-memory environment; separate
full-size wall/RSS/record budgets are required before any performance measurement/claim.
No automatic output truncation, summary substitution or table-scope reduction is permitted.


Stage 2 extends the proposed-M audit inputs with `NativeTestProfile` manifests, test-spec
registry, full fixture HardwareSpecs and expected-record/case manifests. Proposed locations
are `contract/fixtures/mapped/profiles/`, `hw/designs/test-fixtures/` and a reviewed registry
alongside the M admission carrier; exact paths remain a schema decision. Registry and
profile reads are non-import dependencies. Any reached common validator, initializer,
export or loader that imports the profile carrier or reads these data adds corresponding
support obligations under the proposed audited policy; all added Python is already bound
by live U0002. B must audit these edges and direct-entry import shadows against its corrected
Stage 2 proposal before M installation. Neither the historical52-entry inventory nor a
future corrected count is a promised closure for M. No registry or hardware is installed.
