# U-P14 · U7 · Lane B — Design studies: variants, sweeps, and the diff report

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, src/rkuarch/{report,study}/README.md, build-spec §1.2 (the
acceptance demo: the study is minutes 4–5 of it) and §2.6. From rk-sim READ-ONLY:
docs/prompts/P9a-sweep-engine.md and P9b-*.md (its sweep and tornado conventions, and why a
one-at-a-time tornado is labelled local sensitivity rather than a ranking).

TASK: the thing a chip architect actually does with this tool, which is to compare designs. A
study is a set of tables over stipulated variants, and a report that says what moved and why.

1. src/rkuarch/study/: a StudySpec (YAML) names a base design, a list of stipulated
   parameter paths with values (one-at-a-time, or a small full grid), one request template,
   and one engine and fidelity. `uarch study <studyspec>` builds each variant's table through
   the existing pipeline. Tables are cached by request hash, so a rerun rebuilds nothing.
2. VARIANTS MAY ONLY CHANGE STIPULATIONS. A study that edits a claim in a reference spec is
   refused. It would be a counterfactual about a real chip wearing that chip's evidence.
3. The diff report (uarch diff from U-P12, extended):
   - per grid point, the relative change in duration, with its attribution split, showing
     which regime moved (compute-, memory-, NoC- or sync-bound) and which did not move at all;
   - a one-at-a-time tornado over the study's parameters at the operating points the
     StudySpec names, LABELLED "local sensitivity at these points, not a ranking";
   - energy per token from activity counts × per-activity coefficients, which are claims
     or stipulations from the spec, so the energy number carries its own conditional_on;
   - "detail delta": each variant's C2 duration next to its own U-C0 roofline, so the study
     shows how much of each change the roofline would have predicted anyway.
4. Every number renders through report/badged.py. A study over a proposed design says, at
   the top, "every number here is conditional on N stipulations" plus the model card's scope,
   and whether the evidence applies to this design's family at all.
5. hw/studies/: two example studies. hw/studies/npu-m256-sram-and-noc.yaml: SRAM per core
   1.5 MB → 3 MB, and NoC link width 32 → 64 B/cycle. hw/studies/npu-l4-hbm.yaml: HBM
   bandwidth ±25%.

ACCEPTANCE TESTS (write first):
1. A study over two variants rebuilds nothing on rerun (cache hit, by request hash).
2. A variant that edits a claim is refused, and names the path.
3. The tornado is labelled local sensitivity, and a test greps the rendered report for it.
4. Energy per token carries conditional_on and renders "unknown" error when there is no band.
5. A variant that changes nothing the mapping touches produces a diff of exactly zero at every
   point (reuses the L0m relation).

GUARDRAILS: No optimiser and no design search. A study is a set of runs a human chose. No
fitted surrogate; rk-sim deliberately refuses fitted Sobol indices, and so does this.
No area model: area is not modelled, and the report says so.

ADR: docs/decisions/U0014-what-a-design-study-may-claim.md.
```
