# U-P13a · U7 · Lane A — Native NoC at "1+ts": reservation calendars and NoC barriers

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, build-spec §2.4 (the per-subsystem ladder and
fidelity_detail) and §2.8, ADR U0011, U0012 (what did not agree, and why), and U0008's NoC
L2 report.

TASK: the first contention-aware subsystem of the native engine: the NoC at level 1 with
cycle timestamps.

1. NoC level 1 WITH CYCLE TIMESTAMPS ("1+ts"): reservation calendars per link and per router
   output port (the vision note's "F2a"). A packet reserves [start, start + serialisation)
   at each resource along its precomputed route. Head and tail timing propagate wormhole
   dependencies; virtual-channel occupancy and credit backpressure are modelled at packet
   granularity; multicast along rows and columns. BookSim2 STAYS the L2 reference. Do not
   build a flit-level router of your own, and do not build a third NoC backend.
2. Barriers follow sync.mechanism: with noc_semaphore they are NoC messages and contend like
   any other traffic.
3. The NoC diagnostics that level models (latency p50 and p99, maximum link utilisation) are
   filled; the rest stay null.

ACCEPTANCE TESTS (write first):
1. L0, L0m and L1 pass at the new level; L2 NoC (vs standalone BookSim2) passes U-P8's bound
   against the native engine.
2. Contention actually bites: a hotspot mapping on npu-m256 is measurably slower than a
   uniform one at equal MACs and bytes. At NoC level 0 the two are identical, and the test
   asserts both halves.
3. A barrier across 64 cores takes longer under background NoC traffic than on an idle NoC.
4. Determinism: byte-identical at 1 and N workers; the debug build runs clean.

GUARDRAILS: No threads yet. Do not remove the level-0 path: it is a fast mode. Do not tune
reservation parameters to match BookSim. Record the gap and its mechanism in the L2 report.

ADR: none here; U-P13d's U0013 records this level and its BookSim gap.
```
