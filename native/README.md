# native — our event-driven engine (C++20)

Spec: docs/build-spec.md §2.8 (and §2.9 for parallel execution). Built in the engine
container; `make native`, `make native-test`. Binary: uarch-engine (EngineJob → EngineResult).

## Rules
- Time is u64 picoseconds; next_edge() is the only time↔cycle conversion.
- Events are 32 bytes, totally ordered by (t_ps, phase, target, seq). No virtual dispatch on
  the hot path.
- One owner per resource; only events targeted at it mutate it (asserted in debug builds).
- No unordered-container iteration on any path that reaches output.
- Dependencies: nlohmann/json, doctest, Ramulator 2 (from U7). Nothing else without an ADR.
- Determinism before speed. A speed-up that changes bytes is a bug.
