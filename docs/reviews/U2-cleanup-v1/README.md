# U2 worktree cleanup proposal

Historical proposal below; the approved removal is recorded in [Completed](#completed).

**At proposal time: archive verified; no deletion performed.** Approve `U2-cleanup-v1` to remove only the
three U2 worktree folders listed below. This separate approval implements Javid's requested
inventory → preserve → approve removal sequence.

| Folder | Allocated GiB | Preserved local branch |
| --- | ---: | --- |
| `rk-uarch-u2-a` | 0.60 | `u2/analytic` |
| `rk-uarch-u2-b` | 2.36 | `u2/honesty` |
| `rk-uarch-u2-integration` | 8.24 | `u2/integration` |

Removing these folders reclaims approximately **11.21 GiB**
from their current locations. The compressed preservation archive occupies **476.1 MiB**
and stays outside Git at:

`/home/jjaff/AI-infra-simulation/u2-preservation-20261011T025342Z/u2-uncommitted-evidence.tar.gz`

Archive SHA256: `a1c76ea24feca766327ae2dfd36a03d4d94fda9f3e196ecd801faa6368923287`.

All **132,880** uncommitted non-cache files were archived, including ignored generated
tables, historical diagnostics and final post-publication receipts. Every member was compared
byte for byte with its live source. Only disposable caches/environments were excluded;
tracked content remains in the retained Git branch commits. The archive is one cold backup,
not a development checkpoint or a repository upload. It preserves the old evidence so U3
can use normal Git without carrying active U2 folders.

[Exact plan](plan.json) lists commands and preservation checks. Before removal recheck the
archive hash, complete membership/live bytes, clean indexes and unchanged branch heads.
Stop on newly changed files; do not discard them. Removal uses `git worktree remove --force`
only because verified untracked evidence remains in those folders; it does not delete the
local branch refs. Main, U1 folders, `/tmp` outputs and unrelated data are outside scope.

## Recovery

Retained branch refs recover tracked content using `git worktree add` into absent folders.
The tar archive contains entries under each original worktree folder name, so it can restore
uncommitted files there after recreation. Inspect/extract only to the intended recovery
location; do not extract over an active development tree. Verify `SHA256SUMS` before use.

No folder, branch or cache was deleted during preparation. U3 host confirmation and human
runner registration remain separate prerequisites.

## Completed

Javid approved `U2-cleanup-v1`. The archive digest and every member were reverified
against the live files; all three U2 worktrees were then removed using the approved
Git commands. Their local branch refs, the archive, primary repository and both U1
worktrees remain. [Execution receipt](execution.json). Nothing was pushed or committed.
