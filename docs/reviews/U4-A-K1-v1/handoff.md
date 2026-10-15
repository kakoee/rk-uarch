# Private K1 handoff for coordinator reconciliation

Human authority is installed/published at ab7d9e0ab81be02a7294d18aeab8bca5591cfda6;
U0011 SHA256 f452e2263b9e64a837e0a9fccaae73c7a5b01bd601a5f7cee141e06a7ca23a8f
matches the approved after-image. u03-end target 6d39a234 remains an ancestor. A integrated
B's 07eb628d8478f9c0d753eb9d42b9931108501ccd normally before publishing implementation.

## Published implementation

- d8a110e6a037d7fc854b8e06ba5dc56a938e0e31: tests first, accepted manifests/lock/toolchain/
  deny/container mappings. Initial missing-kernel compilation failure is retained.
- ba948995e53a01cfdc3d1f3fdbec6b4c0009122a: kernel, additional FIFO/domain/interleaving
  controls, Make commands, exact licence exception and numbered register patch.
- 357dea8ee43ae098c284c672a44e6a6cf8482d27: B's requested private replay stdout prefix.
  This is the source subject of final native/fault receipts. Later handoff-only bytes
  do not change kernel/tests, manifests, lock, features or container inputs.

Normal main pushes preserve all peer commits. B's workflow, guards and environment
packages are unchanged. No protected M source, policy transition, oracle inputs/artifacts,
ADR, public K2 boundary, mapper or subsystem model is installed by this continuation.

## Actual private boundary

One Rust package `uarch-engine`, one library/test target `uarch_engine`; no released
binary/JSON input/subprocess interface. Rust types are internal integration APIs, not
another serialized public workload format. The crate is publish=false and forbids unsafe.

| Source | Implemented boundary |
| --- | --- |
| native/crates/uarch-engine/src/time.rs | checked u128 edge arithmetic, u64 ps; sole next_edge conversion; resolved integer clock frequencies |
| event.rs | exact 32-byte repr(C) event, schedule-time sequence, (time,phase,target,seq) key, free-list arena, two 4096-slot levels and overflow heap; per-slot heaps retain allocation |
| simulation.rs | private resolved fixed-delay jobs/DAG validation; SoA owner queues/active/busy-until/previous state; owner-target guard; phase0 completion/phase1 readiness/phase2 canonical zero closure; actual completion/event/resource observations |
| topology.rs | sorted CSR adjacency and precomputed XY mesh/shortest torus routes; explicit per-instance tie direction; distinct instances for distinct NoCs; no link timing model |
| tests.rs | 19 private tests, including three 256-case proptests with seed41011 in retained runs |

The wheel finds minima across slot heads before promoting the applicable upper/overflow
window; it does not advance through every idle tick. No optimization or performance claim
is made. Private observations serialize in struct/ordered-vector order with serde_json.
Completion counts come from executed completion paths. The always-recorded private trace
has no on/off feature; public result/observation contracts and optional tracing remain K2.

Owned zero delays, including zero cycles, complete only after grant and do not align to a
later clock edge. Positive cycle delays use next_edge with the selected resolved domain.
At frequencies above one edge/ps, multiple physical edges can round to the same timestamp:
the initial test's 2THz expectation was corrected from2 to1ps under the already accepted
edge formula, without changing that formula. This private arithmetic control is not a
new production hardware/frequency admission. Graphs refuse duplicate IDs/edges, missing
predecessors, cycles, invalid owners/domains/clocks and time overflow; queue refuses past
scheduling and checked sequence overflow. Public schema/profile refusals remain K2/M.

## Observed checks and practical limits

All native execution below is **local WSL2 using matching 1.99.0 tools**, not B's accepted
Linux builder/hosted evidence. Explicit RUSTUP_TOOLCHAIN=stable selects the existing local
alias; its rustc full commit, cargo, rustfmt, clippy and cargo-deny stdout match the five
accepted receipts byte-for-byte. native/rust-toolchain.toml remains exactly1.99.0;
no other release/features or shared toolchain installation was substituted.

