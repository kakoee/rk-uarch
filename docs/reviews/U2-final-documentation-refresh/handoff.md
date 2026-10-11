# U2 fresh documentation session handoff

Proposal only for published commit `7fee0a8ed0c5d7bbb20b65c1cf68672470a5ac60`, tree
`deccb57a573717990762e60fb8819f0ae463ce20`.

- [Proposed narrative](proposed-how-it-works.md); [exact diff for docs/how-it-works.md](how-it-works.patch).
  The live document is unchanged. The patch applies to the published bytes and reconstructs the proposal exactly.
- Replaces active unpublished/v2-failure claims with v3 currentness and attributed completed publication validation;
  preserves both reviewers' original scoped verdicts. Explains H1/H2, C0/STUB, conditions, unknown error,
  unverified energy, nominal/physical separation, CI no-ops and U0021's host limits.
- Independently reproduced the real-reviewed public demo from published inputs in a private clean export:
  fresh capture matched all reviewed input bytes; two fresh table/report runs and producer-disabled saved replay
  matched 61 files / 36,707,563 bytes per run. Both negative producer controls refused as expected.
  Default/opt-in display checks passed. No independent approvals were generated.
- Real H1 row: decode batch 1, context 128, BF16, tp1, duration/U-C0 `0.015038327296 s`, **STUB / unknown error**,
  conditional on 59 stipulations, energy unverified. Table hash `sha256:d55dfc66a0d33aff209a82353eba7e5316db20eb8cb51d56c9d6ab75124ba6be`;
  complete-row digest `sha256:e2f0c393c09b90c0a3ff7761d7b2e6b529a493b4830032a8562138d860843467`.
- Also ran strict `vendor_rk.py --check`, manifest hashes, hardware inventory summary, 14 focused regressions,
  all remaining embedded command blocks, publication-content file-link validation, patch check and private-document
  patch reconstruction. See [command/result evidence](evidence.json), [document checks](document-checks.json),
  [focused results](focused-tests.log), and [preservation](preservation-after.json).

The 1,394-test full suite, same-commit hosted CI, full matrix, H2 characterization and pinned-loader results
are **coordinator receipts read and cross-checked**, not new executions in this documentation session.
No full suite or matrix was rerun. All required final receipts were present and complete; the earlier
case-dispositions pending qualifier and historical B64 ledger remain as recorded, without blanket promotion.

Reproducibility detail: the historical demo driver is not directly portable because it assumes ignored inputs,
local paths and an old tree. The proposal supplies an executed fresh-capture/path adaptation, reconstructs only
the exact reviewed singleton registry, and verifies all input bytes plus existing review hashes/subjects before
reuse. No reproducibility gap remained for this bounded demonstration. Its scope does not replace the matrix;
full-matrix administrative reviews remain synthetic. Generated output trees remain in temporary storage and
were not copied here.

The post-publication receipts are local coordinator files, absent from the reviewed commit. The proposal labels
them accordingly and provides an explicitly local receipt-reading command. Coordinator reconciliation must retain
or publish those receipts separately; a clone alone cannot reproduce their inspection. The existing execution-plan
STATUS and historical inventory/driver wording were not edited. No real measurement/history eligibility,
nonempty energy verification, physical full-workload duration or silicon validation is claimed.

Main, A, B and integration HEADs, indexes and tracked source bytes match the entry snapshot; code, fixtures,
contracts, ADRs, review reports and live documentation are unchanged. The private source export is unchanged.
Only this proposal directory was written outside temporary storage. No agents, commit, push, tag, oracle generation
or adoption, branch movement, worktree removal or sprint closure occurred.
