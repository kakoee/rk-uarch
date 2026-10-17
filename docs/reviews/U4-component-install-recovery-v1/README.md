# Recovery of the approved component installation

The original human helper placed all 29 approved files exactly, then tried to run vendor
verification directly in the working checkout. The existing U0002 import guard refuses the
ignored top-level `tables` directory. The private preview had no such directory and passed.
This was a coordinator helper-context error, not an approved-source or artifact mismatch.
The prior staging recovery had already established the clean-export approach; the original
component helper should have used it consistently.

[Interrupted state](interrupted-state.json) records the observed HEAD, all exact postimages,
nine tracked changes, twenty new approved files and an empty index. No component commit or
push occurred in the failed command. Do not rerun the original installer or discard files.
Its package and evidence remain unchanged.

The [recovery helper](human-commit.py) uses the existing approval unchanged. It does **not**
place source again. It verifies the actual installed bytes, creates a clean `git archive`
of current HEAD, overlays those exact 29 bytes (including every new file), and runs the
unchanged strict vendor check, schema check and the single installation identity test there.
All project imports must come from that export. This verifies the prospective commit tree;
it does not claim the working checkout's extra import namespaces pass the guard.

The guard, selected support policy, saved tables and runtime authorities are untouched.
There is no new allow-list entry, environment bypass, generation or artifact adoption.
The original approval covers the local checkpoint and subsequent coordinator publication.
No renewed semantic/install approval is needed for this recovery of identical bytes.

Default invocation is read-only. Human `UARCH_HUMAN=1` plus `--commit` rechecks state after
verification, stages exactly the 29 approved postimages, and commits through normal hooks.
It verifies parent, path selection and every committed hash, then returns a receipt. It
never pushes or runs native work. Existing unrelated untracked review evidence stays alone.
A failed guard/hook stops without resetting or rewriting the installed work; return output.

The recovery helper imports the exact original helper only after verifying its bytes against
publication `3a615fe5baf52df7dd5fa3e0f908a3e3b61ee8b8`. Recovery publication must be passed as
`--helper-commit`; it must be an ancestor of HEAD and its files must be unchanged. Only review
preparation commits may advance the interrupted HEAD. Source drift, dirty index, unexpected
tracked deltas, selected symlinks, missing new paths or incorrect postimages refuse.

After the human receipt, the coordinator verifies and publishes under the existing approval.
Component native release remains separate. Optimization remains in its independent clone.
