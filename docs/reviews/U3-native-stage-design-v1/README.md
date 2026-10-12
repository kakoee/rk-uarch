# First bounded native stage — Lane A proposal

2026-10-12. **Proposed for Javid (@jjaffari) and coordinator review. No implementation
release, independent review, G2 acceptance or U3 closure is asserted.**

Recommend a single-threaded, BF16 component stage on the existing stipulated `npu-l4`:
small weight-stationary GEMMs, explicit buffers, DMA/unicast transfers and barriers.
Compute 1 / NoC 0 / DRAM 0, exact synchronization, composite at most C1. This is a
useful first part of the eventual Rust engine, **not a decoder layer or model predictor**.
Keep the analytic baseline; do not commission another substantial Python simulator.

## Review package

- [Exact decisions](next-decision.md).
- [Proposed U0011 text](proposed-U0011.md), for a later human-owned ADR commit.
- [Mapped interface and literal cases](interface.md), including protected change inventory.
- [Independent derivations and acceptance matrix](verification.md). All native tests are future.
- [Delivery, environment, budgets and ownership](delivery.md).

## Baseline and existing capability

The requested clone `/home/jjaff/AI-infra-simulation/rk-uarch-u3-a` started clean on
`main` at `42fc3414d6329675164940aa40289689d7ef81ea`. Fetch and safe fast-forward gave
**`1f2beb9b477e796f5f2457ed2f6a3fe3ea45d992`**, the actual design baseline and accepted
architecture amendment. No pre-existing changes were present to move or overwrite.
Repository instructions: [CLAUDE.md](../../../CLAUDE.md) and
[CODEOWNERS](../../../.github/CODEOWNERS). The historical U-P5 filename now contains
the [native design task](../../prompts/U-P5-fork-selection-and-adapter.md).

| Published evidence inspected | What exists; what it does not establish |
| --- | --- |
| [RoPE runtime](../U3-RoPE-runtime-v1/README.md) and [final local validation](../U3-final-local-validation-v1/README.md) | Additive v2 analytic preparation, authenticated coefficients, admission, execution and capture; later human adoption/activation supersedes the early handoff's pending wording. Final receipt reports 1,701 passes/29 skips, not a run by this author. No native mapped admission or public v2 table/report completion. |
| [B standalone report](../U3-B-standalone-report-handoff.md) and [SR-C1](../U3-B-SR-C1/README.md) | Model-v1 analytic checks and durable error recording. Latest source reports remain partial/not_run: L0 14 pass/14 skip; L0m 9 pass/13 skip/5 not_run, aggregate-clock 22/24. Not executed MAC/DMA/queue telemetry, v2 evidence or completed U-P6. |
| [Fork feasibility](../U3-fork-feasibility-v2/README.md) | Source-only evidence of semantic, observation and packaging limits. Its Python U-C1 recommendation was not selected. No fork experiment or renewed investigation is needed. |
| [U0005](../../decisions/U0005-one-production-simulator-and-validation.md), [U0006](../../decisions/U0006-what-verification-can-and-cannot-establish.md), [U0019](../../decisions/U0019-standalone-preparation-and-prepared-input-replay.md), [U0022](../../decisions/U0022-explicit-rope-semantics.md) | Accepted direction, conservative verification, replay and RoPE semantics. These do not accept this detailed stage or its new carriers. |

Live `PreparedBundle` and `PreparedBundleV2` both fix `mapping_scope=analytic_ops`.
`EngineJobV2` fixes analytic identity and `stateless_roofline`; its result validator
recomputes analytic answers. `ResolvedHardware` lacks detailed resource topology,
placements and service policies. Mapping is a skeleton; native Cargo has no members.
A new additive TaskGraph/job/result boundary is necessary, not a rename of protocol/2.

## Four checkpoints, with distinct claims

| Checkpoint | Deliverable and exit | Dependencies |
| --- | --- | --- |
| M — U-P7 mapping/interface | Human-approved schema, strict validators, literal fixtures and component mapper; imports bypass producers. No engine claim. | Exact stage/schema decisions, protected carrier installation and normal U0002 lifecycle planning. |
| K — U-P11a kernel | Fixed-delay TaskGraphs through the subprocess boundary; clocks, ordering, owners, wheel, critical paths and repeat/debug/release determinism. No subsystem fidelity claim. | M; toolchain/license closure; current published host/runner prerequisite. |
| B — U-P11b bounded models | Component workload below; independently checked completed work, DMA limits, capacity, overlap and mapped replay. At most C1/STUB. | K; B's independently authored corpus and public-boundary faults. |
| T — U4b expansion | Full U-P7 policies, operators, precisions, grid/error jobs and complete npu-l4 tables; G3 assessed separately. | B; hardware/precision/semantic amendments and all required coverage. |

