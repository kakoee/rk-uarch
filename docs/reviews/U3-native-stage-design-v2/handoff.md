# Coordinator handoff — revised U-P5 design only

Amendment baseline and required ancestor:
`30812dfc322b742b81521e350d7d5b541221ca0d`.
Initial Lane A HEAD: `bc01563853c38c7ac514548f68be7d16482b344f`, clean worktree/index.
Fetch/fast-forward retained all published peer history. Publication commit IDs are in the
final author handoff, outside self-referential files; use the Git commit introducing this
package to pin the exact review content. Any later integration commits are named there too.

Deliverable: the eight Markdown files in this directory only. Previous A/B proposals,
historical evidence, accepted ADRs, CLAUDE.md, contracts/goldens, runtime and fixtures remain
untouched. Proposed U0011 is ready for review, not installed. Interface/schema field and
protected patch inventories are proposals; M's installable patch is future work.

Review [decisions](decisions.md) against [U0011](proposed-U0011.md),
[interface](interface.md), [verification](verification.md) and [delivery](delivery.md).
Resolve stage/model/zero-delay/schema/observation choices; B's corpus/analytic consumer
selection and two human L1 fixtures; pre-M dependency policy; exact tools/licenses before
K1; TPU readiness and later product semantics. Budgets/host allocation and nightly remain
separate. M and K1 can overlap only once each task's exact release prerequisites hold.

## Checks and limits

The author checks for this documentation package are read-only Git status/ancestry,
reviewed scope diff, local Markdown link existence, JSON projection syntax, independent
standard-library arithmetic checks and whitespace checks. Normal repository commit hooks
must run; no human flag/hook bypass. The final handoff records their actual outcomes and
published hashes. No runtime suite is claimed as rerun. Existing reports keep original
scope/identities; hypothetical V01–V28 outcomes remain not_run.

No engine implementation, native/container build or candidate run, schema install,
artifact generation/adoption, prediction/measurement, host modification, independent
U-REVIEW, G2 acceptance or sprint closure occurred. No source-empty CI job is evidence.
This task stops after normal commits/push and coordinator handoff.

## Author validation at publication preparation

- `git merge-base --is-ancestor 30812dfc322b742b81521e350d7d5b541221ca0d HEAD`:
  passed after fast-forward; the full accepted amendment is present.
- The standard-library Python block in [checks.md](checks.md): passed for all eight
  Markdown files and both JSON projections, including edges, component counts/intervals,
  DMA channel service, RoPE, queue windows and all displayed effort subtotals. Local link
  existence checks pass; the final count is reported by that reproducible block.
- `git diff --check` and staged `git diff --cached --check`: passed before commit.
  Staged path review contained only the eight new package Markdown files.
- Hardware diff from initial HEAD through amendment baseline: no npu-l4 changes, so the
  inherited hardware identity is retained, not claimed as a fresh hardware measurement.
- No pytest/mypy/native/container/CI suite is represented as run for new Markdown only.
  Hooks are kept enabled. Fresh-clone sprint closure checks remain future obligations.

The default sandbox could not start because of its host mount configuration; filesystem
and Git commands used reviewed escalated execution in the user-designated worktree.
The first attempted documentation writer used unavailable `python`; it exited before
creating files. The successful writer/checker used `python3`. Neither attempt invoked a
runtime candidate, artifact generator or dependency installation.

## Published design commit

Exact proposal commit: **`3ebe76b87881e83f0aa62e91018346d1d1b065d4`**,
`docs(u3-a): revise native stage design for accepted delivery amendment`.
Normal push advanced origin/main from `30812df` to `3ebe76b`; `git ls-remote` confirmed
that exact published HEAD. Fetch immediately before push found no additional peer changes;
normal integration reported already up to date. No published history was rewritten.

All eight files, **25 local links**, two JSON projections and independent arithmetic/
effort assertions passed the reproducible documentation checker. Existing executable
pre-commit hooks ran the human-owned-path and frozen-prediction guards successfully.
The worktree/index were clean after the design push. Amendment ancestry passed again.
No runtime, protected path or historical package appears in the proposal diff.

This publication note is a separate documentation commit; its exact hash is in the final
author response. Review/decision content is pinned by the design commit above. Coordinator
must still adjudicate the listed decisions and G2; publication supplies no acceptance.

## Bounded coordinator follow-up

This follow-up continues the existing v2 package in place; the earlier publication record
above remains historical. Starting HEAD was `c82851020489d4a0fd7279dfbc7c798916c29cec`,
with a clean worktree/index. Fetch/normal fast-forward integrated peer audit/readiness and
coordinator work through `8867c0c86cddf17adafafe1717f57d8bc220a2d1`. Current CLAUDE.md,
U0023, coordinator reconciliation and B's audit/migration/readiness supplement were read.

A-C1 is corrected in verification/U0011 and dependent summaries: historical 22/24 and the
proposed deterministic-anchor remedy are **aggregate-only**. Independent native component-
clock tests and a possible future true-premise per_op domain are separate; the existing
per_op whole-query reciprocal premise remains invalid due to memory-only embedding.
Historical reports, thresholds, omissions and outcomes are preserved; no corpus is run.

[Proposed-M dependency note](interface.md#proposed-m-dependencies-for-bs-audit) lists planned
files, initializer imports/re-exports, common-carrier and component-export relationships,
non-import reads and possible support-closure edges. Current broad U0002 enforcement stays
operative. B must confirm actual edges/data controls when M's exact patch exists; its
baseline 52-entry proposal is neither M's future count nor installed policy. B-C1/B-C2
repair tests and migration decisions remain with B/coordinator, not altered by this note.

Focused checks are the existing standard-library documentation checker, a review of the
Git diff and unchanged scope/model/host sections against `8867c0c`, amendment/peer ancestry,
proposal-only changed paths, whitespace and normal human-owned/frozen-prediction commit
guards. Exact executed results and publication commit IDs follow below or in the final
author response; these checks are not runtime evidence or independent acceptance.

Unchanged: M/K1/K2/B/R/T and permitted M/K1 overlap; U7 full tables; U0023 correctness/
performance/nightly separation; B scope and E1–E5 model conventions; all unrelated decisions.
No engine, protected patch/schema installation, artifact generation/adoption, corpus
execution or G2 acceptance. Stop for coordinator reconciliation. Remaining decisions are
aggregate remedy authorization, any new per_op domain, exact M imports/data and B audit
closure/controls, separate policy/migration, and the already listed stage/tool/schema gates.

Follow-up author checks passed: the existing checker reports eight Markdown files,
**36 local links**, two JSON projections and independent arithmetic/effort assertions.
A focused comparison with `8867c0c` confirms seven unchanged sections: README B scope;
delivery task graph, R/T readiness and host/performance policy; verification E1–E5;
U0011 B scope and environment/gate policy. Three clock scopes are explicit; only seven
existing A-owned Markdown files changed. `git diff --check` and amendment ancestry passed.
These are documentation checks, not corpus execution. Publication hashes and normal-hook
results will be recorded after the correction commit.
