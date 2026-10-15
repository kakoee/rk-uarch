# Approved K2 semantic placement and independent C1 experiment

Javid approved both decisions with **“yes, both”**. [Acceptance](acceptance.json) records
exact proposal commit `4ebec62206edc1a9888c70b74f8093b55440320e`, the ten-path patch and
C1 plan identities. No repeated approval is needed for those scopes.

## Parallel next actions

1. Send [the released A prompt](lane-A.txt) to the existing A session. A may perform the
   isolated C1 resolution/fetch experiment and publish its bounded evidence. It uses a
   pinned private export and does not depend on live semantic placement. No compilation,
   native run, live lock/cache mutation, image distribution or C2 release follows.
2. Javid runs the human-only helper below to place the exact ten semantic/schema paths in
   the coordinator checkout. It leaves them **unstaged and uncommitted**. Return its receipt
   for coordinator verification; local commit and push remain separate decisions.
3. B can remain at its reconciliation handoff. Actual finite profile/registry freezing,
   construction probes, public K2 implementation and final binary/host authority follow
   their own reviewed boundaries. U0024 remains unchanged.

## Human placement

Use the full publication commit supplied by the coordinator as PACKAGE_COMMIT below.
The helper accepts that commit or later review-only descendants on main, after checking
all package bytes and the exact approved preimages. It refuses intervening non-review
source changes, dirty tracked/index state, selected-path collisions and symlink paths.
Unrelated untracked reviewer evidence is preserved, not treated as disposable work.

```sh
cd /home/jjaff/AI-infra-simulation/rk-uarch
env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u PARAMS -u SHA -u RK \
  UARCH_HUMAN=1 .venv/bin/python -I -B \
  docs/reviews/U4-K2-approved-release-v1/human-install.py \
  --package-commit PACKAGE_COMMIT --install
```

Omitting `--install` performs read-only preparation without requiring UARCH_HUMAN. The
helper verifies strict currentness, generated schemas, private module origins and the
124 affected contract/loader/prompt checks in a disposable export before placement. This
avoids confusing the existing ignored local `tables/` import-name refusal with source
compatibility; it does not whitelist or bypass the guard in the live checkout.

The helper does not stage, commit, push, change the adopted artifact, generate fixtures,
resolve dependencies or run the native engine. It prints exact parent/paths/patch identity
and placement status. It will not silently retry or overwrite unexpected work. If it
refuses, return the output rather than removing evidence or widening its checks.

## Executed helper checks

[Guard receipt](helper-checks.json): a disposable Git clone passed exact-package preflight,
private candidate verification (124 tests, schema and strict currentness), and preservation
of unrelated untracked work. Ten negative guards refused: missing human authorization,
malformed/nonexistent commit, wrong branch, dirty tracked worktree, dirty index, dirty
release file, pre-existing untracked selected path, selected symlink and committed source
drift. No UARCH_HUMAN was set, and no live placement was executed by the coordinator.

The helper is standard-library-only. Ruff passes. Its two initial long-line lint findings
were corrected before guard testing. Candidate verification from the prior joint package
remains separately attributed; no full suite/native/hosted-CI pass is inferred here.

The protected-path boundary comes from [CLAUDE.md](../../../CLAUDE.md): “Agents propose
and stop on contract/, tests/golden/expected/, CLAUDE.md, docs/decisions/.” This package
prepares the approved human operation without bypassing that boundary.
