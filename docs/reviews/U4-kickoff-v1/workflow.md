# Shared U4 worker workflow

1. Read CLAUDE.md and the actual installed ADRs; the kickoff authorizes U4, not exceptions
   to their still-open concrete decisions. The U3 proposal files retain historical pending
   wording; installed U0011/U0002/U0023 plus the recorded acceptance govern accepted scope.
2. Verify main, origin, clean index/worktree and `u03-end` ancestry. Fetch before work and
   before push. Keep all authoring within your designated independent U4 clone.
3. Make small meaningful commits on main using normal hooks. Synchronize with origin/main,
   rebase only unpublished commits or merge normally as appropriate, resolve conflicts,
   rerun affected checks, and push without force. Verify the remote includes your commits
   and all peer ancestry. On rejection, fetch/integrate and retry; never overwrite the peer.
   No mandatory PR, lane branch or final integration branch. Ordinary owned checkpoint
   commits and pushes are authorized. Protected paths and artifact lifecycle remain separate.
4. Exchange published commit IDs, file links and Git diffs. Do not read another lane's
   uncommitted files as accepted inputs; do not copy whole checkpoint trees, create giant
   review manifests or duplicate prior evidence. Manifests remain for artifact provenance,
   reproducibility and concrete protected-patch identities where needed.
5. Agents propose and stop on contract/, tests/golden/expected/, CLAUDE.md and docs/decisions/.
   Prepare patches under your review directory and verify them in disposable exports with
   explicit import origins. Never set UARCH_HUMAN, bypass hooks or edit peer/reviewer evidence.
6. Preserve installed strict vendor currentness on published main. Unapplied source proposals
   may correctly refuse the current artifact in scratch; record that explicitly. No oracle
   generation or artifact adoption by agents. Keep the reviewed narrower-policy transition
   separate; do not push a half-installed transition as green main.
7. Run checks appropriate to changes and record actual commands, environments and outcomes.
   Distinguish new from inherited results, failures from expected refusals, and real executed
   native tests from empty CI jobs. Tests of live source must not mutate that source.
8. GitHub CI runs asynchronously. Do not wait/poll for CI completion unless Javid requests it.
   Give commit/run links when available and report local checks honestly. Javid will return
   failures for correction. A local pass or successful push is not a hosted-CI pass.
9. Keep prompts synchronized with build-spec when any canonical prompt changes; do not
   rewrite accepted semantics merely to make an implementation convenient. New semantic
   changes require a bounded decision. No rk-sim docs/vision access, external fork revival,
   second Python timing engine, full-table prerequisite or unsupported accuracy claim.
10. Stop at your named checkpoint and return a concise handoff: exact commits, files/APIs,
    observed checks, pending peer/human decisions and next task. Do not close U4 or issue
    independent-review verdicts. Record estimates separately from actual hours.
