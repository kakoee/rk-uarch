# U0011 — Progressive native core: bounded component stage and qualification

**Status: design/semantic scope accepted by Javid (@jjaffari), 2026-10-13,
for U3 closeout only.** This record takes effect upon human installation.
[Exact approval and exclusions](../reviews/U3-reviewed-design-and-policy-v1/acceptance.md)
bind the reviewed proposal at `7afba9b16d954fd46684711764cb3718170e53aa`.
U4 preparation and implementation require separate authorization. No installation of
mapped carriers or artifact-policy code, no generation/adoption, no native execution,
and no G2/U3 closure is granted by recording this design.

The accepted scope is D1 of the [decision packet](../reviews/U3-reviewed-design-and-policy-v1/next-decision.md),
including H-DMA/H-CLOCK and S-COMPONENT/S-CI/S-QUEUE. Outstanding decisions below stay open:
exact schema/fixture/corpus bytes, immutable toolchain and licence approval, human L1
working, reference/product inputs, and all numeric performance/host/noise budgets.
The 5 s/512 MiB and record/size figures remain proposals, not accepted limits.
Estimates and ownership are planning allocations, not release of U4 tasks.

The attachments below are normative design inputs at the reviewed revision; their
original proposal/evidence text is preserved. This acceptance scope governs any retained
“proposed” or “requires human review” wording about the accepted design. It does not
turn an unresolved concrete implementation, budget or installation into an approval.

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
  M fixed-delay carriers/fixtures/import and verified K1; the component mapper is first required at B. Repeat kernel acceptance and faults publicly; private results
  cannot discharge this requirement. No subsystem model claim at K1/K2.
- B implements and verifies the component scope below after K2. Its at-most-C1 results
  cannot claim a decoder layer, model prediction or full product table.
- R extends actual U5 reference-suite admission and independent verification before G3a and
  U-P9 freeze. No full table, FP8 or second-policy prerequisite unless the suite needs it.
- T produces the first full consumed product tables in U7/G3b after G5-correctness and its
  exact input/model decisions; G6 is additionally required for C2 and U10. G4/G7 success
  and G5-performance/automation completion are not product-table prerequisites.

The normative design attachments are [interface](../reviews/U3-native-stage-design-v2/interface.md),
[verification](../reviews/U3-native-stage-design-v2/verification.md),
[delivery](../reviews/U3-native-stage-design-v2/delivery.md) and
[decision boundaries](../reviews/U3-native-stage-design-v2/decisions.md), pinned by the
[exact acceptance inputs](../reviews/U3-reviewed-design-and-policy-v1/decision-inputs.json). V1 is historical, not a competing delivery schedule. Changes to accepted model
laws or mapping choices require prospective review and identity/version changes.

## Bounded model scope and refusals

Production B admits only npu-l4 hash
`sha256:3b7186f3e69d38723ec40f9a074b941934644ac57cc6f61d64865429caac07d9`, frequency ratio 1,
BF16 operands/output with FP32 accumulation, TP1/rank0, 1–16 component q_projection GEMMs,
1≤M≤1024 and 1≤K,N≤256, contiguous layouts, repeat 1, WS ≤256-row tiles, no K split.
Explicit DMA/unicast/barriers and double-buffer placements use FIFO-ready arbitration;
shared resources serialize and independent DMA/compute/cores may overlap. Imported mapped
work runs unchanged after validation. Cold HBM and separately labeled resident test
initialization are distinct; interface.md's checkpoint/invocation/profile matrix binds
all synthetic clocks/hardware/state to a frozen NativeTestProfile and verification-only
job/result identity. Test variants are proposed-design stipulations with rationales,
registered to refuse normal prepare/table/product reports. B retains fixed-delay test
regressions with null subsystem fidelity. Production whitelist/ratio remain unchanged. Resident and other test results cannot
become product table rows or steady predictions.

Compute 1 / NoC 0 / DRAM 0, exact sync, layer_reuse=false, at most C1. This spec has no shared
SRAM; do not imply absent shared SRAM on future hardware that declares it. SRAM bank
conflicts, NoC link/VC contention, DRAM row/physical queue behavior and energy are not
represented. Emit exact unrepresented paths/null diagnostics. DMA request limits and
channel/core-port bandwidth accounting remain required even at level 0.