U-P8 and foundational U-P12 can develop expectations against M alongside K/B.
U6 qualifies the existing engine and adds initial mesh coverage/diagnostics/host metrics;
it does not build or charge for the kernel again. U5 silicon remains after G3, separate
from U6. Hand-built fixtures verify K; M's real producer/import correspondence is still
required before B is accepted.

## Exact bounded scope

Use the complete existing [npu-l4.yaml](../../../hw/designs/npu-l4.yaml), canonical hash
`sha256:3b7186f3e69d38723ec40f9a074b941934644ac57cc6f61d64865429caac07d9` at baseline:
2×2 cores; 256×256 matrix array/core; BF16 inputs/output, FP32 accumulation;
1 GHz core/NoC/DRAM; 16 MiB SRAM/core; 256 KiB accumulator; 1 MiB operand buffer;
1,024 operand bytes/core cycle; four DMA engines/core sharing 256 bytes/core cycle,
32 requests/engine, 256 bytes/request; 32-cycle job and NoC-domain barrier overhead;
8 DRAM channels totaling 10^12 bytes/s, 32 GB capacity, direct timings, no preset,
no shared SRAM. These remain proposed-design stipulations, not measured hardware facts.

B admits a component graph of 1–16 independent or explicitly dependent `q_projection`
OpSpecs (a GEMM test use of existing vocabulary), each with M in 1…1024 and K,N in
1…256. TP=1, selected rank 0, one execution of each op; contiguous BF16 operands;
no bias, sparsity, expert multiplier, KV or rotary node. `ws-rowsplit@1` partitions
M into contiguous blocks of at most 256, assigned core 0,1,2,3 in row-major order.
One K slice, weight-stationary only; double buffer slots per core. Independent ops
reuse slots only after their last consumers complete. A selected external mapping
may use any of those cores with valid placements and FIFO arbitration, within the
same limits. It is executed unchanged. No mapping search or automatic repair.

B supports cold execution with explicit HBM inputs, plus a **resident component
fixture** whose SRAM contents are declared initial allocations. The latter is a
separate test state, never mislabeled cold/steady or emitted as a table row. Steady,
full prepared v1/v2 models, all other operators/formats, rank/TP extensions, K-split
accumulator spill, multicast and other hardware/configurations refuse. Synthetic
clock/DMA variants exercise mechanisms under a test-only profile, not expanded
production hardware support. Literal refusals and later v2 obligations are in the
interface and matrix. No native result can silently omit required model work.

## G2 checklist disposition

| Required item | This package | Remaining decision/evidence |
| --- | --- | --- |
| Exact scope/refusals/expansion | README, interface, delivery | Javid acceptance; no capability implemented |
| Mapped protocol, v2/legacy identity/replay | interface | Human schema decision and subsequent installable schema review |
| Independent math, behavior, faults, reductions | verification | B/human review; future execution; two human L1 derivations still required |
| Toolchain/licenses/absolute budgets | delivery, proposed U0011 | Pin/closure acceptance, resource allocation; no measurements |
| U-P6 analytic checks | Existing partial reports above | B/coordinator disposition of remaining applicable checks; no inherited whole-rung pass |
| Ownership/effort/dependencies | delivery | Human waits and runner policy unresolved |

**G2 remains pending.** Correctness CI, a designated performance host and self-hosted
automation are different capabilities. The coordinator's narrower runner recommendation
is not installed. Published U0005 still requires a designated Linux host, registered
`uarch` runner and an executed manual nightly before native implementation/build/performance.
This design is not blocked by registration, and grants no readiness or waiver.

## Checks performed for this proposal

Read-only source/document inspection, Git status/ancestry and fast-forward checks;
canonical hardware identity calculation using the existing installed environment.
Final documentation checks and publication results are recorded in [delivery](delivery.md).
No runtime suite, native build, container run, host contact, measurement, artifact
capture/generation/adoption, protected-file edit or independent review occurred.
All proposed acceptance cases remain unexecuted. Stop after normal publication for
coordinator review; STUB, unknown error and unverified energy remain unchanged.
