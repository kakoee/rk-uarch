# Bounded source-only reproduction

Use the existing pinned Python/tools, no new dependencies. Original subject: A source aecc6a27e1533eee43e884380ed095cfc1edfd20; handoff e550a8801525c722792d375f78f623aebb72caeb. Do not use a later main revision as the subject. Retained private work is `/tmp/u4-b-diagnostics-final-confirmation-01`; use a fresh directory for any justified replay.

1. Verify A manifest hash193d6621a1c1ad508048efffa990ac9ab08c8244c52c7200ff74700f5e9e4b23 and all64 leaves against the source commit. Run its inspected `probes/reconstruct.py REPOSITORY NEW_WORK`. It applies both routes only, rehashes histories and source/consumer entries, and writes reconstruction.json; no preparation/build command runs.
2. Copy the exact A final package and this B package into their matching docs paths under `NEW_WORK/direct`. Run B `probes/audit.py REPOSITORY NEW_WORK`. It checks both source sets, eleven postimages, actual B leaves, AST compatibility and acyclic binding. No production inventory or identity is generated.
3. From the direct export, use its own preserved isolation runner:

```text
PINNED_PYTHON -I DIRECT/docs/reviews/U4-B-activation-orchestration-v1/probes/isolated_runner.py DIRECT pytest -q -s docs/reviews/U4-B-construction-diagnostics-final-v1/probes/test_final_policy_join.py docs/reviews/U4-A-construction-declarations-final-v1/probes/test_startup_inventory.py docs/reviews/U4-B-capture-diagnostics-v1/probes/test_construction_join.py --basetemp=NEW_TEST_DIRECTORY
```

The final probes select twelve cases, with only fake guardian/worker dispatch. The observation file is explicitly synthetic to exercise `imports()`; no real payload or authority is created. External paths are compared using the exact documented two clone prefixes and every original/current byte hash is verified. Any other path or byte change fails. This is an explicit test-environment join, not production relocation.

The actual retained run sequence is nine passes/three B-probe assumption failures, then three corrected passes, then one import-only pass after B probe static cleanup. No unchanged tests were repeated just to produce a new aggregate receipt. `focused-development.json` stores the exact original log as a JSON UTF-8 string plus its raw SHA256; decode the string to reproduce raw bytes.

4. Existing Ruff and mypy were run only on the two B probes with private `pyproject.toml`, using `--follow-imports=silent` for mypy. Startup-tool mypy was separately run once on baseline and final: expected two unchanged bare-dict diagnostics, not a success. No annotation suppressions or candidate edits are made.

All final source postimages are in evidence/audit.json. A's 39-check source hashes and published/executed test AST equality were verified for inherited applicability; B's unchanged helper/parser hashes are in checks.json. No historical sweep, host-shell mock, fault sweep or trace build is required by this confirmation.
