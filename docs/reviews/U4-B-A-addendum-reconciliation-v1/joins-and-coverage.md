# Exact four joins and prospective coverage

Subject A1a52fa8, complete patch672ac0ef… and plan4a5cbb16… (full hashes in README/identity).
This is independent B review of actual proposal bytes, not human acceptance. The original
8b7a647 and5422511 packages, fixtures, all17 timing literals and receipts remain immutable.
B's `projections.py` imports the old literal/causal answers from the private export, supplies
explicit finite event premises, and translates them into typed **partial subrecords**.
No scheduler, A result-construction helper, native process or complete EngineResult is used.
Unique synthetic sequence labels test structure; they are not claimed schedule allocations.
Every partial projection refuses MappedEngineResult.model_validate. Actual instrumentation,
source/binary authority and public execution remain untested.

| Join | B disposition | New exact checks / prospective difference |
| --- | --- | --- |
| (a) Raw versus owned | **Agree** with distinct actual ClockObservation and owned service. | Same K06-02 graph: a-wait ends835; b-clock grant835, raw1667, owned835. Conflating either field refuses. Raw output must come from actual native next_edge(grant,0), not this Python projection. Positive cycles retain actual-grant conversion. |
| (b) Queue | **Agree** with observed fixed-delay waiting/service, null domain. | All17 witnesses require2 rows/job including zero-length rows. S15 ps-only and S06 clocked-zero need no physical domain. Removing a zero row or assigning core refuses. This prospectively replaces B's unrepresented-queue recommendation, not old records or component queue evidence. |
| (c) Zero bridge | **Agree** with positive-only critical records and immediate links. | S08 remains duration5000, busy0=3000,busy1=3000. Intervals a[0,3000],c[3000,5000]; c.predecessor=z, z.blockers=[a], c.blockers=[z]. Dropping z from the link refuses. A zero-length CriticalInterval now refuses. This is a representation change, not removal of the zero job or its cause. |
| (d) Phase and batching | **Agree with the law; disagree that the exact validator fully enforces it.** | S07 completion phase0, release/readiness phase1, then grants/zero closure phase2; wrong phase refuses. S09 reversed phase1 notification order still grants b,c by canonical ID. However an inline dependency notification can precede its zero completion and pass; see the exact counterexample and minimal amendment below. |

At1GHz and u64_max=18446744073709551615, raw alignment is18446744073709552000,
out of range; one positive cycle would end18446744073709553000. A zero-owned job may
legitimately return raw TimeOverflow/null while completing u64_max. Changing its setup and
clock record to n1 while reusing zero completion refuses. Separately, at1THz alignment at
u64_max fits but n1 would endu64_max+1 and refuses. These are literal structural controls;
actual positive-overflow exit2/TimeOverflow/empty stdout is still a native obligation.

## One substantive counterexample: notification before zero completion

Unchanged B S07: a(owner0,ps1000), b(owner0,clock release1000,n0,depends a),
c(owner1,ps0,depends b). Expected phase2 at1000:

`grant b → complete b → notify c → grant c → complete c`.

Swap only the adjacent `complete b` and `notify c`, retaining original unique sequence
IDs and reindexing actual-position observation ordinals. The trace becomes:

`grant b → notify c → complete b → grant c → complete c`.

All timestamps, phase monotonicity, jobs, durations, counts, busy/critical intervals and
immediate causal links remain identical. A's exact validate_fixed_delay_observations accepts
it. The negative test fails **DID NOT RAISE**, not an import or schema-construction error.
The full outer validator's other event checks also remain invariant: it checks unique
ordinals, time/phase monotonicity and identity/count/interval joins, with no additional
notification-source ordering check. We did not manufacture a full result to bypass that
boundary; this is an isolated actual-validator counterexample plus inspection of its caller.

Cause: notification inventory matches only `(recipient,time,phase)` multiplicities.
Completion-before-**grant** is checked, but completion-before-**notification** is not.
The smallest proposed amendment is [notification-order.proposed.patch](notification-order.proposed.patch):
a20-line check after that existing multiplicity equality, requiring a one-to-one matching
of earlier completion ordinals to notification ordinals within each identical
recipient/time/phase group. Sorted pair matching establishes existence; no new source-event
field, schema, scheduler or timestamp alteration is needed. Indistinguishable notification
records cannot prove a unique parent identity, which is why instrumentation/fault checks
remain necessary. All existing guards remain.

Exact A postimage mapped.py3c207d72… plus this delta gives dee6903c…; see guard-identity.json
for full before/after/delta hashes. The other nine A postimages remain exact. The delta is
unapplied live and requires a **new combined reviewer binding**. Evidence: exact-A baseline
fails the negative assertion; guarded31 checks pass; reverse restores the same failure;
forward restores its pass; guarded123 affected regressions and both type checks pass.
This concrete correction is the only requested A/coordinator reconciliation, not a restart
of corpus design. The coordinator recommendation is not treated as approval of either patch.

## One prospective mapping, preserving membership

`coverage-delta.json` enumerates all113 old IDs and maps them to the proposed revision,
retains100 K07 and100 private Wheel schedules, lists all17 S witnesses and each additional
obligation. It contains no accepted profile, registry, binary or host hash. Existing bundle
bytes stay pinned; future profile/selection identities must be recomputed and reviewed.

