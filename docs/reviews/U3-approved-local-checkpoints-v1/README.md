# Approved U3 local checkpoints — human execution pending

Javid replied **yes** to both separately scoped steps in the
[reviewed decisions](../U3-adoption-checkpoint-and-activation-v1/next-decisions.md).
[Acceptance](acceptance.json) binds proposal `26e1badc9295f7fa42daf09e69a7b6c9d5856a22`
and the exact checkpoint plan. Historical proposal text remains unchanged.

1. U3-adoption-local-checkpoint-v1: stage/commit exactly the seven verified adoption paths,
   parent `187fe3b`, message `chore(u3): adopt reviewed RoPE support snapshot`.
2. U3-rotary-test-activation-v1: install the approved one-file patch, run its 102-case rotary
   contract selection and stage/commit only that file in a second local commit, message
   `test(contract): activate approved rotary v2 admission checks`.

[human_commit.py](human_commit.py) performs these as separate normal Git commits on A's
local main. It verifies its own published bytes, both approvals, exact source parent,
normal hook bytes/configuration, no in-progress Git operation or hidden index flags,
empty index, exact seven-path live changes, current adopted artifact/review, and activation
patch/destination hashes. It reconstructs activation in temporary scratch before staging.
`--check` is repository-read-only: it never stages, activates, commits, sets the human flag
or pushes. The human invocation must supply UARCH_HUMAN=1 and the exact helper commit.

Each real commit verifies its parent, message, staged/committed path set, modes and bytes,
and clean state afterward. The first receipt is written before activation begins, so a
later failure preserves a concrete completed adoption checkpoint. If activation/tests or
any later check fails, stop and return the error; do not reset or blindly rerun. There is
no automatic rollback, resume, generation, rebase, cleanup or push. Receipt locations:
A's ignored `tables/U3-rope-generation-v1/receipts/{adoption-local-commit,activation-local-commit,local-checkpoints}.json`.

After both human receipts are verified, ordinary integration of published coordination
and the final full/static/schema/currentness checks follow. These local commits preserve
A's human schema and runtime ancestry; they do not publish it. Main publication, runner/
manual-nightly, independent review, fork-tool decisions and U3 closure remain separate.

## Coordinator preparation checks

Scoped Ruff and the helper's repository-read-only `--check` passed. The check verified
the seven live adoption paths, strict currentness and human adoption record, exact
one-file activation result, clean index, normal hooks and unchanged parent. No live
activation, staging, commit or push occurred. The prior 653 live contract passes and
102 scratch activation passes remain the executed test evidence; no new full suite ran.

The final human command uses A's `.venv/bin/python -I -B`, this helper's absolute path,
human-supplied UARCH_HUMAN=1, and `--helper-commit` naming the full published commit of
this package. The coordinator will recheck that exact commit before giving the command.
