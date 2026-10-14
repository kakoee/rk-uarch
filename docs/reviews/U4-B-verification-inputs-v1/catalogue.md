# Proposed finite case catalogue — B-inputs/1

This freezes proposed selections, not executable NativeTestProfile bytes or a complete
V01–V28 corpus. Every row is planned native coverage, even when its arithmetic is checked.
Normative semantics: accepted U3 design-v2 interface and verification E1–E4/V01–V28.
No tolerances apply to integer counts, exact rational ratios or timestamps below.

Common premises: seed0, exact sync, priming0; canonical IDs ascending; no cancellation;
complete issue/completion/owner/queue/critical-path observations. K1 uses private tests;
K2 uses test/kernel_fixture/fixture_cold/fixed_delay with null fidelity; retained B kernel
cases have the same restrictions. Other rows use B test/component/fixture_resident or
B test/transport_fixture/cold as named, compute1/NoC0/DRAM0 where represented.
No public command is invented: eventual K2/B invocation is the reviewed Python runner →
native subprocess → strict parser with `--fixture-mode --test-profile` and the exact
case binding. A's runner API/CLI, full profile hash and fixture bytes are pending joins.
For every semantic attack recompute affected identities so it reaches the intended check.

## Kernel, clock and accounting selections

| Case / invocation | Concrete input and source calculation | Expected / bound | Intended fault |
| --- | --- | --- | --- |
| K01 K1/K2 | a:owner0/3000ps, b:owner1/5000ps, c:owner0/2000ps depends a,b; ready a,b=0 | max(3000,5000)+2000=7000ps; path b,c; owner busy sum10000ps | drop b→c gives5000; globally serialize gives10000 |
| K02 K1/K2 | K01 but b owner0, FIFO a before b | 3000+5000+2000=10000ps | give b independent owner service |
| K03 K1/K2 | tuples (1000,0,2,9),(1000,1,0,2),(1000,0,1,8),(1000,0,1,7) | dispatch seq7,8,9,2 sorted (time,phase,target,seq) | sort by time only or seq before phase/target |
| K04 K1/K2 | a owner0/3000ps,p owner1/1000ps,z owner0/0ps after p,c owner1/2000ps after z | z ready1000, grant/end3000; c end5000; one z completion | bypass owner: end3000; retroactive phase0 record |
| K05 K1/K2 | two independent zero jobs owners0/1 → c owner0/3000ps | two completions at0, c end3000; canonical inline closure; cycle mutation refuses | omit/duplicate zero completion or accept cycle |
| K06 K1/K2 | 1.2GHz; (start_ps,n)=(0,3),(834,0),(835,0),(835,1),(0,10^9) | 2500,834,1667,2500,833333333334ps from ceil(2500k/3) | strict-after edge; rounded833ps period |
| K07 K1/K2 | finite 100 entries: f={800000000,900000000,1000000000,1200000000}Hz × k=0..24; t=ceil(k*10^12/f), n=0 | NE(t,0)=t; 0≤tf−k*10^12<f; IDs K07-f-k | cumulative rounding/edge omission |
| K08 K1/K2 | f=0; negative t/n; f1GHz,t=2^64−1,n1 | refuse invalid clock/time or checked time overflow, never success/wrap | unchecked arithmetic; exact M error spelling pending |
| Q01 B observations | membership [0,4000),[2000,6000)ps; windows[0,8000),[1000,5000) | clipped areas8000,6000 request-ps; averages1,1.5 requests | drop initial member: second area3000 |
| Q02 B observations | separate boundary/direction/payload ledger: initial32B, issued128B, completed64B | final96B; initial before a events, include a/exclude b | omit initial inventory or count completion twice |
| Q03 B observations | initial allocations [0,8192),[8192,139264),[139264,147456), reserved slot1[147456,294912) bytes | live union294912B, ≤16777216; early reuse before final consumer refuses | treat transfer bytes as residency or free at issue |

K03 is one literal tie test, not the 100 frozen schedule/arena/wheel cases required by V03.
Those implementation-specific schedules await A's event test API and remain required.
Q01 is finite residence accounting, not stationary Little's law. At its first stationary
claim freeze population/window/censoring and require ≤1%; zero-flow residence is null.
Q02 is an observation-checker input, not a claim that a 32-byte partial completion is a
B engine request. Native observations must obey whole-request completion semantics.

## Component selections

BF16 X/W/Y, FP32 accumulator, q_projection, contiguous, WS, no imported padding,
no K split or retile; resident inputs explicit, no HBM traffic in resident controls.
X=2mk,W=2kn,Y=2mn bytes; useful=2mkn, issued=2m*256*256;
cycles=32+ceil((X+W)/1024)+(510+m)+ceil(Y/1024). All core clocks initially1GHz.
Lower bounds: useful/(2*65536 MAC lanes*1GHz) in seconds; staging/drain cycle service
and exact wave separately. Bounds are necessary, never sufficient or a C2 roofline claim.

