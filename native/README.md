# native — our event-driven engine (Rust)

Spec: docs/build-spec.md §2.8 (and §2.9 for parallel execution). A Cargo workspace, built in
the accepted engine container. Package `uarch-engine` now contains the `uarch_engine`
library and the ordinary component JSON binary. Build with `make native`; no generated
identity file, build archive or compiled case inventory is required. Use
`uarch-engine --protocol uarch-engine/4` with one EOF-delimited job on stdin. Success is
canonical JSON on stdout/status 0; semantic refusal is JSON on stderr/status 2; operational
failure is nonzero. Test fixtures require the explicit `--test-only` argument. The Python
`python -m rkuarch.engines.native.ordinary` consumer independently validates results and bounds process I/O/deadlines.
The complete transition awaits human protected installation; see the README status.

Current version/replay limit: `/4` accepts package version `0.0.1` only, without a local
build identifier, and both run and replay require that installed version. It does not
distinguish builds. Engine `native-stage/2` and model `native-intervals/2` identify the
implemented semantics. A package version change requires a protected contract change and
an explicit compatibility decision at that time; cross-version replay is not supported.
Fixture admission also requires 32-cycle job overhead and 32-cycle barrier latency,
the values supported by the independent checker. Other values refuse as `UnsupportedHardware`.

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

The `/4` route uses engine `native-stage/2`, package version from Cargo/package metadata,
and model `native-intervals` version `2` with observations `/3`. Input/request/prepared/result
hashes remain data integrity checks. Historical K2 `/3` carriers, fixtures, schemas and
oracle bytes remain unchanged and are refused on `/4`. Historical native semantic tests
still exercise their internal admission paths. No historical authority can enable `/4`.

Retired host/deployment gates, startup loaders, construction attestations and campaign
drivers are removed. Historical reports, receipts, fixtures and oracle bytes remain;
reconstructing their old operational tools requires the corresponding Git revision.
Shared semantic validators and historical observation tests remain. The stopped startup
experiment must not be rerun; its historical results do not qualify the new route. Export the `/4` Rust carrier with
`python native/tools/export_ordinary.py`; `--check` is read-only. No oracle regeneration.

Use the accepted local Rust 1.99.0 image, existing offline Cargo cache and Cargo.lock.
`make native-test` runs normal Cargo tests, including the shipping /4 production and fixture
process paths, deterministic repeats, explicit invocation/protocol refusals and hardware
capability controls. Optional Python process checks accept `ORDINARY_NATIVE` pointing to
that local binary. U0024 still defers hosted native execution.
`cargo build/test --locked --offline --target x86_64-unknown-linux-gnu` are normal builds;
record status and test results without requiring compiler-read traces or binary identity.

U0023 separates K1 internal mechanics from K2 public schema wiring and correctness CI
from controlled-host performance. U5/U8 silicon success is not a table-production gate.
G5-correctness alone gates U7/G6/G3b/U10; full G5, U9 entry, simulator-performance
claims and final closure still require controlled-host evidence and self-hosted nightly.
