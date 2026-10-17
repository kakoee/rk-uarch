# Verification cost and ownership inventory

Subject: published `620896870a6479a69fa607dfad8c6582847c4cc1`. Component Stage 3 acceptance
was preserved before work began. This independent main clone excludes untracked reviewer
files. Concurrent CI-C1/O2 proposal, component tests, historical evidence and sealed K2
runtime remain separate. No native execution or sprint qualification is claimed here.

Before final verification, published peer commits `aa5428e` and `56c0871` were
reconciled: component joins and their coordinator decision are documentation/evidence
only, with no overlapping installed source changes. They are preserved in main history.

| Recurring work | Actual selection / inputs | Ownership and cadence | Cost boundary / duplication |
| --- | --- | --- | --- |
| Developer full | `uv run pytest -q`; configured tests, contract/tests, validation | Relevant development / existing requirements | Includes native and nightly markers unless explicitly excluded; not equivalent to CI Python |
| Developer fast | `make test-fast`, excludes nightly, silicon, native | Relevant edits | Includes contract, golden and determinism if present; not release qualification |
| Python CI | Excludes nightly, silicon, native, golden, determinism | Every code push / PR; short docs path retained | Baseline includes contract nodes with optional dependency skipping |
| Contract CI | `pytest -q -rs contract/tests --require-vendor` | Every push / PR including docs | Missing dependencies fail; separate `vendor_rk.py --check` strict currentness and schema `generate --check` remain mandatory |
| Python static | Ruff, both mypy commands, lint-imports | Every push / PR including docs | Separate from test collection; no qualification through a cache hit |
| Prose selection | `test_prompt_sync.py`, `test_ci_scope.py` | Conservative docs-only classifier | Executable docs, JSON/YAML/logs/patches, mixed pushes, uncertain history remain full CI |
| Licences and patches | `test_third_party.py`, `.github/check_third_party_patches.py` | Every push / PR including docs | Licence tests overlap Python, retained because low cost and separate required check |
| Golden / determinism | Existing marker jobs, guarded by fixture existence | Existing relevant-code workflow | Empty fixture guards are historical behavior; no new skip or cadence claim |
| Ordering / perf | Existing prediction check / perf directory selection | Existing relevant-code workflow | No baseline fixtures currently authorizing new performance claim |
| Native local | Pinned debug/release, fmt, clippy, licence, applicable replay and fault checks | U0024 local milestones and identity boundaries | Inherited evidence only; no Rust build or activation in this task |
| K2 first-use | 133 cases × 2 modes × 3 repetitions = 798 real calls | Approved identity/release boundary | Inherited 259.99 s elapsed: shared resolution 79.77 s, case processing 173.87 s; 11 workers, not a safe Python worker default |
| K2 saved replay | Actual saved outputs, no new calls; 26 corruption controls and restores | Required replay obligation | Inherited 194.25 s; sealed runtime untouched |
| Component F5/F6 and guard sweeps | Exact preserved reviewer commands / mutations | Scoped independent review, not ordinary CI | Review complete; prospective tooling does not rewrite or rerun historical verdicts |

Durations above are elapsed, not aggregate CPU. No hosted duration is inferred from this
WSL2 measurement. Machine/cache/load records, baseline and final node outcomes accompany the
handoff. Benchmark noise and profile overhead are disclosed separately.

## Policy and dependency boundaries

No change to required repetition counts, independent review, release checks or U0024.
Remote Rust CI, runner/registry publication, nightly and controlled-host performance remain
deferred. New package dependencies, a new artifact-upload action or normative cadence changes
would require a separate proposal. Existing setup-uv caching can reuse dependency downloads;
it must never reuse test acceptance, a result token or an executable for changed source.

No new module is added under scripts/: the closed import guard and both support inventories
bind that directory. Helpers under .github/ and tests/ avoid changing the adopted generator
closure. Actual vendor currentness must still pass on the resulting checkout.
