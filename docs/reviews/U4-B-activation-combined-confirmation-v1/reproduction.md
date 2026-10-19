# B bounded confirmation reproduction

Use the accepted existing Python/tool environment. The retained work is `/tmp/u4-b-activation-combined-confirm-01/`; no reuse of its output directory for a new run. All proposal application is private. No `prepare`, `build`, Docker, tracing, worker/campaign or startup-integrity command is part of this recipe.

1. Export source12a2ceb731e37dd1e35218706025479f378d251b to a fresh `source/` directory. Verify its A package manifest SHA256267543af7e561057912176bf01d8930c890f1da65cdd49e22b870a93dd9ce0d3 and all22 leaves. Read the handoff/peer batch fromd36e2a90de780ee3ef7de08f1a9a2c1d08547cfa. Do not include3e0fbd2's `ruff.toml` in that export.
2. Run the exact frozen A `probes/reconstruct.py REPOSITORY FRESH_WORK/routes`. The repository must supply the identical hash-checked A package (all bytes unchanged at this publication) and567905c. This performs both patches and file inventories, not construction. Retain its `reconstruction.json` and stdout. The difference567905c..12a2ceb is only the A review package and is recorded in `evidence/freeze.json`.
3. Copy this package's exact `probes/test_final_join.py` to the same package-relative path under `routes/direct`. Invoke the already preserved B isolation runner from **inside that export**:

```text
PY -I DIRECT/docs/reviews/U4-B-activation-orchestration-v1/probes/isolated_runner.py DIRECT pytest -q -s docs/reviews/U4-B-activation-combined-confirmation-v1/probes/test_final_join.py --basetemp=FRESH_TEST_DIRECTORY
```

Expected: four passes;180 project import files,83 pins,821 external hashed files, no live/foreign project origins. Missing/new runtime source and stale tool tests are identity refusals. The capture fixtures and observation file are synthetic and confer no runtime acceptance.

4. Run this package's `probes/audit_inputs.py FRESH_WORK/routes/direct FRESH_WORK/construction.json`, with the exact source export at `FRESH_WORK/source`. This independently enumerates249 paths and renders only AST literal command/environment expressions. It asserts the linker-map suffix and six extra wrapper environment keys. No builder is called.
5. Static checks used `ruff check --config pyproject.toml PACKAGE/probes` and `mypy --follow-imports=silent PACKAGE/probes/test_final_join.py`. The pyproject is identical to the frozen source; the later root Ruff config is explicitly not selected.

Inherited evidence is identified in README.md; it is not part of the rerun selection. The final 249 input hashes, actual B files, five postimages, routes and test hash are in checks.json. This package's manifest excludes only itself and the publication commit. It does not enter any runtime inventory or generate a new candidate identity.
