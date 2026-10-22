# U4 human acceptance and closeout

Human approver: **Javid**. Accepted in the coordinator conversation on **2026-10-22**.
Reviewed closeout baseline: `f89da88eb14ccf513e09c48cd4cdc9e0f1af7684`.

## Exact acceptance

> I accept the unchanged 52-benchmark agreement and existing reference APIs, replacing the outstanding A/B signatures with my human acceptance. Compiler/device correspondence will be checked as part of U5’s measurement work, preserving prediction-before-measurement discipline. Unverified diagnostics will not support causal claims. Existing limitations and U0024 deferrals remain recorded.

This accepts U4 implementation/readiness under the scope adjustment below. It is the actual
human agreement, not an A/B signature or a claim that device observations exist. U4's
remaining technical scope decisions are resolved. Publication of `u04-end` awaits the
required CI result; no tag has been created by this record.

## Accepted scope and its changes from the earlier gate

- **Suite agreement:** the unchanged 52 IDs, six classes and comparison boundaries in
  [BENCHMARK-PLAN.md](../../validation/L3_silicon/tpu-v5e/BENCHMARK-PLAN.md) are accepted.
  Javid's acceptance replaces the outstanding A/B signatures for this suite only. The old
  machine-readable proposal's empty signature fields remain historical; no signature is
  invented. Nine published fact leaves and 17 numeric STUB estimates remain unchanged.
- **Preparation:** use the installed reference APIs and retained reference U-C0 resolver
  described in the [reconciliation](U4-closeout-reconciliation-v1/README.md), rather than
  forcing TpuV5eReference through the legacy HardwareSpec `uarch characterize` command.
  Existing shape coverage is retained; no new workload, engine or coverage waiver follows.
- **Observability:** the earlier U4/G3a requirement for demonstrated compiler/device
  correspondence is moved to the U5 measurement work. Its absence no longer blocks U4
  closeout. Freeze predictions before observing device timing; no pilot or performance
  measurement is authorized by this acceptance. Confirm actual compiler/event membership,
  materialization and state during the separately authorized U5 work. If an observed
  envelope does not match the frozen subject, record it as incomparable. Do not rewrite
  the frozen prediction, silently change its workload, or tune using the observed timing.
  Any changed subject needs an explicit prospective disposition preserving the old record.
- **Diagnostic limits:** initial comparisons may use duration and declared work/traffic
  at their agreed scope. Unverified diagnostic output cannot establish a physical cause
  of error. Any later reliance on diagnostic allocation still needs its existing scoped
  verification; no missing verification is converted into a pass or a new U4 task.

This is a human-approved adjustment to U4/G3a readiness, not a statement that every original
readiness observation has been completed. Original accuracy thresholds and the separation
of verification from validation remain. No accuracy badge or G4 verdict is granted.

## Delivered and retained evidence

- M/K1/K2, bounded components and ordinary runtime are installed; retired operational
  assurance machinery is not a prerequisite for ordinary product use.
- Reviewed U4b /5 reference implementation installed at `3626273`, verified/published at
  `6d443e1`; v2 review resolved B1/B2 without changing the native timing model.
- Original 52-unit campaign and independent review remain inherited at their recorded
  subjects. No new campaign or native build was performed for closeout.
- [GEMM](../../validation/L1_limits/hand/H-L1-GEMM-01.md) and
  [DMA](../../validation/L1_limits/hand/H-L1-DMA-01.md) workings are human-validated with
  disclosed AI assistance. Javid separately approved the corrected two-credit 60/62 ns
  DMA result; the original explanation error and correction remain recorded.
- The published reconciliation reports 99 focused checks, final scoped typing, clean-export
  Ruff and strict artifact currentness; support closure remains 56 files. The original
  prediction-ordering requirement is implemented in the existing CI job.

## CI and tag status

One read of GitHub on this acceptance turn observed run
[39871991074](https://github.com/kakoee/rk-uarch/actions/runs/39871991074) for exact baseline
`f89da88eb14ccf513e09c48cd4cdc9e0f1af7684` as **in_progress**, with no conclusion.
It was not polled or counted as a pass. This acceptance publication changes documentation
only; its own CI result must also be distinguished from baseline evidence. Record the
completed relevant checks before publishing the final closeout tag. Native CI remains
intentionally deferred under U0024.

## Remaining work belongs to later stages

U5 prediction freeze and measurement-kit work, actual compiler/device correspondence,
access/spend authorization and TPU measurements remain unexecuted. U0024 remote/native,
nightly and controlled-host performance obligations remain deferred, not waived.
Known F3/F4/F6 limitations and the F5 staging disclosure remain in the benchmark plan.
Full product tables, other reference chips and final project qualification remain later
work. Optional runtime/trace improvements and compatibility cleanup remain separate
follow-ups and cannot be silently added to U4 closeout.

This acceptance authorizes recording the scope and completing the agreed closeout/tag
procedure once checks are accounted for. It does not authorize paid hardware, a new
campaign, diagnostic repairs, deferred infrastructure activation or another review cycle.

## Acceptance-publication checks

The mirrored prompt and CI-scope/collection checks pass: **33 tests** in a clean export.
Whole-export Ruff passes; all 22 new/changed local links resolve. This publication changes
Markdown only. Model/suite data, source code, artifacts and historical independent review
files remain unchanged. These local checks do not substitute for the pending hosted CI.
