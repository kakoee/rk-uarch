# Fixed-delay observations and public test obligations — not executed

These are hand-derived cases and discriminators for B to reconcile against its published
finite corpus. They are not completed EngineResult fixtures, native observations or human
L1 workings. Keep K1's installed code/inventory and historical evidence unchanged.

## Observations from actual execution

A K2 accounting adapter consumes genuine K1 transitions. It must not regenerate a timeline
from expected durations or copy `dependency_resource_predecessors` to the causal field.
That K1 field deliberately contains all declared dependencies plus the previous owner job,
including dependencies that finished earlier and owner jobs before idle gaps.

Proposed accounting instrumentation records, at dispatch time:

- Every **Dispatch** record, including inline dispatch, with actual schedule-time sequence,
  global observation ordinal, timestamp, phase, target owner and original public job ID.
  Ready/Grant/Complete actions are state transitions, not extra dispatched events.
- Ready timestamp on final dependency notification (or root release), queue entry on Ready,
  queue exit/start on the actual OwnerGrant, and end/completed inventory on actual Complete.
  Capture actual queue residence and ownership, including zero-length lifetimes.
- Incoming dependency completion event identities and actual previous owner completion at
  grant. Keep source dispatch ordinals so a zero-time chain cannot become a causal cycle.
- Resource intervals from grants through completions, excluding zero intervals from busy
  measure. Preserve zero completion in job/event records. Busy time is union per owner;
  include every declared owner with 0 if it had no occupancy.
- Actual event arena high-water mark (queued live events, excluding inline transitions),
  dispatch count and completed-job count. The installed Outcome does not expose max-live
  events; instrument the wheel/arena in a later reviewed implementation, never substitute
  capacity, total events or zero for the high-water metric.

At each job grant J, compute tight enabling predecessors from actual observations:
D is the set of declared dependency completions; P is the actual previous completed owner
job, but only if it constrained this grant. A predecessor is time-tight if its completion
is J.start_ps and its causal dispatch precedes J's grant. For a queued J with start>ready,
P bounds the grant; earlier dependencies do not. For an idle owner after a dependency
completion, the final/latest dependency bounds readiness; an owner job ending earlier is
not a blocker. Retain all tight candidates in sorted `blocking_predecessor_ids`;
choose equal longest causes by lowest public job ID, then resource ID, as the accepted
interface specifies. Record distinct readiness/owner evidence internally even if IDs
coincide. At zero-time ties use actual dispatch order to prevent self/forward/cyclic edges.

Build the critical path backward from an actually last-completed job (ties use lowest
job ID then resource ID), following its chosen tight cause, retaining zero-duration
bridges. Reverse the chain and emit intervals [start,end] of those actual grants/services;
check it partitions [0,duration] without gaps/overlap. Fixed-delay occupancy is proposed
category **overhead**: it has no compute/memory/NoC model semantics. A resource wait is
represented by the blocking predecessor's occupancy, never charged a second time on the
waiting job. A zero bridge has [t,t], zero charge and a real predecessor link. All-zero
execution has duration 0, zero attribution, nonempty actual events/completed jobs, and an
empty or zero-length causal partition consistently chosen by the final convention.

The adapter must check each dependency completes by readiness, FIFO grant order, no
simultaneous occupancy of a single owner, cause-edge membership/time tightness, dispatch
order and last-end=duration. Missing provenance refuses `IncompleteObservations`; arithmetic
alone cannot recover a missing actual event. These strengthen the installed validator,
whose current checks cover identity/inventory/order/union/partition but do not establish
causality. Preserve every installed `validate_result` condition.

For kernel_fixture: op/group/repeat/tile fields are null. Useful MAC/vector/cast counts
increment only on corresponding completed work; fixed-delay jobs have none, so those
modeled work counters are exactly 0, not copied from graph totals. DMA/transfer/allocation
channels are `unrepresented` with explicit fixed-delay reasons, not invented empty physical
observations. Queue membership may likewise be unrepresented until clock-domain semantics
are resolved below. Diagnostics and fidelity are null for unmodeled subsystems; per_op is
empty, u_c0_duration_ps is null, energy unknown/unverified. Complete owner/busy and
unrepresented ledgers are explicit. Trace derives from the same observed records;
trace off/on changes only trace_hash, with equal numeric projection and identical bytes
within each setting. No optional trace controls whether mandatory observations exist.

## Concrete semantic conflicts and proposed resolution

