# Reproduction and evidence attribution

The exact executed scratch root was `/tmp/u4-b-build-provenance-final-01`, with reconstructed `direct` and `prior-then-delta` exports. `evidence/reconstruction.json` records the base and both patch routes. A's reconstruction script was inspected before execution; the independent read/hash audit is preserved verbatim as `probes/audit_identities.py.txt`. Its absolute paths describe this actual run. For another run, substitute only the repository/work paths with the exact pinned checkout and a new private output root.

`probes/test_final_join.py` is B's independently authored final probe. Copy this package into the direct export and invoke it using the isolated runner command in peer-follow-up.md. Actual final result: four passes and two assertions exposing unwanted extra-file acceptance, not six passes. The initial semantically identical probe run is preserved separately; it preceded formatting/fixture re-export cleanup. There is no assertion weakening, xfail or acceptance baseline for the two exposed gaps.

`probes/run_affected.py.txt` is the exact executed seven-case selection and two-case final consumer fault/restoration driver. It only invokes the isolated pytest runner with A's synthetic fixtures and inline mock transport. It checks the exact final adapter digest before its single private mutation and restores bytes in `finally`. `evidence/affected-controls.json` retains exact argv, exit codes and original/mutant/restored digests; its four logs and one mutation patch are included. In a rerun substitute only work root/interpreter/runner path, use fresh basetemps and preserve the asserted source hash. The fault source is a private test mutation, never an installable proposal.

Static checks ran from the reconstructed direct export using existing tools, with project roots resolved by its pyproject.toml:

```text
/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/ruff check docs/reviews/U4-B-build-provenance-final-v1/probes/test_final_join.py native/tools/component_startup_inventory.py validation/component/runtime_selection.py
/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/mypy --cache-dir /tmp/u4-b-build-provenance-final-01/mypy-cache docs/reviews/U4-B-build-provenance-final-v1/probes/test_final_join.py native/tools/component_startup_inventory.py validation/component/runtime_selection.py
```

The main source/protected files are unchanged by B. Only this review package is published. Its manifest hashes actual evidence/probe/document bytes, excludes itself to avoid a hash cycle, and names no new executable. A's 66 manifest leaves and three prior manifests' 105 leaves were independently rehashed; this is inherited-evidence verification, not a replay of their executions.

The B inventory probe checks the 821 original external file hashes, then explicitly normalizes 132 venv paths to the already installed coordinator venv used for the tests. No accepted image was executed; no exact runtime environment, new binary, successful ordinary build, native result, genuine startup assurance or public acceptance is implied. The origin logs show no live/foreign project imports. Test names containing construct/assembly use inert mock transport; they are not actual build commands.
