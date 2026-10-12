# Checklist for coordinator reconciliation of A's native-stage proposal

Interface-independent questions for the upcoming U-P5/U0011 package under accepted
U0005, U0006 and U0022. No native fields, schema, implementation or review verdict is
created here. Every row below is **pending A's proposal**, then the indicated decision
and future execution. A table of intended tests is not a passed test suite.

| Review obligation | Required proposal detail from A | B's proposed check and discriminating fault |
|---|---|---|
| Stage scope and refusal | Exact U4a hardware/precision/workload slice; operators, initial state, ranks, resource levels; transition to U4b full grid | Positive case for each admitted mechanism; negative case for each advertised refusal. No GEMM-only decoder claim. Compute 1 / NoC 0 / DRAM 0, exact sync, at most C1; unsupported required full-grid work blocks G3, not omitted. |
| Resolved input authority | Minimal mapped extension of accepted vocabulary; prepared-v2/RoPE and v1 admission/refusal, mapping/placement/tiling ownership, complete identities | Saved mapped inputs with producer disabled; no re-sharding/repreparation. Rehash a wrong placement, missing dependency or illegal precision: semantic refusal must still bite. Schema-valid does not mean admitted. |
| Work conventions | Algorithmic MAC/vector/cast counts, physical padded/issued/completed work and any eliminated work distinguished; fusion and repeats explicit | Independent integer ledger by op/layer/rank; dropped work, extra TP division, doubled repeats, omitted Q/K rotation/casts/coefficient access each discriminate. Completed work must follow executed jobs, not echo expected totals. |
| RoPE preservation | Explicit table closure/positions/pairing, new K before store, V unchanged; tail copies, BF16/FP16/FP32 capabilities and refusals | Worked RoPE deltas, C=17→33 new-token invariance, partial tail, identity coefficients still cost work; no native claim from analytic v2 admission. Functional tensor execution remains outside scope. |
| Clock/event kernel | Frequencies/domains, integer edges, deterministic ordering, exact dependency completion and zero-delay handling | Literal edge and long-horizon cases; same-time order, missing dependency, rounded period/extra cycle, overflow refusal. No wall-time-derived expected answers. |
| Compute timing | Declared array, dataflow, fill/ceil-tiling/drain and matrix/vector serialization/overlap | Resident GEMM worked independently from A's declared model; tile boundary just below/at/above dimensions. Wrong ceil/fill or omitted cast work must fail. Cannot choose a pipeline formula before A defines it. |
| Shared resources | Ownership, exclusivity, permitted overlap, scheduling/backpressure; outstanding counts and slot reuse | Independent-resource overlap versus shared-resource serialization; queue limit at 1/2/boundary, dropped completion, ignored DMA cap. No NoC-0 contention or refresh verification unless represented. |
| Limits / baseline | Same resolved work, hardware, precision and memory accounting for floor comparison; supported latency/refresh models | Matched roofline limits and transfer/DMA examples, including U-P8's human-worked latency fixture. C2 never below own C0 remains required when C2 is admitted; it is not a C2 claim for U4a. Investigate any earlier floor mismatch rather than equating mismatched work. |
| Outputs and nulls | What is actually observed at each checkpoint; tracing/busy intervals/queue/storage availability and attribution rules | Window bounds, causality, capacity and attribution only where observed; unmodeled remains null, not fabricated zero. Extra overlap attribution, capacity bypass, null→0 discriminate. Energy remains unverified. |
| Replay and failure semantics | Exact implementation/model/assumptions/toolchain/input identities, deterministic canonical output and refusal/error classification | Changed implementation with same version refuses reuse; tamper/missing-case/partial/skipped-only/failed-relation tests. Valid-output mutant failure distinct from protocol error; SR-C1 non-JSON errors retain diagnostics and finish events. |
| Stage progression | U-P7 mapped hand fixtures → U-P11a kernel → bounded U-P11b → U4b mappings/grid/table; exact checkpoint test owners | U4a public-boundary literal and fault corpus; U4b workers 1/N, table bytes and complete-work counts; debug/release replay. No test-only fixture claims production mapping coverage. U6 qualification adds coverage/diagnostics, not a duplicate engine. |
| Toolchain, cost and host | Pinned Rust/container/licenses, absolute host/workload time/memory budgets, runnable debug tests and environment | No inherited 200-second fork or speed-ratio gate. Later noise-floor measurement and accepted U0012 regression threshold; synthetic 2× slowdown must trip it. Distinguish perf instructions from ns when unavailable; no WSL performance claim. |
| Optional L2 / later silicon | Matched represented work and mapping, reference identity/overlap, prospective scope and criteria | Same-library Ramulator comparison is integration only; absent/unmatched evidence not_run. NoC-0 cannot pass a contention sweep. Admitted failures persist if a tool is later removed; no parameter tuning. Frozen predictions and L3/L4 measurements remain separate. |

