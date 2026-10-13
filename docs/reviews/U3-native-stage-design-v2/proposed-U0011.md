# U0011 — Progressive native core: bounded component stage and qualification

**Status: PROPOSED exact text; unapplied.** Decision owner: Javid (@jjaffari).
U0005 selects one production engine; U0023 governs sequencing and host prerequisites.
Neither accepts the detailed choices below. Human acceptance must name this package's
reviewed Git revision, scope decisions and any rejected/modified clauses. Exact schema
installation and immutable tool/license closure remain separate release prerequisites.

## Decision

Develop the one Rust timing simulator progressively, retaining Python analytic U-C0,
preparation/mapping and product layers. Rust executes resolved TaskGraphs without model
construction, sharding, hidden remapping or coefficient generation. Functional tensor
execution is outside scope. Observed work comes from completed jobs, not expected totals.

Deliver **M / K1 / K2 / B / R / T**:

- M prepares the mapped schema/fixtures for human installation, then the approved component
  mapper/export/import. U0023's dependency audit/policy decision precedes protected install;
  if repair is not ready, Javid explicitly retains current U0002 enforcement and budgets
  M/K2/B adoption cycles. No implicit exclusions, stale acceptance or automatic adoption.
- K1 implements internal fixed-delay time/events/resources with private unit fixtures after
  accepted semantics and exact toolchain/dependency/license decisions. It may overlap M.
  Private fixtures are not another public workload format or public admission evidence.
- K2 wires approved public JSON/subprocess/result boundaries after installed mapped carriers,
  M fixtures and verified K1. Repeat kernel acceptance and faults publicly; private results
  cannot discharge this requirement. No subsystem model claim at K1/K2.
- B implements and verifies the component scope below after K2. Its at-most-C1 results
  cannot claim a decoder layer, model prediction or full product table.
- R extends actual U5 reference-suite admission and independent verification before G3a and
  U-P9 freeze. No full table, FP8 or second-policy prerequisite unless the suite needs it.
- T produces the first full consumed product tables in U7/G3b after G5-correctness and its
  exact input/model decisions; G6 is additionally required for C2 and U10. G4/G7 success
  and G5-performance/automation completion are not product-table prerequisites.

The normative proposal attachments are `interface.md`, `verification.md`, `delivery.md`
and `decisions.md` in `docs/reviews/U3-native-stage-design-v2/`, pinned by the acceptance
record. V1 is historical, not a competing delivery schedule. Changes to accepted model
laws or mapping choices require prospective review and identity/version changes.

## Bounded model scope and refusals

B admits only npu-l4 hash
`sha256:3b7186f3e69d38723ec40f9a074b941934644ac57cc6f61d64865429caac07d9`, frequency ratio 1,
BF16 operands/output with FP32 accumulation, TP1/rank0, 1–16 component q_projection GEMMs,
1≤M≤1024 and 1≤K,N≤256, contiguous layouts, repeat 1, WS ≤256-row tiles, no K split.
Explicit DMA/unicast/barriers and double-buffer placements use FIFO-ready arbitration;
shared resources serialize and independent DMA/compute/cores may overlap. Imported mapped
work runs unchanged after validation. Cold HBM and separately labeled resident test
initialization are distinct; the latter cannot become a table row or steady prediction.

Compute 1 / NoC 0 / DRAM 0, exact sync, layer_reuse=false, at most C1. This spec has no shared
SRAM; do not imply absent shared SRAM on future hardware that declares it. SRAM bank
conflicts, NoC link/VC contention, DRAM row/physical queue behavior and energy are not
represented. Emit exact unrepresented paths/null diagnostics. DMA request limits and
channel/core-port bandwidth accounting remain required even at level 0.

Retain verification E3's explicit WS staging+32-cycle overhead+fill/steady/drain+output
law and E4's NoC infinite-bandwidth hop delay, fixed DRAM latency/refresh-derated channel
cap, request striping and credit-until-commit/ack lifecycle. These are model assumptions,
not physical measurements. Coefficient/vector throughput is not inferred from BF16 matrix
rates. Refuse full legacy/v2 models, non-q_projection operators, rotary/KV/fused attention,
other precision/rank/hardware, steady state, K spill, multicast, invalid shapes/placements/
closure, padding or unsupported fidelity. Interface R01–R21 are mandatory controls.

