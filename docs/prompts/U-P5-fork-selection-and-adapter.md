# U-P5 · U3 · Lane A — Bounded native-stage design and verification readiness

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, docs/decisions/U0005-one-production-simulator-and-validation.md,
U0006, U0019, U0022, build-spec §2.4–§2.8, U0023, execution-plan U3–U10 and G2/G3a/G3b/G5,
U-P7, U-P8, U-P11a–c, U-P12, and the published U3 RoPE/runtime and feasibility handoffs.

TASK: design the modest first stage of the eventual production Rust engine, with exact
verification milestones. This is design work, not fork selection or runtime authorization.
Retain the accepted analytic baseline; do not design a second substantial Python engine.

1. Inventory the live prepared-v2/rotary and engine-result carriers and what is still absent
   for a mapped TaskGraph. Propose one versioned mapping/job/result boundary reusing accepted
   vocabulary and identity rules. No duplicate workload IR or sharding inside Rust. Include
   legacy v1 handling, explicit v2 RoPE/conversion/coefficient traffic, fused paged attention,
   precision/rank/KV scope and all refusals. Existing v2 analytic support is not native admission.
2. Bound U4a: one declared hardware configuration, precision and small workload slice, with
   independent examples, then separate expansion paths to U4b's reference suite and U7's
   declared product table. Start
   single-threaded, compute 1 / NoC 0 / DRAM 0, exact sync, composite at most C1. State which
   operators run and which refuse at every checkpoint. A GEMM-only stage cannot claim a
   decoder layer or full-model prediction. No C2, threads or silicon accuracy claim.
3. Specify M / K1 / K2 / B / R / T tasks: M mapped carriers/fixtures; K1 internal kernel
   after accepted semantics/toolchain (may overlap M); K2 public wiring after M installation;
   B bounded models; R actual reference-suite readiness; T first consumed full table in U7.
   Private K1 fixtures are not a competing public format. U-P8/U-P12 independent derivations
   may develop alongside M/K1; public tests wait for K2. No table prerequisite for R.
   With B, schedule TPU sourcing, representability/observability and native admission before
   U-P9. Return any contract/target gap for a decision; do not invent unknown chip facts.
4. Produce the exact verification matrix: independently derived integer counts/transfers,
   clock edges, critical paths, conservation, dependency order, bounded outstanding requests,
   serialization on shared resources, legal overlap on independent resources, replay and
   debug/release determinism. State applicability and reductions under U0006. Plan at least
   one discriminating fault per mechanism, tested through the public execution boundary.
   Derive expectations independently, not by calling production formulas to manufacture them.
5. Propose the reproducible Rust/container environment, license/dependency closure and
   prospective absolute time/memory budgets per declared host/workload. Do not reuse the
   unaccepted 200-second fork diagnostic proposal. Separate correctness Linux CI from
   controlled-host performance and G5 nightly qualification under U0023;
   no candidate build, container run, native measurement or host modification in this task.
6. Map each future external comparison to a component and matched assumptions. Tools are
   optional; name unavailable/unmatched/not-independent evidence honestly. No whole-chip
   reference requirement, no scope relaxation to make an external tool match, no tuning to
   reference outputs. Silicon U5/U8, frozen predictions and evidence limits remain separate.
7. Provide exact proposed U0011 text, any mapped-schema/protected patch, A/B ownership,
   checkpoint acceptance, engineering/review effort and human dependencies. U0005 already
   establishes the direction; do not claim it accepts the later detailed implementation plan.

ACCEPTANCE:
- Every U4a capability and refusal has a literal example and independently justified test.
- The schedule names each deliverable's first consumer, has no dependency cycle and does
  not count kernel work again in U6. Required analytic checks have explicit first-use deadlines.
- Table production and silicon success are separate. Full product tables first serve U7;
  old T budgets and grid requirements are not automatically accepted.
- Exact component/carrier and semantic/toolchain decisions are separate from host budgets;
  neither A's prior proposal nor this direction grants blanket installation authority.
- G2's design checklist is explicitly disposed; unimplemented/unexecuted cases stay pending.
- All protected changes remain unapplied proposals. Ask for the exact stage/schema decision
  only after the package is complete and reviewable. No runtime implementation in this task.

GUARDRAILS: no fork builds, second production Python engine, automatic U-C1 fallback, native
runtime work, source-bound artifact generation/adoption, or edited historical evidence.
Publish owned proposal docs on main using normal Git integration; protected paths remain human.
The historical filename is retained for links; its former fork-selection instructions are retired.
```
