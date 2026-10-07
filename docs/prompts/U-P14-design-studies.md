# U-P14 · U7 · Lane B — Design studies: variants, sweeps, and the diff report

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, src/rkuarch/{report,study}/README.md, build-spec §1.2 (the
acceptance demo: the study is minutes 4–5 of it) and §2.6. From rk-sim READ-ONLY:
docs/prompts/P9a-sweep-engine.md and P9b-*.md (its sweep and tornado conventions, and why a
one-at-a-time tornado is labelled local sensitivity rather than a ranking).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Declare whether a study re-prepares each variant with a named local policy or replays
an externally supplied mapping. Local preparation records a new hardware/mapping identity
per variant. Fixed imported mappings are validated against each variant and refused when
incompatible; re-mapping requires an explicit study choice and recorded producer. Cache
identity includes prepared content and its bindings, not just model/tp or policy label.

TASK: the thing a chip architect actually does with this tool, which is to compare designs. A
study is a set of tables over stipulated variants, and a report that says what moved and why.

1. src/rkuarch/study/: a StudySpec (YAML) names a base design, a list of parameter paths with
   values (one-at-a-time, or a small full grid), a versioned workload
   suite (or one request template), and one engine and fidelity. `uarch study <studyspec>`
   builds each variant's table through the existing pipeline. Tables are cached by request
   hash, so a rerun rebuilds nothing.
2. VARIANTS MAY ONLY CHANGE WHAT A PROPOSED DESIGN IS FREE TO CHOOSE: its stipulated values
   (counts included: array, grid, banks, channels, queue depths), its categorical fields
   (dataflows, topology, interleave scheme, scheduler, page policy, sync mechanism) and the
   request's mapping policy. Every change is recorded in conditional_on as path=value.
   In local-preparation mode the mapping is re-run per variant; fixed imported mappings
   follow the validation/refusal rule above. A study that edits a reference spec, or any claim, is
   refused: it would be a counterfactual about a real chip wearing that chip's evidence. A
   variant that changes sram.bytes without re-stipulating energy.pj_per_byte.sram is refused,
   naming both paths.
3. The diff report (uarch diff from U-P12, extended):
   - per grid point, the relative change in duration, with its attribution split, showing
     which regime moved (compute-, memory-, NoC- or sync-bound) and which did not move at all;
   - per workload in the suite, each variant's normalised speedup over the base, and their
     geometric mean. Never an arithmetic mean of ratios;
   - a one-at-a-time tornado over the study's parameters at the operating points the
     StudySpec names, LABELLED "local sensitivity at these points, not a ranking";
   - energy per token from activity counts × per-activity coefficients, which are claims
     or stipulations from the spec, so the energy number carries its own conditional_on. It
     renders "unverified" while energy_verification is None (the energy rung is deferred
     until after U8), and uses voltage_ratio at frequency ratios ≠ 1 ("unknown" without it);
   - "detail delta": each variant's C2 duration next to its own U-C0 roofline, so the study
     shows how much of each change the roofline would have predicted anyway.
4. Every number renders through report/badged.py. A study over a proposed design says, at
   the top, "every number here is conditional on N stipulations" plus the model card's scope,
   and whether the evidence applies to this design's family at all.
5. hw/studies/: three example studies. hw/studies/npu-m256-sram-and-noc.yaml: SRAM per core
   1.5 MB → 3 MB (pj_per_byte.sram re-stipulated per size), and NoC link width 32 → 64
   B/cycle. hw/studies/npu-l4-hbm.yaml: HBM bandwidth ±25%. hw/studies/npu-l4-dataflow.yaml:
   weight- vs output-stationary (dataflows and mapping policy together: ws-rowsplit@1 vs
   os-tiled@1).
6. hw/studies/workload-suite@1.yaml: models × precisions × phases × named operating points,
   chosen from `uarch characterize` coverage, with a one-line reason per entry. A new suite
   is a new version, never an edit.

ACCEPTANCE TESTS (write first):
1. A study over two variants rebuilds nothing on rerun (cache hit, by request hash).
2. A variant that edits a claim, or any field of a reference spec, is refused, and names the
   path.
3. The tornado is labelled local sensitivity, and a test greps the rendered report for it.
4. Energy per token carries conditional_on and renders "unknown" error when there is no band.
5. A variant that changes nothing the mapping touches produces a diff of exactly zero at every
   point (reuses the L0m relation).
6. Geometric mean: a two-workload fixture where one speeds up 2× and the other slows 2×
   reports a geometric-mean speedup of exactly 1.0.
7. A variant that changes sram.bytes without pj_per_byte.sram is refused, naming both paths.
8. Energy renders "unverified" with no energy_verification, and "unknown" at frequency ratio
   0.6 when voltage_ratio is absent.
9. The dataflow study runs: each variant's conditional_on names its dataflows and mapping
   policy, and a variant whose dataflows lack its policy's dataflow is refused.
10. A count variant (npu-m256 SRAM banks 16 → 32) runs, and its change is in conditional_on.

ADDITIONAL ACCEPTANCE — prepared inputs:
- A variant invalidating a supplied mapping is refused without calling a local mapper.
  An explicitly re-prepared variant records the new mapping identity. Changing prepared
  content under the same input filename causes a cache miss.

GUARDRAILS: No optimiser and no design search. A study is a set of runs a human chose. No
fitted surrogate; rk-sim deliberately refuses fitted Sobol indices, and so does this.
No area model: area is not modelled, and the report says so.

ADR: docs/decisions/U0014-what-a-design-study-may-claim.md.
```