Retain verification E3's explicit WS staging+32-cycle overhead+fill/steady/drain+output
law and E4's NoC infinite-bandwidth named-domain next_edge hop delay, fixed DRAM latency and
refresh-derated rational channel service (ceil-to-ps only, no DRAM edge alignment),
request striping and credit-until-commit/ack lifecycle. E4 defines all crossings,
receiving-mechanism alignment attribution, unlimited credit-bounded issue per edge,
compute-only job overhead and the five-read refresh discriminator. These are model assumptions,
not physical measurements. Coefficient/vector throughput is not inferred from BF16 matrix
rates. Production refuses full legacy/v2 models, non-q_projection operators, rotary/KV/fused attention,
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
initial/terminal members. Finite-window observations are required at B; stationary Little's law retains 1% at
first claim (normally U6 or earlier reliance) after frozen population/window/boundary
premises; zero flow has null residence. Utilization uses busy interval union. Attribution includes causal resource
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

Adopt interface.md's exact owner-grant rule for zero-duration jobs: join the owner FIFO,
complete inline only after grant, preserve deterministic phase2 zero-transition closure.
Busy-owner literal completes at5000 ps; owner-bypass fault gives3000. Zero-hop nonaliasing
same-core unicast is admitted with no NoC delay/alignment; actual DMA still pays port
service. Cyclic dependencies refuse. These semantic corrections require human review.

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
the two memory-only operators head/embed and layers/kv. Unrelated report completion does not gate K1; required checks must
pass before reliance. Never replace them with optional L2.

## Reference readiness, product and qualification

R sources usable TPU representation and explicit unknowns with B, resolves exact formats/
operators/transport/benchmark carriers and measurement granularity, and admits the signed
≥24-benchmark six-class U-P9 suite. Complete applicable RoPE/casts/KV work, steady/priming,
replay/independent faults and attribution used by G4 precede freeze. A GEMM-only executor
cannot close G3a. Unrepresentable/unmeasurable required work returns a target/scope/contract
decision, never fabricated parameters or silent removal. U-P9 remains prediction-only.

Delivery.md names Q6-C/D/W representative inputs and a separately schedulable shared W
operator package: W can feed R/U6/T independently of TPU and is charged once. U6 qualifies
expanded npu-m256 representative execution/diagnostics and integrated
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
K2/B envelope only: ≤5 s/512 MiB for ≤256 fixed-delay jobs/1024 edges or B one cold/resident E3 C1 tile
(576 cold requests), plus separate E4 bursts≤33 requests, one thread/worker, exact cold/resident fixtures, on a separately accepted
controlled Linux allocation. Delivery defines all-in invocation, warm-host+seven-run
maximum/RSS and U0012 noise calibration. This is a planning proposal, not allocation or measurement. Interface.md accounts for
mandatory observation volume; the small performance profile caps65536 records/16MiB
encoded observations without dropping required data. Full B admission is unchanged and
requires its own resource budget before performance work. V1's later 60/120/300 s and 672-point ceilings are withdrawn; R/U6/T need exact
new consumer budgets before performance work. The later prospective U0011-Q addendum defined in delivery.md
supplies U9's representative single-point trigger; the small fixture ceiling does not.
No inherited 200-second fork ceiling.

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

Stage 2 schema decisions also include explicit prepared-op/1 component version, unchanged
strict Counts/ExtCounts plus separate issued-work/traffic carriers, closure-before-stage
validation order, the complete hardware leaf ledger and native-owners/1 enumeration in
interface.md. Delivery.md supplies exact proposed DMA/clock prompt clarifications for
Javid; current prompts are not changed by this proposal. B must re-derive the revised E4
and freeze variant/corpus identities; author arithmetic does not supply B's independent
review or the two human-worked fixtures. Stage 3 remains the same reviewer's adjudication.

## U4 exact M and private K1 release

Javid's separate U4 approval is recorded in
[U4-M-and-K1-release-v1](../reviews/U4-M-and-K1-release-v1/next-decision.md).
This section takes effect only upon human installation following that approval.
The U3 closeout-only restrictions remain historical; this section releases only the
bounded U4 actions below, not K2/B/R/T or sprint closure.

### M carrier bytes and host authority

Accept the 26 additive protected postimages in A's final M package at
`111b24b0d8a41280431a35b9e3115d93630b6d24`, patch SHA256
`d392b24304a5f63fe69679ce991c5dbf2f742e95fee867a82dec2b0eef3a25e3`,
and all eight encoding choices in its
[exact decisions](../reviews/U4-A-M-package-v1/decisions.md).
B's final audit at `1a56ff22068ded35cac944fd8c1de8ffde9cc86d` confirms the
56-file nominal dependency closure for these exact bytes plus the selected repair;
this is not a future fixed count or source exclusion quota.

