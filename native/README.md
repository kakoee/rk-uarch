# native — our event-driven engine (Rust)

Spec: docs/build-spec.md §2.8 (and §2.9 for parallel execution). A Cargo workspace, built in
the accepted engine container; `make native`, `make native-test` build/test the delivered
`uarch_engine` library target in package `uarch-engine`. This is private K1, not a public
binary or EngineJob/EngineResult subprocess boundary; those remain K2.

## Rules
- Time is u64 picoseconds; next_edge() is the only time↔cycle conversion. Clocks are
  integer freq_hz; edges are rounded up to the picosecond, periods never are.
- Ramulator 2 ticks in batches to a conservative horizon, catches up over idle gaps, and
  must match the tick-every-cycle debug mode byte for byte (build-spec §2.8).
- Events are 32-byte `#[repr(C)]` `Copy` structs, totally ordered by (t_ps, phase, target,
  seq). Dispatch is a `match` on kind; no `dyn` on the hot path.
- One owner per resource. The dispatcher derives a dispatch capability from the actual
  event target and the resolved job owner. Every owner mutation requires that capability;
  mismatches assert in debug and refuse in release. Dependency notifications reach the
  successor's owner through addressed events, not cross-owner writes by the predecessor.
- Queued insertion may not regress behind the last popped (time, phase, target, seq),
  or behind the current inline phase. Valid forward same-time insertion remains allowed.
  The phase-2 zero closure uses explicit inline addressed events, ordered by observation ordinal;
  their owner may decrease when canonical owner selection restarts. They share the global
  sequence allocator but are not retroactive wheel insertions. Dispatch records retain
  actual target/kind and distinguish queued from inline messages.
- K1 handles queued phases0/1 and inline phase2 only. Other queued phases refuse; the wheel
  supports phase0..3 but rejects unknown phases. No phase2/3 K2 handler is implemented.
- Private `dependency_resource_predecessors` is the sorted unique union of declared
  dependencies and the previous completed job on that owner, including idle gaps. It is
  not causal-blocker or critical-path evidence; public causal attribution remains separate.
- No HashMap or HashSet on any path that reaches output (clippy disallowed-types).
- `unsafe` only in crates/uarch-ramulator-sys, the C++ bridge to Ramulator 2; every other
  crate has #![forbid(unsafe_code)].
- Dependencies: serde, serde_json, proptest (dev); cxx and Ramulator 2 (from U7); loom (dev,
  from U9). Nothing else without an ADR; cargo-deny checks every licence.
- K2 will bind its public serde types to the installed engine schema. K1 serializes only
  private observation bytes and makes no public schema-conformance claim.
- Determinism before speed. A speed-up that changes bytes is a bug.

## Delivery status and order

Private K1 mechanics are implemented in the `uarch-engine` library target. No public
binary or JSON input is released; those remain K2. Private fixtures compile only under
`cfg(test)`. See [K1 handoff](../docs/reviews/U4-A-K1-v1/README.md) for actual evidence
and historical evidence. Stage2 corrections remain an unapplied proposal pending the
same reviewer’s Stage3 adjudication; U0024 separates local checks from remote qualification. U0005 selects one progressive production engine:
U3 design → U4a M plus K1, then K2/bounded models → U4b reference-suite readiness.
U6 adds qualification at representative mesh points; U7 adds detail and full product tables. Independent mathematics and behavioral tests accompany each
stage. No complete fork or second Python contention engine is a prerequisite. Optional
reference matches are scoped verification; only applicable silicon evidence validates.

U0023 separates K1 internal mechanics from K2 public schema wiring and correctness CI
from controlled-host performance. U5/U8 silicon success is not a table-production gate.
G5-correctness alone gates U7/G6/G3b/U10; full G5, U9 entry, simulator-performance
claims and final closure still require controlled-host evidence and self-hosted nightly.
