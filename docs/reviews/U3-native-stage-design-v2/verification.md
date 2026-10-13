# Revised independent derivations and acceptance

**All native results below are expectations, not passing evidence.** Derived by Lane A
from integer arithmetic and proposed assumptions, without production timing/count helpers.
B must independently review/author the qualifying corpus; two U-P8 fixtures must be worked
by a human with committed working, including the latency-bound stream. No such signoff is
claimed here. Freeze concrete fixtures, seeds, transformations, applicability and budgets
before the two qualifying replays; retain discovery failures and every actual invocation.

## Stage interpretation

E1–E5 retain proposed v1 model arithmetic with revised checkpoint assignments. K1
privately executes U-P11a acceptance 1/1a/2/3/5 and canonical internal results; K2
repeats applicable cases publicly and adds schema/runner acceptance 4/6. Private unit
success cannot discharge a public fault. M and K1 may overlap after their decisions.
B below is the bounded model checkpoint; Lane B owns independent verification.

## Proposed interval conventions and worked examples

### E1: fixed-delay causality and legal overlap (K1 private, K2 public)

Jobs a=3000 ps on owner0 and b=5000 ps on owner1 start at 0. c=2000 ps on owner0
waits for both. Intervals: a [0,3000), b [0,5000), c [5000,7000); makespan=7000 ps.
Critical path b→c; attribution is 5000+2000, while owner busy times sum to 10000.
Moving b onto owner0 under FIFO a-before-b yields a [0,3000), b [3000,8000),
c [8000,10000): makespan=10000. Removing c's b dependency in the first graph gives
5000 rather than 7000 and must fail the dependency assertion. Serializing both independent
owners gives 10000 and must fail the positive overlap control.

Equal-time event tuples `(1000,0,2,9)`, `(1000,1,0,2)`, `(1000,0,1,8)`,
`(1000,0,1,7)` execute in order seq 7,8,9,2. Compare this exact order, not just final
duration. Holding seq fixed while permuting insertion tests the queue; permuting source
JSON arrays first normalizes by IDs before schedule-time seq assignment. Arena reuse,
wheel-slot ties, an event outside both wheels' horizons and a later inserted earlier event
must preserve the same total order as a small sorted-list test oracle.

### E2: exact edges (K1 private, K2 public; synthetic clock fixture only)

At 1.2 GHz, rational edge k is ceil(2500*k/3) ps:
0,834,1667,2500,3334,… . Therefore next_edge(0,3)=2500;
next_edge(834,0)=834; next_edge(835,0)=1667; next_edge(835,1)=2500;
next_edge(0,10^9)=833333333334. Rounding the period to 833 instead would give
833000000000, an error of 333333334 ps. An integer-only implementation can find the
first edge index with k=0 for t=0 and k=floor((t−1)*freq_hz/10^12)+1 otherwise;
then compute ceil((k+n)*10^12/freq_hz) using checked u128 arithmetic. Test overflow
and zero/invalid clocks as refusals, never wraparound. n_cycles never enters table data.

### E3: resident WS tile, quantization and mapped rows (B)

Proposed compute-1 convention for a tile m≤256,k≤256,n≤256:

1. Stage payload X and W from SRAM into the operand buffer, at 1024 bytes/core cycle,
   rounded up once for their combined bytes. No hidden reread/padding traffic.
2. Pay 32 core cycles overhead, independent of tile size; serialize on the matrix owner.
3. Physical array has 256 K rows and 256 N columns. A weight-stationary wave streams m
   output rows: (256−1) fill + m steady + (256−1) drain cycles. Masked K/N lanes issue
   capacity but do not become useful mathematical operations. No weight retention across jobs.
4. Write BF16 output payload into its explicit SRAM buffer at 1024 bytes/core cycle,
   rounded up. FP32 accumulator is capacity, not a hidden DRAM operand. BF16 matrix
   output rounding is included in this modeled output drain; no extra standalone cast
   is asserted or charged as a vector operation. This does not cover U0022's explicit casts.

These phases serialize within the matrix interval; external DMA into the other SRAM slot
may overlap. SRAM bank conflicts are absent. This is an explicit first-stage model law,
not an established real-array latency; change it prospectively if review rejects it.

