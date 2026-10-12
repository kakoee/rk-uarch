# U0011 — Progressive native core: bounded component stage and qualification

**Status: PROPOSED.** Exact text for human review; this file is not an accepted ADR.
Decision owner: Javid (@jjaffari). U0005 establishes direction; this record supplies
proposed scope and obligations, with schema/pin follow-ups explicitly blocking release.

## Decision

Build one progressively developed Rust timing simulator. Retain the Python analytic
baseline and Python preparation/product layers. Rust consumes resolved TaskGraphs;
it does not build models, shard ranks, generate rotary coefficients or run mapping search.
Functional tensor-value execution is outside scope. Only completed jobs may contribute
observed modeled work; expected input totals are comparison targets, not telemetry.

Delivery is M (approved mapped boundary/producer/fixtures), K (fixed-delay kernel),
B (bounded subsystem execution), T (complete U4b workloads/tables), then U6 qualification.
The exact normative proposal attachments are `interface.md`, `verification.md` and
`delivery.md` in `docs/reviews/U3-native-stage-design-v1/`; their reviewed Git revision
must be named in the human acceptance record. Subsequent changes require review and a
new version where semantics change; publishing these attachments is not acceptance.

B admits only the existing npu-l4 hash
`sha256:3b7186f3e69d38723ec40f9a074b941934644ac57cc6f61d64865429caac07d9`, at frequency
ratio 1, BF16 operands/output with FP32 accumulation, TP1/rank0, 1–16 component
q_projection GEMMs with 1≤M≤1024 and 1≤K,N≤256, contiguous layout, explicit DMA/unicast
and barriers. WS rows split into ≤256-row tiles; no K split. FIFO admission and explicit
double-buffer placement determine execution. Cold HBM and separately labeled resident
test initialization are distinct. No full layer/model, rotary, KV, steady, multicast,
other precision, spill or hardware support is claimed. Unsupported work refuses before
events, never disappears into an unrepresented-field warning.

B's model is compute 1, NoC 0, DRAM 0, exact synchronization, layer_reuse=false;
shared_sram is absent for this hardware. Composite is at most C1. SRAM banking, NoC
contention/credits, DRAM row scheduling/queues and energy remain unmodeled and disclosed.
The explicit interval/traffic rules in verification.md are assumptions, not measurements.
Two independent buffers permit DMA/compute overlap; one exclusive resource serializes.

Use one additive versioned mapped boundary (`uarch-prepared/3`, `uarch-taskgraph/1`,
`uarch-engine/3`), reusing OpSpec, prepared v1/v2 semantic carriers and identity rules.
Human approval/installation of its exact carrier/schema/fixture patch precedes K.
Legacy analytic roots remain unchanged; native rejects analytic engine jobs and full
legacy/v2 workloads until explicitly admitted. V2 mapping must preserve authenticated
coefficients, positions, Q/new-K casts and traffic, rank replication, rotated KV append
order and fused paged attention; analytic-v2 availability is not native admission.

## Kernel and reproducibility

Follow build-spec §2.8: single thread; u64 picosecond time; exact u128 clock-edge
arithmetic; next_edge as the sole cycle conversion; 32-byte events ordered by
(t_ps, phase, target, seq); schedule-time sequence allocation; event arena/free list;
two-level 4,096-slot timing wheel with heap overflow; single resource ownership;
CSR topology/declared routes; sorted vectors/BTreeMap on output paths. No unsafe,
SIMD, GPU, MPI, simulation compiler, speculative synchronization or threads in this stage.
NoC-0 must not acquire reservation/link contention merely because the kernel has owners.

Departures remain those in build-spec §2.8: staged engine after design, spec-derived
lookahead rather than assuming one cycle, conservative exact synchronization before
approximation, named mappings rather than compiler/search, no third NoC backend and
no SIMD/GPU/MPI ladder. U7 Ramulator and U9 threading remain separate. A single-thread
stage makes no claim about parallel lookahead or cross-thread speedup.

Same admitted input and engine/model assumptions produce identical complete canonical
results in three fresh processes and debug/release. Source/model implementation hashes,
lock and compiler release identify semantics; executable/image digests and build profile
live in operational receipts so debug/release comparison is meaningful. Deterministic
simulated event metrics remain in results; host wall time/RSS never do. Saved mapped
replay disables all workload/mapping/coefficient producers. Imported mappings are
validated unchanged; placement or policy version changes identity. U4b also requires
workers 1/8 table identity, complete error-job coverage and three-run replay.

## Verification and evidence

Before implementation, freeze the independent integer/edge/critical-path examples,
capability/refusal matrix and discriminating faults in verification.md. K/B acceptance
requires actual public-boundary control/fault/restored executions, not schema rejection
miscounted as a behavioral mutant kill. Retain every invocation, counterexample and
shrinking attempt; follow U0006: applicable failures dominate, incomplete/empty/skipped
or under-budget coverage is not_run, only complete nonempty passing coverage passes.
U-P8 requires two human-worked fixtures. This proposal's agent-authored arithmetic does
not discharge that or independent review. L0–L2 never establishes silicon accuracy.

Optional references require prospectively matched component scope and criteria under
U0008. No complete fork or Python U-C1 engine is required. NoC-0 contention comparison
is not_run. Shared-library comparisons are integration evidence, not independent L2.
STUB, unknown error, null unmodeled quantities and unverified energy persist. Silicon
U5/U8 uses separately authorized frozen predictions and unchanged thresholds.

## Environment, cost and release conditions

Adopt delivery.md's reproducible Linux/container plan and prospective absolute host
budgets: K/B component point ≤5 s and ≤512 MiB; U4b full-model point ≤60 s and ≤4 GiB;
U6 npu-m256 point ≤120 s and ≤8 GiB; later 32×32 stress point ≤300 s and ≤16 GiB,
with the exact workloads and receipt protocol defined there. These are planning ceilings,
not performance observations or the rejected 200-second fork allocation. Human approval
of host allocation and exact frozen workload/pin identities precedes measurement.

Pin a stable Rust release, toolchain components, base image digest, Cargo.lock and all
transitive licenses before build; exact pin resolution is a separate required acceptance
item, not a moving `stable`/`latest` dependency. Initial direct dependencies are serde,
serde_json and dev proptest only. License exceptions require their own explicit decision;
no unreviewed Unicode or operating-system/tool exception is implied. Enforce rustfmt,
clippy -D warnings, no unsafe and cargo-deny. No package is installed by this proposal.

The installed U0005 Linux-host/self-hosted-runner/manual-nightly prerequisite remains
binding until a separate human amendment narrows it. Correctness CI, performance host
qualification and self-hosted automation are distinct. No runner readiness is asserted.
U0002 support-bound runtime changes still need their human generation/adoption lifecycle;
no source exclusions or reused stale receipts are authorized.

T must meet the unchanged U4b/G3 full-table requirements. Missing FP8/RoPE, output-stationary
hardware, layer work, error coverage or applicable tests block G3 unless a new human
scope amendment is accepted. U6 qualifies the existing engine; kernel effort is not
counted twice. This record accepts no test run, gate, independent review, promotion,
hardware purchase, source-bound artifact generation or sprint closure.
