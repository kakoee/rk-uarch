# One proposed semantic completion

Proposal baseline `418d697`; B join `8b7a647e1cd8fd7c8c70f3a6b2528637713ccd04`;
A's prior package `821dc908a3735ef3225f16b56172e802095d77f0` remains byte-identical.
This addendum chooses earliest release, explicit raw alignment observations, non-clocked
FIFO records, positive-only critical intervals, and job-first ties. These are proposals,
not accepted runtime behavior. No native implementation or run is included.

## Raw edge and owned service are separate public assertions

At1.2GHz, edge(k)=ceil(2500k/3). Edges0,1,2,3 are0,834,1667,2500. The first edge at or
after835 is1667, so raw next_edge(1.2GHz,835,0)=1667. An owned zero-cycle job actually
granted835 completes835 under reviewed K1. Neither answer replaces the other.

Proposed `ClockObservation` in required `observations.clocks` contains job_id, domain,
grant_ps, n_cycles, raw_edge_outcome, aligned_start_ps and completion_ps. The executor
calls the **real raw primitive** at actual grant with n=0 to obtain aligned_start_ps,
independently of its owned-cycle completion branch. Result validation joins these records
to actual grants/completions and the job's setup; Python never fills the observation.
A raw-edge overflow is explicit `TimeOverflow`/null; it must not fail a zero-owned job.
Positive owned cycles still use next_edge(grant,n) and refuse completion overflow.

This is a narrow public **output** amendment, not a new clock-query command, input job
kind or event-injection format. It makes the raw n0 obligation observable through the
same actual fixed-delay subprocess as owned completion. Pure primitive tests remain
private tests and retain their own labels. Without acceptance/implementation of this
output amendment, raw non-edge n0 public coverage remains **not_run**, not discharged by
K1. `adr-addendum.md` and the synchronized U-P11a/build-spec amendment say this explicitly.

Prospective mappings (historical files are not rewritten):

| Retained B row | Proposed new expectation/selection | Distinguishing public assertion |
| --- | --- | --- |
| K06-00 | K06-00/release-v2; same graph/setup | raw0; owned2500 for3 cycles |
| K06-01 | K06-01/release-v2; explicit wait834 retained | grant834, raw834, zero completion834; nondiscriminating by itself |
| K06-02 | K06-02/raw-owned-v2; explicit wait835 retained | grant835, raw1667 AND owned835; old expected1667 remains historical, unaccepted |
| K06-03 | K06-03/release-v2; explicit wait835 retained | raw1667, positive one-cycle end2500 |
| K06-04 | K06-04/release-v2 | raw0, 10^9-cycle end833333333334 |
| All100 K07-{f}-{k} | K07-{f}-{k}/raw-owned-v2; retain exact4×25 pairs, no reduction | grant t_k, raw t_k, zero completion t_k; assert 0≤t_k*f−k*10^12<f from actual raw output |
| K08-clock-overflow | K08-clock-overflow/release-v2 | positive completion overflow; exit2, TimeOverflow, no completed result |
| New ZMAX | root zero-cycle release u64_max at1GHz | raw TimeOverflow/null, owned completion u64_max, idle attribution u64_max, busy0 |

Each new B candidate must have a distinct case-selection revision, recomputed finite
profile identity, independently reviewed expected-outcome inventory, complete job joins
and later real engine identity. The table maps names and expectations, not approved
profile hashes. B's113 historical bundles/profile and100 private wheel schedules remain
unchanged. B's K03 ordering/private schedule obligations remain separate; no clock result
claims arbitrary wheel or sequence-exhaustion coverage. Public mutated-primitive, wrong
zero-branch, wrong actual-grant and dropped-clock-observation tests must fail their exact
assertions and then pass after restoration. Internal primitive success alone never counts.

## Release, readiness, ownership and service

For each existing fixed-delay job, release is its ClockSetup.start_ps, otherwise0. A clocked
job must have duration_ps=0; no competing timing instruction is silently ignored. Positive
n uses next_edge at **actual grant**, not nominal start or dependency-ready time. n=0
completes inline at actual grant. A non-clocked job uses checked grant+duration_ps. General
positive-release ps-only work is not expressible by this choice; if a later consumer needs
it, propose a separate release carrier rather than using a fake clock or hidden job.

A job becomes ready exactly once when released and all dependencies have completed.
Ready=max(release,latest dependency completion); owner FIFO determines grant≥ready.
The native release event sets a prerequisite bit. Early dependency notifications update
remaining prerequisites without enqueuing before release; early release does not enqueue
before dependency completion. No Python delay job, runtime duration preprocessing or
reinterpretation of B's visible wait jobs is permitted.

At each timestamp: finish phase0 completions; dispatch all phase1 root readiness, release
and dependency notifications using `(t,phase,target,seq)`; collect all newly eligible
phase1 jobs and enqueue per owner in canonical job-ID order; then enter phase2. Releases
are scheduled in canonical job order at construction; their sequences are assigned then,
not at dispatch. Owner grants are actual inline phase2 events, with new inline sequence
and ordinal. Inline zeros complete and notify in phase2; newly ready inline jobs append
behind already queued work; within one notification batch use canonical job order, with
K1's lowest-eligible-owner scan unchanged. Do not resort events by target after dispatch.
Each dependency edge produces one DEPENDENCY_READY dispatch, retaining multiplicity;
only roots released at0 get TASK_READY. Positive service completes in phase0; zero service
completes inline in phase2 after its grant. This batching of mixed release/notification
readiness is an explicitly proposed K2
extension preserving FIFO laws, not a claim that K1 already handles release events.

Exact hand cases at1.2GHz (ps; each row independently fixed, not a scheduling oracle):

