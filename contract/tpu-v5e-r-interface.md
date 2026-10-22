# TPU v5e R interface amendment — pre-measurement model

The user approved the nominal model and semantic interface at
`180c6b9fb5df6af46f5df3601c7c895a79ac8d23`, including the explicitly labelled STUB estimates,
as the baseline for the one substantial U4b implementation milestone. This document and
the concrete additive carriers accompany that implementation proposal. Protected installation
remains human work under the existing procedure; no new approval process is introduced.
The scope remains 52 units. Final benchmark acceptance, device observability, silicon
accuracy and U4 closure are not asserted.

## Compatibility and ordinary execution

Keep ordinary /4, component model 2, TaskGraph/1 and observations/3 behavior unchanged.
Add R roots `uarch-prepared/5`, `uarch-engine/5`, `uarch-taskgraph/2`, model
`native-intervals` version `3`, engine `native-stage/3`, and R observations/4 in the same
package and native executable. Use the actual installed package version. The R admission
values are checkpoint `R`, invocation `production|test`, eligibility
`reference_suite|verification_only`; test pairs only with verification_only. Numeric STUB
reference estimates are permitted in ordinary production, not restricted to test invocation.
Unsupported semantics and missing required inputs still refuse before events.

Reuse ordinary software/producer versions, hardware/request/input/result data hashes,
rank, assumptions, mapped points, coverage, buffer lifetimes and original mathematical
source closure. R mathematical closure reuses the v2 graph/op/coefficient fields, with
the stated R operand/vocabulary extension and an explicit selected single decoder group.
It does not require constructing an old PreparedBundleV2 whose HardwareSpec demands
physical clocks: never fill a dummy legacy hardware object to obtain mathematical inputs.
New R preparation emits this closure directly; importing an existing v2 source preserves
its original data identity without pretending it was produced for different hardware. A whole-model request cannot silently lose its embedding/head work.
Preserve the provenance of existing v2 artifacts without adding executable/source/build
hashes to ordinary execution. No review records, HostRecords/selectors, startup assurance,
source tracing or development checkout is a runtime dependency. Replay uses supplied data,
not a regenerated workload or coefficient table.

## Finite reference and provenance fields

Add a scoped `TpuV5eReference` branch, identity `tpu-v5e`, design_status=`reference`, instead
of relaxing all existing HardwareSpec fields. Its numeric fields use the **unchanged**
SourcedValue semantics: finite numeric value and unit; claim/spec_derived with a source for
published facts, or claim/stub with source=null, date=null, rationale=null for reasoned
pre-measurement estimates. The estimate's basis and limitations belong in model assumptions
and development documentation, not claim.rationale. No new provenance kind; no stipulations
on reference hardware. An arithmetic allocation of a published peak remains STUB where the
allocation/service interpretation is assumed. Do not demand measured/published provenance
for every required internal parameter.

Required numeric fields (the nominal values/bases are in the bounded U4b model proposal):

| Group | Fields |
| --- | --- |
| Published facts | `tensorcore_count`, `mxu_count`, `mxu_rows`, `mxu_cols` (count); `bf16_peak_ops_per_s`, `int8_peak_ops_per_s` (op/s); `hbm_peak_bytes_per_s` (byte/s); `vmem_capacity_bytes`, `smem_capacity_bytes` (byte) |
| Capacity estimate | `hbm_capacity_bytes` (byte) |
| Matrix estimates | `bf16_mxu_mac_per_s`, `int8_mxu_mac_per_s` (MAC/s); `matrix_fill_equivalent_macs` (MAC-equivalent, service only) |
| Local service estimate | `vmem_bytes_per_s` (byte/s) |
| HBM estimates | `hbm_latency_ps`, `hbm_issue_interval_ps` (ps); `hbm_max_outstanding` (count) |
| Vector estimates | `vector_tile_ps`, `vector_group_startup_ps` (ps); `reduction_cost_ratio`, `exp_cost_ratio`, `reciprocal_cost_ratio`, `rsqrt_cost_ratio` (ratio) |
| Control estimates | `scalar_op_ps`, `kernel_startup_ps`, `barrier_latency_ps` (ps) |

These are 9 fact and 17 estimated leaves in the nominal proposal. Counts/byte capacities
are strict positive integers; rates and nonzero nominal service parameters are finite
positive numbers, represented exactly as rational service values when resolved. No
hardware clock is inferred from peaks or populated with 1 Hz. No null numeric SourcedValue
is introduced. A missing required field refuses with its name; a numeric STUB does not.
Unknown unused physical clock/channel/transaction/bank/energy properties are named as
unrepresented, not represented by a numeric sentinel. Result diagnostics that the model
does not compute remain null. Enumerate the actual consumed STUB leaves for UNKNOWNS at
prediction freeze; the 17-leaf model inventory is not automatically every job's read set.