C1 (m=16,k=n=256): each output has 256 MACs, so 16*256*256=1048576 MACs,
2097152 useful ops. X=8192 bytes, W=131072, Y=8192. FP32 accumulator=16384 bytes.
Staging=(8192+131072)/1024=136 cycles; wave=255+16+255=526;
output=8; total=32+136+526+8=702 cycles=702000 ps at 1 GHz.
All issued lanes are useful here. Resident HBM bytes are zero. A cold version must
also complete 139264 payload read bytes and 8192 payload write bytes through explicit
DMA; 544 read requests and 32 write requests, all full 256-byte fragments. End-to-end
cold time depends on the explicit channel/address schedule, not this resident duration.

C2 (m=3,k=5,n=7): 3*5*7*2=210 useful ops, but physical issued capacity
2*3*256*256=393216 ops. X=30,W=70,Y=42 bytes; stage=1, output=1, wave=513;
total=32+1+513+1=547 cycles. Do not inflate useful ops or transfer padded zeros.
Cold DMA uses one request each for X,W,Y at disjoint aligned base addresses:
100 read/42 write payload bytes versus 512 read/256 write transaction bytes.

C3 (M=257,K=N=256) divides rows into m=256 and m=1 on cores0/1. Useful ops
=33685504; X total=131584, W replicated=262144, Y=131584 bytes. Read=393728.
Core0 time=32+256+766+128=1182 cycles; core1=32+129+511+1=673 cycles.
Resident makespan=1182000 ps, not the sum. Moving both tiles onto one core with distinct
buffers gives 1855000 ps. This checks placement, replicated weights, tail tile and
legal overlap separately from the policy name. These are rank-local component counts;
there is no model TP reduction.

A fully occupied 256×256 output uses 262144 accumulator bytes, exactly the spec capacity.
A synthetic half-size accumulator variant must **refuse** this supplied tile at B, not
retile/spill. The U-P11b spill-traffic monotonicity test is required when spill is admitted
at R if consumed, otherwise T; it is not falsely passed by this refusal. Double-buffering is mandatory at B:
DMA for tile1 into slot1 may overlap compute of tile0 in slot0; reuse of slot0 before
tile0's last consumer completes is refused. Occupancy is the union of live allocations,
not cumulative allocation totals or payload traffic.

### E4: exact NoC0 / DRAM0 / DMA convention (Stage 2 A-F2/F3)

These are revised proposed laws, not tuned measurements. E1–E3 arithmetic is unchanged.
Write NE_d(t,n)=next_edge(domain d,t,n) with the accepted integer edge rule in E2.
Every cycle-valued phase uses it; no `t + cycles*rounded_period`, including hop return.
NoC hop arrival is NE_noc(t,h*router_latency_cycles) for h>0; h=0 returns t exactly.
NoC0 has infinite bandwidth, no serialization/VC/link reservation. Latency/pipeline
alignment is real modeled time, not discarded to retain the old answer.

DRAM latency: align L0=NE_dram(arrival,0); complete L=NE_dram(arrival,
t_rp_cycles+t_rcd_cycles+t_cl_cycles). Baseline48 cycles. Bandwidth is continuous rational
bytes/second, not cycles: chip cap=10^12*(1−350/3900)=10^12*71/78; channel cap=4437500000000/39.
For each FIFO channel request, S=max(integer latency completion L, previous exact F),
F=S+transaction_bytes*10^12/cap; publish `channel_end_ps=ceil(F)` exactly once. Preserve
rational F between requests; **do not align channel completion to a DRAM edge** or feed
ceil(F) back into the next service. Canonical service observations use ceil(S)/ceil(F)
and also exact reduced `service_start_ps_ratio`/`service_end_ps_ratio` numerator/denominator
pairs. These are bandwidth-time values, not an exception to the cycle conversion invariant.
At idle admission the integer-ready L participates in max; no phantom service starts early.

Read: acquire one credit/issue on a core edge; request route; DRAM latency; channel
service; response route from ceil(F); wait for shared core port; start at
NE_core(max(response,port_free),0), complete at NE_core(start,ceil(payload_bytes/dma_rate));
commit destination and release credit together. Write: acquire credit on a core edge;
shared core port first with the same service rule; request route from port completion;
DRAM latency/channel service; acknowledgement route; release at NE_core(ack_arrival,0).
Write ack has no payload-port service. Credit remains held through all waits and final
commit/ack. One core port is shared by all engines and read/write payload; one channel
cap is shared by reads/writes. Each read response and write payload transfer pays its own
ceil(payload/rate) port cycles; do not pool unrelated fragments' remainders.

