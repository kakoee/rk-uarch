# Approved component installation and local checkpoint

Javid replied **yes** to U4-component-semantic-install-v2 at coordinator commit
`56c087187e7b85e757f6ad1090ccf0c36592cd52`. [Acceptance](acceptance.json) records that reply,
the exact approved package and its scope. No new semantic or tool/licence vote is needed.

The [human helper](human-install.py) defaults to read-only preflight. With `--install` and
human-set `UARCH_HUMAN=1`, it places the exact approved 29 files, runs read-only currentness,
schema and the single installation identity test, stages only those files and creates one
local commit through normal Git hooks. It never pushes, builds or runs native work, changes
runtime authority, or generates/adopts artifacts. The installation and checkpoint are one
human invocation within the approved sequence, rather than repeated approval handoffs.

Invoke the helper from the coordinator checkout with this package's exact published commit
as `--helper-commit`. Use the command supplied by the coordinator; no automatic pull occurs.
A malformed/non-ancestor pin, changed helper/payload, changed source/preimage, selected-path
symlink, selected untracked collision, dirty tracked tree/index or ongoing Git operation
refuses. Existing unrelated untracked reviewer evidence is preserved and never staged.
Git environment overrides and replacement objects do not redirect reads or writes.

Before live placement, the helper checks the same candidate in a private archive. It repeats
preflight immediately before placing files, verifies exact postimages, and runs only targeted
installed checks. Broad reviewer/author tests remain inherited. If a guard, check or hook fails,
it stops with existing files/index left for inspection; it does not reset or discard work.
Do not blindly retry a partial installation. Return the complete output for reconciliation.

Return the final receipt. Coordinator verification and publication are already within this
approval. Component native release/first-use authority remains a separate concrete task.
The optimizer can continue in its independent clone; source changes pulled before this command
will require reconciliation instead of silently broadening the approved subject.