| ID | Release / dependency complete / owner free / cycles | Ready, grant, raw alignment, end | Mutant discriminator |
| --- | --- | --- | --- |
| R-Z | 835 / none /0 /0 | 835,835,1667,835 | Aligning zero gives1667 |
| R-P | 835 / none /0 /1 | 835,835,1667,2500 | Ignoring release gives834 |
| R-BEFORE | 835 /500 /0 /1 | 835,835,1667,2500 | Dependency-only readiness500 is wrong |
| R-AFTER | 835 /1200 /0 /1 | 1200,1200,1667,2500 | Release-only readiness835 is wrong even though end matches |
| R-OWNER-P | 835 /none /2000 /1 | 835,2000,2500,3334 | Nominal-start conversion gives2500 |
| R-OWNER-Z | 835 /none /2000 /0 | 835,2000,2500,2000 | Bypassing owner gives835; aligning zero gives2500 |
| R-TIE | 1000 /1000 /1000 /0 | 1000,1000,1667,1000 | Extra alignment or duplicate enqueue/completion fails |

Real future fixtures use explicit ordinary jobs for the named dependency and owner
occupancy, declared by the corpus author. These table columns are hand premises, **not**
a new executable input format. `test_semantics.py` checks these finite equations only.

Concrete same-time1GHz ordering case: a(owner0,1000) root; b(owner0,0) clock-release1000,
n0; c(owner0,0) depends a; d(owner1,1000) depends b,c. At1000 a completes phase0. Phase1
releases b and notifies c; enqueue b then c by ID, independent of their event sequence.
Phase2 grants/completes b; its notification leaves d blocked; grants/completes c; final
notification enables d, then grants d. At2000 d completes phase0. Assert one grant and
completion each, b/c end1000, d end2000; no phase regression; all phase1 dispatches precede
any phase2 grant; resource0 busy1000, resource1 busy1000. Reverse enqueue order, early d,
double release and re-queued zero completion are distinct failing controls. If c's ID were
lexically before b, phase1 FIFO order reverses; a later inline-enabled lower ID does not
preempt already queued work. Add a second owner release at1000 to discriminate target
order from job-ID order. These are unexecuted public obligations.

## Complete observation choice and causal derivation

Events add TASK_RELEASE, DEPENDENCY_READY, OWNER_GRANT. Jobs add release_ps. Every fixed-delay
result has observed clocks (empty iff no clock setup) and observed queue membership.
FIFO waiting [ready,grant] and service [grant,end] rows are emitted even when zero length,
clock_domain=null for **all** fixed-delay owner queues: cycle-controlled service does not
make FIFO arbitration a physical core clock. Order by (queue_id,item_id,population).
Component queue domains remain non-null and keep their existing required observed status.
DMA/transfer/allocation remain explicitly unrepresented for fixed-delay, with no invented
physical observations. Resource occupancy rows are positive [grant,end], ordered by
(owner_id,job_id); zero service remains visible in events/jobs/queue records. Busy time is
interval union per declared owner, including zero for idle owners. Event count counts
actual Dispatch only; max-live counts actual scheduled arena occupancy, not inline events.

Only completion constraints tight at the actual grant can be job blockers: declared
dependencies and actual previous completed owner job, with earlier completion ordinal.
The earlier owner across an idle gap is never causal. List all tight job IDs sorted;
choose smallest job ID, then owner ID. When release ties a job constraint, prefer the job.
Follow the chosen cause of the latest-ending job (tie: smallest job ID, then owner ID),
including zero bridges in the causal walk. Emit **only positive-length** critical records.
The positive service following a zero bridge retains that immediate zero predecessor ID;
job observations preserve the omitted zero chain. All-zero **elapsed-duration** execution has exactly an empty
critical_path.records, attribution0 and busy0, with real event/job/queue inventories.

CriticalInterval.kind distinguishes service from release_idle. Service requires an owner;
release_idle is [0,release] of the causal root, predecessor=null, limiting_resource=null,
category=overhead. It describes the causal origin offset, not physical service and not a
claim that unrelated owners were idle. R-P: release_idle[0,835],service[835,2500], duration2500,
busy1665. R-Z: release_idle[0,835] only, duration835,busy0. If a dependency or previous owner
bounds the grant, follow that actual chain instead of adding release idle again. A's O/F/Z/I/T
and B's K01/K03/K04 remain separate graphs; preserve their hand answers and old records.

The patch retains identity, inventory, time/phase, busy-union and attribution-sum checks.
A typed idle branch adds a new null-resource case; it does not allow null on service or
weaken service checks. Proposed fixed-delay checking also validates complete clock/release/
grant/completion inventories, strict FIFO eligibility from dispatch order, ps/cycle duration
joins, typed queues, exact causal partition and zero conventions. Structural consistency
cannot authenticate execution: real handler instrumentation, independent B tests and
fault/restored controls remain required. No completed result is serialized by this package;
synthetic tests use partial namespaces that cannot parse as EngineResult.

## Exact affected protected surface

`complete.proposed.patch` includes mapped.py, every changed generated mirror, the new
structural test, the affected existing admission test and prospective loader test adjustment,
U0011, and synchronized U-P11a/build-spec text. MappedEngineJob's schema change is the
ClockSetup semantic description; MappedEngineResult and Observations gain the output
fields. Generate all12 mirrors and retain only actual diffs; patch-manifest.json records
exact paths and pre/post hashes. No historical fixture/result/package is rewritten.

The two prospective positive-test adjustments remove dual nonzero-ps/cycle timing and
reseal the synthetic test closure. They do not change published loader source or claim a
loader defect. Prototype arithmetic and partial structural controls are not native passes.
