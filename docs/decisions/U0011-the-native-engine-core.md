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


PROPOSED ONLY — exact prospective U0011 bounded-runtime addendum; no installation yet.

For the single candidate-04 combined-runtime first-use campaign, Javid may approve the
separately identified Python runtime assembled by U4-B-K2-combined-runtime-stage2-v1 from
A d9a22f047d4410aab4abb75e1fc780a51d7a8f6b and B 4684cb9eccc5b5186824a8705cf4d1b44f88af42.
Its isolated hardware.py SHA256 is
98b1b06ddf686da948223ca517b0ac16729fbd0f3f6fd1b5bc6f61c1507cb1b5.
The actual published candidate descriptor, helper publication, human decision and
immutable placement/preflight records must bind the complete runtime, not just this file.

This grants only the expressly approved runtime-copy coexistence: Python consumer imports
use that separate immutable root; original native BuildInputs/BuildReceipts, binaries,
HostRecord, engine selector, jobs and build-source tree remain unchanged. The runtime
identity is additional and mandatory in campaign, operational and replay evidence. It is
not the historical native build-source identity. No acceptance token may be copied or
manufactured; the production resolver still validates the original native tree and issues
fresh genuine bindings. The new runtime requires its own externally published human
approval, root-owned selector, exact closure checks and actual authority-free preflight.

The adopted oracle artifact validates only its unchanged canonical generator/support
source; it does not validate the altered runtime copy. U0002 strict currentness and selected
support policy remain fully operative for generation, verification and canonical CI. No
artifact may be checked as current against the altered hardware.py. No generator, oracle,
producer or table workflow is permitted in this isolated runtime. This is an explicit
bounded execution decision, not an inferred lifecycle exemption or generator-support
exclusion. Canonical installation of these changes and long-term developer-source adoption
remain separate protected-source review and, for changed reachable support, exact freeze,
human two-process generation, candidate audit, separate adoption and integrated publication.

Approval permits human placement into the new immutable root, authority-free preflight,
coordinator publication of actual placement/preflight joins, human binding of that exact
approval and restart into an empty new output. All 798 slots are fresh (780 success and
18 TimeOverflow refusals), with six-way comparisons, producer-disabled relocated replay
and corruption/restoration controls. Prior 88 checked / 89 transport receipts remain
incomplete historical evidence and contribute no completed slots to this campaign.

This does not change U0024, dependency/licence pins, native binaries, semantic/fidelity
requirements, canonical source or artifacts; no component/C3/public qualification,
performance claim, hosted infrastructure change or U4 closure follows. A mismatch, incomplete
placement, failed preflight or changed binding stops the sequence before native execution.

The exact final human decision must also bind policy-choices.md (H1–H4). Publication
requires the actual expected remote, never local tracking refs. Current execution stops
on failure; there is no automatic or preauthorized retry. The outer 7,200-second limit
includes startup, processing and final checks. No additional processing allowance is
granted. The separately proposed bounded retry option requires its own actual confirmation
and concrete fresh-output handoff before any retry. U0002 gains only the supplied narrow
cross-reference; canonical currentness and lifecycle requirements are unchanged.


## Proposed component lifetime and observation completion (not a release)

This section becomes normative only after human acceptance and protected installation of
U4-A-component-stage2-v1's exact combined postimages. It grants neither component native
implementation/build entry nor runtime execution authority; the separate reconciled K2 and
scoped B release remain necessary. Human worksheet workings gate applicable L1 acceptance,
not this preparation. Existing accepted tools, scope and dependencies are not voted again.

Admit explicit ws-rowsplit@2 alongside unchanged @1. @1 retains persistent identical-size
accumulators (no terminal readers); its mapper/default bytes remain unchanged. Historical
@1 producer metadata remains inert for accumulator lifetime readers, including installed
fixtures naming their compute as producer. Only explicit @2 activates transient semantics.
@2 permits transient exact-size accumulator allocations: producer must be a compute that
actually names that accumulator, on its core, with uninitialized initial residency. Every
compute using it is a lifetime reader, follows that producer or is the producer, and remains
subject to exact FP32 4*M*N size. Terminal consumers are precisely the maximal readers in
the dependency DAG. Distinct overlapping allocations are legal only if ALL terminal readers
of one precede the other's producer. Matrix serialization alone is not a lifetime proof.
An unrelated DMA, barrier or compute using another accumulator cannot manufacture production.

The @2 mapper allocates ALL SRAM and HBM operands in min-ID Kahn topological operator
order, then tile order; stable operator prefixes still derive from sorted operator IDs.
This changes operand offsets even on uniform-footprint cores when dependency order differs
from ID order. For two uniform 256³ ops a→(depends on b), b's operands are allocated before
a's under @2; @1 retains a-before-b ID placement. The @2 mapper keeps persistent scratch
on cores with only one footprint. Heterogeneous
cores use exact-size per-compute transient buffers at offset0 and explicit compute-to-compute
edges in stable topological operator order (ID ties), then tile order. Existing op dependencies
remain; different cores and DMA may overlap. Imported valid placements need not use this
strategy. No capacity enlargement, spill, retile, K split, padding or scope waiver follows.

