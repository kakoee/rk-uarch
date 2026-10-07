# U-P11a · U6 · Lane A — Native engine kernel: time, events, the wheel, ownership, and the protocol

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/engines/README.md, build-spec §2.5
(the engine protocol and TaskGraph) and §2.8 (the native engine specification; it is the
spec, not background), ADR U0005, U0007. Javid's ../rk-sim/docs/vision/elements_of_parallel_DES.md
from rk-sim, READ-ONLY, for the parts §2.8 adopts, and build-spec §2.8's "departures" table
for the parts it rejects and why.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Reuse the U2/U4 versioned prepared-job protocol and fixtures. Rust receives resolved
shapes, resource assignments, dependencies and policies; no model builder or mapper runs
inside the engine. Timing/events are outputs of executing those inputs. Extend the accepted
protocol only through its versioned schema procedure, not a parallel Rust-only format.

TASK: the kernel of native/, uarch's own event-driven engine, in Rust, built in the engine
container, and the plumbing that puts it behind exactly the same engine protocol as the
fork: EngineJob JSON in, EngineResult JSON out, invoked as a subprocess binary
`uarch-engine`. Single-threaded. No subsystem models yet: U-P11b adds them.

1. BEFORE MEASURING ANYTHING, write in ADR U0011 (a) the speed factor over the fork that you
   expect on npu-l4 and on a 16×16 mesh, and why (G5 checks it), and (b) a single-point
   wall-clock budget for the npu-m256 and 32×32 grids, above which parallelism inside one
   simulation is needed (U9's gate reads it).
2. Build: native/Cargo.toml (workspace) with crates/uarch-engine (the `uarch-engine`
   binary); native/rust-toolchain.toml pinning the current stable Rust, recorded in U0011;
   a committed Cargo.lock. Dependencies ONLY serde and serde_json, plus proptest as a
   dev-dependency, each added to third_party/LICENSES.md. native/deny.toml makes cargo-deny
   check every crate's licence against the allow-list; if a core crate needs a licence
   outside it (serde_derive's unicode-ident carries Unicode-3.0, for example), stop and
   propose the allow-list change in an ADR. The crate has #![forbid(unsafe_code)];
   clippy runs with -D warnings and disallows HashMap and HashSet; rustfmt is enforced.
   Add the Rust toolchain to containers/Dockerfile.engine, and wire `make native` and
   `make native-test` to cargo.
3. Time: u64 picoseconds. Each clock domain has the resolved integer freq_hz from the
   EngineJob, NEVER A ROUNDED PERIOD (1.2 GHz is 833.33… ps, and rounding it either way
   biases every row or breaks the roofline floor). EDGES ARE ROUNDED, PERIODS ARE NOT: edge k
   sits at t_k = ceil(k · 10^12 / freq_hz) ps, computed exactly in u128.
   next_edge(domain, t_ps, n_cycles) returns t_{k+n}, where t_k is the first edge at or after
   t_ps. It is THE ONLY conversion between time and cycles; units in every name (_ps,
   _cycles, _hz). DVFS is a per-domain frequency ratio, applied through the resolved freq_hz
   when the Simulation is constructed.
4. Event: a 32-byte #[repr(C)] Copy struct {t_ps: u64, seq: u64, target: u32, kind: u16,
   phase: u8, flags: u8, payload: u32, pad: u32} with a compile-time assertion that its size
   is 32. The total order is (t_ps, phase, target, seq), and seq is assigned at schedule time
   from one counter.
   Kinds: TASK_READY, COMPUTE_DONE, DMA_ISSUE, DMA_DONE, NOC_HEAD, NOC_TAIL, MEM_REQ,
   MEM_RESP, MEM_TICK, SYNC_ARRIVE, BARRIER_RELEASE, STAT_SAMPLE, END (MEM_TICK is unused
   until U-P13b's Ramulator 2 path, build-spec §2.8). Dispatch is a match on kind,
   with no trait objects (dyn) on the hot path.
5. Scheduling: an event arena with a free list (no per-event heap allocation after warm-up);
   a two-level timing wheel (4,096 slots, each floor(10^12 / max freq_hz) ps wide, at least
   1) with a min-heap for
   overflow. Ties within a slot are resolved by the total order, never by insertion order.
6. State ownership: every resource (core matrix engine, core vector engine, SRAM bank group,
   DMA engine, router output port, link, memory channel) has exactly ONE owner id. State lives
   in structure-of-arrays indexed by owner id. Only events whose target is that id may mutate
   it: only that event's handler gets &mut access to the owner's state, and debug builds
   assert the target on every mutation. Single-threaded, this is discipline; in U-P17 it
   becomes the partition boundary, enforced by the compiler.
7. Topology: CSR adjacency; precomputed dimension-order routes (XY on mesh, shortest
   direction on torus); multiple NoCs, each with its own direction. Sorted vectors wherever
   iteration order could reach a result. NO HashMap OR HashSet ON ANY PATH THAT PRODUCES
   OUTPUT: Rust randomises their iteration order. Use BTreeMap or sorted Vecs.
8. A fixed-delay executor: a TaskGraph whose jobs are fixed delays (no models yet),
   dependencies resolved by events, so the kernel runs end to end before any model exists.
9. src/rkuarch/engines/native/: the Python side: job writer, subprocess runner, result
   parser, identical in shape to engines/fork/, so `uarch table ... --engine native` reaches
   the binary.
10. The protocol as a schema: reuse U2/U4's EngineJob/EngineResult schemas and fixture
    messages from engines/protocol.py in src/rkuarch/engines/schema/. `make gen` keeps exporting
    them; the freshness check remains read-only. Test Rust serde types against those fixtures,
    including prepared input versions/hashes and refusal cases, so neither side drifts alone.

ACCEPTANCE TESTS (write first):
1. cargo test: event ordering, wheel overflow into heap and back, arena reuse, next_edge at
   domain boundaries, owner assertion fires on a foreign mutation (debug build); proptest
   checks the wheel against a sorted reference over random schedules.
1a. Clock edges: at 1.2 GHz, next_edge(core, 0, 3) == 2500 and next_edge(core, 0, 10^9) ==
   833_333_333_334 (no drift); proptest over random freq_hz and k asserts
   0 <= t_k · freq_hz − k · 10^12 < freq_hz (never early, under 1 ps late); a fixed-delay job
   of N core cycles started at t = 0 never ends before N / freq_hz exactly.
2. cargo fmt --check, cargo clippy --all-targets -- -D warnings and cargo deny check
   licenses pass; the engine crate forbids unsafe.
3. A fixed-delay TaskGraph's duration equals its critical path worked by hand in the test,
   and its EngineResult is byte-identical across 3 runs and between debug and release
   builds.
4. The Python side round-trips an EngineJob through `uarch-engine`, and the EngineResult
   validates against the engine protocol.
5. Ties: events with equal t_ps resolve by (phase, target, seq), whatever order they were
   scheduled in.
6. Protocol drift: the Rust types parse and re-emit every schema fixture unchanged, and a
   fixture with an unknown field is refused, as Pydantic's extra="forbid" refuses it.

GUARDRAILS: No subsystem models; they are U-P11b. No unsafe. No threads, no SIMD intrinsics
(std::simd, core::arch), no GPU, no MPI; those are U-P17 at the earliest, and only what it
builds. Do not delete or bypass the
fork: it is the permanent L2 reference. Cycles never leave native/ and engines/. Do not
optimise before determinism holds.

ADR: docs/decisions/U0011-the-native-engine-core.md, started here: the expected speed factor
and the single-point budget (both written before any measurement), the pinned Rust version,
the time base as built (build-spec Rev 2.3: resolved integer freq_hz, rounded edges),
and each departure from the vision note. The lookahead-collapse premise in particular: real routers take several
cycles per hop (Tenstorrent documents ~9 router-to-router on Blackhole), so it is not L = 1.
```
