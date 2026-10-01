# U-P13d · U7 · Lane A — Mesh mapping policies, the composite rule, and C2 at mesh scale

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/mapping/README.md, build-spec §2.4
(the per-subsystem ladder and the composite rule), §2.8, ADR U0011, U0012, and the handoffs
of U-P13a, U-P13b and U-P13c.

TASK: make the mesh class a first-class target and the composite honest: mesh policies, the
composite rule in code, and full C2 tables at mesh scale.

1. Mesh-class mapping policies in src/rkuarch/mapping/ (Python, shared by every engine):
   - summa-2d@1: GEMM outputs blocked over the core grid, operands multicast along rows
     and columns;
   - head-parallel@1: attention heads distributed over cores, attention_fused tiled per head
     group, KV resident per head group and read in pages of the request's block size.
   Each carries its own docstring derivation of per-core bytes and MACs. L0 checks those
   against the graph.
2. THE COMPOSITE RULE (build-spec §2.4), enforced in native/ and re-checked in Python:
   - report C2 ONLY IF compute is at level 2, NoC and DRAM are at level 2 or "1+ts", a
     shared SRAM (when present) is at "1+ts", AND synchronisation is exact;
   - otherwise C1, if any subsystem is at level 1;
   - otherwise C0-equivalent.
   Emit the full per-subsystem vector as fidelity_detail, with build-spec §2.4's keys and
   values only. A request that asks for C2 and cannot get it degrades or raises exactly as
   build-spec §7.4 says for default vs override.
3. Scale: build full tables for npu-m256 (16×16) and a 32×32 variant. Record the simulator
   metrics from U-P12 for both, and the single-point wall-clock against ADR U0011's budget.
4. If G5 was rescheduled from U6 (U-P11c item 3), run it now at the closest matching
   configuration.

ACCEPTANCE TESTS (write first):
1. G6: the npu-m256 table reports composite C2 with detail {compute: 2, noc: "1+ts",
   dram: 2 or "1+ts", sync: "exact"}. A job with any subsystem below the rule is refused C2,
   with the reason.
2. Roofline floor: no row of any native table is faster than its U-C0 roofline.
3. summa-2d@1 and head-parallel@1 pass L0's per-core bytes and MACs check against the graph.
4. Determinism: byte-identical at 1 and N workers; sanitizer build clean.
5. The 32×32 table builds, and its metrics and wall-clock are recorded.

GUARDRAILS: Do not claim C2 below the rule. No threads yet. Do not remove the level-0 and
level-1 paths: they are the fast modes, and the ladder is a feature.

ADR: docs/decisions/U0013-the-composite-fidelity-rule.md, covering the rule as built, each
level U-P13a–c added, and their L2 gaps with mechanisms.
```
