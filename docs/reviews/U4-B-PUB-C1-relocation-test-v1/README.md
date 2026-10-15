# PUB-C1 — unapplied relocation-test correction

The exact coordinator preview reproduces PUB-C1. This proposal corrects only
`tests/unit/test_u2_b_tooling_binding.py`; no production or protected change is needed.
The original/reverted positive fails with `ModuleNotFoundError: rkuarch.workload`, while
corrected/restored passes. The complete affected module plus support/lifecycle regressions
passes **137 tests, no skips**. This is a test proposal, not publication or installation of
any human source/adoption history.

## Exact subject

[Reconstruction commands](reconstruction.json) and [identities](identity.json):

- Published preview base: `a6802a344f9f068fef7f1c63fbb72acec876dfc4`.
- Local human commit: `5e774682a7abdc21aa0bac6a8f738e66c852d3e5`, parent
  `0cf24d91eeca5cc45182eb6fb03202677fd97dcb`.
- Original combined tree: `02cff99854337d59086861086f562119940d6e6c`.
- Proposed combined tree, only the test changed:
  `1a053e7b4f2633835e1d77fe1edb1844d78decb8`.
- [Unapplied patch](test-correction.patch) SHA256:
  `64fce5ddcc4e75dcd540e359336d9daad6bb86492162c4044a29a235fa0bef5c`.
- Test preimage SHA256: `efc96c7602d2c18ca47a62cd5f82bbf3974d62caa6cc6103da33492fdfd634e4`.
- Test postimage SHA256: `41acad3e368de53a5f1cf4a433adf4a20956c2d33e1160dc14119b1f3ad1f74a`.

B started at published `3d78ee8f6de22a8b3cb6031cb2d4eabbae820a5a`, then integrated peer
review documentation at `65ddf0cc969bd82ea1f70b12fa2120ab333e90be`. The unpublished human
object was fetched **only into a new private clone**, from the coordinator's existing private
preview. Its merge was left uncommitted and its index tree verified. No fetch, pull, edit,
commit or push was performed in frozen A. The proposed tree was calculated with a separate
private index; the original preview index remains intact.

## Bounded correction

The existing support-only repository still executes strict manifest, snapshot-input,
generator-currentness and frozen-input checks, plus the historical-identity refusal. That
phase proves the selected generator support is sufficient for validation; it does not claim
to contain the consumer implementation.

The relocated **producer-disabled consumer probe** additionally copies twelve explicit Python
files from that same preview source. They supply workload/prepared, analytic, table and
nominal-candidate imports and their initializers/transitive imports. They are a separate
fixture requirement, never entries added to generator support. [identity.json](identity.json)
records the twelve exact paths and hashes; none belongs to the selected 56-file inventory.
The list came from observed private imports, not a copied package/repository tree. A future
consumer import change must explicitly reconcile this fixture list.

The child interpreter now uses `-I -B`, explicit paths rooted at its relocated working
directory, and removes PYTHONPATH/MYPYPATH. Every imported scripts/rkuarch/uarch_contract/
contract module must resolve beneath that directory, expanding the previous two-module
origin assertions. All six oracle/producer denial patches remain active around the strict
checks and input load. Complete candidate bytes are still compared before and after both
copies. The added consumer files must also remain identical to their source.

## Newly executed evidence

| Control | Result |
| --- | --- |
| [Original](baseline.log) / [command](baseline.json) | Expected failure: missing rkuarch.workload; preceding strict checks pass |
| [Corrected](corrected.log) / [command](corrected.json) | 1 passed |
| [Reverted](reverted.log) / [command](reverted.json) | Same expected missing-module failure |
| [Restored](restored.log) / [command](restored.json) | 1 passed |
| [Affected selection](affected-and-regressions.log) / [command](affected-and-regressions.json) | 137 passed, no skips, 108.07 seconds |
| [Read-only strict currentness](strict-currentness.log) / [command](strict-currentness.json) | Current artifact accepted; selected inventory exactly matches all 56 current source hashes |
| [Probe controls](probe-controls.json) | Two positives, six intended producer/oracle denials, foreign-origin refusal and missing-consumer refusal |
| Scoped static checks | Changed test passes Ruff check/format; private one-file diff whitespace passes |