Accept the Git-record trust mechanism: qualifying loaders must obtain registry/profile
hashes and expected engine identity from separately reviewed host authority inputs bound
to Javid's exact published acceptance record. Caller-supplied objects, self-hashes, paths
and flags cannot create approval. Each actual qualifying corpus/profile/registry and
engine binding still needs its own acceptance before public use. No placeholder engine
identity or synthetic host anchor in a proposal is thereby made qualifying.

Authorize preparation of the combined M/selected-policy source installation and freeze
under U0002. The selected repair remains exactly SHA256
`c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b`;
U3's policy choice is not reopened. Human protected installation, the exact frozen source
and input decision, two human generations, candidate audit and separate adoption remain
required. Do not publish a source-only half-transition as current. M runtime loader/mapper
and public K2 work require their separately bounded implementation release and first-use
inputs. This section accepts the schema/prototype, not native execution observations.

### Exact K1 tools and scoped licences

Bind the following text to A's tool package at
`83a9a14fd76a00b7858ddd140cc0e0589f80a267`, reconciled by B at
`1a56ff22068ded35cac944fd8c1de8ffde9cc86d`:

For private K1 correctness work, accept Rust 1.99.0 for
x86_64-unknown-linux-gnu, minimal profile plus rustfmt and clippy, at the compiler commit,
manifest and component checksums in U4-A-toolchain-v1/pins.json. Accept the exact
serde=1.0.229, serde_json=1.0.154 and dev proptest=1.12.0 requirements, disabled defaults,
enabled features and full Cargo.lock/checksum closure in that package. These are the only
direct kernel dependencies; transitives are admitted only at the locked identities.

Accept Unicode-3.0 solely for unicode-ident 1.0.27, whose licence is
`(MIT OR Apache-2.0) AND Unicode-3.0`, with its recorded crates.io checksum and retained
notices. Select MIT for its alternative permissive arm. This exception admits the Unicode
identifier tables reached through serde_derive/proc-macro2/syn. It does not add Unicode-3.0
to a global allow-list, cover future versions, or admit another dependency. A changed
version, checksum, licence expression or feature closure requires renewed review.

Accept cargo-deny 0.20.2 at the official musl binary digest in cargo-deny.json as a run-only
verification tool, and the exact deny-proposed.toml policy. Its private-workspace exclusion
covers only publish=false first-party packages; it grants no licence to rk-uarch and
exempts no external registry dependency. All external crate licences remain checked.

Accept the exact Linux amd64 official Rust container manifest and OS package bytes in
container.json/os-packages.json, with the recorded copyright notices, solely as the private
build/test environment. The exact Dockerfile.engine.proposed adds only checksum-verified
fmt/clippy and cargo-deny tools. GCC/binutils and Debian utility GPL licences, glibc LGPL
and GCC runtime exceptions, and the compiler/tool distribution's recorded licences are
acknowledged as build/run environment obligations, distinct from the permissive engine
crate allow-list. Retain all installed copyright notices and corresponding upstream source
references. This is not approval to modify/distribute those components, publish this image,
link glibc statically, or waive any licence obligation. Distribution or new components
require a separately scoped review. cargo-deny covers crates, not this OS/tool inventory.

These decisions release private K1 implementation and correctness checks after normal
task authorization, independently of M. They approve no native result, public K2 admission,
host provisioning, performance budget/claim, hardware expenditure, or artifact generation
and adoption. Before K1 evidence counts, Lane B's real Linux CI uses these same exact pins.

### Bounded work authorized after this human record

Lane A may implement private K1 under U-P11a acceptance 1/1a/2/3/5, including its
required discriminating tests, using only the accepted tool/dependency inputs. It does
not wait for M installation, the complete later B corpus, human L1 worksheets or a
self-hosted runner. All such later first-use obligations remain in force.

Lane B may complete the accepted disposable build/test environment, offline cache,
tool discovery and actual K1 CI proposal under those same pins. No shared-host changes,
image distribution or paid provisioning is released here. Final builder digest, nonempty
real test inventories, debug/release execution and fault/replay checks must be observed
before native CI evidence counts. A base image digest and synthetic logs do not suffice.
If CI needs private image distribution, propose the exact destination/access mechanism
before publication; do not infer permission from this build/test scope. Preserve the
existing documentation-only CI path. Do not replace a working job with placeholders.

Normal owned implementation commits/pushes are authorized, with affected checks and
peer ancestry preserved. Protected-file changes still use human ownership. K2 public
execution, later model stages, performance claims, generation/adoption and U4 closure
are outside this K1 release. Actual K1 completion remains subject to verification/review.

