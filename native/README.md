# native — our event-driven engine (Rust)

Spec: docs/build-spec.md §2.8 (and §2.9 for parallel execution). A Cargo workspace, built in
the engine container; `make native`, `make native-test`. Binary: uarch-engine
(EngineJob → EngineResult), behind the same subprocess protocol as every engine.

## Rules
- Time is u64 picoseconds; next_edge() is the only time↔cycle conversion. Clocks are
  integer freq_hz; edges are rounded up to the picosecond, periods never are.
- Ramulator 2 ticks in batches to a conservative horizon, catches up over idle gaps, and
  must match the tick-every-cycle debug mode byte for byte (build-spec §2.8).
- Events are 32-byte `#[repr(C)]` `Copy` structs, totally ordered by (t_ps, phase, target,
  seq). Dispatch is a `match` on kind; no `dyn` on the hot path.
- One owner per resource; only events targeted at it mutate it (asserted in debug builds).
- No HashMap or HashSet on any path that reaches output (clippy disallowed-types).
- `unsafe` only in crates/uarch-ramulator-sys, the C++ bridge to Ramulator 2; every other
  crate has #![forbid(unsafe_code)].
- Dependencies: serde, serde_json, proptest (dev); cxx and Ramulator 2 (from U7); loom (dev,
  from U9). Nothing else without an ADR; cargo-deny checks every licence.
- The engine protocol's JSON Schema (src/rkuarch/engines/schema/) is the contract with the
  harness; a Rust test holds the serde types to it.
- Determinism before speed. A speed-up that changes bytes is a bug.

## Delivery status and order

Native is planned, not yet implemented. U0005 selects one progressive production engine:
U3 design → U4a M plus K1, then K2/bounded models → U4b reference-suite readiness.
U6 adds qualification at representative mesh points; U7 adds detail and full product tables. Independent mathematics and behavioral tests accompany each
stage. No complete fork or second Python contention engine is a prerequisite. Optional
reference matches are scoped verification; only applicable silicon evidence validates.

U0023 separates K1 internal mechanics from K2 public schema wiring and correctness CI
from controlled-host performance. U5/U8 silicon success is not a table-production gate.
G5-correctness alone gates U7/G6/G3b/U10; full G5, U9 entry, simulator-performance
claims and final closure still require controlled-host evidence and self-hosted nightly.