The 137-test selection includes the entire affected module, `test_u2_b_tooling.py`,
`test_u2_support_policy.py`, `contract/tests/test_u2_historical_snapshot.py` and
`contract/tests/test_committed_snapshot.py`. It retains tamper, stale-support, policy,
public-loader, bootstrap, direct-command, historical-integrity and current-adopted-artifact
controls. The producer-denial probe controls execute the exact corrected subprocess code;
the six deliberate calls hit only the replacement denial functions. The foreign-origin
control substitutes module origin metadata; it never imports code from another checkout.
The missing-consumer control removes/restores one file solely in the finished temporary
relocation fixture, and verifies byte/mtime restoration.

Every pytest invocation used explicit config/root and private paths with PYTHONPATH/MYPYPATH,
VIRTUAL_ENV and UARCH_HUMAN unset. Initial project module origins are retained in each log;
child origin assertions cover the relocated consumer imports. Per-run receipts compare all
private source bytes/mtimes before and after. No editable/live source is used as a fallback.

An additional inventory audit initially called the **legacy** `u2_inputs.support_files()`
API and failed its equality assertion before running the CLI. [Initial failure](inventory-launcher-initial.log)
and [command](inventory-launcher-initial.json) are retained. The corrected audit uses
`u2_support.inventory/verify`, then the strict CLI; it passes. This was a B audit-launcher
error, not a production/test-patch failure or reason to expand support.

## Preservation and unchanged inventory

[Preservation](preservation.json) confirms the real 49-file adopted artifact remains identical
to the preview index. Its manifest is unchanged:
`b19016be07307ed987037d8a079f85af0366eab018b1132c2668394acd756bcc`.
The selected inventory still contains **56 files**, byte-identical SHA256:
`c8d4953b44bea66f63d2c192e27e3823a71580083acd4b2cd1704686af674ee9`.
The policy and input-sums hashes are also recorded unchanged in identity.json. Across all
five pytest phases, the temporary synthetic candidate, support-only repository artifact and
relocated artifact have identical complete byte inventories and the same selected-support
bytes. Temporary fixture preparation is synthetic test setup; no oracle, human generation,
staging or real adoption was performed.

The only private source diff is the test. No source trees or whole-repository manifests are
published. Logs remove trailing whitespace only and retain raw-output hashes in receipts;
the exact patch is preserved as a patch. Scratch paths in receipts describe these executions,
not permanent test dependencies.

## Reproduction and coordinator stop

Use a **new disposable clone** whose local donor has the two exact commits. The commands in
reconstruction.json clone without hardlinks, check out the published base, fetch the human
commit into that clone only, and perform `merge --no-commit --no-ff`. Require the exact preview
tree before proceeding. Do not perform this merge in a live lane.

In that private tree, require the recorded test preimage, then use `git apply --check` and
`git apply` with test-correction.patch. Run the recorded isolated pytest command with paths
adjusted to the newly created private root and an absent external basetemp. Reversing the
patch must recover the original failure; reapplying must recover the pass. Run the complete
recorded 137-test selection and strict-currentness check. Require the single-path diff,
recorded postimage/tree, unchanged support inventory and artifact bytes. The probe command
receipts describe the additional independent refusal controls.

Inherited, **not rerun here**: the coordinator's broad selection (1,893 passed, one PUB-C1
failure, 29 skips, ten deselections), full-tree Ruff, both mypy commands, schema freshness and
import contracts. Their inputs/results remain in U4-M-policy-publication-preparation-v1.
This correction does not claim that broad selection has been rerun successfully.

Stop for coordinator reconciliation of this exact test patch, an updated publication preview
and the appropriate integrated checks. Human source/adoption history remains local; any test
installation or source publication requires its separate authorization. K1 Stage 3 proceeds
under its separate handoff and reviewer; this package changes no K1 files or reviewer reports.
No native acceptance, K2, infrastructure work, hosted-CI polling or closure is claimed.