## Proposed K2 first-use semantic completion (not an implementation release)

This paragraph takes effect only on separate human acceptance/installation of the exact
U4-A-K2-semantic-construction-v1 patch and reconciled corpus. Retain uarch-engine/3 and
uarch-native-observations/1 for their first public fixed-delay implementation; there are
no installed completed native result fixtures to migrate. Bind the exact revised schema
bytes and these laws in new engine/model implementation identities and the host record.
Existing M inputs retain their identities; this does not approve old profiles for execution.

ClockSetup.start_ps is the earliest release of its existing fixed-delay job. Jobs without
ClockSetup release at0 and use their declared duration_ps. Clock-driven jobs require
fixed_delay.duration_ps=0; n_cycles exclusively controls their owned service. Readiness
is max(release, all dependency completions); ownership/FIFO may postpone grant further.
For n>0, completion is next_edge(domain, actual grant, n); for n=0, completion is the
actual grant, including non-edge grants. This preserves reviewed K1 zero ownership behavior.
The future release mechanism is a separately reviewed K2 extension, not a change to
historical K1 code/evidence. Python supplies neither hidden jobs nor computed durations.

Release events with start_ps>0 dispatch at phase1; start0 is implicit. Complete phase0
at time t, dispatch phase1 release/readiness/dependency notifications in event total order,
then enqueue all newly eligible phase1 jobs per owner by canonical job ID and enter phase2.
Phase2 owner grants and inline zero completion/notification closure preserve K1 owner
scan and append order; no event regresses to phase0/1 at the same t. Releasing a job with
unfinished dependencies only sets its released state. Finishing dependencies before
release only records readiness prerequisites. Neither transition grants early or twice.

Expose actual TASK_RELEASE, DEPENDENCY_READY and OWNER_GRANT dispatches. For every
clock-driven job, observations.clocks records the raw next_edge(domain,grant,0) invocation
outcome independently of owned completion. At1.2GHz/grant835/n0 the raw edge is1667 and
owned completion835. An unrepresentable raw edge records TimeOverflow/null; it does not
make an otherwise valid zero-owned job overflow. A positive-cycle completion overflow
still refuses the job, with no completed result. The raw call is execution instrumentation,
not Python arithmetic filled into a result. Retain direct primitive tests separately.

Fixed-delay queue membership is observed, in picoseconds: one waiting [ready,grant] and
one service [grant,end] row per job, including zero lengths; clock_domain=null because
owner FIFO itself is not clocked. Component queue domains remain non-null. Job records
include actual release_ps. Resource intervals contain positive owner occupancy only.
Critical intervals distinguish service (owner required) from release_idle (owner null,
predecessor null, overhead, [0,release]); release_idle is a causal origin offset, not
resource occupancy or an assertion that all other owners were globally idle.

Derive tight causal predecessors from actual dependency completions and the previous
owner completion at grant, only when ending at that grant and dispatched earlier.
Earlier owner history/dependencies are not blockers. Preserve all tight job IDs sorted;
choose the smallest public job ID, then owner ID; job causes precede a tied release cause.
Choose the latest-ending job, with equal ends resolved by smallest job ID then owner ID.
Follow chosen causes through zero bridges, but emit only positive critical intervals.
All-zero duration requires an empty critical partition and zero attribution, while actual
dispatches, jobs, queue rows and completions remain present. Fixed-delay attribution is
all overhead. No resource busy time is charged for release_idle; busy time remains union.

The complete patch adds carrier checks, affected generated schema mirrors and synthetic
structural tests. These are not native observations, independent acceptance or qualification.
Public validation must additionally exercise real execution and the published fault/replay
matrix. Protected installation, source-support lifecycle if affected, dependency/cache
construction, K2 implementation/build and final human first-use authority remain separate.

For U-P11a K2's “every acceptance case” and design-v2 verification E2's “K1 private,
K2 public”, retain all raw clock obligations at the public boundary through the new actual
raw-call observations. The sole proposed representation exception is arbitrary Wheel/Arena
insertion/reuse/sequence-exhaustion probes: retain the full100 private schedules and fault
controls, repeat all representable ordering/owner behaviors and reached timing faults
publicly, and record residual private-only coverage explicitly. This paragraph is the
prospective E2 clarification; the historical design-v2 package remains unchanged. No
event-injection workload carrier is introduced, no obligation is deleted and no private
execution is relabelled public. Without acceptance of this exception, literal all-case
public coverage remains blocked, even after public clock instrumentation is implemented.
