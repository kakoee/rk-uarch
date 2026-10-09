# Executed commands

All work uses cwd `/home/jjaff/AI-infra-simulation/rk-uarch-u2-a` and the existing
`/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python`. No installation occurred.
The default tool sandbox initially failed to start because of the host's
`/mnt/wslg/distro` mount alias; subsequent scoped commands used approved escalation.
That startup failure did not execute repository work.

Before changing production, with `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:contract:src`:

```sh
/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python -B -m pytest \
  -p no:cacheprovider tests/integration/test_u2_a_condition_order.py -q --tb=short
```

`baseline-tests.txt`: exit1, 3 failed/1 passed. Then Ruff format on the new test and
Ruff check `--no-cache` passed. The identical pytest invocation produced
`baseline-final-tests.txt`: exit1, 3 failed/1 passed. `tests-first.json` binds that
final test file and the unchanged baseline production file. The exact stipulated
one-line replacement was applied only after inspecting these expected failures;
the resulting source SHA256 was asserted against the user-provided value.

`python -B docs/reviews/U2-A-RR-C1/checks.py` executed every exact argv recorded in
`checks.json` with bytecode disabled, pytest cacheprovider disabled, explicit `/tmp`
mypy/XDG/Hypothesis caches. All six commands exit0. The strict-support harness's
exit0 means that it caught and asserted the required **ValueError refusal**, not that
old inputs became compatible. Logs retain pytest counts and mypy's 62 checked files.
The unaffected 108-test selection and new 4-test selection do not overlap.

The full actual captured-result probe runs:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:contract:src \
/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python -B \
  docs/reviews/U2-A-RR-C1/actual_replay.py
```

Its stdout/stderr is `actual-replay.log`; its receipt records exact script/source/test
hashes, argv/environment, complete input/result/context identities and phase timings.
It does not modify B outputs or generate/adopt oracle artifacts. It leaves a new
canonical saved prepared bundle in the receipt's `/tmp` path; no cleanup is performed.
The received real package is loaded and rebuilt in memory by existing public APIs.
No `check_support=False` call or fingerprint rebinding is used.

`changes.patch` was produced by `git diff
7aab97d35ca554b0477ac5719dfa4e5306f8bbab -- src/rkuarch/table/build.py`, followed by
`git diff --no-index -- /dev/null tests/integration/test_u2_a_condition_order.py`
(the latter exits1 to indicate an addition). Nothing is staged.

Finally `python -B docs/reviews/U2-A-RR-C1/final_audit.py` checks exact source/test
bytes against executed receipts, unchanged baseline HEAD, the one-path tracked diff,
empty index and the specific received B report/handoff hashes. It writes only the
small preservation receipt and exact new changed-path list. This is not a complete
archive audit, support refresh or whole-worktree manifest.
