# Bounded reproduction and evidence limits

Use the accepted existing host Python 3.12.14 and repository Ruff/mypy only. No installation,
image build, resolver session, native job, authority binding or protected edit is needed.
The original sealed deployment must already exist unchanged; report unavailable inputs,
never recreate authority. This package reads it, and only temporary test paths are writable.

Get `PUB` from publication.json's **helper_commit**, not current main. Let `REPO` be the
normal B clone, `PKG=docs/reviews/U4-B-K2-combined-runtime-stage2-v1`, and `OLDPKG` the original
`docs/reviews/U4-B-K2-combined-runtime-v1`. Create separate new empty private export roots
`FINAL` and `BASELINE` under /tmp. Export exact Git bytes:

```sh
git --no-replace-objects -C "$REPO" archive "$PUB" "$PKG" pyproject.toml | tar -x -C "$FINAL"
git --no-replace-objects -C "$REPO" archive cbb0313e13abc0ca99311df323a0c64f4f7886c1 \
 "$OLDPKG/bindings.py" "$OLDPKG/prepare.py" "$OLDPKG/launch.py" \
 "$OLDPKG/candidate.json" "$OLDPKG/evidence/private-preflight.json" \
 docs/reviews/U4-B-K2-parallel-first-use-v1/parallel_core.py | tar -x -C "$BASELINE"
```

These local exports are test subjects, **not publication proof**. Execute export commands
with inherited GIT variables/config redirects removed (or use a known clean host shell).
The production renderer separately verifies the actual expected HTTPS remote in a new object
store and records the observed main. There is no offline production substitute.

Set `PY=/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python` and `P=$FINAL/$PKG`.
Use a new output root for guard/composition commands. Tests explicitly require STAGE2_BASELINE
and hash-check the original Store helper; there is no dependence on an unexplained historical
/tmp file. Host helper imports are checked against STAGE2_PACKAGE. Project imports occur only
inside the accepted container composition, where their exact paths and hashes are verified.

```sh
env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UARCH_HUMAN \
 STAGE2_PACKAGE="$P" STAGE2_BASELINE="$BASELINE" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
 "$PY" -I -B -m pytest -q -c "$P/pytest.ini" --rootdir="$FINAL" -p no:cacheprovider \
 "$P/test_stage2.py" "$P/test_packaging.py"

env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UARCH_HUMAN \
 STAGE2_BASELINE="$BASELINE" "$PY" -I -B "$P/check_corrections.py" \
 --package "$P" --output "$GUARD_OUTPUT"
```

The tests include 798 explicitly **synthetic receipt-shape slots** (not native result objects,
acceptance tokens, success receipts from real execution or qualification). Harmless /bin/sh
process fixtures exercise launch polling/admission; they do not invoke Docker or native.
The guard helper copies only the package into new private paths, shows corrected pass / actual
assertion failure without the essential guard / exact-byte restoration pass. The baseline
selection is the seven original `test_F1_unpushed_local_tracking_ref_is_not_publication`,
`test_F1_replace_and_environment_redirects`, `test_F2_incomplete_launch_refuses_before_process`,
`test_F3_private_flags_cannot_create_placed_evidence`,
`test_F4_store_transient_disappears_during_actual_poll`,
`test_F5_earlier_helper_shadow_refused`, `test_F6_unknown_decision_condition_refused` tests,
plus the separate `test_F1_replacement_object_alone_refused`. Run those current tests with
STAGE2_PACKAGE pointing to BASELINE/OLDPKG: expected failures demonstrate the original flaws.
The original baseline logs preserve their then-executed formatting and paths unchanged.

For the final affected composition, use an isolated helper-only sys.path (no project checkout):

```sh
env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UARCH_HUMAN "$PY" -I -B -c \
 'import runpy,sys; p=sys.argv.pop(1); sys.path.insert(0,p); runpy.run_path(p+"/check_composition.py",run_name="__main__")' \
 "$P" --repo "$REPO" --subject "$PUB" --output "$COMPOSITION_OUTPUT"
```

This renders the exact 40-file private payload from pinned Git sources, verifies three A
postimages and all old native bindings, then runs nine accepted-container import/fault controls.
Original inputs are mounted read-only, new inputs private/read-only, native subprocess/fork
execution blocked, selectors absent. Positive/restored composition is **not actual immutable
placement/preflight**; the recorded actual mount source and unsealed inode observations show why.
The command uses --pull never, network none, existing UID1000/cap-drop/no-new-privileges.
No native compilation/execution, resolver or authority creation. No extra genuine-session join
is needed: the unchanged session/case/transport/result paths retain their pinned prior evidence.

Run Ruff check across the clean tracked export (not untracked reviewer probes), format --check
on this package's scripts, and scoped mypy:

```sh
/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/ruff check --config "$FINAL/pyproject.toml" "$FINAL"
/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/ruff format --check --config "$FINAL/pyproject.toml" "$P"/*.py
env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UARCH_HUMAN "$PY" -I -B -m mypy \
 --config-file "$P/mypy.ini" --cache-dir "$TYPE_CACHE" "$P"/*.py
```

Mypy checks bodies of all 11 owned scripts/tests with strict equality and unused-ignore
checks. It is deliberately scoped (`follow_imports=skip`, `ignore_missing_imports=true`),
not a claim that the project's strict production suite was rerun. Static checks do not
execute native code. Both protected proposal patches are checked/applied only to a disposable
export of their recorded published preimages, then their exact postimages are recorded.

Preservation evidence hashes complete private before/after snapshots of the original root
and stopped campaign; only compact equality/count/hash receipts are published. Reviewer
originals are read/hash checked, never copied wholesale, changed or formatted. The pending
stress run is not observed as a completed test. No hosted CI polling.
