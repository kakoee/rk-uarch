# Coordinator response to the post-fork plan review

2026-10-12. For Javid and the independent reviewer. **Recommendations only; no
architecture amendment, lane implementation, gate closure or publication authorized.**

Review: [README](README.md), reviewed repository commit
`afb35022971e56703fe35104b818b8a226c039d7`, tree
`b3dd42e39ca86d765df10c9c732c61009050b687`.
The report's Git blob identity before this response was
`b6030c0cbcfc74225084ef5482b1436c83592157`. The report is preserved unchanged.

## Overall response

I agree with **sound architecture, bounded but substantive planning amendments**.
The current schedule and worker instructions do need changes; “no redesign” should not
be read as “nothing in the prompts needs changing.” Keep one progressive Rust engine,
the analytic baseline, independent verification and scoped hardware validation.

I missed dependencies left over from the fork plan. In particular, retaining the full
table as a prerequisite for a different chip's silicon campaign had no demonstrated
consumer justification. I also described early table work as rk-sim integration too
loosely. Standalone export/replay and nominal compatibility do not establish that
rk-sim consumes the tables. These are coordinator planning errors, not failures by
workers following their assigned prompts.

The replacement should be: build and verify a bounded engine; extend it to the actual
reference-chip benchmark needs; freeze and measure those predictions; expand mechanisms
and generate product tables when a declared consumer needs them. This is not a promise
that the full G4 campaign can run immediately after the small GEMM stage.

## Findings and dispositions

“Agree” below accepts the finding as a planning issue, not its implementation or a
change to an accepted requirement. All findings remain open until the appropriate
amendment and, where applicable, implementation are reviewed.

| Finding | Coordinator disposition and correction |
| --- | --- |
| PF-01: full table gates unrelated silicon | **Agree.** Separate readiness for the reference benchmark suite from readiness for a consumed table. Keep small representative execution/replay tests before silicon. Move grid coverage, interpolation and composition experiments to their actual table consumer. Preserve each mandatory verification obligation at its first use. The proposed G3a/G3b names are workable; exact gate wording must name capabilities and consumers. |
| PF-02: required inputs cannot meet G3 | **Agree.** The accepted npu-l4 supports WS/BF16, and U0022 refuses the FP8/ragged extensions the current table work needs. Do not change those inputs implicitly. Defer extensions only if their dependent delivery also moves. Determine precision and hardware requirements from the first chosen consumer rather than automatically inheriting the old grid. |
| PF-03: TPU readiness absent | **Agree; feasibility first.** Schedule sourcing, representability, measurement-observability and native-admission work before prediction freeze. A usable reference cannot be manufactured by filling unknowns with plausible numbers. Unknown structural/timing inputs need explicit treatment and sensitivity/claim limits; the current carrier placeholders cannot serve as physical assumptions. If the required suite cannot be represented or measured meaningfully, return a concrete scope/target decision. Do not silently substitute a chip or drop a benchmark class. Apply the same readiness requirement to Blackhole. |
| PF-04: C1/C2 integration mismatch | **Agree.** This is a defect in the planned reader and dependency, not an observed bug in a deployed rk-sim consumer. For the current C2-only product direction, require G6 plus the consumed-table exit. Specify a reader refusal for a non-C2 or inconsistent declared composite, with positive and negative tests. Hash verification alone does not establish fidelity or accuracy. Changes on the rk-sim side retain that repository's approval rules. |
| PF-05: overbroad source binding | **Agree with the problem; remedy needs design.** The function binds all Python under three named trees plus other specified inputs, not literally every Python file in the repository. Prefer auditing the actual generator/support dependency closure and proposing a narrower explicit inventory. Include dynamic imports, data/configuration, package versions and environment dependencies, not just static import statements. Do not choose automatic CI regeneration now: U0002 explicitly forbids CI generation and requires human generation/adoption. A narrower inventory needs discriminating relevant-change and unrelated-change tests, migration review and the applicable human lifecycle. |
| PF-06: runner prerequisite | **Agree with separation; qualify readiness.** Correctness work can use approved Linux CI with pinned tools and real executed tests. The existing native job is a conditional scaffold and currently has no native sources to exercise; its presence is not demonstrated readiness. Controlled-host requirements should apply to simulator-performance evidence and scaling. Long execution needs suitable capacity/time limits, which is distinct from needing a controlled benchmarking host or GitHub runner. Do not mandate self-hosted automation merely because a run is long; separately specify the nightly obligation and its milestone. Prospective cold-clone policy may be amended without rewriting U1/U2 exceptions. |
| PF-07: kernel behind schema | **Agree with a bounded split.** After acceptance of the kernel's semantics and toolchain, time/event/resource internals and private unit fixtures may precede public carrier installation. Public subprocess wiring, mapped execution and compatibility claims still wait for the accepted protocol. Internal types must not become a competing public workload format. |
| PF-08: attribution used before qualification | **Agree, with an additional limitation.** Verify any attribution used in G4 before the freeze. A large predicted attribution share does not demonstrate the cause of measured error. The current 70% assignment rule can select an investigation hypothesis, not establish causal explanation. Exact fail-branch wording needs that distinction; no tuning or promotion follows from the heuristic. Keep thresholds unchanged unless separately approved. |
| PF-09: U6 repetition and temporary mesh table | **Agree on scope reduction, not eliminating regression.** U6 should add expanded-scope qualification, mesh admission at representative points, diagnostics, independent review and host-cost evidence. Existing applicable tests must run on the changed integrated revision; rerunning them is useful regression protection, not duplicated development. A full C1 mesh table has not been justified as an exit. |
| PF-10: analytic completion blocks native design | **Partly agree.** Decouple unrelated analytic report completion from kernel development. Do not blanket-waive remaining analytic cases or declare them low-value just because the model is simple. Map each to its first consumer, including roofline checks as well as silicon predictions. Resolve applicable correctness gaps before reliance; retain unsupported/not_run outcomes and the accepted conservative reductions. A case-by-case dependency disposition should precede any pause of B's C1–C5 work. |
| PF-11: earlier consumer-conformance check | **Agree as a bounded risk-reduction task.** Prefer exercising actual permitted vendored interfaces wherever possible. Any new adapter is test scaffolding, not an independent reader or completed rk-sim integration. Document that interpolation, serving/orchestrator integration, future consumer revisions and C2 admission remain untested where applicable. Preserve nulls and refusals: analytic fixtures do not gain C2 eligibility for convenience. Protected fixture/schema changes remain subject to normal ownership. |
| PF-12: compute convention lacks physical evidence | **Agree with the limitation and earlier feedback.** Independent derivation against a stipulated law can verify its implementation; that is useful even though it cannot validate the law. Physical comparisons also depend on reference parameters and compiler mapping, so they do not automatically isolate this one law. Optional matched references remain scoped and optional. |
| PF-13: mixed phase prompts and stale instructions | **Agree.** Give each authorized phase its own inputs, deliverables, tests and stop boundary; synchronize canonical and extracted text. Resolve the restricted-document instruction conflict by specifying permitted sections or removing the dependency. No need to invent new process beyond usable task instructions. |
| PF-14: unnecessary full study/scale tables | **Agree conditionally on consumer audit.** Prefer declared suite points for studies and scale tests where they answer the question. Do not simply replace a required report/table interface with an incompatible result type. Verify the study path can consume sparse/point results, or budget a minimal adapter. Full grids remain required where interpolation or a product envelope actually consumes them. |

