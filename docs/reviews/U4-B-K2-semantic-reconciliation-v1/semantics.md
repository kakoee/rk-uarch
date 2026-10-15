# Independent prospective semantics

Status: B proposal and finite host mathematics, not accepted semantics or native results.
The entire `8b7a647` package remains immutable. The raw K06-02 answer1667 is correct;
only its projection into an owned zero-cycle job is prospectively superseded. The old
projection is unresolved historical evidence, not silently corrected evidence.

At1.2GHz, edges are `ceil(2500*k/3)` =0,834,1667,2500,3334,4167,… . The first edge
at/after835 is1667. Thus raw `next_edge(835,0)=1667`; positive one-cycle service granted835
ends2500. An owned zero-cycle job does no clock conversion and ends at its actual grant835.
The832ps difference is exact. Rounding a period to833 produces2499 instead of2500;
using a strictly-later edge at834 produces1667 instead of834 for the raw zero query.
`raw_edge` independently searches a small rational edge table; it is not A's helper.

Proposed public interpretation agrees with A's published821dc90 sketch: a ClockSetup
binds earliest release, domain and cycles; clock-driven fixed duration must be0. A ps-only
job has release0 and no synthetic physical domain. `ready=max(release, dependency ends)`;
owner grant is no earlier than ready and observes FIFO by ready time then canonical job ID.
Positive cycles use next_edge at **actual grant**, zero cycles end at grant. Delayed owner
availability cannot be erased by evaluating at the nominal release. No Python-inserted
wait jobs or precomputed runtime duration implement this extension. The old corpus's
explicit `a-wait` is an actual independent fixture job, preserved as such. S01/S06 remove
that crutch in the proposed public mapping: their release must be genuinely implemented.

The complete literal input, job intervals, busy totals, proposed critical rows, grant
orders and selected causes are in `literals.py`. All times below are ps; clock jobs use
1.2GHz. No row is an EngineResult or a fixture/profile acceptance.

| Witness | Independent obligation | Exact distinguishing result |
| --- | --- | --- |
| S01 | Release835, one cycle | ready/grant835, end2500, busy1665; release offset835 |
| S02 | Dependency ends500, release835 | ready835, end2500; critical offset835, global idle only335; owner1 busy500 |
| S03 | Dependency ends1000, release835 | ready/grant1000, end2500; critical dependency1000 + service1500 |
| S04 | Owner busy until3000, release835, one cycle | ready835, grant3000, end4167; not2500; busy4167 |
| S05 | Same busy owner, zero cycles | grant/end3000; never release835 or a later clock edge |
| S06 | Root released835, zero cycles | ready/grant/end835, busy0, offset835; never1667 |
| S07 | Release and dependency complete1000, inline zero chain | b and c each grant/complete1000, exactly once; positive a occupies0–1000 |
| S08 | Zero bridge waits on busy owner | z ready1000, grant/end3000, c ends5000; chosen chain a,z,c includes [3000,3000] |
| S09 | b and c both ready1000 on owner0 | b zero before c by ID; c depends a, ends1001; tight candidates for c are a,b, choose a |
| S10 | Three all-zero dependent jobs at0 | duration0, busy0, critical records **empty**; all jobs and dispatches retained |
| S11 | Release and dependency tie1000 | choose actual tight dependency a over release-offset alternative; end2500 |
| S12 | Previous owner a ended500; dependency b ends2000 | grant2000, end3334; c cause b, not stale a; owner0 busy1834, idle1500 |
| S13 | Release at edge834, zero cycles | end834, busy0; paired with S06 off-edge distinction |
| S14 | Release at edge834, one cycle | end1667, service833; paired with S01 service1665 |
| S15 | Pure-ps835, no clock | grant0,end835; queue cannot acquire a made-up core domain |
| S16 | Owner and dependency both end1000 | both tight, canonical chosen cause a; c ends1001 |
| S17 | Busy owner until100, z ready1, b ready3 | grants a,z,b despite b<z lexically; zeros complete100 |

`verify_witness` checks these supplied literals, not a dynamically scheduled graph.
`verify_links` checks finite supplied dispatch order, FIFO eligibility, tight causes and
critical adjacency. It never constructs a runtime result. Fault controls change readiness,
grant/end, occupancy, critical cause, FIFO order or tie choice and require assertion failure
between positive baseline/restoration. Those are host mathematical fault controls, not
executed Rust mutants. Arbitrary crashes/import errors are not numerical kills.

## Causality, zero representation and event order

Propose actual predecessor completions must equal grant time and precede grant in actual
dispatch order. Candidate set is declared dependencies plus the actual previous owner job,
filtered by tightness; do not copy all K1 history. Retain all tight IDs in the job record;
choose lowest public job ID for the critical chain. Tight real job cause wins a tie against
release (S11). The terminal is lowest job ID among jobs ending at the maximum time.
Those are explicit proposal choices pending A's completed delta/coordinator acceptance.

Retain zero-length service bridges **when on the chosen nonzero critical chain** (S08).
Do not force every completed zero job into that chain: S09 chooses a directly, while b
remains in real job/event records. For duration0 choose exactly an empty critical array,
zero attribution and zero busy totals, with nonempty real job/event inventory. For a lone
late zero job (S06/S13), choose just [0,release] offset; no redundant zero service row.
These deterministic conventions replace A's earlier “empty or zero-length” choice only
prospectively; installed schema permissiveness is not a native implementation decision.

Release offsets are elapsed-time causes, not occupancy, and not necessarily global idle.
S02's offset0–835 overlaps a real500ps service on another owner. Conversely S12's owner0
idle500–2000 overlaps owner1 service. Fixed-delay service and release offset can both be
category overhead, but require distinguishable provenance: release backed by the actual
release event; service backed by grant/completion. A's completed exact carrier/semantic
delta must make that distinction machine-checkable. No release interval is added to busy.

At time1000 S07 needs phase0 release/completion, then phase1 readiness, then phase2 grant;
zero completion and consequent readiness/grant stay inline in phase2. Do not enqueue an
earlier phase at the same time. Actual queue events carry their assigned sequence; inline
observation ordinal preserves actual dispatch. Owner restart can descend IDs in phase2;
resorting traces by target destroys causality. Sequence/ordinal exhaustion and future/past
insertion refusals still need real implementation controls. Literal logical transition
checks are not fake EventObservation output or proof that instrumented native code exists.