| Case / invocation | Concrete input and calculation | Expected / bound | Intended fault |
| --- | --- | --- | --- |
| C01 B resident | m16,k256,n256, X offset0,W8192,Y139264; slot1 reserved147456; HBM none | useful2097152; issued2097152; SRAM read139264/write8192B; acc16384B; 702000ps (32+136+526+8 cycles); useful-work floor16000ps | omit overhead/fill/staging/drain; invent HBM bytes |
| C02 B resident | m3,k5,n7; X/W/Y separate aligned starts0/256/512 bytes, acc84B | useful210,issued393216; SRAM100/42B; 547000ps | count padded lanes or padded traffic as useful |
| C03 B resident | M257,k=n256; m256 on core0,m1 on core1; distinct slots; W copied per core | useful33685504; read393728/write131584B; intervals1182000/673000ps; makespan1182000 | drop tail/W copy; sum parallel durations |
| C04 B resident | C03 both tiles on core0, disjoint live slots, FIFO | 1855000ps; same counts | overlap exclusive matrix owner |
| C05 B test cold | C02 HBM X1536/30B,W3584/70B,Y5632/42B; separate SRAM starts0/256/512; X/W before compute before write | reads100/write42 payload; 512/256 transaction; exactly3 requests; no cold end-to-end answer until full graph freeze | payload↔transaction confusion; compute before commit |
| C06 B test resident ACC1/ACC2 | m=k=n256; accumulator131072 vs262144B | 262144B required; ACC1 capacity refusal, ACC2 fits; no spill/retile | ignore accumulator capacity |
| C07 B test component | legal SRAM allocation ending16777216 vs one byte beyond; HBM ending32000000000 vs beyond; live alias mutation | exact end accepted subject to valid job joins, beyond/alias refuses; full reachable graph still pending | off-by-one capacity or alias ignored |
| C08 B test resident clock pairs | exactly24 shapes m={1,3,16,64,255,256} × k={5,256} × n={7,256}; core1/2GHz, ratios1/2 with matching scales_with_core; IDs C08-m-k-n | same useful/issued/traffic; integer cycles law above; T_2GHz=T_1GHz/2 exactly; no DMA | unchanged clock/double scaling or whole-query premise substitution |

C08 is one proposed 24-pair relation, not 24 variants per every V17 relation. Full bandwidth,
credit, symmetry, idle-core and unused-stipulation relations need their own concrete
24-pair ledgers before qualification. Proposed C08 candidate-call cap240 including
controls/discovery/shrink/mutants; two frozen replay pairs per shape consume96 calls.
Additional private arithmetic tests consume zero native calls. Missing shapes, surviving
required faults or exceeded budget cannot pass. No discovery or native replay occurred.

## DMA/NoC selections and corrected E4 discriminators

D baseline: core0(0,0), DMA engine0, channel6/controller3(1,1), XY route two hops,
request j HBM address1536+2048*j (j starts0), SRAM256*j, payload/transaction256B.
Every burst reads disjoint initialized HBM into allocated SRAM; ready at0. Channel6 local
address is floor(address/2048)*256+address%256. Each request holds one engine credit from
issue through SRAM commit/read or acknowledgement/write. No compute overhead on DMA.
NoC1GHz/router2 cycles; DRAM1GHz/48 latency cycles; core1GHz/256B per port cycle;
chip1e12B/s,8 channels,refresh350/3900; max_outstanding32 unless named otherwise.
Per-channel rate=4437500000000/39 B/s; 256B service=159744/71ps. Exact F_j=52000+
(j+1)*159744/71 for simultaneous baseline requests; publish ceil(F_j), carry F_j exactly.

