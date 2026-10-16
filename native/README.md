# native — our event-driven engine (Rust)

Spec: docs/build-spec.md §2.8 (and §2.9 for parallel execution). A Cargo workspace, built in
the accepted engine container. Package `uarch-engine` now contains the `uarch_engine`
library and the `uarch-engine` fixed-delay JSON binary under the approved K2 construction
milestone. Actual public execution remains gated on an independently accepted human host record.

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
- Dependencies: exactly accepted serde, serde_json, sha2 (`force-soft`), proptest (dev)
  and their preserved C1 lock closure. No opportunistic updates; cargo-deny checks licences.
- K2 validates complete admitted carriers and joins independently; the owned carrier snapshot
  comes from installed M shapes. Private mechanics observations are not public qualification.
- Determinism before speed. A speed-up that changes bytes is a bug.

## Delivery status and order

The construction source and interfaces are in
[the owned K2 package](../docs/reviews/U4-A-K2-construction-v1/peer-interface.md).
Normal library/binary builds require an explicitly generated identity file in a private
source export; an unbound checkout intentionally has no fallback engine identity.
`native/tools/freeze_inputs.py` verifies source bytes against an explicit published commit.
`native/tools/generate_identity.py` takes checked BuildInputs/ToolInputs/BuildTrust files and
writes only the named identity output into that private export before Cargo is invoked.
No generated identity or binary belongs in the live source tree. The exact build commands,
image/cache/flags and two mode identities are recorded in the owned build handoff.

Library unit tests operate on private mechanics and explicit synthetic validation controls;
the public tests in `tests/native/test_u4_a_k2_public.py` are authored but not invoked during
construction. No component model, final host authority, qualification or image distribution
is released by a successful local build. Historical K1/C1/C2 evidence remains unchanged.

U0023 separates K1 internal mechanics from K2 public schema wiring and correctness CI
from controlled-host performance. U5/U8 silicon success is not a table-production gate.
G5-correctness alone gates U7/G6/G3b/U10; full G5, U9 entry, simulator-performance
claims and final closure still require controlled-host evidence and self-hosted nightly.
