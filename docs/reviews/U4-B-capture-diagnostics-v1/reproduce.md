# Exact private reconstruction and focused checks

These instructions describe synthetic proposal checks only. They do not authorize capture/build/Docker or production preparation commands. The retained receipts already execute the final affected selection; repetition is unnecessary unless the proposed inputs change.

Use a fresh private directory, the existing pinned Python environment, and no dependency installation. Export B implementation commit `ac9c5f645e4b21d69c5ed18430cefbc1fd9e6868` with `git archive`. Copy this published B evidence package into that export (including its join probe); do not modify the original review files.

Apply, in order, from inside the export:

```sh
git apply --check docs/reviews/U4-A-activation-combined-preparation-v1/proposals/activation-full-unapplied.patch
git apply docs/reviews/U4-A-activation-combined-preparation-v1/proposals/activation-full-unapplied.patch
git apply --check docs/reviews/U4-A-construction-declarations-v1/proposals/construction-declarations-unapplied.patch
git apply docs/reviews/U4-A-construction-declarations-v1/proposals/construction-declarations-unapplied.patch
git apply --check docs/reviews/U4-B-capture-diagnostics-v1/proposals/diagnostic-monitor-unapplied.patch
git apply docs/reviews/U4-B-capture-diagnostics-v1/proposals/diagnostic-monitor-unapplied.patch
```

Do not also apply A's capture-only patch: it duplicates the capture portion of the construction patch. Check A's six intermediate postimages before the last patch, then the nine `combined_executed_inputs` in `checks.json`. The monitor alone transitions from A's `300c7093…` to the combined `8c527a57…`. Compare actual files against `executed-source-bindings.json`; this is source evidence, not a runtime binding. The original live monitor remains untouched.

From the export, with `EXPORT` set to its absolute path and the pinned existing Python used below:

```sh
/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python -I   "$EXPORT/docs/reviews/U4-B-activation-orchestration-v1/probes/isolated_runner.py"   "$EXPORT" pytest -q   validation/component/test_capture_diagnostics.py   docs/reviews/U4-B-capture-diagnostics-v1/probes/test_construction_join.py   docs/reviews/U4-A-construction-declarations-v1/probes/test_repair.py::test_historical_v2_serialization_and_production_refusal
```

Expected: 34 passed, no live/foreign project imports. The isolated runner pins private `pyproject.toml` and project import paths; do not invoke a live-clone copy of the runner. Static checks used the existing Ruff/mypy against the helper, its test and B's join probe inside the composed export; mypy used `--follow-imports=silent`. The source binding includes the probe and unchanged runner identities.

`probes/fault.py.txt` preserves the actual narrow procedure and its private paths. It removes only raw-byte/write equality, runs the three positive phases plus the unrecorded-classified-bytes negative, and restores the exact helper in `finally` before rerunning those four controls. `fault-removed.log` must show one behavioral failure and three passes; `fault-restored.log` must show four passes. This receipt predates the A monitor composition, but its helper/parser bytes and imported ROOT/PARSER/PARSER_HASH are identical. It is applicable reused fault evidence, not another final-source run.

The final 34-test run uses the corrected synthetic syscall list. The earlier monitor run refused at an incomplete fixture list before the intended negative; `pipeline.log` and `pipeline-fixed.log` preserve that distinction. The failing development run supplies no intended guard-kill credit.