| Case / invocation | Explicit variant / calculation | Expected / bound | Intended fault |
| --- | --- | --- | --- |
| D01 B transport | isolated baseline read | arrival4000,latency52000,F=3851744/71,publish54250,response59000,commit60000ps | add compute overhead gives92000; quantize BW to DRAM gives55000 |
| D02 B transport | isolated baseline write; initialized SRAM→HBM | port1000,arrival5000,latency53000,channel55250,ack/release60000ps | extra return port or missing outbound port |
| D03 B transport | five baseline reads,32 credits | all issue0; channel ends54250,56500,58750,61000,63250; commits60000,62000,64000,66000,69000ps | remove refresh: first channel54048,commits60000,62000,64000,66000,68000; first four finals mask fault |
| D04 B transport | 12 baseline reads,32 credits | twelfth exact F=5608928/71ps,ceil78999ps | repeated rounded service yields79000; exact ratios required even if final masks |
| D05 B transport | two baseline reads,max_outstanding1 vs2 | issues0,60000 /0,0; completions60000,120000 /60000,62000 | ignore credit cap or release before SRAM commit |
| D06 B transport | three baseline reads,cap2 vs32 | third issue60000/end120000 vs issue0/end64000 | cap ignored; same-work check required |
| D07 B transport | 33 baseline reads,cap32 | first32 issue0; request33 issue60000; population≤32; finalinflight0 | release at latency completion yields52000 issue; unlimited cap yields0 |
| D08 B transport | baseline requests channel6 addr1536 and channel7 addr1792, SRAM0/256; IDs r00/r01 | both response59000; shared port commits60000,61000 in ID order | duplicate per-engine/read port; independent-channel nonoverlap |
| D09 B transport | baseline read/write separately; NoC1.2GHz only | read arrival3334,latency52000,channel54250,response58334,commit60000; write port1000,arrival5000,latency53000,channel55250,ack59167,release60000 | fixed-ps return gives read response57584/end59000; baseline final masks same fault |
| D10 B transport | core0.8/NoC1.2/DRAM0.9GHz; read/write separately | read 3334→56667→58917→62500→63750; write port1250,arrival5000→58889→61139→65000→65000 | use wrong domain/round period; ceil feedback |
| D11 B transport | contiguous HBM1536 length513 to SRAM0; baseline | fragments(ch,payload,transaction)=(6,256,256),(7,256,256),(0,1,256); payload513,transaction768,3 credits | cross stripe without splitting, floor fragment count |
| D12 B transport | HBM1791 length2; valid distinct SRAM range | (6,1,256),(7,1,256); transaction512 for payload2 | assume aligned base or combine across channel boundary |
| D13 B transport | standalone two-hop256B SRAM unicast; barrier arrivals60000/62000 | unicast4000ps; barrier NE_noc(62000,32)=94000 | router latency forced1 gives2000; barrier overhead omitted |
| D14 B transport | same-core unicast at835ps, NoC1.2GHz, distinct initialized source and allocated destination | commit835ps exactly; no hop alignment; one payload commit | charge edge or elide transfer; alias control refuses |
| D15 B transport | D01 with DMA rate512 vs256B/core cycle | still60000ps: per-request ceil is one cycle in both | pool fragment remainders to claim speedup |

D01–D10 channel/address/credit cases use the same graph primitives with exact stated
numbers; D08 r00 precedes r01 at shared port. Count assertions do not synthesize completion
telemetry. F_j above is valid only for the simultaneous admitted burst; never apply it
across a credit stall. D05/D06 derive later requests from their actual grant time and
idle-channel lifecycle (60000ps per isolated credit). D07's request33 issue needs only
first commit, not a second traffic simulator. Saturated ±5% bandwidth and latency-stream
checks still need frozen nonempty windows and proved saturation/latency premises; no
five-request transient is claimed to pass the steady limit.

## Exact admission attacks and remaining variant bindings

Against each valid control: missing/wrong profile or case→TestProfileMismatch; unlisted
hardware/clock/graph tuple→TestVariantNotAdmitted; production K2 or wrong scope→
UnsupportedCheckpointScope; wrong state/priming→UnsupportedInitialState; synthetic
registered spec renamed/copied into ordinary prepare→TestOnlyHardware; test result sent
to table/report→TestOnlyScope; rehashed production relabel→AdmissionMismatch. Omitted
mandatory observations→IncompleteObservations. Rehash only after intended mutations;
malformed old roots/duplicate JSON keys/stale hashes remain separate identity controls.

Proposed variants used here: baseline test P0, core2GHz ratio2, NoC1.2GHz,
core0.8/NoC1.2/DRAM0.9GHz, credits1/2/32, accumulator131072/262144,
DMA rate256/512. Rationale respectively: isolate edges, crossings, round-trip capacity,
exact capacity and per-request rounding. All are verification-only proposed designs.
Inherited BW×2, LAT×2, operand-rate×2, router/job/barrier×2, TDP100/200, symmetric relabel
and idle2×3 families remain reserved, not executable cases in this first catalogue.
No operand-buffer boundary is invented outside reachable B shape limits.

Before native credit: A exact schema/profile/fixture joins, case hashes and approval;
complete required V matrix (including wheel/heap/arena/foreign-owner controls); human
L1 working; real Linux pins/tests; baseline/fault/restored observations and recorded
native calls. This bounded input checkpoint does not declare the eventual corpus complete.
