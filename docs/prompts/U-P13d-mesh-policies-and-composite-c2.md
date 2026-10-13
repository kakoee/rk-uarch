# U-P13d · U7 · Lane A — Mesh mapping policies, the composite rule, and C2 at mesh scale

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/mapping/README.md, build-spec §2.4
(the per-subsystem ladder and the composite rule), §2.8, ADR U0011, U0012, and the handoffs
of U-P13a, U-P13b and U-P13c.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Mesh mapping policies extend the standalone preparation frontend and emit the same
versioned TaskGraph format that external producers can supply. The native engine consumes
resolved mapped inputs, never chooses SUMMA/head placement itself. Export/import preserves
policy version, hardware binding and content identity; no search or compiler integration.

TASK: make the mesh class a first-class target and the composite honest: mesh policies, the
composite rule in code, and the U-P7 T full product table at its actual earned composite.
G6 verifies mechanisms; G3b verifies the consumed table. Both require G5-correctness,
not its performance/automation completion. No silicon-pass prerequisite. Keep functional
scale admission separate from pending host metrics; no performance claim while controlled-
host evidence or executed self-hosted nightly is missing.

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
3. Product: build the complete npu-m256 consumer table under U-P7 T/G3b. Resolve required
   hardware/precision/RoPE/ragged and schema decisions first, preserving the demo scope.
   Scale: use prospectively declared representative 16×16 and 32×32 points, after an
   accepted 32×32 design exists. Verify functional scale admission on approved correctness
   Linux. Separately record U-P12 controlled-host costs against U0011 for the scale-metric
   obligation, with executed self-hosted nightly before any qualified performance claim.
   Pending metrics do not block G6/G3b/U10; they do block the corresponding performance
   qualification, U9 entry and final closure. No full 32×32 grid without a named consumer.
4. Extend G5's independent correctness corpus and public-boundary fault checks to every
   new modeled mechanism. Run admitted matched component references; missing optional
   references are disclosed and do not become a deferred whole-fork requirement.

ACCEPTANCE TESTS (write first):
1. G6: the npu-m256 table reports composite C2 with detail {compute: 2, noc: "1+ts",
   dram: 2 or "1+ts", sync: "exact"}. A job with any subsystem below the rule is refused C2,
   with the reason.
2. Roofline floor: no row of any native table is faster than its U-C0 roofline.
3. summa-2d@1 and head-parallel@1 pass L0's per-core bytes and MACs check against the graph.
4. Determinism: byte-identical at 1 and N workers; the debug build runs clean.
5. Functional: declared 32×32 scale points execute with verified inputs/scope and correctness
   checks. Missing required design/admission blocks this functional obligation.
6. Separate scale-metric obligation: controlled-host observations and executed self-hosted
   nightly support any performance claim. Keep its pending status separate; acceptance 6
   does not gate G6/G3b/U10, but is required for the scale performance claim, U9 entry and
   final closure. Never fabricate metrics or close the obligation from functional success.

GUARDRAILS: Do not claim C2 below the rule. No threads yet. Do not remove the level-0 and
level-1 paths: they are the fast modes, and the ladder is a feature.

ADR: docs/decisions/U0013-the-composite-fidelity-rule.md, covering the rule as built, each
level U-P13a–c added, and their L2 gaps with mechanisms.
```