At a core edge, issue all ready requests that have credits in canonical (engine_id,
request_id) order; there is **no separate finite issue-rate cap** in B. A read issues no
payload onto the core port. Write issues acquire credits before queuing for that port.
Later ready requests wait until NE_core(ready,0). NoC/DRAM arrivals do not require a second
core-domain issue. Only compute jobs pay job_overhead_cycles, once per mapped compute
tile; DMA/NoC jobs pay none, barriers pay only their NoC-domain barrier latency. This is
an explicit assumption requiring human acceptance despite the spec's generic overhead
rationale, not a new hardware fact.

Fixtures: core0=(0,0), local DMA engine0; controller3 attaches(1,1), channels6/7. Request j
(0-based) uses HBM address1536+2048*j, length256, hence channel6 and local channel offset256*j.
SRAM offset256*j, valid initialized source for writes/valid allocated destination for reads.
Mesh route X then Y has2 hops each way, NoC index0. Read bursts of1/2/5/33 issue at0 with
32 credits (except request33); two-read one-credit variant issues second at60000. IDs r00,
r01,… determine same-time channel order. No job overhead and no other traffic. Buffers
are nonaliasing and within capacity. Therefore the33rd read cannot issue before60000;
this is not a placement-independent statement. Channel0 from core0 instead completes
at52000; channels2–5 at56000. B freezes exact addresses/routes in its future profile.

Complete proposed timestamps in ps (alone unless noted). `req_align` is NoC entry edge;
`dram_align`, `resp_align`, `core_align` expose crossing waits. Channel service start for
burst read2 is the exact prior F, displayed as ceil54250. Port intervals are explicit.

| Case (core/noc/dram GHz) | credit/issue | write port | req_align → request arrival | dram_align → latency end | channel start → end (ceil) | resp_align → response/ack | core_align → read port end / write release |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| read1 (1/1/1) | 0 | none | 0 → 4000 | 4000 → 52000 | 52000 → 54250 | 55000 → 59000 | 59000 → 60000 |
| read2 same burst (1/1/1) | 0 | none | 0 → 4000 | 4000 → 52000 | 54250 → 56500 | 57000 → 61000 | 61000 → 62000 |
| write1 (1/1/1) | 0 | [0,1000) | 1000 → 5000 | 5000 → 53000 | 53000 → 55250 | 56000 → 60000 | 60000 → 60000 |
| read1 (1/1.2/1) | 0 | none | 0 → 3334 | 4000 → 52000 | 52000 → 54250 | 55000 → 58334 | 59000 → 60000 |
| write1 (1/1.2/1) | 0 | [0,1000) | 1667 → 5000 | 5000 → 53000 | 53000 → 55250 | 55834 → 59167 | 60000 → 60000 |
| read1 (0.8/1.2/0.9) | 0 | none | 0 → 3334 | 3334 → 56667 | 56667 → 58917 | 59167 → 62500 | 62500 → 63750 |
| write1 (0.8/1.2/0.9) | 0 | [0,1250) | 1667 → 5000 | 5556 → 58889 | 58889 → 61139 | 61667 → 65000 | 65000 → 65000 |

Wait attribution is to the receiving modeled mechanism: request/response NoC alignment
and hops→noc; DRAM entry alignment, latency, channel wait/service/ceil quantization,
core-port wait/alignment/service and ack-to-core alignment→memory. Compute staging/wave/
drain alignment→compute; initial compute overhead alignment/service→overhead; barrier
alignment/latency→sync. Waiting for another owner follows that owner's causal predecessor
rather than inventing a new busy interval. For first baseline read: noc[0,4000),
memory[4000,54250), noc[54250,59000), memory[59000,60000); sum60000. Unequal-clock read
(0.8/1.2/0.9): noc[0,3334), memory[3334,58917), noc[58917,62500), memory[62500,63750).
Channel and NoC alignment observations must distinguish the old58250 response from59000;
final-time equality at1GHz cannot establish canonical replay. The old fixed-ps NoC reading
at1.2GHz yielded59000 instead of60000 and must fail the new exact clock assertion.

Refresh fault fixture: five same-channel256-byte reads at0,32 credits, addresses as above.
Final completions **[60000,62000,64000,66000,69000]**. Removing refresh derating gives
**[60000,62000,64000,66000,68000]**: the first two are masked, fifth discriminates. Also
check first channel end54250 versus54048, since no final-time masking occurs there.
This is a prospective model fixture; B re-derives it and freezes identity before native
execution. Missing/surviving fault blocks V13, never repaired by widening tolerance.

