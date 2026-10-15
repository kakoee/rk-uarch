# Human checkpoint verified; publication held on PUB-C1

The human commit `5e774682a7abdc21aa0bac6a8f738e66c852d3e5` has the exact approved parent,
tree, message and ten paths. A's HEAD/index/worktree are clean. [Human receipt](human-commit-receipt.json).
No push from A or live merge was performed by this preparation.

A private clone combines that human history with published `a6802a3` without conflict.
[Identity](identity.json) records the exact integration tree and change scope. The preview
has no merge commit; it is a testable tree, not a published state. Tests and static tools
use that private source with verified import origins and unset ambient Python paths.
No source or dependency installation is performed in a live lane.

[Static checks](static-checks.json) record full-tree Ruff, both CI mypy commands, strict
artifact currentness, base/rotary/mapped schema freshness and both import contracts.
The initial import-check launcher used an invalid entry-point indexing API and failed;
the corrected launcher passed. Both diagnostics are retained, not treated as code failures.
The CI Python selection completed locally: **1,893 passed, 1 failed, 29 skipped,
10 deselected**, exit 1, in 908.95 seconds. [Full result and timings](full-suite.log).
The skipped cases are analytic capability limits, not a skipped human adoption.
The strict-currentness and real-adoption controls passed in this selection.

**PUB-C1 holds publication.** The old test
`test_same_candidate_survives_adoption_and_fresh_layout` constructs a checkout using only
`support-files.json`, then imports consumer modules to block their producers. Under the
new selected-dependency policy those modules are not all part of generator support. The
subprocess fails with `ModuleNotFoundError: rkuarch.workload`; the preceding strict checks
pass. A separate one-test rerun reproduces the failure in 1.64 seconds
([traceback](lifecycle-repro.log)). This identifies a test-environment assumption; it does
not authorize widening support or weakening the relocation/no-producer guarantee.

[Bounded B follow-up](lane-B-lifecycle-test-followup.txt) requests an unapplied test-only
correction, independent private origins and retained controls. The human checkpoint is
preserved; no production/test fix was installed. No publication approval is requested yet.
Logs are copied with trailing whitespace removed only; raw-log SHA256 values are recorded.

[Conditional CI inputs](conditional-job-inputs.json) distinguish empty golden, determinism,
performance and frozen-prediction jobs from executed checks. Remote/native CI remains
deferred under U0024. No native/K1 correction is part of this integration; no new native
correctness, performance, full G5, K1/K2 acceptance or closure follows.

[Proposed publication](next-decision.md) uses the normal merge direction detailed in
[merge-direction.json](merge-direction.json): merge published review documentation into A,
then normally fast-forward origin/main. This preserves the human protected-file commits
without asking an agent to create another protected-file change or bypass hooks.
New peer work must be inspected before publication; only review-only additions may reuse
the tested implementation result. Publication remains unapproved until Javid's decision.

[Preservation](final-preservation.json) confirms the test preview still matches its index
and A remains clean at the human commit. During testing, main advanced to B's
`3d78ee8f6de22a8b3cb6031cb2d4eabbae820a5a`, adding only K1 review preparation files.
The coordinator fast-forwarded that documentation; these local test counts still identify
the earlier preview exactly. B's separate K1 handoff matches the prepared twelve-path review
tree and patches, so its same-reviewer Stage 3 may proceed independently of PUB-C1.