## Exact observation premises to reconcile, not assumed telemetry

**DMA/control volume.** Name each boundary and direction (e.g. controller-to-local
storage), payload versus transaction/padding bytes, read versus write, multicast fanout,
retries/cancellations and interval endpoints. Per direction in a lossless window:
`in_flight_end = in_flight_start + issued_bytes - completed_bytes`. With 32 bytes
initially in flight, 128 issued and 64 completed, final in-flight must be 96 bytes.
A missing 32-byte completion or inventory discrepancy must be exposed. If cancellation
or partial completion is supported, define its extra term first. Payload counts across
multiple boundaries cannot be summed as unique delivered bytes without the routing rule.

Compute consumption is not a conserved byte inventory: operands can be reused and
outputs newly produced. SRAM occupancy needs an allocation/lifetime ledger with initial
and final state, sizes, aliases and capacity, separately from DMA transfer accounting.
The old “DMA in = compute consumed + written back” is not generally a valid identity.
A must provide sufficient actual issue/completion/lifetime observations, or mark these
checks unsupported for that stage; no such observations are inferred from analytic counts.

**Queue/clock windows.** For a named queue, distinguish waiting versus in-flight/service,
arrival/admission versus blocked submissions, departures, capacity, initial/final items,
observation interval and clock domains. For finite windows require
`integral N(t) dt = sum over jobs of residence overlap with the window` plus complete
membership; missing initial/final jobs invalidates the naive L=lambda*W calculation.
The U-P6 1% steady-state check needs a prospectively specified stable measurement window,
consistent arrival/departure population and boundary policy, not a finite-run waiver.
Empty queues/zero flow do not supply a residence mean. Resource utilization likewise
needs busy-interval unions/capacity over the same window, not sum of overlapping busy times.
A must say which observations are available and how integer clock edges/time units are
preserved. No observation protocol is invented by this checklist.

## Review and execution dependencies

A owns the exact stage, mapping/protocol proposal, Rust model and prospective budgets.
B owns the independent literal/property/mutant design and evidence reductions; coordinator
reconciles mismatches. Javid decides exact stage/schema and any protected changes. At least
two U-P8 fixtures require actual human working; agent derivations are preparatory only.
Before execution, enumerate every required case and its relation/premise/mode/domain,
control, target fault, cap and expected public outcome. Freeze implementations and concrete
inputs before qualifying replay; retain discovery errors, shrinking calls and failures.
Applicable failure dominates; unfinished/under-budget/unsupported coverage cannot pass.
A separate accepted review is not manufactured by these source hashes or author tests.

The published Linux/runner/schedule/manual-nightly prerequisite still applies before
native implementation/build/performance work. Preparation is allowed while it is pending;
no prerequisite amendment is asserted. Coordinator review of A's package and this checklist
comes next. No optional tool build, schema installation, simulator implementation, report
attachment, silicon campaign, nightly configuration, independent verdict or closure follows.
