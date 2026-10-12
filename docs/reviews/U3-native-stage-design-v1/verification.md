# Independent derivations and future acceptance

**All native results below are expectations, not passing evidence.** Derived by Lane A
from integer arithmetic and proposed assumptions, without production timing/count helpers.
B must independently review/author the qualifying corpus; two U-P8 fixtures must be worked
by a human with committed working, including the latency-bound stream. No such signoff is
claimed here. Freeze concrete fixtures, seeds, transformations, applicability and budgets
before the two qualifying replays; retain discovery failures and every actual invocation.

## Proposed interval conventions and worked examples

### E1: fixed-delay causality and legal overlap (K)

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

### E2: exact edges (K; synthetic clock fixture only)

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
at T; it is not falsely passed by this refusal. Double-buffering is mandatory at B:
DMA for tile1 into slot1 may overlap compute of tile0 in slot0; reuse of slot0 before
tile0's last consumer completes is refused. Occupancy is the union of live allocations,
not cumulative allocation totals or payload traffic.

### E4: NoC-0, DRAM-0 and DMA limits (B)

NoC-0 unicast pays h*2 NoC cycles at 1 GHz, independent of bytes: two hops=4000 ps.
Request and response each traverse their explicit routes. No link serialization/queue
or VC contention exists at this level. U-P8's finite-link-width formula becomes
hops*latency + **zero** serialization under the level-0 infinite-bandwidth premise;
its finite-bandwidth contention/serialization cases remain not_run until that level
exists. This applicability clarification needs acceptance with U0011, not silent
introduction of a reservation model or pretending the finite-link test passed.

Proposed DRAM-0 fixed latency is t_rp+t_rcd+t_cl=48 DRAM cycles, regardless of history;
no modeled open-row advantage. Refresh derates service bandwidth, not this latency:
chip cap=10^12*(1−350/3900)=10^12*71/78 bytes/s;
per-channel cap=4437500000000/39 bytes/s. Do not multiply chip bandwidth by eight.
One full request's channel service time=256*10^12/cap=159744/71 ps;
ceil=2250 ps. Maintain an exact rational channel virtual finish time and round each
completion edge up once; don't accumulate rounded per-request periods. Fractional
service arithmetic and deterministic channel FIFO are bookkeeping for a bandwidth cap,
not a row-buffer/FR-FCFS model. Do not claim modeled DRAM queue-depth or credit enforcement.

Read lifecycle: credit acquired at request issue; request hop delay; align to DRAM edge;
48-cycle latency; FIFO channel bandwidth service; response hop delay; align to core edge;
per-core DMA port payload service at 256 bytes/core cycle; commit into SRAM and release
credit. All four DMA engines share that core port. Write lifecycle: acquire credit,
core-port payload service, request route, DRAM edge + latency + channel service,
return acknowledgement route, core edge, then release. No response payload port service
for a write acknowledgement. Requests cannot issue on fractional core edges. Read/write
requests share their channel cap; no independent double bandwidth. Credit covers the
entire round trip. DMA request counters and core-port/channel waits are observable;
DRAM physical queue/row statistics are null.

Two-hop 256-byte read issued at t=0: request arrives 4000; latency ends 52000;
channel completes ceil(52000+159744/71)=54250; response arrives 58250;
core edge=59000; one payload-service cycle completes at **60000 ps**.
For two same-channel reads issued at 0 with sufficient credits: second channel finish
ceil(52000+2*159744/71)=56500; response 60500; edge 61000; DMA completion
**62000 ps**. If a test-only hardware variant limits that DMA engine to one outstanding
request, second issue is 60000, completion **120000 ps**. These are exact two-request
fixtures, not asymptotic bandwidth measurements. A stock-limit fixture submits 33 reads
on one DMA engine: at most 32 may be live; request 33 cannot issue before the first
completion at 60000 ps. Observe credit/issue history as well as duration, since a
bandwidth bottleneck can mask an ignored-credit bug in the final makespan. Hardware variants are separately sourced
synthetic fixture inputs, proposed under B-owned hw/designs/ with stipulation rationales, and refuse under B's production hardware hash.

For a long low-load single-request stream the cap is 256 bytes/60000 ps =
4266666666.666… bytes/s, below channel bandwidth. A synthetic two-credit, large-latency
stream must approach min(channel cap, shared DMA-port cap, credits*256/round_trip), with
startup/drain excluded explicitly and ≤5% tolerance under U-P8's premises. Reducing
credits never speeds this fixed mapping. A separate prepopulated channel-service fixture
isolates sustained DRAM cap (8 channels sum to 10^12*71/78), so insufficient DMA arrival
rate cannot be misdiagnosed as a derating failure. Exact finite-stream bounds include
startup/terminal inventory; no universal steady-state equality for arbitrary queued loads.

Barrier example: arrivals at 60000 and 62000; NoC edge already aligned; 32 cycles
release at 94000 ps. A consumer cannot issue earlier. Channel/port service intervals
serialize only for the same resource; independent channels/cores may overlap.

### E5: retained v2 obligations (T, refused at B)

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

