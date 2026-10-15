# Final M trust joins and corrected SRAM inputs

This supersedes only D02/D14's initialization/graph binding in B-inputs/1; no accepted
model law changes. All inputs remain proposals under docs/reviews, not installed test
hardware or qualifying human-approved profiles. Agent-authored literal inputs and arithmetic
are not native evidence or human L1 work. [fixture-identities.json](fixture-identities.json)
records complete bundle/point/graph/profile/spec identities; the five files under fixtures/
contain exact canonical JSON (two bundles, two profiles and one registry). The literal
[authoring script](fixture_authoring.py) binds its own bytes as authoring identity; it calls
no mapper/workload producer, oracle or native engine. The carrier is imported only in scratch.

Both cases use B/test/transport_fixture/**fixture_resident**, seed 0, priming 0, no clock_setup
and verification_only. Source SRAM preloading is explicit. Destinations are allocated and
uninitialized, named producing jobs and terminal readers match. Cold-SRAM mutation with a
matching resealed test profile refuses UnsupportedInitialState; without matching the profile
it first refuses TestVariantNotAdmitted. Removing source preload without adding a producer
refuses InvalidDependency. Product attachment refuses TestOnlyScope. Rehashing a changed
profile does not replace the original test-host anchor. None of those synthetic host anchors
claims Javid's acceptance; production loader authority remains the proposed Git-acceptance
mechanism requiring his decision.

## D02 — one isolated resident-source write

Baseline npu-l4 hash unchanged. Source s: core 0 SRAM[0,256), bank 0, preloaded, final reader w.
Destination h: HBM[1536,1792), uninitialized, producer w. DMA engine 0, channel 6,
controller 3/core 3, XY route[0,1,3]. One 256 B payload/transaction request w.r0; no predecessors.
All clocks 1 GHz, 32 credits available, one used; shared port 256 B/core cycle; no compute overhead.

Independent E4 derivation: port ends 1000 ps; outgoing four NoC cycles end 5000;
48 DRAM cycles end 53000; exact channel rate 4437500000000/39 B/s, service 159744/71 ps;
exact finish 3922744/71 ps, ceil 55250; return aligns 56000 then four cycles ends 60000;
core ack/release 60000. Makespan 60000 ps; read payload/transactions 0, write 256/256 B,
unicast 0. A second port charge on acknowledgement or generic 32-cycle job overhead fails.
The resident source is a test premise, not implicit cold initialization or measured memory.

## D14 — zero-hop at an explicitly produced nonedge readiness

The historical scalar law at 835 ps remains valid mathematics but was not a complete public
transport graph: transport fixtures have no arbitrary external start timestamp. This exact
revision makes readiness observable through allowed jobs, instead of fabricating that field.

Proposed-design hardware differs only in ID and the NoC 1.2 GHz stipulation/rationale;
core/DRAM stay 1 GHz. New spec hash is in the case manifest and the proposed test-only registry;
baseline is not registered as test-only. The variant is not installed under hw/designs and
cannot confer production permission. Eventual hardware placement/registry approval precedes use.

- a reads HBM[1536,1792), channel 6 → core 0 SRAM[512,768).
- b reads HBM[1792,2048), channel 7 → core 0 SRAM[768,1024).
- Both issue 0 on engine 0, route[0,1,3], distinct requests a.r0/b.r0, 256 B each.
- c depends on b; it transfers 256 B from explicit resident ss:SRAM[0,256) to
  uninitialized sd:SRAM[256,512), both core 0, route[0]. No alias, no DMA credit for c.

Independent crossings for each read: arrival 3334 ps, DRAM entry 4000/latency end 52000,
channel exact 3851744/71 and published 54250; return aligns 55000 and ends 58334.
Separate channels overlap; shared port starts 59000, commits a at 60000 then b at 61000
(canonical a-before-b). Hence c ready/commits at **61000 ps**, no positive service interval
and exactly one unicast commit. Wrong NoC edge alignment yields **61667 ps**; an added hop
also fails. Two credits acquired 0, released 60000/61000; final inflight 0. Read payload and
transactions 512/512 B, write 0/0 B, unicast 256 B. No physical NoC bandwidth/queue claim.
The declared graph contains the two read producers; this is not a second timing engine.

## Actual final A joins and remaining first-use bindings

| First use | Exact final A input / B disposition |
| --- | --- |
| K01 public fixed delays | kernel/kernel-job/profile final identities in A package.json; 7000 ps expectation unchanged, new assumptions/profile/clock hashes supersede early input identities |
| K06/K07 clocks | Final ClockSetup hash checked against profile. A's nonempty 3-cycle positive, changed 4-cycle job refusal and full caller rehash against original host anchor rerun in the 65 M tests. Actual 100 edge entries/specs/graphs are still to freeze before K2, not a K1 schema prerequisite |
| K1 private kernel | No public profile/registry required. Real private tests, pins/licences and Linux checks suffice at their released boundary; full later B/L1 corpus is not a K1 gate |
| C02 resident | A resident.json/resident-profile.json: m=3, k=5, n=7, explicit preloads, 547000 ps resident compute expectation; qualifying native result remains absent |
| C05 cold | A component/component-job channels 0/1/2 versus B C05 channels 6/6/6; useful 210, issued 393216, payload 100/42, transaction 512/256 agree; placement/identities and whole-job timing do not transfer |
| D02/D14 | Exact new resident bundles/profiles/registry here; published hashes are proposals, not trusted production installation or executable engine identities |
| Other K/Q/C/D cases | Full graph/spec/profile/job binding and actual expected engine identity still needed at K2/B first use; K03's 100 wheel/heap schedules depend on real private API; no invented test names or complete-corpus claim |
| Human L1 | H-L1-DMA-01/H-L1-GEMM-01 remain unassigned/unfilled; SKIP, never agent signoff; applicable B L1 deadline unchanged |

Validation order remains syntax/embedded identities, host trust/invocation/profile tuple,
checkpoint/hardware/state, then resource semantics. Carrier self-consistency is not launch
permission. Final host registry mismatch is RegistryTrustMismatch; untrusted/rehashed profile
is TestProfileMismatch. Exact trusted registry/profile and engine authority inputs must come
from the accepted loader record, never from the same untrusted request being checked.
