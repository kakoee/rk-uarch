# U3 final local validation after human adoption and activation

Status: local validation passed. Ready for a separate normal-push decision.

Javid's two human commits were verified against their approved parents, trees, messages,
path sets and exact bytes:

- `ed9d7bb02a37ce83e93c9fb6d003553ffeacbdc0`: seven-path artifact adoption.
- `fa8716b07f50ccd56d006293677b08fd292e91fd`: one-path rotary admission activation.

The 28 admission cases are active. The complete strict contract selection now passes
681 tests without skips. The candidate/adopted manifest remains
`1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a`.

## Integration and bounded corrections

A merged published `main` at `1720caf44dff984b7c380f0ffaffa8f460648930` with an ordinary
merge, `314b6a17d15433d8d69a1d86be0e8c5c4aa177f3`. Its 43 incoming paths were coordinator
review documents/scripts. Both human commits remain ancestors.

Two local corrections followed:

1. `92a21ca04904a93783fc4cc369783b276a4c5399` sorts imports in the coordinator's review
   probe after the additive runtime became available. One documentation script changed.
2. `3a148a0bc953ad0a536de1934184ba9e313e544d` repairs two legacy CLI refusal tests whose
   setup assumed the natural order of comparison hashes was noncanonical. Adoption changes
   those hashes. The tests now start from canonical inputs, explicitly swap recipe indexes
   for the wrong-index attack, or omit a supplied comparison for the omission attack.
   Both original refusal messages, no-output checks and artifact-preservation assertions
   remain. The two tests failed before the correction and pass afterward.

Neither correction changes runtime code, protected paths or adopted artifact bytes.
All 97 frozen support files still match both `187fe3b` and the adopted inventory.
No regeneration or new adoption is needed for these two changes.

The full-suite target is `3a148a0bc953ad0a536de1934184ba9e313e544d`, tree
`24f1a418ea052d1400c89c38b1968d142d0f829e`.

## Final result

Full suite: **1,701 passed, 29 skipped, zero failures/errors**, 822.16 seconds.
The 29 skips are the existing analytic capability/precondition cases; no rotary admission
case is skipped. All ten required checks also passed on the tested revision.
See the [full log](full-suite.log) and [structured result with every skip reason](full-suite.json).

## Evidence

- [Human commit verification](human-checkpoint-verification.json)
- [Integrated history](integration.json)
- [Environment and tested identity](tested-tree.json)
- [Required checks and their outputs](required-checks.json)
- [Initial coordinator lint correction](integration-correction.json)
- [Hash-order test correction](hash-order-correction.json)
- [Interrupted run with the two test-setup failures](interrupted-hash-order-run.log)
- [Source preservation, changed paths and conditional CI job inputs](scope-check.json)

The first interrupted run completed 13 tests before stopping for the lint correction.
The second completed 547 passes and two setup failures before stopping for the test correction.
Neither interrupted run is a completed full-suite result.

Local checks use A's Python 3.12.14 environment on ElfinKidsLaptop Ubuntu/WSL2, with
`PYTHONPATH` and `MYPYPATH` unset. Required checks include Ruff, both CI-form mypy commands,
import contracts, both contract schema families, both engine schema families, direct strict
vendor verification and all contract tests with `--require-vendor`.

## Scope limits and next action

This is local software validation. Hosted CI has not run on these unpublished commits.
The golden, determinism, native, patches, perf and prediction-ordering conditional CI jobs
currently have no matching inputs; their no-op status is not runtime evidence. Licence tests
are part of the full pytest suite.

Historical evidence remains historical. No new full 1,008-point workload run or physical
RoPE oracle parity is claimed by this check. The approved artifact lifecycle preserved the
existing oracle values and explicitly absent RoPE channels.

The complete integrated suite passed. The [separate publication decision](next-decision.md) proposes a normal push,
preserving all human and lane commits. No force push, branch deletion, generation or
artifact adoption is included. Afterwards the primary clone can fast-forward to the same
published revision and hosted CI can be checked on that exact commit.

Independent review, public v2 product/report integration, fork/tool decisions, the Linux
runner/manual nightly, hardware validation and U3 closure remain outside this checkpoint.

This record is committed separately and merged into A after validation. That final merge
adds only files in this review directory; runtime, tests, schemas and adopted inputs remain
byte-identical to the tested revision. The final merge SHA is reported with the publication
request. No full-suite rerun is claimed for that documentation-only merge.

The saved interrupted traceback trims trailing whitespace on blank lines for Git hygiene.