| U-P11a requirement | Actual local evidence | Remaining |
| --- | --- | --- |
| 1 | event order, overflow/promotion, arena reuse, owner guard debug panic/release refusal, sorted-reference wheel properties (bulk and interleaved) | B real Linux execution/review |
| 1a | 1.2GHz literals, billion-cycle833333333334ps, boundary/fractional/multiple clocks, rational never-early property, overflow refusals | same |
| 2 | fmt; clippy all-targets/all-features -D warnings; pinned cargo-deny licenses/bans/sources; forbid unsafe/disallowed unordered types; exact input hashes | same; B's actual recipe discovery |
| 3 | literal7000ps critical path and5000ps busy-owner-zero discriminator; 19/19 debug and19/19 release; six fresh-process private result payloads identical | same; public repetition waits K2 |
| 5 | exact phase/target/sequence tie order plus random schedules and canonical FIFO readiness | same |

No ignored tests. Empty doc-test suites are not counted. [test-inventory.json](test-inventory.json)
contains the exact discovered target and all19 names, each multiplicity1 in both modes.
[local-checks.json](local-checks.json) records commands/exits; adjacent logs are real outputs.
[metadata-check.json](metadata-check.json) records B guard validate_package/plan/metadata
success on actual Cargo metadata: all27 external crate identities/features match.
[archive-checks.json](archive-checks.json) records SHA256 checks of all locked archives.
Raw verbose Cargo metadata is reduced to its stdout hash and observed guard results to
avoid duplicating the accepted dependency package. All five native mappings and installed
Dockerfile match the accepted package; no new dependencies or feature changes.

Replay is `tests::canonical_replay_private_bytes`, `--exact --nocapture`, prefix
`UARCH_K1_REPLAY_V1=`. Three independent cargo/test process invocations per mode produced
SHA256 30c1e07014f238784ba570a367db1584847134280b2e4190c91761b9b179094a.
One [canonical payload](canonical-private-result.json), six printed execution logs and
[comparison receipt](replay-summary.json) are retained. These are executed internal
observations, not a schema fixture fabricated from expected values.

Three semantic faults were applied only to a disposable `git archive` of357dea8:
rounded-period timing, insertion ordering before target ordering, and dependency-ready
zero completion bypassing the owner. Each ran baseline/fault/restored in **both** modes:
12 positive executions passed;6 fault executions failed the intended assertion. The zero
fault observed3000 versus required5000ps. [fault-anchors.json](fault-anchors.json) gives
original file hashes, unique replacement strings, test names and diagnostic anchors;
[fault-results.json](fault-results.json) and logs retain actual commands/status. Scratch
source was restored and removed; live source was never mutated for these checks.

The accepted deny policy passes. The unexcepted policy refuses Unicode-3.0 (actual
cargo-deny exit4); this is an expected refusal, not a failed accepted-policy check.
Collector corrections before final receipts: expected deny status changed from1 to4;
replay glob narrowed to six payload files after it included its previous summary. The
latter was a collector error, not differing engine bytes. Clippy's initial nested-if
warning was fixed before its recorded pass. No failing result is represented as a pass.

Ordinary checks: strict live vendor currentness passed;33 Python licence/prompt/CI-scope
controls passed; repository ruff passed; make native built the library; git diff --check
and reverse-application of numbered register patch passed. Existing v1/v2 runtime/source
was untouched; no broad Python runtime rerun or new legacy acceptance is claimed.

## B/human joins and stop boundary

B07eb628 reports Docker unavailable in this WSL environment. The accepted final builder,
offline cache, tool discovery and actual Linux checks remain pending, not replaced by
A's matching local tools. No final RepoDigest, CI pass, native qualification, performance
result, K1/G3a/U4 closure or independent verdict is asserted. Hosted CI is asynchronous;
A does not poll it.

B owns its environment and CI. Consume exact target/name/prefix/anchors above, perform
original/fault/restored and six-process replay under accepted pins, then freeze the real
builder identity and test inventory. There is no new request to accept the settled tools.
Two live CI gaps are explicit in [lane-B-checkpoint.md](lane-B-checkpoint.md): the legacy
patch job rejects any numbered patch, and the native job still installs unpinned cargo-deny.
A leaves both peer-owned workflow changes to B. The numbered register patch is an applied
local register delta, not a modification to upstream dependency code. Its reverse check
proves the installed postimage; an apply check can use the ab7d9e0 preimage.

A owns kernel/model laws; B owns independent verification/CI; Javid/coordinator own exact
protected acceptance and human artifact lifecycle. M/policy freeze stays wholly separate.
Next A work is bounded correction from B/coordinator K1 review. Public K2 needs its own
release and installed mapped boundary; it is not started here. Remaining A review-fix
allowance2–6h (estimate, not actual hours), B environment/CI work remains its own estimate;
external host/distribution choices and waits are not silently budgeted or authorized.