1. **Public event vocabulary.** Installed K1 dispatches `DependencyReady` and `OwnerGrant`;
   installed EventObservation.kind lacks both. Mapping either to TASK_READY or omitting
   them silently would falsify dispatched events and metrics. `event-kinds.proposed.patch`
   adds `DEPENDENCY_READY` and `OWNER_GRANT` to the protected carrier and exactly the two
   affected schema mirrors. It has a read-only apply check and pre/post hashes. It is
   **unapplied** pending human reconciliation/install. Do not alter installed validators
   or claim result readiness until this is resolved. Preserve the monotone (time,phase)
   rule: inline phase-2 closure may visit owners in descending ID order; sorting events by
   target afterward would destroy actual dispatch order. Unique ordinals record dispatch.
2. **ClockSetup.start_ps and zero cycles.** The installed carrier binds domain/start/cycles
   but K1 has no root release input; its nonzero cycle delay calls next_edge at actual grant.
   K1 intentionally completes zero-cycle jobs inline at grant, while the raw next_edge
   primitive with n=0 aligns to the next edge. Do not compute a Python duration or insert
   a hidden delay job. Proposed first-use convention: clock setup means earliest job
   release `start_ps`; readiness is max(release, dependency completion); after actual
   owner grant, n>0 uses next_edge(domain, grant, n), n=0 uses grant. Require the fixed
   duration field to be 0 for a clock-driven job to remove dual timing instructions.
   This needs explicit semantic reconciliation and native release-event support. Until
   accepted, no nonempty clock setup is executable at K2, even though the M loader can
   validate its complete joins. Do not exclude B's clock cases to claim a complete pass.
   Raw next_edge(1.2GHz, 1, 0)=834 and a zero-cycle queued job at grant 1 completes at 1
   are deliberately different tests. Freeze this distinction with B.
3. **Idle before release / attribution.** For a job released at t>0, [0,t) is part of elapsed
   duration but has no preceding job occupancy. Proposed representation is an overhead
   interval with cause_job_id equal to that job, predecessor_id null and its declared
   owner, backed by the actual release event. Explicitly label this external start offset,
   not resource busy time. This interpretation and a release-event kind (propose
   `TASK_RELEASE`, additional to the two-kind patch) need a separately reconciled exact
   protected delta. The two-kind patch is necessary but not sufficient for clock release.
4. **Queue clock domain.** FixedDelay has an arbitrary owner and no domain; QueueObservation
   requires core/noc/dram even for pure-ps synthetic work. Do not invent a physical clock
   domain. Either accept `unrepresented` for this channel at fixed-delay (already permitted
   by installed validate_result), or propose an explicitly non-clocked queue carrier if
   the public corpus requires queue records. Grant/ready timestamps still support exact
   FIFO checks. No physical DMA/queue model claim follows.

Items 2–4 are decision proposals, not changes to U0011 or M semantics. Their unresolved
status blocks corresponding public execution/results, not saved-input loader publication.

## Hand-derived cases and discriminating faults

All numbers are ps. Roots ready at 0; dependencies and owner FIFO determine other starts.
IDs below are public IDs; ties use their lexical order. Every test must check raw event
and job records as well as duration, so an aggregate-only surviving mutant is a failure.

| Case | Input and hand working | Required output / fault killed |
| --- | --- | --- |
| O: positive overlap | a(owner0,3000), b(owner1,5000); c(owner0,2000) depends a,b. a=[0,3000], b=[0,5000], c=[5000,7000]. | duration 7000; busy0=5000, busy1=5000; c blockers=[b], path b[0,5000],c[5000,7000]. Serializing independent roots gives 10000; copying a as a c blocker fails causality. |
| F: FIFO owner serialization | a(owner0,3000), b(owner0,1000), c(owner1,2000) depends b. a,b ready0; a first by ID. b=[3000,4000], c=[4000,6000]. | duration6000; b blockers=[a], c=[b]; path a,b,c. Owner bypass gives3000, including b start0. Busy0=4000, busy1=2000. |
| Z: busy-owner zero bridge | a(owner0,3000), b(owner1,1000); z(owner0,0) depends b; d(owner1,2000) depends z. z ready1000, grant/complete3000; d=[3000,5000]. | duration5000, busy0=3000,busy1=3000; z blockers=[a], d=[z], critical a[0,3000],z[3000,3000],d[3000,5000]. Zero owner bypass gives3000; copying b into z blockers or d blockers fails tightness. |
| I: idle owner excludes stale history | a(owner0,1000), b(owner1,5000), c(owner0,1000) depends b. c=[5000,6000]; owner0 idle[1000,5000]. | duration6000; c blockers=[b], never a; busy0=2000. Blind K1 predecessor copying is killed even though duration is correct. |
| T: equal causes | a(owner0,2000), b(owner1,2000), c(owner2,1000) depends a,b. | c blockers=[a,b]; chosen cause a; duration3000 and overhead3000. Reverse insertion must not change canonical bytes or chosen cause. |
| Q: zero chain | a(owner0,0), b(owner0,0) depends a, c(owner1,0) depends b. | duration0; three actual grants/completions, no busy intervals; blockers b=[a],c=[b]; no fabricated positive duration or missing observation. |
| C: fractional domain | root a(owner0) clock core1.2GHz,start0,n3, fixed duration0. | end2500; n=10^9 gives833333333334. Rounded period gives2499 /833000000000 and is killed. Public case waits for clock convention. |
| C0: zero distinction | raw next_edge at start1,n0; separately zero-cycle job released1. | primitive834; job end1 only after grant under proposed convention. Conflation fails. Release portion overhead[0,1], resource busy0. |
| OF: checked overflow | a duration u64_max, b duration1 depends a. | `TimeOverflow`, exit2, empty stdout; no wrapped duration or completed result. |