| Selection | Prospective assertion / status |
| --- | --- |
| K01/K02/K03-owner/K04/K05/K05-chain | Original intervals and ownership remain. Add release0, exact observed queues, dispatch/causal links and positive-only critical projection. All-zero elapsed time gets one empty critical representation. |
| K06-00..04 | Same inputs; raw/owned pairs:0/2500,834/834,1667/835,1667/2500,0/833333333334. K06-02 old completion1667 remains historical/unaccepted; new owned835 is prospective only. |
| All100 K07(f,k) | Retain4×25 exact pairs and never-early rational bounds. Both actual raw alignment and zero completion equal t_k. Off-edge K06-02 remains independently required. |
| K08-clock/add-overflow | Preserve both admitted runtime refusal cases; no success result. Distinguish raw-only diagnostic overflow from owned positive overflow. |
| S01–S17 | Retain every existing timing, busy and chosen-cause literal. Translate release to phase1, queue domain to null, omit zero critical rows but retain immediate links. No arbitrary new timing cases or engine identities. |
| Additional ZMAX / overflow split | Root zero at1GHz/u64_max has raw diagnostic overflow and owned success; separate raw-success/positive-overflow control at1THz/u64_max. Need actual future admitted profile/registry joins before native use. |
| Additional notification-order control | S07 bad adjacent inline notification/completion swap must refuse without changing total duration. New guard proposal above; real event mutation/fault/restoration remains required. |

Public raw-clock coverage is now **representable**, conditional on acceptance and actual
instrumentation of A's ClockObservation output. B5422511's proposed raw-only private exception
is prospectively unnecessary; no private primitive run is relabelled public. Retain direct
private clock controls as additional evidence. The sole residual representation exception
proposed by A's exact ADR is arbitrary Wheel/Arena insertion/reuse/sequence-exhaustion probes:
all100 private schedules and faults remain, all representable ordering/ownership and reached
timing faults repeat publicly. This exact exception still needs human acceptance. Without
it, literal all-case public coverage remains blocked. No input event-injection IR is added.

## V01–V28 boundaries retained

| V | Stage / prospective mapping and outstanding obligation |
| --- | --- |
| V01 | K2 strict public syntax/admission R01–R21, complete input/result/host closure and refusals; B component-only admission later. |
| V02 | K2 original K01/K02 overlap/FIFO intervals and missing-dependency/global-serialization faults. |
| V03 | K2 actual phase1 batches/phase2 closure, S07/S09/S17 and K03-owner;100 private Wheel schedules plus exact private exception above, no count reduction. |
| V04 | K2 all K06/K07100 actual raw+owned observations and both K08 refusals; off-edge/raw-overflow/positive-overflow new obligations. Private raw tests retained separately. |
| V05 | K2 real owner adaptation/foreign mutation/range and allocation refusals; null-domain queues confer no physical routing claim. |
| V06 | B useful/issued/per-op/repetition C01–C03; no K2 compute credit. |
| V07 | B fragments/payload/transactions/accepted=completed+inflight, final0; C02/C05 joins pending. |
| V08 | B credits1/2/32,33-request max32 and E4 latency/credit fixtures; no K2 queue-model pass. |
| V09 | B shared port/channel serialization, retained distinct B D08 placement. |
| V10 | B two-hop4000/read60000/barrier94000, exact graph/clock/fault joins. |
| V11 | B live capacity/slots/half-accumulator refusal; spill at later first use. |
| V12 | B resident702000/547000 and legal DMA/compute overlap. |
| V13 | B long-stream saturation/latency ±5% with frozen windows, not a five-request substitute. |
| V14 | K2 actual positive intervals and immediate zero links, typed release offset vs busy; S02/S08/S12/S16. Real instrumentation and causal faults pending. |
| V15 | K2 three new processes/mode=six debug/release outputs per trace setting; two qualifying frozen replays and discovery/failure ledger. Not executed here. |
| V16 | K2 saved producer-disabled relocated public replay and full caller rehash refusal; existing loader evidence distinct from future runner. B placement variants later. |
| V17 | B/R/T≥24 valid pairs per applicable relation,≤240 calls/declared ledger including discovery/faults, two qualifying replays. |
| V18 | R/T full layer/head/tail/repeats/E5; no K2 model execution. |
| V19 | R/T paged payload vs allocated capacity and SRAM fused scores. |
| V20 | T complete grid/error/policy/precision, workers1/8 and repeats, steady1/2; missing required points block G3b. |
| V21 | B finite population/window/censoring then U6 stationary≤1%; K2 software FIFO rows are no physical queue evidence. |
| V22 | U6 controlled-host noise/absolute metrics/2× detector; deferred under U0024. |
| V23 | B Q02 inventory32+128−64=96 with completion fault. |
| V24 | B Q01 clipped8000/6000 integrals and initial-member fault; no K2 physical population credit. |
| V25 | B live allocation union/reservation/early-free/alias faults. |
| V26 | K2 S05–S10/S17 and K04/K05 actual zero ownership/closure, new notification-order refusal; B D14 transport remains separate. |
| V27 | R signed≥24 benchmarks/six classes with steady/fused attribution before G3a. |
| V28 | T ragged/error/precision/C2 consistency, no FP8/RoPE substitution, no G3b claim. |

All public process controls remain: wrong executable/build/record refuses before launch;
missing/incomplete/foreign output, bad status, malformed/extra bytes, stale identity and
no-op/empty selection refuse. Operational failures do not count as semantic fault kills.
Modeled picoseconds are distinct from simulator wall time. Component A/B placements and
the two actual human L1 workings remain at their own boundaries; neither is fabricated
or made into a new K2 prerequisite. No public/native coverage is claimed by this proposal.
