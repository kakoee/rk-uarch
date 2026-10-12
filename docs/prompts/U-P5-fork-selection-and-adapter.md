# U-P5 · U3 · Lane A — Bounded native-stage design and verification readiness

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, docs/decisions/U0005-one-production-simulator-and-validation.md,
U0006, U0019, U0022, build-spec §2.4–§2.8, execution-plan U3–U6 and G2/G3/G5,
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
   independent examples, then an explicit expansion path to U4b's full required grid. Start
   single-threaded, compute 1 / NoC 0 / DRAM 0, exact sync, composite at most C1. State which
   operators run and which refuse at every checkpoint. A GEMM-only stage cannot claim a
   decoder layer or full-model prediction. No C2, threads or silicon accuracy claim.
3. Break the dependency cycle explicitly: U-P7 mapping/schema phase → U-P11a fixed-delay
   kernel → U-P11b bounded models/executor → U-P7/U-P11b full coverage/table phase. Hand-built
   mapped fixtures may test the kernel; they do not stand in for production preparation.
   U-P8 and foundational U-P12 tests can develop against the accepted boundary in parallel.
4. Produce the exact verification matrix: independently derived integer counts/transfers,
   clock edges, critical paths, conservation, dependency order, bounded outstanding requests,
   serialization on shared resources, legal overlap on independent resources, replay and
   debug/release determinism. State applicability and reductions under U0006. Plan at least
   one discriminating fault per mechanism, tested through the public execution boundary.
   Derive expectations independently, not by calling production formulas to manufacture them.
5. Propose the reproducible Rust/container environment, license/dependency closure and
   prospective absolute time/memory budgets per declared host/workload. Do not reuse the
   unaccepted 200-second fork diagnostic proposal. List runner/manual-nightly prerequisites;
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
- The schedule has no dependency cycle and does not count kernel work again in U6.
- G2's design checklist is explicitly disposed; unimplemented/unexecuted cases stay pending.
- All protected changes remain unapplied proposals. Ask for the exact stage/schema decision
  only after the package is complete and reviewable. No runtime implementation in this task.

GUARDRAILS: no fork builds, second production Python engine, automatic U-C1 fallback, native
runtime work, source-bound artifact generation/adoption, or edited historical evidence.
Publish owned proposal docs on main using normal Git integration; protected paths remain human.
The historical filename is retained for links; its former fork-selection instructions are retired.
```