Component results require uarch-native-observations/2; fixed-delay /1 remains byte/shape
compatible. /2 adds a typed activity table and explicit activity references on clocks,
resource intervals, ordinary queues and critical intervals. Request identity is a field,
not a suffix hidden in an activity string. A compute/barrier activity has null request_id;
DMA activities name an exact declared fragment; unicast uses its declared job ID. Activity
IDs are unique stable strings and are not parsed to infer causality. Subphase, kind, owner,
category and receiving domain are explicit. Zero-duration activities remain represented.

Activities record ready, actual start and end, dispatch/completion observation ordinals,
occupied status and typed tight predecessor links. Both ordinals join actual dispatched
EventObservation records by job, owner, time and the endpoint kinds specified below. Job observations join the declared graph
and actual completed state; request observations join declared fragment/job/engine/direction,
buffers, bytes and route. Aggregate counts derive from completion, never declared work alone.
Resource records cover precisely occupied activities; alignment/waiting does not invent busy
intervals. DRAM latency and acknowledgement alignment are not channel/core-port service.
NoC0 latency and DMA inflight can overlap. Busy time is half-open union, not sum.

Receiving domains are core for compute, read/write ports and acknowledgement; noc for
request/response/unicast hops and barriers; dram for DRAM latency; null for rational channel
service. Alignment is a separate nonoccupied activity of the receiving subphase and category.
Every clocked subphase has one service activity and one separate alignment activity,
including zero-length alignment, with one exact clock record for each. Rational channel
service and zero-hop routing have no alignment or clock record. Service ready follows its
alignment; alignment ready follows the prior subphase (or request issue/job dependency readiness for
the first). Actual resource acquisition may occur later than that readiness. Clock records reference the exact activity. Existing E3/E4 next_edge and
zero-owned-duration laws govern; zero-hop movement stays at arrival without edge alignment.
Channel exact start/end ratios are reduced; published integer endpoints are ceilings. Never
feed integer publication rounding back into channel service. Timing formulas remain E3/E4.

Channel queues are channel_service:<channel>, exact declared fragment and channel owner,
waiting/service only, clock null. DMA queues are dma_inflight:<flattened-engine>, exact
fragment and DMA owner, inflight only, clock null. Ordinary queues are
activity:<subphase>:<owner>, reference the exact activity and request (or compute/barrier job),
use its receiving domain and waiting [ready,start] or service [start,end]. Service population
means active mechanism, including nonoccupied alignment/latency, not resource busy time;
only occupies_resource selects busy intervals. Ordinary service rows are explicit; zero
waiting rows may be omitted, nonempty waits may not. Channel waiting/service and DMA
inflight each require exactly one row per declared request. The same identity,
owner and population laws apply before checking domains; nonnull cannot escape validation.
Finite queue windows clip initial/terminal members, count events at start not end, retain
separate waiting/service/inflight populations and return null residence for zero flow.

Transfers use boundary IDs request_noc, dram, response_noc and core_port for each DMA
request (write core_port precedes request_noc; read core_port follows response_noc), and
unicast_noc for unicast. Direction always remains read/write/unicast from the declared
request; request/ack control hops carry zero payload/transaction bytes, payload-bearing
NoC/core-port boundaries carry payload bytes and zero HBM transaction bytes, dram carries
both declared payload and rounded transaction bytes. Boundary enter joins the first subphase's ready time (before its receiving wait/alignment)
and leave joins the last service completion; dram spans latency readiness through channel
completion. Allocation owners are
sram:<core>, matrix:<core> for accumulator, and channel:0 for HBM
capacity accounting (HBM allocation is shared address capacity, not channel-local capacity).
Allocation interval covers every actual use; explicit transient acc begins at its producer
grant and frees at its last completed terminal reader; persistent scratch/reservations stay
live through run end. Initial inventory records declared preloaded state.

Causal links are explicit sequence, dependency, resource or credit relations. Every supplied
predecessor ends at the activity start and is a legal actual cause; historical idle predecessors
are forbidden. Zero-length links form a DAG and cannot be dropped. Select the terminal
activity ending at makespan and each tied tight predecessor by ascending
(owner_id,job_id,request_id-or-empty,subphase,activity_id). Reverse that path and omit only
zero-length intervals to obtain the critical partition. Waiting follows the actual blocking
activity, not an invented busy wait. Category follows the receiving mechanism, preserving
compute overhead separately. Independent checker must verify candidate completeness and
actual blocker eligibility from transitions, not just the total duration or these strings.

Profile expected_outcome is an admission predicate, not a resource-guard waiver. Retain
expected-negative profile cases as TestVariantNotAdmitted controls. Public semantic negatives
require separately reviewed exact input hashes in a success-admission profile and an external
immutable expected-refusal selection; they must fail resource validation before job execution.
No mutable caller rehash, embedded trust anchor, bypass flag or hidden trust is authorized.
Synthetic profiles/results remain unit-only evidence. Their acceptance is not native success.

### Proposed Stage 2 structural completion

