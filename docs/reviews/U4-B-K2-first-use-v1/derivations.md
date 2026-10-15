# Independent finite answers and interface mapping

All answers are B agent mathematics, independently authored from accepted E1/E2, not from
A's executor. No function here accepts an arbitrary task graph and simulates it.
`author.literal_cases` freezes literals plus the finite 4×25 rational-edge table;
`test_inputs.py` checks that table with rational bounds and a bounded edge search.
The actual bundle bytes, clock arrays, expected readiness/start/completion intervals,
selection and seeds are committed under fixtures/. No native output has been invented.

K01: a=[0,3000) on0, b=[0,5000) on1, c=[5000,7000) on0. Path b,c gives7000;
busy sum10000 is not causal attribution. Drop b→c gives5000; globally serialize gives10000.
K02: FIFO a,b,c on0 gives [0,3000),[3000,8000),[8000,10000). Same counts, different timing.
K03-owner: a on1 and b on0 both end1000, c on0 zero after both. At equal times owner0
precedes owner1 in the applicable dispatch order even though canonical job a precedes b.
Exactly3 completions; c grants/completes1000. The equal-duration critical path has a tie:
a or b may explain1000 subject to A's documented canonical tie policy; do not fabricate a
unique predecessor. Expected intervals remain exact whichever tie policy is reviewed.
K04: p finishes1000 but z on busy owner0 waits until a finishes3000. z has one zero-length
service and c completes5000. Path a,z,c has3000+0+2000, while p is a declared dependency
that does not explain the binding wait. Bypassing ownership gives3000 and must fail.
K05: a,b each complete once at0; c completes3000. K05-chain: a1000→b0→c0→d2000 completes3000.
Cycles, missing IDs and duplicate/omitted zero completions are different refusal/fault targets.

K06: core1.2GHz gives edge ceil(2500k/3), so inputs (t,n)=(0,3),(834,0),(835,0),
(835,1),(0,10^9) end2500,834,1667,2500,833333333334ps. Clock jobs have duration_ps0
and an explicit ClockSetup. For nonzero t, an ordinary fixed-delay a-wait on owner1 lasts
t ps, with dependency to b-clock on owner0; no public start-time/event injection is invented.
ClockSetup.start_ps equals this independently established grant time. A's eventual adapter
must reconcile/validate this mapping to Delay::Cycles; it must not silently ignore either
start_ps or the cycle override. No claim of an implemented adapter is made here.

K07: four frequencies × k0..24, t=ceil(k*10^12/f), n0. Check NE(t,0)=t and
0≤t*f−k*10^12<f. Nonzero t uses the same explicit wait job; k0 remains a nonempty
one-job zero-duration graph. Clock conversion stays within engines/native inputs, not table
rows. K08-clock: wait u64::MAX, then one1GHz cycle. First admissible edge index is
18446744073709552, giving end18446744073709553000 >18446744073709551615.
Tests compute this bound directly.
K08-add: delay u64::MAX then1ps also overflows. Neither may wrap or manufacture a result.

## K03: existing interface, no new public schema

The original literal event keys (1000,0,2,9),(1000,1,0,2),(1000,0,1,8),(1000,0,1,7)
sort by (t_ps,phase,target,seq) to seq7,8,9,2. This is an Event::key comparator probe.
`Wheel::schedule(t_ps,phase,target,Kind::TaskReady,payload)` allocates its own seq; do not
pass the literal seq9/2/8/7 as a fictitious public scheduling parameter.

The 100 frozen private schedules use max_freq1.2GHz, slot width833ps, exact near/far/heap
boundaries0,4095w,4096w,(4096²−1)w,4096²w, plus same-time ties. Each has8 scheduled events
in explicit order, expected seq0..7 assigned at insertion and sorted expected pops. Schedule
the listed reuse event after drain; require seq8 and fresh payload, unchanged arena capacity8,
nonempty overflow promotions and exact payload inventory. An earlier-time insertion after
a future-time insertion already occurs in these lists. Test interleaved insertion after
partial drain and past/phase-regression refusals with the existing private tests separately;
this batch does not claim every interleaving or arena fault has run.

Map these proposals to the installed `Event`, `Wheel::{new,schedule,pop,level_counts,
promotions,arena_slots}` and `Arena::{insert,remove,capacity_slots}` APIs in event.rs.
Existing K1 event_layout_and_tie_order, wheel_levels_overflow_promotion_and_past_refusal,
wheel_reuses_arena_after_warmup, arena_reuses_freed_slots_and_refuses_double_free and
wheel_interleaved_scheduling_matches_reference retain their own historical evidence.
These new vectors have only host sorted-oracle checks, not Rust execution receipts.

Public K2 observes real generated event records from K03-owner, K04/K05 and K07. Require
applicable total order, phase-safe inline zero closure and complete dispatch/grant/completion
inventory; inject semantic faults in the actual executor and detect them through the public
runner. Full arbitrary-wheel/arena probes remain private internals plus their public
fault-discrimination linkage. No claim that K03-owner alone discharges100 schedules, and
no contract extension solely to expose Wheel internals. Coordinator/A must confirm this
V03 interface mapping before public qualification.

A null `causal_job_path` in this answer key means that no unique canonical path is frozen
for that row, not that a public result may omit causal observations. All successful rows
still have exact independent job intervals. For clock cases, the wait interval (when present)
followed by the clock interval partitions the duration; zero-length intervals contribute0.
Equal-length alternatives in K03-owner/K05 need A's canonical tie rule. The public checker
must verify the actual critical partition against these independent intervals and real
execution, including empty-duration cases, before any K2 causal-attribution claim.
