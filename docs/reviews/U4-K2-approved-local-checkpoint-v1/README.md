# Approved local K2 semantic checkpoint

Javid approved `U4-K2-semantic-local-checkpoint-v1` with “yes”.
[Acceptance](acceptance.json) binds the exact ten-path [commit plan](../U4-K2-semantic-local-checkpoint-v1/commit-plan.json)
at `1e48088209b2c3bd8bb5b2c58422cd7473ebc37e` and message:

```text
feat(contract): complete K2 clock and causal observation semantics
```

[The helper](human-commit.py) defaults to read-only verification. With `--commit`, a human
invocation stages only those ten paths, verifies staged bytes, commits with normal hooks,
and verifies the parent, exact committed selection and clean tracked/index state. It never
sets UARCH_HUMAN, bypasses a hook or pushes. Unrelated untracked review evidence is preserved.

Use the full published helper commit supplied by the coordinator:

```sh
cd /home/jjaff/AI-infra-simulation/rk-uarch
env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u PARAMS -u SHA -u RK \
  UARCH_HUMAN=1 .venv/bin/python -I -B \
  docs/reviews/U4-K2-approved-local-checkpoint-v1/human-commit.py \
  --helper-commit HELPER_COMMIT --commit
```

Return the receipt. Push remains a separate decision. A's already authorized isolated C1
experiment is independent; this commit grants no C2, native execution, actual host/profile
authority, qualification or closure. No generation/adoption is performed.

[Checks](checks.json): twelve checks in a disposable clone, including exact-scope success,
preservation of unrelated untracked work and ten expected refusals: short/nonexistent commit,
wrong branch, selected-byte drift, unrelated tracked edit, nonempty index, changed acceptance,
missing required hooks, selected symlink and missing human invocation. No UARCH_HUMAN was set,
no protected commit was made, and live source was untouched during these tests. Ruff passes.
The earlier identical-byte 124-test/schema/currentness results remain inherited, not rerun.

This human step is required by [CLAUDE.md](../../../CLAUDE.md) and the normal protected-path
hook. The separate local-commit approval is now recorded; no further approval is requested
for executing this exact command. If the helper refuses, return the output and preserve the
worktree/index for reconciliation instead of widening the selection.