## Input, observation and replay contract

Propose additive `uarch-prepared/3`, `uarch-taskgraph/1`, `uarch-engine/3` with strict tagged
scope/jobs, complete semantic/placement/assumption/hardware identities and no hash cycle.
Reuse OpSpec/PreparedOp(v2), rank, producer, KV and rotary vocabulary; old analytic roots
remain strict/unchanged. Native refuses analytic jobs and refuses full v1/v2 work until
explicitly admitted. Reserved version names and installable exact schema/fixture patch
require human review before installation/K2. This prose does not install a carrier.

R/T preserve authenticated coefficients, positions, Q/new-K FP32 arithmetic and casts,
full-tail transfers/coefficient traffic, rotated-before-store append, local KV replication,
complete group repeats/head/tail and fused paged attention. No hidden coefficient defaults,
score DMA, second TP division or dropped work. U0022 FP8/ragged gaps require separate
semantic decisions before their consumer runs; BF16-only cannot meet the FP8 demo.

Mandatory `uarch-native-observations/1` proposal records dispatched events, completed jobs,
DMA/control-volume issue/completion, allocation lifetimes, represented queue membership,
resource intervals and causal critical path. Useful versus issued/padded/cast work and
payload versus transaction bytes remain distinct. Expected coverage is a separate ledger.
Conservation is final=initial+issued−completed per boundary/direction/unit; compute operand
reuse is not conserved DMA bytes. Queue area uses clipped residence intervals including
initial/terminal members. Nonempty stable-window Little's law retains 1%; zero flow has
null residence. Utilization uses busy interval union. Attribution includes causal resource
predecessors, partitions duration exactly and is not a physical explanation of error.

Three fresh-process and debug/release runs yield identical canonical results at each
admitted native stage. Implementation/model/compiler/lock/assumptions/input identities
bind results; executable/image/build-profile/host time/RSS belong in operational receipts.
Saved mapped replay disables all workload/mapping/coefficient producers. Trace changes
only its declared trace field; numeric projections match with trace on/off and full bytes
match within each setting. Table workers 1/8 and repeated table bytes are T; batch workers
1/N apply where delivered. No hidden reconstruction or filename-only identity.

## Kernel semantics and verification

Follow build-spec §2.8: single thread; u64 picoseconds and exact checked u128 edge arithmetic;
next_edge is the sole cycle conversion; 32-byte events ordered by (t_ps,phase,target,seq),
schedule-time sequence; arena/free list, two-level 4096-slot wheel with heap overflow,
single resource ownership, CSR topology/declared routes and ordered output collections.
No unsafe, SIMD/GPU/MPI, compiler/search or threading at these stages. No link reservations
are invented at NoC 0. Later lookahead is spec-derived, not assumed one cycle; exact
conservative sync precedes approximation. Ramulator/U9 remain separate work.

Adopt interface.md's proposed zero-delay milestone closure only after explicit semantic
review: canonical ready-DAG processing at the same time, no earlier-phase completion
inserted behind issue and no exclusive interval for zero duration. Zero-hop transfers
add no invented delay, cyclic dependencies refuse. Verify literal and fault controls.

K1 acceptance is U-P11a 1/1a/2/3/5 internally; K2 executes all applicable acceptance cases
publicly including protocol 4/6. B/R/T require their applicable independent literal counts,
transfers, edges, limits, conservation, capacities/credits, causality, serialization and
positive overlap, replay and fault/restored-control matrix in verification.md. At least
two U-P8 fixtures need committed human working, including latency-bound DMA; author agent
calculations do not discharge this or independent review. Required observations cannot be
postponed to optional tracing. Overflow/refusal tests differ from numerical mutant kills.

