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