## Qualifications to the review's decision recommendations

1. **Do not blanket-accept A's items 1–5.** The bounded component direction is promising,
   but the exact schemas, model conventions, license/toolchain pins and budget choices
   have distinct acceptance needs. The revised scope also invalidates parts of T's
   estimate. Preparing an exact component/schema proposal is not installation approval.
2. **Do not treat every early hardware observation as permanently disqualifying.** A
   pilot could be legitimate development evidence if declared prospectively and kept
   separate from a later frozen, held-out validation campaign. However, the current
   U-P9 discipline does not authorize it. Recommend no pilot now; any future proposal
   must address information exposure, held-out cases, provenance and claims explicitly.
3. **Do not convert an upper budget into an expected runtime.** The 11.2-hour arithmetic
   is a serial ceiling from A's proposed limit, not a measured forecast. It illustrates
   possible capacity cost; the missing consumer is the stronger reason to defer the grid.
4. **Do not promise that a narrow conformance test retires most integration risk.** Its
   measured coverage must be stated. U10's real consumer remains a separate obligation.

## Recommended decisions for discussion

| Review decision | Recommendation to Javid |
| --- | --- |
| J1: gates and table timing | Prepare a bounded amendment separating silicon readiness from the first consumed table; retain all necessary workload/verification checks before their first use. |
| J2: runner policy | Prepare a prospective correctness/performance/automation split, including executable CI readiness and cold-clone requirements. No host registration or allocation is bundled. |
| J3: artifact inventory | Commission the dependency audit and exact narrowing proposal. Keep current enforcement until that proposal and migration are approved. Do not bundle a switch to automated generation. |
| J4: rk-sim boundary | Correct the planned C2 prerequisite and require explicit composite rejection. Preserve rk-sim's separate boundary approval; no production rk-sim edit now. |
| J5: silicon preparation | Commission sourcing/representability/measurement feasibility first, then a concrete admission scope. No measurements, purchase or blanket contract extension is included. |
| J6: kernel sequence | Permit internal kernel work after its semantic/toolchain decisions; retain the accepted schema as a prerequisite for public protocol wiring. |
| J7: U6 and analytic scope | Reduce U6 to its actual additions plus integrated regression. Give remaining analytic obligations explicit consumers and milestones instead of deleting or automatically postponing them all. |

These recommendations can become one coherent plan/prompt amendment for review, with the
artifact-policy change separately designed. They are not seven approvals inferred from
the reviewer verdict. Accepted ADR history, including prior thresholds and human actions,
must remain intelligible; any prospective supersession should be explicit.

## Useful next work after direction is agreed

- **Coordinator:** prepare the exact amendment to execution order, gates and phase prompts,
  with explicit changes to accepted requirements for human review. Include consumer and
  reference-readiness checks so the same dependency mistake does not recur.
- **A:** bound the component protocol proposal and kernel/toolchain tasks; with B, identify
  reference-chip representation and admission gaps. Do not implement the obsolete full
  table requirement or silently expand the accepted hardware.
- **B:** independently challenge the bounded model derivations, design discriminating
  checks, and research reference inputs and measurement feasibility. Prepare the small
  consumer-conformance scope and the source-dependency audit. These are separate bounded
  tasks, not an instruction to implement them all before the kernel can start.

## Checks performed for this response

Read the complete review and checked the relevant gate/prompt text, U0005/U0002, A's
scope/decisions/effort, B's outstanding proposals, hardware definitions, U0022 refusals,
the planned P18 reader, `scripts/u2_inputs.py` and hosted CI configuration. Confirmed
the broad source glob and strict support enforcement directly in source. Did not rerun
the reviewer's private-export probe, prompt-sync tests or any runtime suite. No external
hardware facts or current service limits were independently researched for this response.

Only this response was added. No protected file, live plan, prompt, runtime, artifact or
reviewer text changed. No staging, commit, push, host action or gate closure performed.
