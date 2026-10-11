# U2 v3 adoption — local validation complete

Javid's approved **U2-artifact-adoption-v3** is installed and locally validated. All work remains uncommitted. Main and the A/B/integration branch heads and indexes are unchanged. Publication, U0021, tagging and sprint closure are pending.

The complete 48-file candidate matches manifest `20eee19b0e864ad07a7b122da7544e385116fdd50d279e1fac1bfbbf03a697ad`. The displaced v2 directory remains under `tables/U2-adoption-v3-displaced-v2`; all 48 files still match committed v2. The candidate directory is preserved too.

## Results

- **1,394 tests passed; zero failures, errors or skips.** Ruff, both exact CI mypy commands, import contracts, schema freshness and strict vendor verification pass.
- Actual execution: 1,008 nominal evaluations, 96 physical points, six preparations. Nominal compatibility passes exactly with zero adjustments. Physical outcomes remain **96 failed discrepancies, 48 capacity execution failures and 864 not-run cases**. These are retained model-comparison outcomes, not hidden test failures. Four human-captured precision refusal observations remain bound in each track; this run did not regenerate them.
- Complete 24-row table and both report modes: **40,320 comparison ratios** checked with full contributor identities and actual serialized HTML/Markdown values. Default displays zero comparison values; opt-in displays 18,768 STUB values with unknown error. All 1,008 fixture labels and the visible **59 stipulations** are preserved. Energy remains unverified.
- Six repeated output/spec files are byte-identical. Saved prepared-input replay reproduces all **3,316 package/output files** byte for byte, with preparation, nominal evaluation, analytic execution and capture producers disabled. The full table/provenance identity and all 59 conditions match.
- All three changed-capability probes refuse with `RenderIdentityBindingMismatch`. Generated output manifest and all members were independently verified.

## Test-binding reconciliation

The initially installed tree `6271581813f8be6bbc48ad8863ea1618beb59fce` had 1,247 passed, six failures and 141 setup errors. Every unsuccessful case expected the old v2 manifest in one of two B test fixtures. The two former strict-support failures passed after adoption.

A test-only correction in `tests/integration/test_u2_b_r202_public.py` and `tests/unit/test_u2_b_stage2_reference.py` explicitly authenticates v3 and constructs current inventory carriers while retaining the original v2 inventory fixture unchanged. Test bodies, attacks, controls, expectations, production files and all 87 frozen support inputs are unchanged. No new generation is required. The correction was first validated in scratch, then installed uncommitted in integration only; A/B were not edited. Its exact diff is [proposed-test-binding-v2.patch](proposed-test-binding-v2.patch), with [installation receipt](test-binding-installation.json).

Final tested tree: `57e2963cedfc67e6592132a860cdd96253d428ea`. This differs from the full runtime tree only in those two tests; [support equivalence](test-binding-support-equivalence.json) verifies all 87 frozen inputs. These are review tree identities, not commits or branch-history protection.

Earlier unsuccessful runs remain recorded: a one-fixture proposal left the second fixture's 47 setup errors; an initial scratch invocation from `/tmp` also mislocated CLI subprocess imports. The final full suite ran from the exact checkout root, with its own source/contract paths. Mypy ran with PYTHONPATH and MYPYPATH unset and fresh external caches.

## Evidence and limits

- [Completion summary](completion.json), [full suite](proposed-binding-v2-full-suite.log), [JUnit](proposed-binding-v2-full-suite.xml), [static checks](final-static-checks.json).
- [Runtime phases](runtime-progress.json), [serialized report checks](serialized-surface-results.json), [independent final verification](final-verification.json), [environment](environment.json).
- [Approved placement](acceptance-and-placement.json), [adoption review](adoption-review.json), [test correction receipt](test-binding-installation.json).

The runtime driver adapts the existing v2 driver to v3 identities and the clean export; its exact adaptation is saved. One historical report-helper assertion now scopes default hiding to comparison predictions rather than declared input coordinates, matching accepted B-F5 behavior. All 40,320 prediction, badge and contributor assertions remain. Full-matrix administrative packaging reviews remain explicitly synthetic; they confer no accuracy or evidence eligibility. The separately completed eight-point public demonstration retains its actual independent AI recipe/registry reviews and their limited scope.

Environment: ElfinKidsLaptop, Ubuntu/WSL2 Linux 6.6.87.2, CPython 3.12.14. This is a clean local Git-tree export, **not** the required fresh GitHub clone or hosted CI run. No simulator-performance or hardware-validation claim follows. No CI no-op is counted as an executed check.

Large runtime products remain under `tables/U2-adoption-v3-runtime/outputs`; their generated-artifact manifest is `8fbc26b677aed6531eb74711108a3a94bcb98d02ade7431155ae18740ea2ee41`. They were not staged. The next publication steps remain separately controlled: review exact local checkpoint contents, commit, publish main for the U0021 cold clone and same-commit Ubuntu CI, then tag and close only after verification. Preserve worker worktrees until publication is verified.