All alignment records are nonoccupying, with the same owner/category/receiving domain as
their service. Alignment dispatch/completion kinds are TASK_READY / DEPENDENCY_READY.
No alignment exists for channel service or zero-hop NoC. Each service has these properties:

| Subphase | Owner | Category | Domain | Occupies | Dispatch / completion event |
| --- | --- | --- | --- | --- | --- |
| compute_overhead | matrix:core | overhead | core | true | OWNER_GRANT / COMPUTE_DONE |
| compute_stage, compute_wave, compute_drain | matrix:core | compute | core | true | OWNER_GRANT / COMPUTE_DONE |
| read_port | dma_port:core | memory | core | true | OWNER_GRANT / DMA_DONE |
| write_port | dma_port:core | memory | core | true | OWNER_GRANT / MEM_RESP |
| channel_service | fragment channel | memory | null | true | MEM_REQ / MEM_RESP |
| dram_latency | fragment channel | memory | dram | false | MEM_REQ / MEM_RESP |
| request_noc, response_noc, unicast_noc | local/source router | noc | noc | hops > 0 | NOC_HEAD / NOC_TAIL |
| ack | dma_port:core | memory | core | false | TASK_READY / DMA_DONE |
| barrier | canonical barrier owner | sync | noc | false | SYNC_ARRIVE / BARRIER_RELEASE |

Occupancy is determined from declared phase/route, never from claimed duration. Compute and
ports have an occupied row even for zero duration. Positive-hop NoC occupancy reports the
union of in-flight router-attributed latency; it does NOT serialize hops or introduce a
bandwidth resource. Zero-hop service remains a nonoccupying zero-duration causal record.
This NoC convention is proposed for explicit human semantic acceptance with D1. The independent checker must check channel
and port arithmetic/arbitration directly over service activities even if a row is omitted.
Structural checks independently require the exact occupied-row bijection. Rational channel
endpoints remain on those mandatory rows; published integer endpoints are their ceilings.

Event references require exact job/owner/time/kind joins, separate dispatch and completion
ordinals, including zero duration. Every event must be referenced by a phase endpoint; no
unconstrained STAT_SAMPLE records. Global event ordering remains the existing observation
order law. The phase value retains its scheduler ordering role; it is not a substitute for
endpoint kind. No new service-duration law follows from endpoint encoding.

## Transitions and structural eligibility (F2/F3)

Phase sequences: compute overhead→stage→wave→drain; DMA read request_noc→dram_latency→
channel_service→response_noc→read_port; DMA write write_port→request_noc→dram_latency→
channel_service→response_noc→ack; unicast and barrier each have one phase. Expand each phase
as alignment then service when alignment is present. Phase identities must be unique per
(job, request, subphase, kind); The independent checker independently requires the exact admitted inventory.