Barrier arrivals60000/62000 yield NE_noc(62000,32)=94000 at1GHz. Lower-credit stream and
refresh bandwidth limits retain their ±5% steady-window criteria only with independently
proved saturation/latency premises and startup/drain treatment. The single-credit low-load
read bound is256/60000 ps=12800000000/3 bytes/s. Separate prepopulated channel-service
fixtures isolate bandwidth; a slow DMA arrival stream is not a refresh saturation test.
Those transport fixtures use the explicit B test-profile admission, not production scope.

### E5: retained v2 obligations (R where consumed and T, refused at B)

One layer, B=1,new S=1,C=17,Hq=2,Hkv=1,D=4,R=4,BF16. Each rotated pair has four
multiplies and two add/subtracts. Q has 4 pairs:24 arithmetic +16 casts=40 vector ops;
K has 2 pairs:12+8=20. X/Y bytes Q=16 each,K=8 each. Each node gathers cos and sin:
2 arrays*2 coefficients*4 bytes=16 bytes. Total reads=16+8+16+16=56, writes=24,
matrix delta=0. Two decoder repeats give 120 vector,112 reads,48 writes; no head/tail
or expert multiplication. With R=2 the unrotated tail still transfers: vector=30,
reads=40,writes=24. Prefill B=2,S=3 multiplies the R4 case by six:360 vectors,
336 reads,144 writes. FP32 would remove casts and double X/Y bytes:36 vectors,
80 reads,48 writes; it is not supported on the current BF16-only hardware.

C=17/block16 requires two page allocations but only 17 valid tokens/read and one append.
For the one KV head/D4/BF16 case, K+V read payload=2*17*4*2=272 bytes,
allocated K+V capacity=2*32*4*2=512 bytes, append payload=16 bytes. The partial page
contributes 16 valid payload bytes across K/V, not 256; transaction rounding is separate.
Fused decode QK and AV each cost 2*Hq*C*D=272 matrix ops, total544; no score DRAM
buffer is legal. Softmax's separately declared vector work remains required; 544 does
not describe total attention work. Global Hq4/Hkv1/tp2 has the same local Q/K rotary
work on each rank; dividing local K by tp would be wrong. Both pairings retain equal
counts but unequal semantics: X=[1,2,3,4],cos=[0,1],sin=[1,0] yields adjacent
[-2,1,3,4], split-halves [-3,2,1,4]. These are normative input/reference checks,
not numerical execution by a timing simulator. No named-model coefficient claim follows.

## Acceptance matrix and discriminating faults

All rows are **future/not_run** today. K2/B required public cases block their checkpoints if absent.
R01–R21 in interface.md are required M admission fixtures and repeated at the public native
boundary when it exists. At K2 and later, behavioral faults must exercise valid inputs through Python runner → native
subprocess → result parser. Freeze baseline, altered and restored implementations and retain
outputs. Rehashed semantic attacks bypass only identity failures, never real validation.
A crash or setup error is not a timing/count mutant kill.