The ordinary mapped assumptions carry the finite policies below plus allocation budgets
and limitations, using a new model-specific assumptions revision. No external documentation
file or reviewer record is consulted to execute a valid job. Policy values and numeric
inputs participate in existing data identities; there is no new authority manifest.

## Mapped work, precision and resources

Use the same OpSpec/PreparedOp and TaskGraph vocabulary, extended additively. Keep existing
projection/decoder and v2 rotary mathematics. Add the five required microbenchmark OpSpec
names: `stream_read_sum` (BF16 X[E] to FP32 scalar, E casts/E-1 adds), `stream_fill`
(runtime BF16 scalar to distinct Y[E]), `stream_copy` (disjoint BF16 X/Y[E]), `paged_gather`
(BF16 K/V pages, explicit int32 indices, valid extents, distinct BF16 contiguous outputs),
and `scalar_add` (two FP32 scalar inputs and one FP32 result). No second workload IR.

Isolated BF16/INT8 matrix controls reuse projection dot semantics with explicit M/K/N.
Add int32 only to R storage/accumulator dtypes, not rk-sim's generic compute PrecisionFormat.
Raw signed INT8 inputs in [-7,7], K<=4096, INT32 accumulation/output have no scales,
requantization or hidden BF16 output conversion. BF16 final conversion occurs after the
complete K chain. Projection-to-RoPE's declared intermediate BF16 rounding point remains.

R matrix compute adds `matrix_engine_index` 0..3 with core_id=0. Output tiles (M<=1024,
N<=128) round-robin the four owners in stable order. K slices <=128 stay on that owner,
cover each reduction element exactly once and share one live partial buffer. Physical K/N
are 128; M is the actual streamed row count. Useful/issued coverage, array padding, causal
masking and conversion boundaries are explicit. Graph admission checks disjoint complete
M/N/K partitions and dependencies, not merely equality of count sums.

Reserve each 512 KiB logical accumulator window inside the shared 96 MiB VMEM allocation
budget, not in an invented physical accumulator capacity. HBM/SMEM model budgets are
12e9 B / 512 KiB. Double-buffer operands within that same VMEM namespace. Each K slice
writes the partial; later slices read it; final conversion reads it once. Charge these
local transfers once. Register/dedicated-accumulator details remain unrepresented. Budgets
are explicit mapper assumptions, not hardware claims. Infeasible supplied mappings refuse;
only a newly supplied explicit spill/retile mapping can change placement.

Vector tasks bind mathematical op/member IDs, BufferRanges, logical last-two-axis shape,
leading multiplicity, typed primitive counts, reduction axes/stages and explicit fusion
group. Closed primitive classes: add, subtract, multiply, compare, select, negate,
reduction_sum, reduction_max, exp, reciprocal, rsqrt, cast, broadcast and index. Casts bind
both storage dtypes. FP32 scalar math maps to a 1x1 vector shape; scalar/index/control
work uses the control owner. Validate typed counts against bound mathematics rather than
trusting caller durations or total-count assertions. Fusion may remove only declared
materializations, never mathematical work or required rounding. Process 8x128 vector work
tiles with at most 64 KiB transient logical scratch reserved inside VMEM. This is a software
limit, not a physical register-file capacity; extra materializations/spills are explicit.

Buffers/ranges retain lifetime and ownership rules; spaces are hbm, vmem and smem, with
logical accumulator buffers tagged within vmem. Ordered transfer spans bind source,
destination, direction, owner/op and payload. Split at maximum 8192 B, page/buffer boundaries
and holes, preserving tails. These are logical service requests, not physical transactions;
no fictitious 256 B transactions, channel IDs or NoC routes. Page table values and valid
lengths are supplied and checked. Full coefficient data stays in HBM; only small indices/
positions may persist in SMEM. Declared shared coefficient rows require both consumers.

## Exact service laws and state

Use one native scheduler/resource implementation with model-specific service rules:

1. Scalar control serializes matrix-slice/vector-group dispatch, one scalar_op_ps each;
   explicitly supplied index instructions also occupy that owner. Separate MXUs can overlap.
   Each matrix slice occupies its MXU for
   `1e12*(M*K_physical*N_physical + matrix_fill_equivalent_macs)/mxu_mac_per_s` ps after
   staging/dispatch. Four chosen shares cannot exceed the published chip peak. Fill is a
   delay-equivalent penalty and contributes no executed MAC count. VMEM transfers use the
   shared byte-rate server. Explicit graph dependencies and buffer lifetimes limit overlap.
2. HBM issue requires a free logical window slot and its independent issue spacing. Earliest
   bandwidth service is issue+hbm_latency_ps. Reads/writes share a rational bandwidth cursor;
   service is payload*1e12/hbm_peak_bytes_per_s. Hold the slot through integer completion.
   Keep the accepted release/issue tie ordering. VMEM endpoint traffic is charged separately;
   do not also charge control per span unless the graph explicitly contains that work.
