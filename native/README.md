# native — our event-driven engine (Rust)

Spec: docs/build-spec.md §2.8 (and §2.9 for parallel execution). A Cargo workspace, built in
the engine container; `make native`, `make native-test`. Binary: uarch-engine
(EngineJob → EngineResult), behind the same subprocess protocol as every engine.

## Rules
- Time is u64 picoseconds; next_edge() is the only time↔cycle conversion.
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
