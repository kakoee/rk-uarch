# Check commands and evidence limits

Executed in `/home/jjaff/AI-infra-simulation/rk-uarch-u4-b` on main, based on published
`bbf87c43ec8616d0bd60d9de06303b70bf8d8002`. The existing read-only development environment
provided Python/pytest/Ruff. The native image provided all native tools. No install command
was run and host Python is not part of the accepted native image.

```bash
PYTHONDONTWRITEBYTECODE=1 /home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python -B \
  -m pytest -c pyproject.toml --rootdir . -p no:cacheprovider \
  --basetemp /tmp/u4-b-private-final-regression -q -rs \
  tests/unit/test_third_party_patch_check.py tests/unit/test_third_party.py \
  tests/unit/test_ci_scope.py tests/unit/test_prompt_sync.py \
  docs/reviews/U4-B-K1-environment-v1/test_environment.py \
  docs/reviews/U4-B-final-reconciliation-v1/test_ci_host_guard.py \
  docs/reviews/U4-B-K1-private-ci-v1/test_private_ci.py
/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/ruff check --no-cache .
bash -n docs/reviews/U4-B-K1-private-ci-v1/private-pull.sh \
  docs/reviews/U4-B-final-reconciliation-v1/native-host.sh \
  docs/reviews/U4-B-final-reconciliation-v1/native-container.sh
git diff --check
```

77 Python checks passed. The initial synthetic Docker fixture had an incorrectly escaped
newline, causing three fixture syntax failures before authentication behavior ran; correcting
it to a raw string made all three pass. Two owner-helper long-line lint failures were fixed;
final repository lint passed. These early failures are not native or registry refusals.

Live strict vendor currentness ran with `PYTHONPATH`, `MYPYPATH`, `VIRTUAL_ENV`, `UARCH_HUMAN`
removed, bytecode disabled, and explicit `sys.path[:0]=['.','src','contract']`. It printed
`/home/jjaff/AI-infra-simulation/rk-uarch-u4-b/scripts/vendor_rk.py` as its origin and verified
the installed snapshot, matrix and compatibility. No protected input or oracle changed.

The actual Docker argv/statuses appear in `native-check.json` and `native-fault.json`.
The Docker stages ran `native-container.sh inspect` and `checks` against a disposable
published export, using the invoking uid/gid, read-only source, isolated writable target
and receipts directories, and `--network none`. The Python host invoked the current
`validate_plan`, full/target `validate_metadata`, and `validate_results` outside the image.
Six actual replay files were compared, not hashes of runner output.

For the fault, the pre-existing `replay-mutation.json` anchor changed only the disposable
`simulation.rs`. The guard consumed the actual successful mutated native output and bytes,
refused `replay bytes differ`, and passed restored inputs. The mutation target and restored
target were distinct to avoid stale build artifacts. Source bytes/mtimes matched before
and after. Newly tested script hashes and exact commands are in the receipts; no mutation
was applied to the live clone. Disposable source/target directories are removed after
collecting the bounded evidence. The local image is retained for the owner.

`owner-registry.py` has only synthetic refusal tests. `private-pull.sh` has fake-Docker
success/failure cleanup and event/destination controls. No real login, registry push/pull,
owner UI setting, secret availability or full hosted wrapper execution is claimed. No
GitHub CI completion is polled or awaited. Existing source-isolation and scope tests pass;
`.github/workflows/ci.yml`, `.github/ci_scope.py` and the actual native selection are unchanged.

Final integration review also checked the construction controller's earlier discovery phase:
it intentionally discovers tests before selecting the replay. The guard preserves that phase
while requiring the replay at CI preflight/results. A dedicated regression test passes, and
the final guard was rechecked against the actual metadata, test logs, six replay payloads,
mutated payload and restored results. The receipt retains both initial and final host-guard
hashes; the native script/executions did not change during that compatibility correction.