3. A vector primitive on logical (r,c) uses ceil(r/8)*ceil(c/128) 8x128 tiles per leading
   index. Cheap operations/casts/broadcast cost vector_tile_ps per tile; exp/reciprocal/rsqrt
   use their multipliers. Group setup is charged once. Pairwise last-axis reduction stage s
   has ceil(L/2^(s+1)) active outputs per row and costs padded tile count times
   reduction_cost_ratio*vector_tile_ps. Stop after ceil(log2 L) stages; L=1 has none.
   Forward odd tails without inventing combines. Keep true useful combines R*(L-1),
   physical issued primitives and reduction critical dependencies distinct.
4. Charge kernel_startup_ps once per declared benchmark invocation, including a full layer
   once, not once per op/HLO/tile. It represents estimated device program entry/prologue/
   exit, not host launch gaps. Only explicit barriers cost barrier_latency_ps; dependency
   edges themselves are free. This boundary is modeled, not observed.
5. Use checked rational ps, ceil at event completion and retain rational bandwidth cursors
   to avoid per-span rounding drift. Preserve the same event ordering/overflow checks;
   B's clocks/next_edge remain unchanged. No Python-supplied durations or second engine.
6. Prime one fixed invocation, report the next, compare two primes. Reset logical context
   and scratch/counters; retain only declared persistent SMEM metadata. Reload HBM payload
   inputs each invocation by default. An explicitly modeled fixed point is not proof of
   actual XLA retention or HBM traffic. Only the reported iteration contributes results.

The nominal parameter catalogue supplies a complete value set including STUBs. Diagnostic
sensitivity alternatives are not accuracy bounds or mandatory extra suite rows. Actual
compiler/event/retention correspondence remains unresolved; do not force its acceptance
by treating a source-level operation name or a warm-up call as an observation.

## Counts, checking and claims

R observations/4 record actual completed typed useful/issued work, semantic convention
counts, conversion work, payload and local traffic, resource/queue/allocation intervals,
state transitions and blocking causes. Keep service-only fill/control startup distinct
from mathematical work. Do not copy the /4 vector-count equality if R semantic conventions
and typed primitives differ. Preserve per-op work even when only enclosing timing exists.
Physical transaction/energy/unmodeled diagnostics are null. The single installed checker
dispatches by admitted model/format, verifies the numerical laws independently, and keeps
B checks unchanged. Canonical data hashes, replay and deterministic output remain required.

Preserve the retained U-C0 aggregate/per-op structure, with a versioned reference resolver:
per-op useful compute time is matrix_ops/chip_peak plus typed useful primitive counts
at effective rates (1024*1e12/vector_tile_ps, divided by special/reduction multipliers;
scalar/index work uses scalar_op_ps). Memory time is mathematical operand HBM bytes/HBM rate for the admitted analytic scope,
not dynamic native reload/partial traffic substituted to force agreement.
Aggregate=max(sum compute, sum memory); per_op=sum(per-op maxima). C0 leaves native fill,
padding, local staging, latency/credits, setup and dispatch/startup unrepresented; do not
insert those native costs into C0 or alter historical analytic profiles. Separately check
native duration against kernel startup once plus max occupied demand across exclusive
native owners. This independent resource-demand lower bound is a test identity, not a
new engine or a replacement for C0. Do not assert the old additive-compute C0 formula is
a lower bound on every legal overlap. Numeric STUBs neither prohibit truthful model-fidelity reporting after applicable
verification nor establish accuracy. Deterministic tests verify the implementation of
assumed laws; they cannot validate those assumptions against TPU v5e. Default calibration
remains STUB, error unknown, energy unverified. No prediction or U4 closure follows from
installing or approving this interface document.


## Concrete implementation choices within this interface

The initial mapper uses packed matrix inputs/weights and explicit transfers when joining
contiguous decoder activations. Output row spans and paged gather layouts are explicit;
there is no free reinterpretation of a packed output as a contiguous tensor. QK uses the
transposed K view defined by its mathematical member; AV uses V. Scores and probabilities
are materialized, with an explicit BF16 conversion before AV. These remain stated mapping
choices, not compiler observations.

Reference transport bounds are 256 MiB input, 512 MiB output, 500,000 tasks and 2,000,000
sequences, with a 600-second ordinary process deadline. Component bounds are unchanged.
The selected largest graph is checked with complete serialized observations. Ordinary
canonical data identities are unchanged; a bounded-block serializer avoids copying entire
reference graphs during hashing. This is data handling, not executable attestation.

`ReferenceSource.scalar_inputs` records RMSNorm epsilon, the chosen attention scale and
raw INT8 input bounds when applicable. Persistent SMEM metadata names its control producer;
priming records before/after residency and fixed logical context. Consumed STUB reporting
includes admission checks and actual service-law reads. A length-one reduction has no
combine stage and does not consume its reduction multiplier.
