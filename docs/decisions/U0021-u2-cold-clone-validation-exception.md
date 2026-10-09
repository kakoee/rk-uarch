# U0021 — U2 cold-clone validation-host exception

**Status:** ACCEPTED by Javid (@jjaffari), 2026-10-07.
Records his explicit kickoff authorization as acting human decision-maker for both U2 lanes.
No Reza approval is claimed. This record is local and uncommitted; acceptance is not publication.

**Scope:** Sprint U2's final published revision, identified by its exact commit when validated.
U0021 was unused when checked; reserved U0001–U0018 and accepted U0019/U0020 retain their
assignments. U0020 remains unchanged and applies only to U1.

## Context

The execution plan requires the joint sprint exit on the designated Linux box from a cold
clone. U0020 permitted a different host only for U1. U2 therefore required a new decision
rather than inheriting the old exception. U2 delivers Python analytic execution, standalone
preparation/replay and deterministic table/report output; it does not deliver the later
fork/native performance or hardware-validation work.

## Explicit authorization

Javid approved the following during U2 kickoff:

> Approve a new U2-only exception: fresh GitHub cold-clone validation on
> ElfinKidsLaptop’s Ubuntu/WSL2 environment, supplemented by hosted Ubuntu CI
> on the exact same published commit.
>
> Record this as a new decision; do not extend or rewrite U0020 retrospectively.
>
> Run the complete U2 exit checks, including actual workload/analytic parity,
> end-to-end table/report production, deterministic output and prepared-input
> replay with producers disabled. Record exact environments and distinguish
> executed checks from CI no-ops.
>
> This does not approve WSL2 for simulator-performance benchmarking or waive
> U3’s self-hosted runner and later hardware-validation requirements.
> Establish the designated Linux host before work that requires it.

## Decision and required evidence

Replace U2's designated-Linux-box cold-clone host condition with a fresh clone directly from
GitHub on ElfinKidsLaptop's Ubuntu/WSL2 environment plus hosted Ubuntu CI on that exact
published commit. This is an explicit host exception, not a claim that a separate Linux
machine was used. All U2 checks and numerical thresholds remain required.

At validation time, record:

- Exact published commit, remote origin, detached checkout identity and clean initial/final
  Git state. Use a new virtual environment and cache and document any base-interpreter reuse.
- Actual hostname, OS, kernel, architecture, Python, uv, lockfiles and relevant package versions;
  corresponding hosted CI runner/environment and job/run URLs. Do not copy U1 host details
  as if measured anew.
- Adopted oracle manifest/generator/component/matrix identities and strict verification,
  with approved artifact adoption references where refresh was required.
- Complete U2 joint exit: actual workload parity with full fixture accounting and accepted
  attribution; aggregate analytic duration within ±0.1% of each fixture's upstream-generated
  expectation using its own params; independent rank/operator correctness; per_op >=
  aggregate and attribution sums; table -> report; characterize demo; repeated output bytes;
  local export/replay with producers disabled; independent supported imports; invalid-input
  refusals before execution; contract/static/schema/prompt and provenance/report regressions.
- Exact commands, exit codes, outputs and artifact hashes. Distinguish A-only, B-only and
  integrated results, actual executed checks from conditional CI no-ops, and synthetic
  contract/harness probes from real workload/engine results.

If the integrated revision changes after validation, determine and perform the checks needed
to bind closure evidence to the final published revision. Do not present another commit's CI
or an unpublished worktree as same-revision cold-clone evidence.

## Alternatives and consequences

The default designated Linux box remains appropriate and is still required before work that
depends on it. The approved temporary alternative permits U2 correctness and deterministic
output validation to proceed on the available WSL2 host with hosted Ubuntu corroboration.
It does not provide a simulator-performance benchmark host or hardware accuracy evidence.

Neither suite success nor this exception promotes a model badge, validates silicon, changes
a parity budget, resolves embedding accounting or satisfies B-F16 without actual artifacts.
U3 must still register the self-hosted runner, re-enable its nightly schedule and show the
required green run before U-P5. Later engine/performance/silicon requirements remain intact.

## Publication and closure

This accepts only the U2 validation-host arrangement and its evidence obligations.
U0003/U0004 acceptance, complete artifact adoption, independent reviews, commits, pushes,
U2 closure approval and publication of u02-end remain their own steps.

## U0003 accepted check-scope addendum

Accepted by Javid under U2-U0003-acceptance-v1; see
[the exact acceptance record](../reviews/U2-U0003-acceptance-record.md).

Leave the accepted host arrangement and quoted historical authorization intact. Under
the exact U0003 S acceptance, replace the listed physical workload/analytic nominal-parity
checks with: (1) independently specified physical operator/shard/count/timing tests and actual
local/imported replay with producers disabled; (2) isolated test-only nominal compatibility
on the complete adopted inventory, unchanged <=5% absolute count spend, <=0.5% residual and
+/-0.1% stored duration; (3) complete hash-bound physical discrepancies, including failures,
null/absent/unassessed and pre-call refusals. Report the lost independent physical full-workload
duration claim plainly. Add complete artifact/evidence closure and all-surface STUB opt-in
checks. All other U2 checks, fresh GitHub WSL2 clone and same-published-commit hosted Ubuntu
CI remain required. This changes check scope only; no U3/later-host waiver or acceptance of
unpublished code follows. Record this new decision separately from the original host approval.
