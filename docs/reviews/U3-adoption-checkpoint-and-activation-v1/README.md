# U3 human placement verified; local checkpoints proposed

The coordinator verified Javid's returned placement receipt against A's live files.
All 48 canonical candidate members equal the approved generated candidate. The exact
seven modified/new paths match their approved bytes; the real index remains empty,
A's HEAD remains `187fe3b035bee9cbeae13b03c8b4ac6ef0ee276f`, and the rotary activation
test remains byte-identical to that commit. No other tracked/untracked path changed.
[Verification](verification.json) includes exact hashes and the returned human receipt.

This completes the placement reconciliation for the already approved artifact. The seven
changes remain uncommitted and are not protected by branch history yet. The generated
candidate and original run receipts remain under A's ignored tables directory. Prior U2
review records and historical snapshots are unchanged.

## Checks executed on the live placed tree

- Direct `python scripts/vendor_rk.py --check`: manifest, matrix and current compatibility
  verified. Both previously stale-support contract gates now pass.
- `pytest -q -rs contract/tests --require-vendor`: **653 passed, 28 skipped** in 6.04s.
  [Log](live-contract-tests.log). The skips are exactly the pending rotary admission tests.
- `ruff check .` and both CI-form mypy commands with PYTHONPATH/MYPYPATH unset: passed
  (78 source files, 31 contract-test files). Both import contracts passed.
- Old and new contract schema generators and the new engine schema generator: passed.
  No full-repository suite or full comparison-matrix execution is claimed by this step.

## Separate activation check

A's original one-file zero-context activation patch is unchanged: SHA256
`4280f13077b703283d3e8237011f18bd6641ee9c4580337d8b822d5193613e26`.
It removes the pending skip, updates pending prose and renames the test. All case fixtures,
assertions and runtime source remain unchanged. The proposal path remains in A's reviewed
local Git history at `docs/reviews/U3-RoPE-runtime-v1/protected-tests.patch`.

The coordinator exported A's exact HEAD to disposable scratch, overlaid the seven approved
placed paths, and applied that activation patch only there. Both rotary contract modules
passed **102 tests, zero skips**, in 1.92s ([log](activation-scratch-tests.log)). Exact old/new
test-file hashes are recorded in verification.json. No live activation or protected commit
occurred. The earlier 14-fault experiment remains attributed to the prior runtime review;
it was not rerun here. Test counts overlap and must not be added as distinct coverage.

## Two local checkpoints, separately scoped

[The exact plan](checkpoint-plan.json) and [two proposed decisions](next-decisions.md)
are ready for Javid. First commit only the seven already approved adoption paths on A's
local main. Then install and commit only the one-file activation patch in a second human
commit. Normal ownership hooks remain enabled. Stop if either expected parent, scope or
content check fails. No reset, force push, automatic regeneration or evidence relabelling.

Activation has not yet been authorized. CLAUDE.md says agents propose and stop on contract/;
the accepted runtime authorization explicitly reserved this installation for the human.
Adoption selection/placement was approved earlier; this asks for its local commit, not a
second adoption decision. Both exact local commits can be approved together while remaining
separate operations and separate Git history entries.

After those receipts are verified, integrate published coordination into A by an ordinary
merge preserving its human/runtime/checkpoint ancestry, then run the final integrated static,
schema/currentness, rotary/legacy/report and full-suite checks. Publishing A's source is a
separate later step. Neither these checkpoints nor 102 passing tests complete independent
U-REVIEW, U-P6, runner/manual-nightly, fork selection/U0005, v2 evidence integration or U3.
