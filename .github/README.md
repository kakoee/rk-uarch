# CI test selection

Every main push and pull request starts `ci`. A stdlib-only classifier reads the
GitHub event and the Git diff of the complete push or PR merge checkout. A change
gets the short path only when every changed path is a regular, non-executable
Markdown file in `docs/`, `rk-sim-side/prompts/`, or the root `README.md`.

The short Python job retains lint, both type checks and import checks, then runs
prompt synchronization and the CI-selection regressions instead of the full Python
suite. Contract/currentness/schema and licence checks still run. Golden, determinism,
native, performance and ordering jobs are explicitly skipped; this is not evidence
that those checks executed. There is no whole-workflow path exclusion, so check names
remain available. See GitHub's [skipped-job status semantics](https://docs.github.com/en/pull-requests/reference/status-checks).

JSON, YAML, logs, patches, executable examples, tests, dependency files, workflows
and unknown paths take the full route, even under `docs/`. Some documentation-area
JSON files are test inputs, so that directory is not blanket-exempt. A mixed push
runs the full suite even if its last commit changes only Markdown. Renames inspect
both paths. Missing history, new branches, non-ancestor baselines, unknown events,
empty diffs and classification uncertainty default to full CI.

`.github/ci_scope.py` and its tests are outside the adopted oracle's source closure;
this CI-only change does not install the prospective dependency policy or regenerate
artifacts. Workflow or classifier changes themselves trigger full CI. To check the
selection locally:

```sh
uv run pytest -q tests/unit/test_ci_scope.py tests/unit/test_prompt_sync.py
```

Hosted CI is checked by Javid asynchronously; agents need not wait for a run to finish
unless asked. Failed checks can be brought back for a separate fix. This does not
waive a required pass before tagging or making a validation claim.

## Temporary native execution deferral

Javid has deferred remote/hosted native execution. The live native job is explicitly
skipped; this is not a native pass or K1 qualification. Other checks and the docs-only
classifier remain active. See [scope and resumption](../docs/reviews/U4-native-CI-deferral-v1/README.md).
