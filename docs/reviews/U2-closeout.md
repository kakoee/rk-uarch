# U2 closeout acceptance

**Status: technical exits and closeout accepted by Javid; final documentation publication and tagging pending.**
Accepted decision: **U2-closeout-v1**, recorded in the [approval receipt](U2-closeout-acceptance.json).
This acceptance applies to published
implementation `7fee0a8ed0c5d7bbb20b65c1cf68672470a5ac60`, tree
`deccb57a573717990762e60fb8819f0ae463ce20`. It does not claim a
closeout commit/push, `u02-end` tag, cleanup, U3 start or G2 decision. Javid acts for both
U2 lanes; no Reza approval is claimed.

## Delivered and accepted scope

The [accepted U0003 S decision](U2-U0003-acceptance-record.md) separates physical resolved
operator correctness/replay from test-only nominal aggregate compatibility. The
[accepted U0004/H1/H2 decision](U2-B1-acceptance-record.md),
[bounded proof decision](U2-B-proof-implementation-acceptance-record.md) and
[design index](../u2-design.md) remain authoritative. No thresholds, hardware values,
schema, supported scope or evidence policy changes are proposed here.

U2 supplies sourced/stipulated H1/H2 hardware inputs, component truth/export and derivation,
standalone rank-local workload preparation, analytic aggregate/per-op execution, hashed
tables, honest HTML/Markdown reports, and authenticated prepared/captured-input replay.
The [current narrative](../how-it-works.md) includes a reproducible H1 analytic row with its
complete-row and table hashes, conditions, STUB label, unknown error and unverified energy.
TPU v5e and Blackhole p100a remain accepted draft references, not complete physical specs.

## Publication, artifact lifecycle and reviews

Main-only publication is verified in the [execution receipt](U2-main-publication-v1/execution.json).
The [four local checkpoint receipts](U2-final-local-checkpoints-v1/commit-execution.json) and
[coordinator verification](U2-final-local-checkpoints-v1/coordinator-commit-verification.json)
identify A/B's shared software snapshots and integration's source/adoption commits. The
current A/B branches stay local; their worktrees and unselected local work remain preserved.
Uncommitted files are not protected by Git history.

The upstream pin remains `1e5706e0ebfcc67c1a7333079a35b75f693e9963`. The adopted v3
48-file manifest is `20eee19b0e864ad07a7b122da7544e385116fdd50d279e1fac1bfbbf03a697ad`;
the frozen input manifest is `08d0e905cc50943d286b9c6dbcfb2cf844c969dda28b9446162d12734870871c`.
[Human generation](U2-real-generation-v3/created.log),
[second-run identity](U2-real-generation-v3/verified-identical.log),
[audit](U2-artifact-adoption-v3/audit.json), [adoption approval](U2-adoption-v3-execution/acceptance.json)
and [complete placement](U2-adoption-v3-execution/acceptance-and-placement.json) preserve
U0002's lifecycle. Earlier v2 bytes remain reachable in Git. No refresh or artifact edit
is part of this documentation proposal.

Both original three-stage software review loops are **ACCEPTED** on review tree
`53f9f21b7cc3f84c0cbdb5f3f1e74e6e4aeca522`; see unchanged [A](U2-lane-A-review.md) and
[B](U2-lane-B-review.md) reports. That acceptance is not relabelled as independent review
of later adoption/documentation. Subsequent coordinator evidence supplies the explicitly
deferred exit gates:

| Deferred exit | Evidence now available |
| --- | --- |
| A-F1/B-F3 currentness, cold clone and hosted CI | [U0021 final verification](U2-published-validation-v1/final-verification.json) and [CI scope](U2-published-validation-v1/ci-summary.json) |
| A-F3/B-F6 real-reviewed public workflow | [Published-revision public demo](U2-published-validation-v1/public-demo/result.json), exact reviewed input reproduction, both fresh/replay runs and producer traps |
| A-F7/A-F8/B-F7 commands, normative links and narrative | Published design/workflow selections plus [fresh-session handoff](U2-final-documentation-refresh/handoff.md), its 14 focused tests, command reproduction and link checks |
| B-F1/B-F2/B-F8 installed model-card/contributor/display fixes | Named committed regressions in the 1,394-pass suite; original independent response/revert adjudications preserved |

This coordinator reconciliation does not edit original reviewer verdicts. The fresh
[documentation session](U2-final-documentation-refresh/session.json) separately executed
the standing refresh, reconstructed the public demo and quoted row, ran 14 focused tests,
checked 41 links, and left source/HEADs/indexes unchanged. The coordinator's additional
publication edits only move receipt inspection to repository-relative paths and reconcile
current status; the [bounded delta](U2-closeout-preparation-v1/documentation-reconciliation.patch)
is preserved separately from the original proposal.

## Published-revision validation

