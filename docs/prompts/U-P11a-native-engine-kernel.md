# U-P11a · U6 · Lane A — Native engine kernel: time, events, the wheel, ownership, and the protocol

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/engines/README.md, build-spec §2.5
(the engine protocol and TaskGraph) and §2.8 (the native engine specification; it is the
spec, not background), ADR U0005, U0007. Javid's docs/vision/elements_of_parallel_DES.md
from rk-sim, READ-ONLY, for the parts §2.8 adopts, and build-spec §2.8's "departures" table
for the parts it rejects and why.

TASK: the kernel of native/, uarch's own event-driven engine, C++20, built in the engine
container, and the plumbing that puts it behind exactly the same engine protocol as the
fork: EngineJob JSON in, EngineResult JSON out, invoked as a subprocess binary
`uarch-engine`. Single-threaded. No subsystem models yet: U-P11b adds them.

1. BEFORE MEASURING ANYTHING, write in ADR U0011 (a) the speed factor over the fork that you
   expect on npu-l4 and on a 16×16 mesh, and why (G5 checks it), and (b) a single-point
   wall-clock budget for the npu-m256 and 32×32 grids, above which parallelism inside one
   simulation is needed (U9's gate reads it).
2. Build: native/CMakeLists.txt; dependencies via FetchContent at pinned tags, ONLY
   nlohmann/json (MIT) and doctest (MIT), added to third_party/LICENSES.md. -Wall -Wextra
   -Werror; a sanitizer preset (ASan+UBSan) used by the nightly job.
3. Time: std::uint64_t picoseconds. Each clock domain has an integer period_ps.
   next_edge(domain, t_ps) is THE ONLY conversion between time and cycles; units in every
   name (_ps, _cycles). DVFS is a per-domain frequency ratio applied when the Simulation is
   constructed.
4. Event: a 32-byte trivially copyable struct {u64 t_ps; u64 seq; u32 target; u16 kind;
   u8 phase; u8 flags; u32 payload; u32 pad} with static_assert(sizeof(Event)==32). The total
   order is (t_ps, phase, target, seq), and seq is assigned at schedule time from one counter.
   Kinds: TASK_READY, COMPUTE_DONE, DMA_ISSUE, DMA_DONE, NOC_HEAD, NOC_TAIL, MEM_REQ,
   MEM_RESP, SYNC_ARRIVE, BARRIER_RELEASE, STAT_SAMPLE, END. Dispatch is a switch on kind,
   with no virtual calls on the hot path.
5. Scheduling: an event arena with a free list (no per-event heap allocation after warm-up);
   a two-level timing wheel (4,096 slots at the finest domain period) with a min-heap for
   overflow. Ties within a slot are resolved by the total order, never by insertion order.
6. State ownership: every resource (core matrix engine, core vector engine, SRAM bank group,
   DMA engine, router output port, link, memory channel) has exactly ONE owner id. State lives
   in structure-of-arrays indexed by owner id. Only events whose target is that id may mutate
   it; debug builds check this with an owner assertion on every mutation. Single-threaded,
   this is discipline; in U-P17 it becomes the partition boundary.
7. Topology: CSR adjacency; precomputed dimension-order routes (XY on mesh, shortest
   direction on torus); multiple NoCs, each with its own direction. Sorted vectors wherever
   iteration order could reach a result. NO std::unordered_map ITERATION ON ANY PATH THAT
   PRODUCES OUTPUT.
8. A fixed-delay executor: a TaskGraph whose jobs are fixed delays (no models yet),
   dependencies resolved by events, so the kernel runs end to end before any model exists.
9. src/rkuarch/engines/native/: the Python side: job writer, subprocess runner, result
   parser, identical in shape to engines/fork/, so `uarch table ... --engine native` reaches
   the binary.

ACCEPTANCE TESTS (write first):
1. doctest: event ordering, wheel overflow into heap and back, arena reuse, next_edge at
   domain boundaries, owner-assertion fires on a foreign mutation (debug build).
2. The build passes with -Wall -Wextra -Werror, and the sanitizer preset runs the doctests
   clean.
3. A fixed-delay TaskGraph's duration equals its critical path worked by hand in the test,
   and its EngineResult is byte-identical across 3 runs and under the sanitizer build.
4. The Python side round-trips an EngineJob through `uarch-engine`, and the EngineResult
   validates against the engine protocol.
5. Ties: events with equal t_ps resolve by (phase, target, seq), whatever order they were
   scheduled in.

GUARDRAILS: No subsystem models; they are U-P11b. No threads, no SIMD intrinsics, no GPU, no
MPI; those are U-P17 at the earliest, and only what it builds. Do not delete or bypass the
fork: it is the permanent L2 reference. Cycles never leave native/ and engines/. Do not
optimise before determinism holds.

ADR: docs/decisions/U0011-the-native-engine-core.md, started here: the expected speed factor
and the single-point budget (both written before any measurement), and each departure from
the vision note. The lookahead-collapse premise in particular: real routers take several
cycles per hop (Tenstorrent documents ~9 router-to-router on Blackhole), so it is not L = 1.
```
