# Revised bounded native-stage proposal — Lane A

2026-10-12. **Proposed for coordinator and Javid review. No G2 acceptance, runtime
release, independent verdict or U3 closure.** This replaces v1 as A's current proposal;
all historical proposals and evidence remain intact.

The first model stage remains a single-threaded BF16 component executor on the frozen
stipulated npu-l4: small WS GEMMs, explicit DMA/unicast, buffers and barriers. Separate
M / K1 / K2 / B / R / T. K1 internals may overlap M after accepted kernel semantics and
exact toolchain/license decisions. K2 public execution waits for installed approved mapped
carriers. R serves the actual TPU benchmark suite; full product tables first serve U7.
Correctness Linux CI, controlled-host performance and executed nightly have separate exits.

## Review package and authority

- [Exact proposed U0011](proposed-U0011.md): unapplied human-owned ADR text.
- [Interface/schema proposal](interface.md): additive carriers, observations, literal refusals.
- [Verification](verification.md): retained independent arithmetic, B reconciliation, analytic deadlines.
- [Delivery](delivery.md): consumers, ownership, checkpoints, reference readiness, effort and budgets.
- [Decision ledger](decisions.md): retained/revised/deferred choices and exact human decisions.
- [Coordinator handoff](handoff.md): publication/check scope and next actions.
- [Reproducible author checks](checks.md): documentation, JSON and independent arithmetic only.

Authority: [U0005](../../decisions/U0005-one-production-simulator-and-validation.md),
[U0023](../../decisions/U0023-consumer-driven-delivery-and-validation-readiness.md),
[current U-P5](../../prompts/U-P5-fork-selection-and-adapter.md) and
[execution plan](../../execution-plan.md). U0023 governs prospective ordering over the
preserved older U0005 text. Inputs: [A v1](../U3-native-stage-design-v1/README.md) and
[B v1](../U3-B-verification-readiness-v1/README.md). Their stale full-grid/runner wording
is explicitly superseded here; their evidence is not relabeled or edited.

The requested `/home/jjaff/AI-infra-simulation/rk-uarch-u3-a` started clean at
`bc01563853c38c7ac514548f68be7d16482b344f`. Fetch and fast-forward integrated all published
peer history through amendment `30812dfc322b742b81521e350d7d5b541221ca0d`; ancestry passed.
There were no local edits to move or overwrite. CLAUDE.md and CODEOWNERS were read;
no applicable AGENTS.md was found. Only this new proposal directory is edited.

## Exact B scope retained

Hardware: existing npu-l4 canonical identity
`sha256:3b7186f3e69d38723ec40f9a074b941934644ac57cc6f61d64865429caac07d9` (retained from
v1; hardware bytes unchanged at amendment baseline). 2×2 cores, 256×256 array per core,
1 GHz domains, 16 MiB SRAM/core, 256 KiB accumulator, 1 MiB operand buffer,
1024 operand bytes/cycle, four DMA engines/core sharing 256 bytes/cycle, 32 outstanding
requests/engine and 256 bytes/request; 32-cycle job/barrier overhead. Eight HBM channels,
10^12 bytes/s total, 32 GB, explicit direct timing and refresh derating. These are design
stipulations, not measured chip facts. No preset fallback or shared SRAM is invented.

Admit 1–16 component `q_projection` GEMMs, TP1/rank0, frequency ratio 1, BF16 X/W/Y,
FP32 accumulation, 1≤M≤1024 and 1≤K,N≤256, each executed once. WS rows split into
≤256-row blocks on cores 0–3 in row-major order; no K split. Explicit imported mappings
within that admitted policy/scope execute unchanged. Contiguous operands, no bias/sparsity,
no KV/rotary, no layer/head/tail claim. Double-buffer placement and FIFO arbitration
permit independent DMA/compute overlap and serialize shared resources.

Cold HBM input is production component scope. Explicitly preloaded SRAM is a separately
labeled resident test fixture, never mislabeled steady or made a product row. Models:
compute1 / NoC0 / DRAM0 / exact sync / layer_reuse=false, composite at most C1.
Banks, physical DRAM queues/rows, NoC contention and energy remain unrepresented/null.
Completed work is observed from jobs; functional tensor execution is outside scope.

Refuse full v1/v2 models, all non-q_projection operators, rotary/casts/KV/fused attention,
other precision/ranks/hardware, steady state, K spill, multicast, imported padding,
invalid placements/capacities/dependencies, unknown versions and unsupported fidelity.
[Interface R01–R21](interface.md) gives literal negative cases; verification E1–E4 gives
positive mechanisms. R and T expand only through their own exact accepted scopes.

## G2 disposition

| Gate requirement | Reviewable proposal | Remaining obligation |
| --- | --- | --- |
| Exact stage/refusals and M/K1/K2/B/R tasks | This scope, interface, delivery | Human acceptance; nothing implemented |
| Mapped schema plan | Interface fields, strict unions/identities/observations and patch inventory | Human plan decision; exact patch/install before K2; dependency audit or explicit retain-enforcement decision before M install |
| Kernel semantics/toolchain | U0011, E1/E2, zero-delay convention, delivery closure list | Exact semantic decision and immutable Rust/tool/license closure before K1; pins unresolved |
| Derivations/public faults/U0006 | Verification V01–V28 and B checklist crosswalk | B review/frozen corpus, two human hand fixtures, future actual executions |
| Analytic first-use deadlines | Verification's aggregate-only C1, separate native/per_op clock scopes, C2–C5 and remaining relations | B/coordinator case-level selection; applicable checks pass before reliance |
| Reference/product consumers and effort | R six-class readiness, T U7 demo, separate estimates | Reference/contract feasibility and product semantics decisions; no hardware spend authorized |
| Performance/automation | Distinct correctness/performance/nightly conditions | Budgets/host acceptance before measurements; real nightly by G5 automation |

G2 remains pending, including independent review and human adjudication. Publication is
a bounded design handoff, not permission to start native code or install any schema.

## Coordinator follow-up

The [published reconciliation](../U3-design-audit-reconciliation-v1/README.md) identifies
A-C1: the historical 22/24 cell and proposed anchor remedy are aggregate-only. The current
verification attachment and U0011 text now state that scope; native component-clock tests
and any future true-premise per_op domain stay separate. Historical evidence is unchanged.
[Interface's proposed-M dependency note](interface.md#proposed-m-dependencies-for-bs-audit)
consults B's published audit and identifies initializer/import/data relationships that may
enter support; it claims neither a new closure count nor an exemption from generation
binding. See the [follow-up handoff](handoff.md#bounded-coordinator-follow-up).