[U0021](../decisions/U0021-u2-cold-clone-validation-exception.md) was executed on a fresh
GitHub clone of the exact main commit, detached, with clean initial/final Git state on
ElfinKidsLaptop Ubuntu/WSL2. The virtual environment and caches were new; the recorded
CPython 3.12.14 base interpreter was reused. [Commands](U2-published-validation-v1/checks.json),
[environment](U2-published-validation-v1/environment.log), [module origins](U2-published-validation-v1/module-origins.json)
and [complete verification](U2-published-validation-v1/final-verification.json) bind this claim.

- **1,394 tests passed**, zero failures/errors/skips. Lint, both strict type checks, import
  contracts, schema freshness and strict current vendor verification passed.
- All **25 full runtime phases passed**: 1,008 nominal calls, 96 physical points and six
  preparations; 24 report rows, 40,320 comparison paths and 59 H1 stipulations.
- Six repeated report/spec files were byte-identical. All **3,316 saved-input package/report
  files** were byte-identical with producers disabled. All three capability substitutions refused.
- All 9,962 output members verified; manifest
  `8fbc26b677aed6531eb74711108a3a94bcb98d02ade7431155ae18740ea2ee41` matches the earlier
  committed local run. Large generated outputs remain outside Git.
- The actual-reviewed eight-point public CLI demo reproduced 61 files / 36,707,563 bytes
  across fresh/repeat/saved replay and matched the earlier committed output identities.
- H2/70B/FP8 tp8 characterization passed with explicit synthetic assignment. A separate
  isolated test round-tripped the public H1 export through the exact pinned upstream loader;
  this did not execute the oracle or add a production rk-sim dependency.

[Hosted Ubuntu CI 38101625804](https://github.com/kakoee/rk-uarch/actions/runs/38101625804)
passed on the same commit: 1,394 Python tests, 579 contract tests and two licence tests,
plus static/currentness/schema checks. Golden, determinism, native, perf, ordering and
only the patches step were conditional no-ops. Licence tests did run. Actual U2 byte
repeat/replay checks ran in the WSL2 clone; CI no-ops grant no corresponding coverage.
The [full validation report](U2-published-validation-v1/README.md) retains those distinctions.

## Limits, case reconciliation and U3 carry-forward

Passing these checks does not validate silicon or physical full-workload duration. Nominal
aggregate compatibility passes with unchanged budgets; physical results retain **96 executed
discrepancies, 48 capacity failures and 864 not-run cases**. Four earlier precision-refusal
observations per track remain preserved, not freshly generated. Default reports hide all
40,320 comparison magnitudes; opt-in shows 18,768 labelled STUB values. Errors remain
unknown and energy unverified. Actual AI declaration reviews apply to the eight-point
standalone demo; full-matrix administrative packaging reviews remain explicitly synthetic.

[Case-specific reconciliation](U2-published-validation-v1/case-dispositions.json) supplies
named R202/C04/C06/C07/C09/C10 evidence. B-F16's accepted precision/export/adapter scope
has technical and actual lifecycle evidence; it is not a physical-accuracy claim. B05 real
history/measurement eligibility and S10 nonempty energy verification remain unsupported
under the accepted bounded decision. Historical B64 56/eight and other namespaces are
not rewritten into a blanket all-cases-passed claim. No missing HardwareSpec, measurement,
family relation or positive evidence eligibility is invented to close a case.

U3 remains unstarted. Before U-P5, establish the designated Linux host, register its
self-hosted runner and re-enable/test the nightly schedule. U0021 does not approve WSL2
for simulator-performance benchmarking or waive later hardware validation. Fork/native,
multi-worker/thread and later detailed mapping/energy/measurement work retain their sprint
ownership. **G2 is U3's fork gate, not U2 closure.**

Javid requested separate A/B working folders against main for U3, with each lane committing
and pushing to main and integrating upstream changes on demand. Use ordinary Git commits,
diffs and synchronization; do not carry forward manual checkpoint-tree copying. Never
force-push shared main or rewrite published history. Provenance/reproducibility manifests
remain appropriate for generated artifacts. This records the preference, not U3 start.
Actual human engineering hours and the retrospective are **unreported**; estimates and
agent elapsed time are not substituted for them.

## Decisions and remaining publication steps

Javid accepted **U2-closeout-v1** with the reply `approve`: the completed technical exits,
explicitly bounded limitations above and the reviewed documentation/evidence selection.
The approval receipt binds the exact proposed Git tree; it does not reuse earlier publication
authorization or authorize the separate actions below.

Acceptance is recorded. The exact final local documentation commit is prepared separately
for execution approval. Keep commit execution, its push and verification, and `u02-end` tagging separate.
The final tag must name the tested approved result on main. For a documentation-only
closeout commit, verify production/test/support identity to the validated implementation,
check changed commands/links and obtain that final commit's hosted CI; document the scope
of inherited runtime evidence rather than calling it a new same-commit matrix run. Any
runtime/support change requires renewed applicable validation and artifact lifecycle checks.
Keep worker worktrees until final publication is verified; deletion/cleanup requires its
own explicit authorization. No cleanup or tag is part of this proposal.
