# U4-K2-semantic-local-checkpoint-v1

**Status: proposed; local commit approval pending.** Human placement under
U4-K2-semantic-candidate-v1 is now independently verified. All ten live postimages match
[the approved candidate](../U4-K2-joint-candidate-v1/candidate.json); the real index is empty.
[Placement verification](placement-verification.json) records exact paths and hashes.

Approve a **local human commit of only the ten installed paths** in
[commit-plan.json](commit-plan.json), with this exact message:

```text
feat(contract): complete K2 clock and causal observation semantics
```

Selection: three mapped JSON schemas, mapped admission tests, the new permanent K2 semantic
test, mapped contract implementation, build-spec, U0011, U-P11a and the mapped-loader test.
It installs the accepted raw-clock/owned-duration distinction, nullable unclocked FIFO
observations, release/causal/critical semantics and notification-before-completion refusal.
The fixed-delay Rust kernel and dependency manifests do not change.

Before committing, require main, an empty real index, exact approved live hashes, exactly
the expected tracked diff and the new selected test, and unchanged approved package bytes.
Allow unrelated untracked historical evidence without adding it. Any intervening source or
selected-path change requires reconciliation. Ordinary preparation documentation may precede
this commit; pin the actual parent when preparing its human command.

Validation: exact live hashes/scope and whitespace checked by the coordinator. The human
installer's 124 affected tests/schema/currentness pass and the coordinator's identical-byte
checks remain applicable; no repeated test run or full-suite/native result is claimed here.
The two notification regressions fail without the guard and pass restored, as recorded in
the earlier joint candidate. No artifact-generation/adoption cycle was triggered by the
verified selected support.

**Commit only.** Push remains a separate decision after the returned commit receipt.
C1 remains independently authorized in its private export. This decision does not accept
its resulting dependencies, permit C2/engine compilation, freeze final host/profile records,
release public K2 execution or close a checkpoint/sprint.

The commit must be performed by the human with normal hooks: [CLAUDE.md](../../../CLAUDE.md)
reserves contract/ and docs/decisions/ to humans. The previous placement approval explicitly
kept commit and push separate; this asks only for that next local checkpoint.
