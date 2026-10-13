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
- `git diff --check` and staged `git diff --cached --check`: required before commit;
  final publication handoff records the executed outcome. Stage only this package.
- Hardware diff from initial HEAD through amendment baseline: no npu-l4 changes, so the
  inherited hardware identity is retained, not claimed as a fresh hardware measurement.
- No pytest/mypy/native/container/CI suite is represented as run for new Markdown only.
  Hooks are kept enabled. Fresh-clone sprint closure checks remain future obligations.

The default sandbox could not start because of its host mount configuration; filesystem
and Git commands used reviewed escalated execution in the user-designated worktree.
The first attempted documentation writer used unavailable `python`; it exited before
creating files. The successful writer/checker used `python3`. Neither attempt invoked a
runtime candidate, artifact generator or dependency installation.