U0006 governs: preserve every invocation/discovery/shrink/control/error and exact identities;
freeze cases/premises/budgets before two qualifying replays. Applicable counterexamples or
surviving required mutants fail; otherwise missing/empty/skipped/incomplete/under-budget
coverage is not_run. Only complete nonempty passing applicable coverage passes. B owns
independent corpus/reductions, A supplies mechanisms, coordinator reconciles disagreements.
Analytic C1–C5 and remaining cells have first-consumer deadlines in verification.md, including
native roofline checks and U-P9/U-P15 baselines. C1's historical 22/24 clock cell and
proposed deterministic-anchor remedy are aggregate-only. Independent native component-clock
tests and any separately approved true-premise per_op domain do not inherit that remedy
or its evidence; the existing per_op whole-query reciprocal premise remains invalid with
memory-only embedding. Unrelated report completion does not gate K1; required checks must
pass before reliance. Never replace them with optional L2.

## Reference readiness, product and qualification

R sources usable TPU representation and explicit unknowns with B, resolves exact formats/
operators/transport/benchmark carriers and measurement granularity, and admits the signed
≥24-benchmark six-class U-P9 suite. Complete applicable RoPE/casts/KV work, steady/priming,
replay/independent faults and attribution used by G4 precede freeze. A GEMM-only executor
cannot close G3a. Unrepresentable/unmeasurable required work returns a target/scope/contract
decision, never fabricated parameters or silent removal. U-P9 remains prediction-only.

U6 qualifies expanded npu-m256 representative execution/diagnostics and integrated
regressions, not another kernel or full C1 table. R/G3a or successful G4 is not required
for independent qualification. T preserves the npu-m256/70B/FP8/tp8 demo and all consumer
coverage/error/worker/public-pipeline requirements. BF16/npu-l4/tp1/second-policy work
requires its declared consumer, including U-P14; no automatic npu-l4 or 32×32 grid.
U10 requires G6+G3b and rk-sim's separately accepted C2-only boundary.

Blackhole: U-P16 S sourcing → U-P15a admission/tests → U-P15 freeze → U-P16 M measurement.
U5/G4 and U8/G7 thresholds, frozen-before-measured ordering and evidence scopes remain.
No pilot, hardware spend or measurement is authorized by this record. Optional component
references need prospective matched scope/criteria, pins and implementation-overlap review;
same-code is integration, unavailable/unmatched stays explicit, observed disagreements
persist. No complete fork requirement, second Python engine or fork-speed target returns.

## Environment, budgets and independent gate outcomes

Before K1, accept exact Rust release/commit/checksums, target, compiler components,
Cargo.lock/transitive features/licenses, cargo-deny version, base image digest and OS tool
inventory/recipe. Initial direct dependencies: serde/serde_json and dev proptest only;
no blanket license exception. Immutable values are unresolved in this proposal and require
a pin-only decision before coding. Real Linux CI executes fmt/clippy -D warnings, license
and debug/release tests with B-pinned tools; no empty workspace/no-op job proves readiness.

Accept performance workload/host/time/RSS budgets separately before measuring. Proposed
K2/B envelope only: ≤5 s/512 MiB for ≤4096 fixed-delay jobs/16384 edges or B≤16 maximum
component ops, one thread/worker, exact cold/resident fixtures, on a separately accepted
controlled Linux allocation. Delivery defines all-in invocation, warm-host+seven-run
maximum/RSS and U0012 noise calibration. This is a planning proposal, not allocation or
measurement. V1's later 60/120/300 s and 672-point ceilings are withdrawn; R/U6/T need exact
new consumer budgets before performance work. No inherited 200-second fork ceiling.

Record G5-correctness, G5-performance and G5-automation separately. Only correctness gates
ready U7/G6/G3b/U10 with their own tests. Full G5 requires all three. Controlled-host
performance evidence AND executed applicable self-hosted nightly gate full G5, U9 entry,
any simulator-performance claim and final closure. Missing either leaves diagnostic host
observations provisional; it does not prohibit otherwise ready correctness/product work.
Before nightly exists, required correctness selections execute explicitly on approved
Linux. No WSL performance claim. Fresh hosted checkout and separate fresh local clone at
the same published commit remain prospective sprint correctness-closure requirements.

STUB, unknown error, unverified energy and null unmodeled quantities persist. This record
claims no implementation, schema installation, native run, performance result, artifact
refresh/adoption, G2/G3a/G3b/G5 acceptance, independent verdict, badge or sprint closure.
