# U3 RoPE runtime coordinator reconciliation — 2026-10-11

**Ready for combined-freeze preparation.** No new blocking contradiction found in the
bounded A implementation at local commit `187fe3b035bee9cbeae13b03c8b4ac6ef0ee276f`,
tree `fe10c7d4b08a6910f165da9b92f8e13a2a37c107`. This is coordinator reconciliation,
not independent U-REVIEW, current artifact acceptance, permission to push A, or U3 closure.

Published main remains on the separately checked v1 implementation through `4815b7c`.
Its hosted CI passed after the illustration/toolchain portability correction. A includes
that correction through an ordinary merge. Its human schema commit `eeb2f4d` is preserved;
A's clean local main, index and all implementation files were left untouched by this review.
No protected installation, oracle generation, adoption or source-bound publication occurred.
Only this small coordination package is selected for publication.

## Scope and checks executed by the coordinator

The eight new runtime Python modules, four engine schema mirrors and owned tests implement
the accepted additive v2 route. Existing source files are unchanged relative to published
`4815b7c`; protected paths are unchanged since human installation `eeb2f4d`. The new route
requires explicit coefficients and binds the bundle, request, job, result, assumptions and
execution implementation. It preserves the separate v1 route. B's standalone v1 reports gain
no new v2 applicability. Public v2 tables/reports and evidence attachment remain outside scope.

Executed on the exact local A revision:

- Focused rotary/carrier/old-schema selection: **270 passed, 28 skipped** in 69.02s.
- Full contract selection with `--require-vendor`: **651 passed, 28 skipped, 2 failed** in
  5.17s. Both failures are `input support inventory changed`: current snapshot compatibility
  and exact adopted 1008/four-refusal currentness. No other contract failure occurred.
- `ruff check .`, both exact CI mypy commands with PYTHONPATH/MYPYPATH unset (78 source and
  31 contract-test files), and both import contracts passed. Both contract schema generators
  and the new engine schema generator passed; old schema freshness is in the focused suite.
- Re-executed A's published fault exercise against **187fe3b**, applying the proposed protected
  test activation only in a disposable Git export: **102 passed, zero skips**. All **14**
  injected faults caused assertion failures, with passing baseline/restored controls. Changed
  implementation bytes under an unchanged version refused old work in a fresh process.
  [Compact results](exercise-results.json) are coordinator executions of the author's harness.
- A separate [coordinator probe](probe.py) checked **12 configurations / 24 points**: FP32,
  BF16 and FP16; partial/full rotation; tp1 and tp2 with replicated K; decode and prefill.
  Layer reuse, attention form, pairing and analytic mode vary together in this probe, so it
  is not an exhaustive cross-product. Expected operations, transfers and allocation are derived
  directly from the explicit tiny model and U0022 equations, without production count helpers.
  Every point met its U-C0 floor. JSON-round-tripped replay returned identical result bytes
  with producer calls and imports disabled. [Results](probe-results.json).

These selections overlap. They are not summed into a unique test total. The coordinator did
not rerun the full suite or any full U2 matrix. A's reported full run remains attributed to A:
1,656 passed / 57 skipped / two currentness failures at `2791341`; the later 15 test-only join
controls are included in the coordinator's 270-test selection. No hosted CI result applies
to unpublished A, and no simulator or hardware measurement was performed.

## Protected test activation

A's one-file proposal at `docs/reviews/U3-RoPE-runtime-v1/protected-tests.patch` removes the
28 admission skips, updates their pending prose and renames the test. It preserves all case
fixtures and was exercised successfully above. It is suitable to include in the later exact
human activation/adoption decision; **it is not installed or newly approved by this review**.
The live 28 skips remain pending. CLAUDE.md requires agents to propose and stop on contract/;
the existing runtime authorization also explicitly reserves this installation for the human.

## Next bounded task

Send [this prompt to B](lane-B-freeze-preparation.txt). B prepares the combined source/input
freeze proposal and a guarded human-generation helper against A's exact local revision,
using the existing tooling. It may prepare inputs and verify them without invoking rk-sim.
It must reconcile the complete support inventory and preserve nominal v1 fixture semantics:
RoPE is absent from those historical oracle channels and must not be invented there.

A holds its runtime bytes and local commits. Primary continues to track published main.
No need to copy either lane's checkpoint tree or merge source-bound work into published main.
The generated-input manifest is retained for provenance and reproducibility; Git remains the
review/history mechanism for source. Any source change requires reconciliation before freezing.

The coordinator will review B's exact freeze proposal before Javid runs generation twice.
Candidate audit, exact human adoption and protected-test activation, final integrated checks,
and a separately verified main push follow. No old source/input digest may be relabelled current.
Fork-tool choices remain deferred as requested. Reza's runner setup/manual-nightly prerequisite
and independent verification/report integration remain separate pending U3 work.
