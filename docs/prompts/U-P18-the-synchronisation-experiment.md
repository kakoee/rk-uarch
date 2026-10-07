# U-P18 · U9 · Lane B — The synchronisation experiment: error vs quantum at a backpressured boundary

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, validation/README.md, build-spec §2.9, ADR U0017. From rk-sim
READ-ONLY: docs/vision/rack-to-kernel-24-month-execution-plan.md: E6, the FUNDED PLAN's gate G1 (not this plan's G1) and its
criterion. That is the company's central technical bet, and this prompt is where it gets
measured. docs/context-and-decisions.md §2.3 (why the prototype deferred it).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Compare worker/thread/synchronization configurations using the same saved prepared
workload and mapped TaskGraph. Partitioning simulator ownership must not repartition model
tensors or change the declared chip mapping. Record prepared input identity with every run
so timing differences cannot hide a change in the workload producer.

TASK: measure whether lax synchronisation survives a BACKPRESSURED boundary, publish the curve
whatever its shape, and wire the result into what the composite fidelity may claim.

1. PRE-REGISTER FIRST, in docs/decisions/U0018-the-error-vs-quantum-curve.md, committed
   before any run:
   - the boundary: core partitions ↔ memory-controller partition with closed-loop credit
     backpressure. It is deliberately the hard one: an uncontended boundary passes and proves
     nothing;
   - the operator mixes: at least one real decoder-layer mix, decode and prefill;
   - the quantum values: at least 5, from Q = L to Q = 64 L;
   - the metrics: wall-clock speedup over exact mode, and the deviation of the escalated
     component's latency DISTRIBUTION (p50 and p99 of memory-request latency, and per-query
     duration), not only the mean;
   - the pass criterion, copied from the funded plan's G1 (its E6) and labelled there as that plan's
     own assumption: ≥ 5× over conservative at ≤ 10% latency-distribution deviation.
2. validation/sync/: the harness runs exact and lax modes on the same jobs, reports
   error-vs-speedup over Q with exact mode on the same axes, and writes a hashed curve file the
   model card can cite, scoped by boundary type, design family and operator mix.
3. Enforcement: provenance/ accepts a lax-mode composite C2 ONLY when the job's Q, boundary type
   and family fall inside a cited curve's measured range AND that curve's deviation at Q is
   within the pre-registered bound. Otherwise C1, with the reason in the fidelity detail.
4. Publication: docs/results/sync-error-vs-quantum.md, with method, data, the curve, and the
   verdict against the pre-registered criterion, written the same day the curve exists,
   pass or fail. The funded plan calls a dated result "the cheapest fundraising asset", and
   says to publish it "regardless of outcome".

ACCEPTANCE TESTS:
1. The pre-registration commit precedes every curve file (git-ordering check, reusing
   check_ordering).
2. The curve exists over ≥ 5 values of Q on ≥ 1 real operator mix, with exact mode on the
   same axes.
3. A lax job inside a covering curve's range keeps C2; one outside drops to C1; both are
   asserted in one test so neither half can pass alone.
4. The publication file exists and states pass or fail against the pre-registered criterion
   in its first sentence.

GUARDRAILS: Do not choose the boundary, mixes or threshold after seeing data. Do not report
only the mean deviation, because tails are where decoupling breaks. Do not tune Q per
workload to make the curve look better. This prompt MEASURES whether lax parallelism is
justified; it does not make lax mode the default.

ADR: docs/decisions/U0018-the-error-vs-quantum-curve.md (the pre-registration, then the
verdict appended).
```
