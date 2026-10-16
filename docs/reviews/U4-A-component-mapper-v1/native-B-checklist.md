# U-P11b B implementation checklist against installed K2 and M

Implementation-ready preparation only. No Rust source edit, binary build or native job is
part of this handoff. Entry requires coordinator K2 campaign reconciliation **and** exact
component-stage implementation/build/execution release, reviewed component cases/profile/
registry, semantic decisions below and actual independent host binding. The published
combined-runtime reconciliation at 41f286e does not grant this release. Do not assume a pass.

The current Rust seam is `protocol.rs::respond` → `admission.rs::validate` →
`Simulation::with_releases`/`run` → `accounting.rs::construct`. `Validated` contains only
fixed-delay Jobs; `Job.duration` is Picoseconds or named-domain Cycles. Component work must
be admitted as typed compute/fragment/unicast/barrier state, not translated into Python-
computed durations or passed through a renamed fixed-delay result. Keep fixed-delay regressions
and their null subsystem fidelity unchanged. Current `event.rs` already names DMA/NoC/memory/
barrier events; extend actual handlers/observations, not the enum merely to imply coverage.

| Work and exact code seam | Completion criterion and B frozen control/fault |
| --- | --- |
| `admission.rs`, `hardware.rs`, `carrier.rs` | Mirror installed closure/resource laws plus M's full-operand/cold-output/barrier-owner consumer guards. Parse all points before selecting one. Exact npu-l4 production hash/ratio1, BF16/FP32, TP1/rank0, 1–16 q_projection, no K split/spill. R01–R21 controls reseal identities to reach semantic guards; stale identity controls remain separate. Preserve test-only synthetic hardware/profile registry gating. |
| New compute state beneath `simulation.rs` | One exclusive matrix owner interval per declared tile, no weight retention. E4 initial compute-only overhead32 and its alignment precede X+W staging using ceil(payload/operand_bytes_per_cycle), then WS fill255 + m steady + drain255; BF16 output drain ceil(2mn/rate). Every phase uses `time.rs::next_edge` at its actual predecessor completion; no rounded periods. C01=702000ps, C02=547000ps, C03 cores0/1 makespan1182000ps, useful33685504/read393728/write131584B. C04 one-core1855000ps only after its accumulator carrier premise is resolved. Omit staging/fill/drain/overhead controls must each fail. |
| Capacity/allocations | Exact 4mn accumulator and X+W operand capacity; two nonaliasing SRAM slots and Y lifetime through final write. C06 half accumulator refuses, full fits; no spill traffic claim. C07 exact SRAM/HBM endpoint controls and Q03 live-union294912B. Current distinct-footprint accumulator limitation and opt-in lifetime proposal are in protected-gaps.md. Do not silently retile C04 or treat it as passed. |
| NoC0 transition handlers | Use route.core_ids length−1 and router_latency_cycles; h>0 calls next_edge(noc,t,h*latency), h=0 preserves t exactly. No bandwidth/link/VC reservation. D13 two-hop unicast4000ps. D09/10 expose unequal clocks. Corrected D14 is B's producer-dependent transport graph, ready/commit61000ps; wrong alignment61667ps. The old835ps scalar is mathematics, not a public input. One zero-hop payload commit, no positive busy interval. |
| DRAM0 latency and rational channel server | `next_edge(dram,arrival,48)` baseline. cap = BW/channels × (t_refi−t_rfc)/t_refi exactly; baseline4437500000000/39B/s. For FIFO request: S=max(integer latency end, prior exact F); F=S+256×10^12/cap. Store reduced checked u128 ratios; ceil only publication, never feed ceil(F) back or align service to DRAM edge. D01 first end54250, D04 twelfth exact5608928/71 →78999 versus rounding fault79000. D03 fifth read69000 versus no-refresh68000; first four final completions mask the fault, so also require first channel54250 versus54048. |
| DMA fragment arena/state | Read credit acquired at core issue edge, then outbound route→latency→channel→return route→shared port→commit and release together. Write acquires credit before outbound port, then route→memory→ack route→core-edge release, no ack payload port. D01 read60000, corrected resident D02 write60000. D05 cap1 issues0/60000 ends60000/120000 versus cap2 issues0/0 ends60000/62000; D06 third120000 versus64000; D07 request33 issues60000, maximum32 credits. Releasing at latency end52000 fails. |
| Issue scheduling/phase crossings | Issue every credit-eligible request at the edge, sorted engine ID/request ID; no finite issue-rate cap. Phase0 completions/releases, phase1 readiness/arrivals, phase2 admission, phase3 statistics. Cross-owner zero-delay transitions use pending ready batches/inline closure without scheduling into an earlier same-time phase or owner key. K04/K05 owned-zero still queue behind active work and complete once. Preserve original raw next_edge(n=0) alignment versus owned-zero service law. D14 zero-hop must not become an ownership/dispatch bypass. |
| Core port/channel contention | One payload port per core shared across all DMA engines/read and write; one rational cap per channel shared by directions. FIFO ready time then engine/request IDs. Per-request ceil(payload/rate), never pool remainders. D08 two channels same response59000 → commits60000/61000; D15 doubling port rate512 leaves256B one-cycle service unchanged. Distinct cores/channels may overlap; do not globally serialize. |
| Barriers and dependencies | Resolve declared terminal participants, canonical barrier owner, one NoC overhead32 after last arrival; no compute overhead. D13 arrivals60000/62000 →94000. M's dependent operators wait on the actual predecessor join, with no implicit tensor forwarding or sharding. Independent ready tiles remain eligible concurrently. |
| Counts in `accounting.rs` | Increment only on successful tile/fragment/unicast completion, once per ID. Useful2mkn versus issued2m×256×256; no expected-total fallback. Fragment payload versus256B transaction separately by direction; compute staging SRAM reads/outputs separate from DMA SRAM traffic. C02 useful210/issued393216/SRAM100,42; C05 payload100/42,transactions512/256; C03 copied W counted per tile; D11 payload513/transactions768; D12 payload2/transactions512. Dropped/duplicate completion and padded-work-as-useful faults fail. |
| Allocation/queue/resource observations | Emit actual intervals/membership from state changes, not reconstructed expected counts. Buffers with no producer and reserved scratch are initially live until end; explicit lifetimes follow producer/final consumers. Q01 clipped areas8000 and6000 request-ps; Q02 final=32+128−64=96 bytes per boundary/direction/unit. Half-open window events include t0/exclude t1 with endpoint state immediately before events. Null zero-flow residence. Union busy intervals, exclude waits, preserve empty zero-duration service. Stationary Little's law ≤1% only at its separately frozen first reliance, not inferred from finite windows. |
| Causal attribution | Record actual resource predecessor and per-request subphase, including zero-time causal links. Backtrack tight blockers, canonical stable ties; no historical idle predecessor as cause. Compute staging/wave/drain alignment→compute; initial overhead alignment→overhead; NoC alignment/hops→noc; DRAM alignment/latency/queue/service/ceil, port wait/alignment/service and ack-core alignment→memory; barrier alignment/service→sync. D01 partition[0,4000)noc,[4000,54250)memory,[54250,59000)noc,[59000,60000)memory. D10 read partition0/3334/58917/62500/63750. Sum exactly duration; do not relabel queue wait as resource busy. |
| Result/public boundary | Preserve Python framing, descriptor/host verification, input/output caps, checked overflow, canonical hashes, error vocabulary and no partial success. Require all component observation sections observed, not K2 unrepresented placeholders. C1 maximum fidelity, u_c0_duration_ps=null, null energy/bank/link/row diagnostics and exact unrepresented paths. Three fresh-process and debug/release complete-byte replay; trace toggle only declared trace projection. Producers disabled on imported job replay. Existing K2 host/build authority never authorizes these results. |

`component-stage-tests.py.txt` is an unapplied public-boundary assertion module. Its
`component_run` fixture must call the released real process path and return validated
MappedEngineResult; `component_cases` supplies accepted jobs/anchors. Missing fixtures
must fail once applied, not permanently skip. Current Python unit tests prove only input
construction/admission/relocation. No expected timing is injected into mapped jobs.

Before execution, freeze B's C/D/Q profile bytes (including C08's24 pairs), expected semantic
outputs, human H-L1-GEMM-01/H-L1-DMA-01 working and baseline/fault/restored budget. Preserve
published B D02/D14 JSON and its proposed authority as distinct from A's generated placement.
A does not create a human signature. K2 findings remain inherited until the coordinator's
pinned campaign actually reconciles them. Local review supports only U0024 interim work;
remote qualification, controlled-host performance/nightly and closure remain pending.

Deferred explicitly: accumulator spill/steady/full decoder/RoPE/KV and reference precision
belong to W/R as consumed; NoC contention, physical DRAM queues/row models, compute2, mesh and
stationary qualification to U6/U-P13; FP8/ragged/full model product tables to T/U7 after
semantic admission. No full generic U-P11b acceptance case silently overrides U0011 B.