| ID/stage | Public observation and exact assertion | Discriminating fault |
| --- | --- | --- |
| V01 M/K2 | Old/new roots strict; unknown field, duplicate key, stale closure and all R01–R21 refuse before execution | Accept unknown field / silently route analytic job to native |
| V02 K1/K2 | E1 duration 7000; per-owner serialization case 10000; exact completion inventory | Remove dependency; or globally serialize independent owners |
| V03 K1/K2 | E1 tie ordering; sorted oracle for wheel/heap/arena with 100 frozen schedules | Compare only time; wrong phase/target tie; reuse stale arena payload |
| V04 K1/K2 | E2 edges and u128/u64 limits; 100 frozen (freq,k) cases satisfy 0≤t_k*f−k*10^12<f | Rounded period; edge strictly after instead of at boundary; overflow wrap |
| V05 K1/K2 | Foreign-owner mutation cannot succeed; normal multi-owner public fixture completes | Route event to wrong owner; debug assertion/error retained, no success result |
| V06 B | E3 C1/C2/C3 useful/issued/per-op counts, repeats and read/write payload exactly | Drop tile; duplicate completion; count padded lanes as useful; omit replicated W |
| V07 B | Cold fragment inventories: accepted=completed+inflight, final inflight=0; payload/transaction split C2 | Release without transfer; count issued as completed; confuse bus/payload bytes |
| V08 B | 33-request fixture has per-engine credit maximum ≤32; one-credit E4 120000; stock two-request case 62000 | Ignore max_outstanding; release credit at memory issue rather than SRAM commit |
| V09 B | E4 read/write share core port and channel cap; independent channels overlap | Give each engine full per-core port rate; duplicate read/write channel bandwidth |
| V10 B | 2-hop NoC transfer 4000; 2-hop read 60000; barrier release94000 | Extra hop cycle / latency forced to1; omit barrier overhead |
| V11 B | Live buffer inventory stays within capacity; slot reuse waits; E3 half accumulator refuses | Ignore live alias or capacity; free buffer at issue rather than final consumer |
| V12 B | Resident C1 interval702000, C2 547000; DMA slot1 overlaps compute slot0 with legal dependencies | Omit overhead/fill/staging/drain; serialize independent DMA/compute; overwrite slot0 |
| V13 B | E4 five-read refresh discriminator69000 vs68000, exact channel end54250 vs54048; long-stream ±5% with frozen window/premises; queue conservation | Omit refresh factor; multiply total BW by8; drop terminal inventory |
| V14 K2/B/R | Attribution causal intervals sum exactly to duration, E1 picks b→c; unmodeled diagnostics null | Normalize busy-time sum as path; double attribution; null→0 |
| V15 K1/K2/B/R | Three fresh-process results byte equal, debug/release equal, two qualifying saved replays | Include wall clock/path/hash-map order; change code with unchanged version |
| V16 M/B | Producer-disabled saved and relocated imports give same results; changed placement changes graph/job identity | Invoke mapper/model/coefficient producer; key cache by filename/policy name |
| V17 B/R/T | Stage-qualified L0m: 24 distinct valid fixed-work cases/relation, ≤240 candidate calls; monotone BW/latency/credits, identical-core permutation, idle-core invariance | Reverse parameter effect; charge idle cores; mutate work during timing transform |
| V18 R/T | E5 plus complete independent layer/head/tail counts; once-only groups; explicit v2 casts/traffic | Drop/duplicate Q/K, rotate V/cache/pages, extra TP division, omit casts/tails/coefficients |
| V19 R/T | Paged/fused memory correspondence; scores remain SRAM; exact append and named rotated producers | Spill score to HBM; full-page payload; append twice; feed unrotated K |
| V20 T | Full grid/error coverage; 1/8 workers, repeated table bytes, all consumer-required policies/precisions; steady1/steady2 | Skip required point; worker-order assembly; report priming counters as measured iteration |
| V21 B then first stationary claim | B requires finite-window membership/causality/owner/overlap checks and observations; stationary Little's law ≤1% only at first claim with frozen population/window/boundary, normally U6 or earlier reliance | Omit queued interval or censored request; prohibit all overlap |
| V22 U6 | Absolute host receipts; prospective noise protocol; accepted regression detector catches synthetic2× | Disable delay detector / compare wrong input or host identity |

V05 is an intentional ownership fault whose required observation is a refusal/assertion,
not a successful timing mutant. V01 is likewise an admission test; do not mix either with
V02/V06/V08 numerical discrimination. Every mutant needs a passing unaltered/restored
control and its designated assertion, not merely any test failure. B chooses exact fault
sites after implementation exists; this matrix fixes the semantic fault targets first.

U0006 reductions: an applicable relation counterexample or surviving required mutant
fails its relation and enclosing stage, even if other cases are unfinished. Otherwise
missing, empty, skipped-only, interrupted or under-budget coverage reduces to not_run.
Complete nonempty passing applicable coverage alone passes. Preserve rich per-relation
states; unsupported observations are explicit skips, not positives. Required future
capabilities stay pending for their future checkpoint, not removed from their G3a/G3b/G5-correctness obligations.
Malformed output/timeout/crash is retained as an execution error with null result and
not_run, unless a separately observed applicable assertion already failed. SR-C1's durable
recording behavior must survive native integration; do not repair malformed output.

