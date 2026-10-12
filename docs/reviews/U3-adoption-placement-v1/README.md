# U3 exact artifact adoption — accepted; human placement pending

Javid (@jjaffari) replied **yes** to U3-artifact-adoption-v1. The
[acceptance record](acceptance.json) binds the exact candidate, four-path binding patch
and administrative review approved in proposal commit `064473d21b6a0e42e965703e4ae2fbb09f7568ed`.
The [historical proposal](../U3-artifact-adoption-v1/next-decision.md) remains unchanged.
The approved review bytes may now record this actual human administrative adoption decision.
This is not an independent model-validation verdict or permission to activate protected tests.

The coordinator repeated the complete candidate/receipt audit after approval; it passed.
All 1,008 rows and four precision refusals remain unchanged. The currentness failures are
resolved only after the approved candidate is actually placed in A's canonical directory.

## Human placement helper

[human_place.py](human_place.py) targets only A's exact local `187fe3b` revision. It checks
the reviewed proposal files against Git, the published helper/acceptance bytes, approved
freeze and environments, A's clean state and normal hooks, complete 48-file candidate,
old canonical manifest, all target hashes and exact seven-path resulting change scope.
It reconstructs the approved pin patch in disposable scratch before touching any live file.
`--check` is repository-read-only and does not require or set the human flag.

The actual human invocation requires UARCH_HUMAN=1 and the full published helper commit.
It verifies the complete artifact, writes only differing members and the exact binding
updates, then checks strict currentness and the approved administrative review. The 45
unchanged artifact members are verified byte for byte. The old U2 review remains untouched.
It records `tables/U3-rope-generation-v1/receipts/adoption-placement.json` in A.

The helper leaves all seven changes **unstaged and uncommitted**. They are not protected by
branch history until the separately reviewed local commit. It performs no generation,
protected-test activation, staging, commit, push, runner action or closure. A's local branch
continues to contain the earlier human schema and runtime commits. Primary publishes only
this acceptance/helper package, not that source history.

After receiving the printed placement receipt, the coordinator verifies the live exact bytes.
Protected-test activation and the local commit are prepared separately, followed by integrated
checks and a separately verified publication push. If any step fails, return the output and
leave the files/receipts in place for reconciliation; do not blindly rerun or reset the work.

## Preparation checks executed

The coordinator ran scoped Ruff and the helper's `--check` using A's isolated interpreter.
Preflight passed for all 48 candidate files and exact seven-path placement. It reconstructed
the approved patch in temporary scratch and verified every resulting hash; no live placement,
staging or commit occurred. A remained clean at `187fe3b`. No full-suite rerun is claimed;
the earlier conditional 784-pass / 28-skip check remains in the adoption proposal.

The human command uses A's `.venv/bin/python -I -B`, this helper's absolute primary path,
`--helper-commit` set to the exact published commit containing this package, and human-supplied
`UARCH_HUMAN=1`. Unset PYTHONPATH, MYPYPATH, VIRTUAL_ENV and PARAMS as in the earlier generation
command. The coordinator supplies that full command after publication and commit-pinned
read-only recheck.
