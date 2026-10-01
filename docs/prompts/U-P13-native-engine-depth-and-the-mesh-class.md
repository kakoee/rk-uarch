# U-P13 · U7 · Lane A — Native engine depth: contention, the mesh class, and composite C2

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/mapping/README.md, build-spec §2.4
(the per-subsystem ladder and the composite rule), §2.8, ADR U0011, U0012 (what did not
agree, and why). Ramulator 2 documentation (its External frontend, for use as a library).

TASK: take the native engine from C1 to an honest composite C2, and make the mesh class a
first-class target.

1. NoC level 1 WITH CYCLE TIMESTAMPS: reservation calendars per link and per router output
   port (the vision note's "F2a"). A packet reserves [start, start + serialisation) at each
   resource along its precomputed route. Head and tail timing propagate wormhole
   dependencies; virtual-channel occupancy and credit backpressure are modelled at packet
   granularity; multicast along rows and columns. BookSim2 STAYS the L2 reference. Do not
   build a flit-level router of your own, and do not build a third NoC backend.
2. DRAM level 2: Ramulator 2 linked as a library through its External frontend, at the SHA the
   engine image pins, one instance per memory controller, configured from the spec's DRAM
   organisation and timing (never from a preset the spec does not name). Keep DRAM level 1
   (a per-channel queue with a row-buffer approximation and the spec's page policy) as the
   fast path. Addresses map to channels and controllers by memory.interleave, so the NoC sees
   the traffic pattern the interleaving creates. The job chooses; EngineResult
   reports which ran.
3. Compute level 2: SRAM bank conflicts (from the mapping's buffer placement) and
   DMA/compute interleaving at cycle timestamps, still O(1–10) events per tensor job wherever
   no conflict occurs. When the spec has a shared_sram, model it at level 0 (capacity and
   bandwidth cap) and level 1 (a per-port queue with cycle timestamps, "1+ts"), attached to the
   NoC like a memory controller. Barriers follow sync.mechanism: with noc_semaphore they are
   NoC messages and contend like any other traffic.
4. Mesh-class mapping policies in src/rkuarch/mapping/ (Python, shared by every engine):
   - summa-2d@1: GEMM outputs blocked over the core grid, operands multicast along rows
     and columns;
   - head-parallel@1: attention heads distributed over cores, KV resident per head group
     and read in pages of the request's block size.
   Each carries its own docstring derivation of per-core bytes and MACs. L0 checks those
   against the graph.
5. THE COMPOSITE RULE (build-spec §2.4), enforced in native/ and re-checked in Python:
   - report C2 ONLY IF every shared resource (NoC, DRAM, SRAM banks, shared SRAM when
     present) is at level 2, or at
     level 1 with cycle timestamps, AND synchronisation is exact;
   - otherwise C1, if any subsystem is at level 1;
   - otherwise C0-equivalent.
   Emit the full per-subsystem vector as fidelity_detail. A request that asks for C2 and
   cannot get it degrades or raises exactly as build-spec §7.4 says for default vs override.
6. Scale: build full tables for npu-m256 (16×16) and a 32×32 variant. Record the simulator
   metrics from U-P12 for both.

ACCEPTANCE TESTS (write first):
1. L0, L0m, L1 pass at every new level; L2 NoC (vs BookSim2) and L2 DRAM (vs standalone
   Ramulator 2) pass their U-P8 bounds against the native engine.
2. G6: the npu-m256 table reports composite C2 with detail {compute: 2, noc: 1+ts,
   dram: 2 or 1+ts, sync: exact}. A job with any subsystem at level 0 is refused C2, with
   the reason.
3. Roofline floor: no row of any native table is faster than its U-C0 roofline.
4. Contention actually bites: a hotspot mapping on npu-m256 is measurably slower than a
   uniform one at equal MACs and bytes. At level 0 the two are identical, and the test asserts
   both halves.
5. Determinism: byte-identical at 1 and N workers; sanitizer build clean.
6. Interleaving bites: changing memory.interleave's granularity changes the per-controller
   traffic split and the NoC diagnostics, at equal bytes.
7. With a shared_sram at level 0, C2 is refused, with the reason.

GUARDRAILS: Do not claim C2 with any subsystem at level 0. No threads yet. Do not remove the
level-0 and level-1 paths: they are the fast modes, and the ladder is a feature. Do not tune
reservation parameters to match BookSim. Record the gap and its mechanism.

ADR: docs/decisions/U0013-the-composite-fidelity-rule.md.
```