The immutable selected public corpus must include arbitrary owner IDs, multiple notifications
at the same time, zero-grant ordering across owners, missing owners/dependencies, cycles,
queue ordering, wheel levels/overflow, sequence overflow, rational/u64 bounds and invalid
frequencies from B's applicable K1 catalogue. The table above is not a substitute for that
catalogue, the current 28-test inventory or required human workings.

## Exact public-boundary acceptance matrix

These tests must run against the actual accepted binary and finite host record after
release. Do not install a fake process as the native positive control.

| Test | Exact assertion |
| --- | --- |
| PY-ROUNDTRIP | encode each admitted complete job, run Rust, parse through installed validate_result; exact O/F/Z/I/T/Q timings, busy unions, causal links and partitions above |
| DIRECT-PARITY | Same canonical job via raw stdin and Python writer; identical result bytes; Rust independently validates every join |
| REPLAY-6 | Three new debug processes and three new release processes, each saved/relocated input with Python workload/mapping producers disabled; one exact result-byte digest per trace setting, equal across all six |
| CANONICAL | Installed vectors and numerical/Unicode boundary matrix in K2-proposal; exact UTF-8 and SHA256 equality, not decoded numerical equality only |
| JSON-REFUSE | Duplicate top/nested keys, unknown top/nested fields, NaN/Infinity, invalid UTF-8, concatenated JSON and truncated stdin: exit2, stdout empty, exact categorized error |
| TYPE-REFUSE | bool/string/float where strict integer required, negative/u64 overflow, malformed u128 ratio: semantic/parse refusal before Simulation |
| HASH-REFUSE | Stale job/graph/point/bundle/assumptions/spec identities, cross-v1/v2, broken closure: expected installed category, empty stdout |
| HOST-REFUSE | Rehash full caller graph→point→profile→admission→bundle→job; unchanged host anchor still refuses. Wrong engine/compiler/model, wrong registry/profile/seed/clock/case likewise refuse in direct Rust and Python |
| ORIGIN-REFUSE | Different executable advertising same identity, PATH shadow, stale target artifact/debug-release swap, modified trust record or unaccepted profile: no launch |
| SCOPE-REFUSE | Analytic v1/v2, component, transport, prepared_model, product invocation and negative-outcome profile cannot enter fixed-delay Simulation |
| STATUS-REFUSE | status0+empty/partial/error/noncanonical result, status2+result, unknown status/code, stderr on success, duplicate stderr error keys: no result returned |
| EXEC-FAIL | Signal, timeout, cap, spawn failure, internal panic: distinct operational failure, never an expected semantic refusal pass |
| RESULT-REFUSE | Wrong job/engine/owner/admission; missing job/event; invented work; busy sum instead of union; causal edge from idle predecessor; critical gap/overlap or totals not duration: reject without repairing |
| OBS-FAULTS | Drop an actual inline dispatch, copy K1 predecessor inventory, sum overlapping work, count grants as events, replace max-live with capacity: each fails its explicit observation assertion |
| RESTORE | Each numerical/observation mutant has passing unmodified pre-control, intended distinguishing failure, passing restoration on identical corpus; crashes do not count as numerical kills |

Freeze expected refusal codes/pointers with B for malformed multi-error inputs before
qualifying runs. Each collected applicable case must run nonempty; a skipped or missing
case is not_run. No remote/CI/performance claim follows these proposed obligations.