A `sequence` link is only from the immediate preceding activity in this expanded sequence.
A `dependency` link is from a terminal activity of a declared predecessor job to a first
activity of the dependent job (for DMA, a request's first activity), with predecessor end
also equal to predecessor job completion. A `credit` link is only from a different request's
last activity to a request's first activity on the same DMA engine. A `resource` link has the
same owner and an occupying predecessor from a different job/request. Its successor is
the first compute alignment (whole-tile ownership), port alignment, or channel service.
Only matrix, port and channel owners are contended; same-tile phases use sequence links. No NoC resource links.
All links remain tight (predecessor end = successor start), with preceding completion ordinal
no greater than dispatch ordinal. Cycles, including zero-duration multi-activity cycles,
are refused. Nonzero-start activities require a tight cause even off the critical chain.

Structural eligibility is necessary but not sufficient. The independent checker derives the COMPLETE tight cause
set from transitions, declared dependencies, actual previous resource occupant and exhausted
credit release. Merely sharing engine/owner/time is insufficient. Credit completeness uses
issue/release state at the engine limit; first/last eligibility alone does not prove exhaustion.
Resource causes must actually gate the grant, and cannot be borrowed from a later activity.
Preserve same-time ties and zero-duration links. Canonical chosen path uses existing stable
(owner, job, request-or-empty, subphase, activity) order among eligible causes.

## Job summaries and legacy fields (F8)

Canonical job owners: Compute matrix:core; DMA dma:core:engine; NocTransfer source router;
Barrier barrier:job. Component tasks declare no delayed release: release_ps MUST be 0.
ready_ps is max declared predecessor job completion (0 with none); start/end are min first
activity start / max final activity end across that job's request sequences. DMA summaries
also join issue/complete records. Job readiness may precede credit acquisition.

The `/1` scalar causal fields cannot express `/2` activity/request transitions. In `/2`,
job.blocking_predecessor_ids MUST be empty and critical.predecessor_id MUST be null. They
are explicitly unrepresented; typed activity.predecessors is the causal witness. `/1`
meaning/validation is unchanged. No new schema field is needed for this decision.


Ports arbitrate by existing E4 FIFO (ready time, flattened DMA engine ID, request ID).
Zero-duration endpoints retain separate dispatch/completion events. The explicit cycle
check gives a stable early refusal; strict endpoint ordering also precludes a valid cycle.

### Proposed optional profile-version binding decision

Current profile/1 promises graph and point identity, not the bundle mapping policy. A policy
relabel with unchanged graph/point remains admissible under that historical promise. Hashing
the whole request elsewhere does not enlarge that promise. Human decision F11 may retain
this behavior, relying on a separately authenticated execution selection that explicitly
binds policy, or accept the following minimal extension for new B admissions.

Recommended profile/2 retains the profile carrier and required fields and extends each entry
with required `mapping_policy: {name, version, buffer_depth}`. Entries must be checkpoint B
and scope component or transport_fixture. All three policy fields must equal the bundle
before other profile variant checks (`TestVariantNotAdmitted: profile mapping policy`).
Format/entry mixing is `TestProfileMismatch: profile policy format`. The existing external
profile hash authenticates these bytes. A caller cannot promote a rehashed profile into a
trusted one. Profile/1 entries and serialization remain unchanged, including historical K2
and @1 anchors. A profile/2 entry can bind either @1 or @2 for a new reviewed case.

This proposed implementation accepts both formats; it cannot infer whether authority is old
or newly approved. Future component authority/selection must explicitly require profile/2
if that option is chosen. No fallback to profile/1 is allowed for such a selection. Current
historical controls retain profile/1 and graph/point-only meaning. Profile/2 needs new profile
hashes, bundle/job hashes and future external anchors; graph/point need not change. No engine,
build, runtime authority or native result is created by this proposal. If the human retains
profile/1, omit the isolated PolicyProfileEntry/profile-format/admission additions and their
schema deltas/tests before freezing the accepted candidate; do not silently claim binding.

## Component DMA issue observations /3 — proposed amendment, not installed

This section is normative only after exact human installation of the reviewed amendment
postimages. It grants no runtime placement, HostRecord, selector, profile authority or
public campaign. The historical component /2 and fixed-delay /1 contracts and receipts
remain unchanged. These rules add an observation of the existing E4 core issue edge;
they add no service-rate cap, channel/port service, workload scope or hardware parameter.

New component model identity `native-intervals`, version `2`, requires observation format
`uarch-native-observations/3`. A /3 result with another model identity, or model/2 with
/2 output, is `ResultBindingMismatch`. Native fixed-delay model/1 and component model/1
continue to use /1 and /2 respectively. Existing protocol `uarch-engine/3`, input graph,
profile/2 policy promises and admission `U0011-stage2/1` remain unchanged: the new model
version binds the new output/lifetime law, not a retroactive reinterpretation of old
input/profile promises. Future execution selections must explicitly bind the new model,
engine, raw job, schema/ADR/checker bytes and expected observation version. No automatic
upgrade of historical jobs, outputs, selections or anchors is permitted.

### Waiting, pending and acquired are distinct

Each declared DMA fragment is in one of three states after its job becomes ready:
(1) unreserved waiting, (2) pending with one reserved engine credit while awaiting the
core edge, or (3) acquired/inflight from issue through commit/ack. Before job readiness
it belongs to none. Per flattened DMA engine, acquired plus pending MUST NOT exceed
max_outstanding. Waiting consumes no credit. Pools are independent between engines;
shared core payload-port arbitration remains the installed independent mechanism.

At each actual eligibility opportunity, reserve all available credits in ascending
(job ready time, request ID) order among requests eligible on that engine at THAT
opportunity. Equal readiness timestamps do not make requests simultaneously eligible:
a dependency must have actually completed before the opportunity. A request initially
ready at time0 can reserve before another request becomes ready via an inline zero-time
predecessor, even if the newly ready request has a smaller ID. Never retrospectively
sort all requests with the same readiness timestamp into a single opportunity.

An eligibility opportunity occurs initially before phase2 work, then at the first
reservation pass after one or more terminal sequence completions. A DMA terminal releases
its credit; terminal job completion can enable dependent jobs. All scheduled phase0
completions at one timestamp drain before one opportunity. Each inline phase2 terminal
completion creates a distinct subsequent opportunity, including at the same timestamp.
Nonterminal completions and pending-to-acquired conversion do not create opportunities.
Every opportunity is recorded, even if it grants nothing, including the final release.
Repeated scheduler passes without an eligibility-changing transition are not extra
opportunities. Native eligibility/reservation timing is otherwise unchanged.

A reservation occurs at the earliest opportunity at which all dependency jobs have
completed and an unreserved engine credit permits it. Reserving a credit is atomic with
removing the request from unreserved waiting. Pending consumes capacity immediately but
creates neither credit_acquire_ps, inflight time, payload traffic nor a busy/resource
interval. Later-eligible arrivals cannot steal a reserved slot. Across independent engines,
the witness serializes grants by (job ready time, flattened engine ID, request ID);
capacity and the ready/request ordering law apply independently to each engine.

At `next_edge(core_hz, reservation_ps, 0)`, atomically convert pending to acquired and
emit DMA_ISSUE. There is no intermediate double charge and no momentary free slot.
credit_acquire_ps equals issue_ps; credit_release_ps equals commit/ack completion.
Neither count nor byte traffic is derived from reservation or declared work. All
eligible reserved requests may issue on the same core edge; there is no finite issue
rate or one-issue-per-cycle cap. A refusal/overflow emits no partial successful result.

Positive-duration scheduled completions, including alignment completion, use phase0
and are processed before phase2 eligibility/grants at the same timestamp. Zero-duration
endpoints remain distinct inline phase2 events under installed U0011; a zero-duration
ack release must precede by observation ordinal a subsequent reservation using it.
Phase2 reaches its existing ready/grant fixed point in canonical owner/request order.
An issue alignment ending now precedes its zero issue service; conversion precedes the
first transfer phase. No later event may be used as an earlier cause. Reservation order within an opportunity follows the ready/request tie rule;
request eligibility at different opportunities is preserved without serializing clocks
or independent pools. Existing schedule-time event sequence and global ordering survive.

### Exact /3 inventory and endpoints

Every DMA fragment, read or write, prepends exactly two activities, including zero
alignment: `dma_issue/alignment` followed by `dma_issue/service`. Both use its canonical
flattened DMA engine owner, category memory, receiving domain core, occupies_resource
false. Alignment is [reservation_ps, issue_ps], ready_ps is job ready_ps, with endpoint
kinds TASK_READY / DEPENDENCY_READY. Service is [issue_ps, issue_ps], ready_ps issue_ps,
with endpoint kinds TASK_READY / DMA_ISSUE. All four endpoint observations are distinct
and correctly joined; service dispatch follows alignment completion, then service
completion follows dispatch. Both have exact next_edge clock witnesses with n_cycles0.
The first former transfer phase becomes ready at issue-service completion. No dma_issue
transfer boundary or resource/busy interval is added. Existing boundary byte accounting
and request/response/DRAM/core-port entry/exit laws remain unchanged.

/3 DMA observation extends the existing record with REQUIRED reservation_ps: u64 for
DMA and null for unicast. Unicast gains neither issue phase nor reservation. /3 has
separate activity/queue/DMA carriers; /2 enums and required fields remain unchanged.
Each DMA fragment has exactly one ledger row in EACH of these populations, including
zero-length rows, with null activity_id and clock_domain and its DMA engine owner:

| queue_id | population | interval |
| --- | --- | --- |
| dma_waiting:E | waiting | [job.ready_ps, reservation_ps] |
| dma_pending:E | pending | [reservation_ps, issue_ps] |
| dma_inflight:E | inflight | [issue_ps, complete_ps] |

These are separate populations, never summed as duplicate inflight counts. Ordinary
core-domain activity queues remain attached to each issue activity: waiting [ready,start]
and service [start,end], with explicit service rows and the installed optional empty
ordinary waiting row. Ledger rows are always explicit. Half-open population/finite-window
rules remain installed: zero-length intervals contribute zero residence area, preserve
endpoint flow counts, and null residence remains restricted to zero flow. Atomic
conversion prevents capacity double counting even at zero alignment.

### Exact reservation-order witness

/3 additionally requires `reservation_opportunities: Observed[DmaReservationOpportunity]`.
Each record has `opportunity_ordinal: u64`, `t_ps: u64`, `event_cursor: u64` and
`granted_request_ids: tuple[NonEmpty,...]`. The ordinal is contiguous from0. The cursor
is the number of existing endpoint observations already emitted immediately before the
real reservation pass, and grants are appended as the scheduler actually reserves them.
It is NOT an issue-alignment dispatch ordinal. This is a separate transition witness,
not a new activity, clock, event-wheel endpoint, traffic count or resource interval.
All requests appear in exactly one grant list, and each binds reservation_ps to t_ps.
Empty lists are required. No successful partial witness is permitted.

The initial witness is ordinal0/time0/cursor0. Each inline terminal completion implies
cursor=completion_ordinal+1. A scheduled phase0 terminal implies the cursor after the
entire same-time phase0 completion batch; multiple terminals in that batch imply one
opportunity. A dependency job is complete at a cursor only when ALL its sequence terminal
completion ordinals precede the cursor. A credit is available only after its acquired
request's terminal completion precedes the cursor; earlier pending reservations still
occupy slots. This distinguishes opportunities at identical timestamps.

The independent checker MUST reconstruct the exact opportunity inventory from terminal
endpoint transitions, then derive all eligible requests and available credits at each
cursor. It must verify the complete earliest grant list and ready/request ties against
that derived set. Trusting the claimed list, using readiness timestamps alone, accepting
alignment-dispatch order as reservation order, or checking only capacity is insufficient.
A fully joined forgery that moves a not-yet-eligible request into an earlier opportunity
must be refused even if its timestamps, grants, queues, causes and capacity agree.

B-ISSUE-ORDER-01 is the discriminator: with cap1 and r00 dependent on inline zero-hop
unicast, initially ready r01 reserves/issues0 and completes60000; r00 reserves/issues60000
and completes120000. The paired graph makes r01 dependent, reversing these roles. Both
ready timestamps remain0, and the unicast completion creates a separate empty opportunity
while capacity is occupied. The exact historical B inputs remain unchanged.

This revises the UNINSTALLED /3/model2 proposal in place; it does not revise installed
/1 or /2 semantics. Prior draft /3 results without this required witness are retained
historical evidence, not accepted as outputs of the revised proposal. Installation and
future bindings must name the exact revised schema/checker/source hashes. No decoder
fallback, synthetic retrofit of historical outputs or silent receipt upgrade is allowed.

### Exact causes, job start and allocation

The first issue alignment carries all and only eligible tight dependency/credit causes.
Dependencies are declared predecessor-job terminal activities at the dependency's actual
job completion. For /3, approved correction a1 defines credit attribution at the request's
RESERVATION OPPORTUNITY CURSOR, not at alignment dispatch and not by timestamps alone.
Let t=reservation_ps and c=the event_cursor of the unique opportunity granting this request.
Strict waiting requires t > job.ready_ps. Preserve the prior-saturation predicate: the
other same-engine requests with reservation_ps < t <= complete_ps number exactly the
engine's credit limit. Without both strict waiting and this prior saturation, the credit
cause set is empty, including when dependency readiness equals reservation.

When both predicates hold, the exact eligible set comprises ALL acquired same-engine
requests that release at t and whose terminal observation ordinal is STRICTLY LESS than c.
Every supplied credit predecessor must be a terminal activity and satisfy that ordinal
bound. A release at or after c cannot explain this reservation, even when its timestamp
matches t and its terminal precedes the later issue-alignment dispatch. Pending
reservations consume capacity but cannot themselves be releasing causes. A release at an
earlier timestamp is not tight. Alignment delay alone is not credit waiting.

Include eligible same-time releases observed before c even if they precede the previous
opportunity. Do not restrict the set to releases since the previous opportunity. This is a
same-time eligible-release ATTRIBUTION SET, not exclusive assignment of a particular freed
slot to a request. Earlier grants at t do not consume or remove an otherwise eligible
release from the attribution set. Capacity itself remains enforced from actual prior
grants and terminal order at each cursor. This /3 definition supersedes timestamp-only
credit-set readings and exclusive-slot interpretations of "actual blocking activity";
historical /2 text, bytes and verdict scopes remain unchanged.

In the mixed cap2 cc0-v3 control, r00.read_port completes at ordinal50; the write ack
alignment completes at51 but does not release credit. r02 is granted at cursor52 and has
only r00.read_port as its credit cause. r01.ack terminates at55; r03 is granted at cursor56
and includes BOTH r00.read_port and r01.ack. The gapped counterpart obeys the same ordinal
rule. A7's later ack at53 cannot be a cause for r02's unchanged cursor52, even if the
alignment dispatch is moved to54. Both structural and independent consumers must refuse it.

Structural validation additionally checks capacity at reservation cursors: previous grants
remain active while their terminal ordinal is >= c, and each new grant consumes one slot.
The independent checker still derives complete eligible grant lists and capacity; this
small structural join does not replace that mandatory independent check.

For release60000 on a1GHz core: ready59999 reserves/issues60000 with credit-only cause;
ready60000 reserves/issues60000 with dependency-only cause; ready60001 reserves60001,
issues61000 with dependency-only cause. Both zero alignments remain in the inventory.
The issue service and first transfer phase use immediate sequence links. No issue phase
has a resource predecessor; payload ports/channels retain their existing resource causes.
Canonical critical-path ties, zero-duration causal DAG and complete eligible-cause rules
remain installed. Issue alignment contributes memory attribution, never busy time.

DMA job.start_ps is the minimum reservation_ps across its fragments, NOT minimum issue_ps;
ready_ps remains the maximum declared predecessor completion, end_ps maximum commit/ack.
This follows the installed first-activity summary rule with the new explicit first phase.
A produced nonpersistent buffer allocates at its producer job.start_ps, so a DMA-produced
buffer may allocate at reservation before payload service. Allocation does not claim data
production or work completion. Declared terminal consumers retain exact completion-based
free endpoints. With no terminal consumers, retained output has free_ps null through run
end, as before. Initial/no-producer reservations and @1 accumulator persistence remain
unchanged; @2 exact producer/all-terminal-reader laws remain unchanged. Every actual use
must still be covered. Compute and unicast job/allocation endpoints do not change.

### Installation and verification boundary

Install ADR, typed carriers, mapped JSON schema mirrors and structural validator together;
install the independently reviewed /3 checker and exact native schema/runtime changes as
one reviewed source transition. Keep the old /2 checker, schemas/fixtures/receipt bindings
as historical controls. Native snapshot exports must explicitly select model/1 for old
K2/component schemas and model/2 for the new /3 schema, preserving old snapshot bytes.
New source/model/build identities and future profile/selection joins are mandatory; no
old fixed-delay or component candidate identity is inherited by the amended model.

Before installation require discriminating read/write issue-gap, cap1/cap2, independent
engine, same-time release/dependency boundary, zero-alignment and unlimited same-edge
issue controls, producer allocation endpoints, exact queue inventories, false/missing
causes, early acquisition, capacity double booking, false issue-rate delay and restored
baselines. Private exports and synthetic anchors do not install this amendment or create
authority. Human L1 and later public/D3 acceptance remain separate. Existing bounded
construction trace gaps remain unaccepted and no trace rebuild is implied by this change.


### Prospective first-use restrictions and consumer binding (Stage 2 F2/F4)

Approval U4-issue-edge-credit-causes-a1-v1 and renewed approval
U4-issue-edge-F2-scope-reconfirmation-v1 authorize correction direction/private proposal
work only, not installation or public execution authority. The renewed approval widens
only F2; the accepted a1 /3 law and F4 consumer-binding behavior are unchanged.

Native component model1 / observations2 first use is BLOCKED for same-engine,
same-instant acquired-credit releases regardless of read/write direction, including
write/write. The established affected subclass has a strictly waiting request reserved
or issued between releases observed at that timestamp. Unclassified same-engine,
same-instant acquired-release cases are blocked regardless of direction; write/read
labels alone never establish safety. This proposal explicitly takes the broader
conservative policy of blocking the entire same-engine/same-instant acquired-release
class. The prospective offline classifier is explicitly more conservative: any /2 graph
with multiple requests on one engine remains blocked without separately reviewed complete
timing classification. It implements no timed-safe exception. At most one declared request
per engine proves only absence of this F2 class for an independently validated graph,
never execution authority or relief from F4. Any future prospective exception must
prove its classification from actual release and reservation/issue order, receive
separate resolution and approval, and carry exact reviewed prospective selection and
consumer bindings; direction alone is not such proof. /3 is unaffected.

cc0-v1 and ww0-v1 are preserved, hash-bound reproducers of the unresolved /2 discrepancy;
cc-v1 additionally retains its known issue-gap limitation. The restriction is neither
a /2 repair nor a waiver. Its exit requires a separate exact reviewed resolution of the
law/implementation/consumer discrepancy, discriminating regressions, renewed approval
and explicit prospective first-use selection/authority. Historical /2 source, checker,
carrier bytes, the historical106-case selection, receipts and verdict scopes remain
unchanged. Reconstructed reviewer fixtures are labelled as reconstructions, not new
native executions or runtime authority.

A future first-use record MUST bind the engine model, observation format, structural
validator and independent checker by exact source/schema identities. Component model1
selects observations2 and check_v2 only subject to the F2 restriction. Component model2
selects observations3 and the exact revised check_v3. Structural validation AND the matching
independent checker must both pass. A model2 job cannot obtain evidence from check_v2
acceptance, even if that frozen checker alone lacks model binding. Do not choose the
checker only from a result's self-declared format. Frozen /2 checker bytes stay unchanged;
new wrapper/selection requirements are prospective B/coordinator-owned records. No old
K2 HostRecord, selector, placement or runtime authority authorizes new component identities.
Human installation, genuine L1, U0024 limits and later public authorization remain separate.

## Basic provenance and ordinary native execution — simplification amendment

This prospective amendment records Javid's direction: retain the native engine in U4,
remove the later assurance/authority expansion, and return provenance to the basic purpose
in Reza's handoff 1d497be1a1c3b7fc621391d9f9c715cccaa09e97. It does not restore that old
fork-first schedule or move full tables back into U4. Existing model laws, supported scope,
independent verification, U4b reference readiness and later product work remain unchanged.
The exact text and carrier/source transition require the repository's normal protected-file
installation procedure. No old approval record is rewritten or called a passed test.

### Ordinary installed software, basic provenance

An installed rk-uarch package and its native executable must run supported simulation jobs
without the development checkout, .git, source/build evidence archives, compiler logs,
reviewer files, source inventories, per-executable approval records or root-owned host
selectors. Use the existing package/engine/model version vocabulary; a source repository
is not a runtime dependency. The current /4 schema accepts package version `0.0.1` only,
without build identifiers, and run/replay require the same installed version. That version
does not distinguish builds. Compatibility policy is deferred until a version change is
required; no cross-version replay support is promised. Record the software/engine/model and
schema/mapping versions needed to interpret
the result, and the existing hardware/request/prepared-input/result/table data hashes.
Record model assumptions and scope as already required. Do not replace missing provenance
with fictitious versions or fabricate unknown identities.

No executable digest, compiler-lock hash, implementation-file hash or full build-input
fingerprint is required in the ordinary job, result, package acceptance or launch path.
Ordinary execution does not reread/hash developer artifacts or re-run a release review.
Data hashing remains for the actual job, hardware, prepared workload and result; removing
executable attestation does not remove data integrity or model/version compatibility.
Use installed version metadata and supported capabilities to detect ordinary mismatches;
this is reproducibility metadata, not proof against a malicious executable or environment.
Runtime modules and schemas must ship in the package, including consumers actually needed
for result validation. A development test suite is not a runtime dependency.

### Development and verification

Keep the accepted compiler/dependency pins, Cargo.lock, licence checks and normal build/test
commands. Build and test normally with the accepted local environment under U0024. Keep
ordinary logs useful for debugging; they are not a transitive launch prerequisite. Do not
replace the retired system with a new versioned review/attestation manifest framework.
A clean build checks that the package can be constructed from its stated sources/tools;
no exhaustive filesystem read proof, compiler-line allowlist or independently bit-identical
executable rebuild is mandatory. Historical binary checksums may remain in old receipts;
new ordinary runtime code neither computes nor requires them.

Keep tests of actual simulation laws, capacities, ownership, dependency order, useful work,
observations, unsupported scope and malformed input/output. Keep independent mathematics,
required human L1 workings, discriminating faults, saved-input replay and specified
fresh-process/debug-release output determinism. Table-build and worker determinism refer
to output data, not to the byte identity of compiler-produced executables. Retain status,
timeout/resource limits and complete error reporting. Where containers are used for tests,
cleanup may affect only full IDs created and owned by that test, never a label-wide sweep.
No weakened timing law, hidden tolerance change or invented passing evidence follows.

### Explicitly withdrawn operational gates

Withdraw mandatory root-owned sealed runtime placement, HostRecord/HostSelector chains,
per-build human runtime authority, compiled finite-case/corpus authority, D3 approval-record
chains and build-evidence consumption as ordinary execution prerequisites. A user selects
an executable/package and supplies valid inputs; they do not need a coordinator to approve
each executable or workload. Test-only variants still cannot masquerade as supported product
predictions. Preserve semantic/capability validation and explicit test invocation where
needed, without binding ordinary jobs to a pre-approved inventory of exact file hashes.

Withdraw the custom Python startup-attestation/loader framework and A-F3 assurance gate.
The operating assumption is a normal user-controlled installation and process: declared
package dependencies, normal import behavior and no arbitrary pre-start tampering by the
user/environment. Validate installation/import behavior in development and keep modules
correctly packaged. This does not claim to resist a hostile interpreter, malicious startup
hook or process already under another program's control. A-F3 is retired by scope change,
not fixed, passed or waived through invented startup evidence. The previously blocked
substitution/revert experiment is not retried, reconstructed or transferred.

Withdraw exhaustive construction tracing, tracer canaries, trace-based diagnostic policy
and read_audit_complete gates. Historical missing/unknown trace records retain their true
status. Retire trace and startup/read/binary-assurance prerequisites together rather than
setting old booleans true or satisfying them with placeholders. Ordinary compiler output
is handled by compiler status, artifact presence and existing test/lint policies, not a
per-line human allowlist. Failure/timeout must not become success.

### Transition and supersession

This amendment supersedes U4-build-provenance-scope-v1 and the later bounded-provenance
review-record successors wherever they retain executable/source evidence or startup
assurance as runtime gates. It replaces the operational authority portions of this ADR's
U4 M/host and runtime/deployment clauses, the later activation proposal items 1–8 insofar
as they demand the withdrawn mechanisms, and their dependent implementation instructions.
Exact original model laws, corrected issue-edge /3 behavior, hardware/model admission,
finite resource limits, result-consumer semantics and genuine human L1 remain applicable.
The unresolved affected historical /2 behavior stays restricted until separately repaired;
this simplification is not a model correction or an inaccurate historical success claim.

Use an explicit minimal carrier/API version transition where current strict schemas require
implementation_hash, compiler_lock_hash or host-approved profile/engine anchors. Do not
smuggle constants or dummy hashes through the old schema or build a second workload IR.
Keep historical results and review reports unchanged. Old runtime proposals may remain as
history but cannot be imported, initialized or required by the new ordinary execution path.
Obsolete gate tests are explicitly retired/replaced; their historical findings are not
relabelled fixed. New tests cover the simpler supported contract and retained correctness.

The native-first U4 scope and U0023/U0024 scheduling remain. Human ownership of protected
repository paths, artifact generation/adoption, silicon measurement permissions, accuracy
claims and independent milestone review are unchanged. They are development processes,
not approval files that every user must install or present at runtime. No scope expansion,
new engine, benchmark grid, remote infrastructure or new security/attestation project is
part of the simplification. Do not claim U4/G3a closure from completing it.


### Concrete carrier transition proposed with the ordinary implementation

Keep existing `/3` carriers and schemas for historical interpretation. Add strict
`OrdinaryBundle` (`uarch-prepared/4`), `OrdinaryJob`/`OrdinaryResult` (`uarch-engine/4`).
Reuse the existing mapped points, TaskGraph, assumptions, hardware and observations `/3`.
`SoftwareIdentity` records package `0.0.1`, engine `native-stage/2`, and model
`native-intervals` version `2`. `SoftwareProducer` records name/version. No implementation
hash or compiler-lock hash remains in these new carriers; no dummy identity is substituted.
`OrdinaryAdmission` retains checkpoint B, production/test invocation and eligibility, with
no profile hash/case id. No registry/profile/host fields exist on the new job. Production
still requires the existing supported hardware hash and model capabilities; this hash is
input identity, not authorization. Test hardware requires explicit test-only invocation.
Old results are neither migrated silently nor regenerated. The analytic path is unchanged.

Protected carriers and source install together from the exact combined proposal patch.
The author may validate a disposable reconstruction; human installation and focused
independent review remain outstanding. This does not establish U4, G3a or shipping closure.