All rows are **future/not_run** today. K/B required cases block their checkpoints if absent.
R01–R16 in interface.md are required M admission fixtures and repeated at the public native
boundary when it exists. Faults must exercise valid inputs through Python runner → native
subprocess → result parser. Freeze baseline, altered and restored implementations and retain
outputs. Rehashed semantic attacks bypass only identity failures, never real validation.
A crash or setup error is not a timing/count mutant kill.

| ID/stage | Public observation and exact assertion | Discriminating fault |
| --- | --- | --- |
| V01 M/K | Old/new roots strict; unknown field, duplicate key, stale closure and all R01–R16 refuse before execution | Accept unknown field / silently route analytic job to native |
| V02 K | E1 duration 7000; per-owner serialization case 10000; exact completion inventory | Remove dependency; or globally serialize independent owners |
| V03 K | E1 tie ordering; sorted oracle for wheel/heap/arena with 100 frozen schedules | Compare only time; wrong phase/target tie; reuse stale arena payload |
| V04 K | E2 edges and u128/u64 limits; 100 frozen (freq,k) cases satisfy 0≤t_k*f−k*10^12<f | Rounded period; edge strictly after instead of at boundary; overflow wrap |
| V05 K | Foreign-owner mutation cannot succeed; normal multi-owner public fixture completes | Route event to wrong owner; debug assertion/error retained, no success result |
| V06 B | E3 C1/C2/C3 useful/issued/per-op counts, repeats and read/write payload exactly | Drop tile; duplicate completion; count padded lanes as useful; omit replicated W |
| V07 B | Cold fragment inventories: accepted=completed+inflight, final inflight=0; payload/transaction split C2 | Release without transfer; count issued as completed; confuse bus/payload bytes |
| V08 B | 33-request fixture has per-engine credit maximum ≤32; one-credit E4 120000; stock two-request case 62000 | Ignore max_outstanding; release credit at memory issue rather than SRAM commit |
| V09 B | E4 read/write share core port and channel cap; independent channels overlap | Give each engine full per-core port rate; duplicate read/write channel bandwidth |
| V10 B | 2-hop NoC transfer 4000; 2-hop read 60000; barrier release94000 | Extra hop cycle / latency forced to1; omit barrier overhead |
| V11 B | Live buffer inventory stays within capacity; slot reuse waits; E3 half accumulator refuses | Ignore live alias or capacity; free buffer at issue rather than final consumer |
| V12 B | Resident C1 interval702000, C2 547000; DMA slot1 overlaps compute slot0 with legal dependencies | Omit overhead/fill/staging/drain; serialize independent DMA/compute; overwrite slot0 |
| V13 B | E4 exact derating, long-stream ±5% with frozen window/premises; queue conservation | Omit refresh factor; multiply total BW by8; drop terminal inventory |
| V14 K/B | Attribution causal intervals sum exactly to duration, E1 picks b→c; unmodeled diagnostics null | Normalize busy-time sum as path; double attribution; null→0 |
| V15 K/B | Three fresh-process results byte equal, debug/release equal, two qualifying saved replays | Include wall clock/path/hash-map order; change code with unchanged version |
| V16 M/B | Producer-disabled saved and relocated imports give same results; changed placement changes graph/job identity | Invoke mapper/model/coefficient producer; key cache by filename/policy name |
| V17 B/T | Stage-qualified L0m: 24 distinct valid fixed-work cases/relation, ≤240 candidate calls; monotone BW/latency/credits, identical-core permutation, idle-core invariance | Reverse parameter effect; charge idle cores; mutate work during timing transform |
| V18 T | E5 plus complete independent layer/head/tail counts; once-only groups; explicit v2 casts/traffic | Drop/duplicate Q/K, rotate V/cache/pages, extra TP division, omit casts/tails/coefficients |
| V19 T | Paged/fused memory correspondence; scores remain SRAM; exact append and named rotated producers | Spill score to HBM; full-page payload; append twice; feed unrotated K |
| V20 T | Full grid/error coverage; 1/8 workers, repeated table bytes, both policies/precisions; steady1/steady2 | Skip required point; worker-order assembly; report priming counters as measured iteration |
| V21 T/U6 | Trace causality/owners/overlap; Little's law on declared completed window ≤1%; modeled diagnostics | Omit queued interval or censored request; prohibit all overlap |
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
capabilities stay pending for their future checkpoint, not removed from G3/G5 denominators.
Malformed output/timeout/crash is retained as an execution error with null result and
not_run, unless a separately observed applicable assertion already failed. SR-C1's durable
recording behavior must survive native integration; do not repair malformed output.

Premises matter: whole-query clock inverse scaling is not valid for mixed memory/compute;
use isolated compute E3. Cold/steady, DRAM row hit, bank conflicts, energy, finite NoC
contention and Little's law for unmodeled physical DRAM queues are not B passes.
Use completed DMA inventory/response windows for B conservation; T/U6's declared queue
metric must include terminal/censored intervals. The C2 roofline gate is inapplicable to
B's C1 label; same-work basic compute/bandwidth lower bounds still detect impossible B
answers. None of these reductions grants physical accuracy or a badge.