Premises matter: whole-query clock inverse scaling is not valid for mixed memory/compute;
use independently justified isolated native compute E3. That test is separate from the
aggregate-only analytic C1 remedy and any future true-premise per_op domain. Cold/steady,
DRAM row hit, bank conflicts, energy, finite NoC contention and Little's law for unmodeled physical DRAM queues are not B passes.
Use completed DMA inventory/response windows for B conservation; B/R/U6's declared queue
metric must include terminal/censored intervals. The C2 roofline gate is inapplicable to
B's C1 label; same-work basic compute/bandwidth lower bounds still detect impossible B
answers. None of these reductions grants physical accuracy or a badge.

## Reconciliation against every B checklist row

[B's checklist](../U3-B-verification-readiness-v1/native-checklist.md) stays historical.
U0023 supersedes its U4b-full-grid/runner wording. This is A's reconciliation proposal,
not B approval or an independent review.

| B obligation | Revised checkpoint/detail | Probe |
| --- | --- | --- |
| Scope/refusal | M/K2/B; R suite; T U7 product | R01–R21, valid controls and every unsupported operator/precision |
| Resolved authority | M producer/import, K2/B execution | V01/V16, rehashed placement/dependency/precision semantic attacks |
| Work conventions | B E3, R/T full groups | V06/V07/V18, useful/issued/completed distinct, no dropped/repeated work |
| RoPE | B refuses; R before used layer/operator, T product | E5 and B's independent partial-tail example: 960 vector/960 read/576 write; omitted casts→576 vectors, double repeat→2880 |
| Clock/event | K1 private then K2 public | E1/E2/V02–V05 plus zero-delay interface convention, 100 frozen schedules/edges |
| Compute timing | B WS law | E3; M=255/256/257; K,N=1/255/256 positive, 257 refusal; wrong ceil/fill fault |
| Shared resources | B DMA/channel/core-port/buffers | V08–V12; caps 1/2/32, 33 requests; positive independent overlap |
| Limits/baseline | B independent bounds; R relied-on baselines; U7 every C2 row | E4, two human fixtures, same-work joins and first-use checks below |
| Outputs/nulls | K2 events; B mandatory observation sections | V14/V21 plus clipped windows, allocation unions and null→0/attribution faults |
| Replay/failures | K2/B/R then T | V15/V16; exact identities and SR-C1 durable errors/finish records; invalid output not a numerical kill |
| Progression | M ∥ K1 → K2 → B; B→R; verified scope→U6→U7 T | Three fresh processes/debug-release; table 1/8 workers at T, batch 1/N when delivered |
| Toolchain/cost/host | Closure before K1, budgets before measurement | Real Linux fmt/clippy/deny/tests; distinct controlled-host/U0012 and executed nightly |
| Optional L2/silicon | Scoped comparison map in delivery; U5/U8 separate | Unavailable/unmatched/not-independent explicit; no deleted disagreement or whole-chip inference |

B's 10 ns transfer includes finite serialization; E4's NoC0 two-hop answer is 4000 ps.
Keep both with their premises, never force agreement by changing tolerances. B's 8 ns/
64-byte DMA example is synthetic fixed-round-trip work; the proposed npu-l4 lifecycle
instead gives E4's 60000/62000/120000 ps. B's arithmetic remains preparatory, not human
hand working or a native execution result.

Add V23 (B): DMA window inventory 32+128−64=96; remove one completion and require the
inventory assertion. V24 (B): interface's 8000/6000 request-ps windows; remove initial
membership and require area assertion. V25 (B): allocation union at every alloc/free,
including slot reservations; early-free/alias fault. V26 (K1/K2, retained at B): busy-owner zero job→5000 ps, bypass fault→3000;
zero-hop propagation/cyclic refusal and phase-regression fault. V27 (R): signed-suite
coverage/steady/attribution, omitted fused-unit work blocks G3a. V28 (T): no FP8/RoPE
substitution, complete ragged error jobs, C2 consistency; omitted point blocks G3b.
Each requires baseline/fault/restored controls, frozen inputs and independent assertions.
V21's minimal observations are mandatory at B; full Chrome tracing arrives in U6.

B positives/refusals: compute E3/R06; WS C3/R09/R11; DMA E3–E4/R11/R19;
resident C1/R15; SRAM/accumulator E3/R10; unicast E4/R09; barrier E4/R12;
double buffer E3/V12/R10; credits/channel/port E4/V08–V09; scope E3/R02–R08/R17–R19.
Include 1/16/17-op boundary cases. Synthetic variants never expand production admission.
The extra-SRAM-traffic spill test is required at R if consumed, otherwise its first
U6/T consumer; B's capacity refusal does not pass that later capability test.

## Analytic obligations by first reliance

B freezes and seeks authorization for exact version/mode/domain selections before C1–C5
implementation. Historical L0 14 pass/14 skip and L0m 9 pass/13 skip/5 not_run, and the
aggregate-only clock cell at 22/24, remain their original results. Deadlines below do not
claim execution or approval.

| Remaining scope | First consumer/deadline | Required disposition / owner |
| --- | --- | --- |
| C1 v1 aggregate-only compute-clock distinct coverage | Before first bound, analytic frequency prediction or report relying on this aggregate domain, whichever first | Historical `analytic.aggregate_clock/1:aggregate:d4-bf16-v1` remains 22/24, not_run; B's proposed aggregate-only 24-anchor remedy, bounded discovery, 240 calls/ledger and separate unchanged-clock mutant need acceptance |
| Native component-clock checks (separate from analytic C1) | E2 at K1 privately/K2 publicly; isolated resident-compute E3 clock relation at B under its explicit synthetic test profile | Independently derive edge/timing expectations from accepted native conventions and true premises; no aggregate anchor, analytic pass or whole-query per_op law is inherited |
| Future per_op exact reciprocal-clock domain (separate proposal) | Before any claim using that domain, if proposed and approved | Existing whole-query premise is false with memory-only operators head/embed and layers/kv and remains skipped; a new domain needs independent dominance proof for every op, exact selection/budgets and separate approval, not the aggregate C1 remedy |
| C2 memory/mixed clock | Before first actual analytic bound/frequency prediction relying on changed clocks; no later than applicable U-P9 baseline | B proves memory dominance at the base (slower) clock (then also k·f); aggregate T'=T requires aggregate dominance, per_op T'=T requires it for every op; wrong-memory-scaling mutant |
| C3 unused stipulation | Before any fixture/report/study claims invariance: earliest B metamorphic use, otherwise U-P14 | B supplies admitted proposed-design TDP100/200 W fixture/rationale; identity changes, timing does not; 24 pairs/cap retained |
| C4 unavailable execution observations | Never use analytic counts for native telemetry; native analogues required at K2/B/R/U6 as represented | Keep unsupported/skipped/not_run; energy after separate evidence, physical queues when represented |
| C5 independent v2 corpus/producer/replay/mutants | Before any native v2 roofline reliance, even before silicon; no later than applicable R RoPE/layer acceptance and U-P9 baseline | B freezes stratified modes/formats/pairing/R/context/rank/repeat/attention cells; unavailable precision is no implicit native admission |
| Existing count/traffic/mode-order/attribution/null/replay | Before exact-input analytic floor reliance at B/R/U6; U-P9/U-P15 both analytic modes for admitted suite | B selects checks; A proves same-work/hardware join; inherited pass is not new-input evidence |
| DRAM bandwidth/refresh/latency | Independent E4 before B acceptance; analytic rate checks before any analytic bound; all C2 rows at U7 | Separate peak versus refresh/actual traffic; never full-model floor for a component |
| Report/eligibility/card completeness | Before publishing that evidence claim, possibly before R; no K1 prerequisite | B retains conservative reductions; integration/U0002 separately reviewed |
| Batch/context, symmetry/idle-core, cold/steady, queue/utilization | Analytic supported laws before floor/baseline/report reliance; native symmetry B fixture, cold/steady R, complete-work batch/context R/T, physical queues later | B enumerates premise-qualified cells; missing required cases block first consumer |

U-P9/U-P15 baseline predictions are consumers even without a C2 assertion. If reliance
moves earlier, its checks move too. K1 uses independent math, not analytic answers, so
unrelated report completion does not block it. B may use independently derived component
bounds only; no analytic component API or full-model admission bypass is proposed.
First actual admitted analytic reliance triggers applicable checks, R/U-P9 at the latest
for required baselines; an earlier new comparison needs its own admitted interface. C1–C5 are
not blanket-paused. Two genuinely human-worked L1 fixtures, including latency-bound DMA,
remain required before B's applicable L1 acceptance; agent arithmetic does not supply them.

Freeze case IDs/premises/inputs/seeds/faults/restored controls/call caps before execution.
Native L0m retains at least 24 distinct valid pairs per applicable relation and at most
240 calls per ledger; extra modes/domains/mutants get separate declared ledgers. Discovery
failures persist even if two qualifying replays pass. Small independent math/event oracles
are permitted; no second production engine.
