# AD-M1 — prospective currentness control correction

**Unapplied test proposal; no live installation or adoption.** The coordinator must reconcile
this additional test path with its still-unapproved adoption selection. A was read only through
its frozen Git object and preservation checks; it was not pulled, edited, committed or pushed.
B integrated published main at `e78a413fc83cf29d8a154274db04a94b6a770b2c`, preserving peer history.

The zero-context [test patch](test-control.patch), applied with `git apply --unidiff-zero`, changes only `tests/unit/test_u2_support_policy.py` from
source `0cf24d91eeca5cc45182eb6fb03202677fd97dcb` (tree
`275bcefbe616a049aa6d0a968ff81b5728f0563d`). The frozen production source, generator metadata,
selected support policy, artifact bytes and existing authority receipts are unchanged.
No accepted semantics, environment or licence choice is reopened.
[selection.json](selection.json) binds the exact before/after hashes and patch digest
`c86a85823ecffae979ef0dc096986e1727dc87f0f250ddcb8fe2b146cc5be8cc`. An AST source-segment
comparison confirms that the other 35 existing definitions, including the source-write guard
and real-adoption gate, are unchanged.

The defective test always required the pre-adoption `input support inventory changed` refusal.
Its replacement runs the genuine strict library checks in a fresh process from the **same
isolated source and artifact** used by the direct command. It checks contract pin, manifest,
snapshot inputs and `check_generator(..., current=True)` in CLI order. Strict success requires
CLI exit zero and the exact success output. A strict validation refusal requires CLI exit one
and the exact library reason; unrelated exit codes/messages cannot pass. Imports and origin
assertions run outside the validation exception handler, and subprocess failures or stderr
fail the test. The previous origin, direct help and historical-integrity checks remain intact.
Historical integrity still makes no current-compatibility claim.

Five new discriminating cases cover an added bound data file, corrupted artifact member,
false CLI success, wrong CLI refusal reason, and a library import failure. Mutations are confined
to each test's existing throwaway `isolated_root`. All existing guards, historical controls and
`test_current_new_policy_adoption_requires_strict_validation` remain unchanged.

## Conditional evidence

[verification.json](verification.json) records exact source/patch identities, commands, exits,
source origins and preservation counts; adjacent logs retain observed results. [verify.py](verify.py)
recreates a private Git archive, validates all 49 saved candidate members, conditionally copies
that candidate and applies only the coordinator's exact adoption-bindings patch plus this test
correction. It never invokes staging or generation. The existing proposed review bytes are used
only as part of that exact conditional patch; this package creates no new authority record.

Inputs:

- Saved candidate: `/home/jjaff/AI-infra-simulation/rk-uarch/tables/U4-M-policy-generation-v1/candidate`.
- Manifest: `b19016be07307ed987037d8a079f85af0366eab018b1132c2668394acd756bcc`.
- Coordinator bindings patch SHA256:
  `ed9029f25260abd7b1db21d0bdd3229267315bf22958e447d51a49ac0ad77da4`.
- Existing interpreter: `/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python`.

Baseline/corrected/reverted/restored runs use the genuine compatible candidate. The original
assertion fails with `assert 0 == 1`; the correction passes; reversing the exact patch restores
that failure; reapplying the exact patch restores success. Genuine strict-library currentness
also succeeds independently before these tests.

| Final execution | Observed result |
| --- | --- |
| Genuine candidate strict validation | Pass |
| Baseline / corrected / reverted / restored | 1 expected failure / 1 pass / 1 expected failure / 1 pass |
| Affected conditional selection | 307 passed, 1 staging case deselected, 0 skipped; 195.23 s |
| Prior-artifact complete policy selection | 104 passed, 1 expected real-adoption skip; 36.60 s |
| Prior-artifact strict currentness | Exact `input support inventory changed` refusal |
| Proposed test and review harness Ruff | Pass |

The conditional export retained all 2,024 files with only the proposed test's bytes/mtime
changed; all other bytes/mtimes were unchanged. After restoring the old artifact in scratch,
all 2,023 export files remained unchanged through the prior-policy run. A's 2,022 tracked
files and all 61 saved generation files (candidate plus receipts) retained their bytes/mtimes;
A's HEAD remained the exact frozen commit. Final disposable exports were removed.

The affected selection follows the coordinator's policy, historical-snapshot, public-consumer,
stage2-reference and M-admission selection. One case is deliberately deselected:
`test_historical_guard_refuses_current_canonical_before_candidate` calls `prepare_inputs`.
Its prior result is inherited, not newly executed here. The harness disables `prepare_inputs`,
`run_oracle`, `collect_snapshot` and `publish_snapshot` before test collection. Test-generated
fault copies are not oracle artifacts or adopted outputs.

A second phase restores the exact prior artifact **only in scratch** and reruns the complete
policy selection. Historical integrity succeeds, strict currentness refuses specifically with
`input support inventory changed`, and the unchanged real-adoption gate skips. The conditional
candidate phase's positive gate is not a live skip closure or actual adoption receipt.

An initial expanded run found four new-control setup failures (303 passes): an import-name
guard intercepted a new top-level script, and three mutations hit read-only temporary member
copies. [The retained receipt](initial-control-failures.json) and log record these failures.
The final controls add a bound data file and chmod only their temporary artifact member;
production guards and saved candidate permissions are unchanged. No failure was waived.

Every pytest launch uses explicit `-c`/`--rootdir`, isolated Python, bytecode/cache suppression,
and unset PYTHONPATH/MYPYPATH/VIRTUAL_ENV. The harness asserts imports originate in the private
export. The retained direct-entry fixture supplies its explicit **inner isolated-root** import
paths to its own subprocesses; it never inherits the live checkout's module roots. The strict
library subprocess verifies all relevant module origins and the exact artifact root again.

Reproduce only while A remains at the frozen commit and the saved inputs remain available:

```bash
python3 -B docs/reviews/U4-B-AD-M1-control-correction-v1/verify.py
```

The reproducer writes owned evidence files and temporary exports; it does not install the patch.
Its temporary export is removed on completion. No whole-repository manifests or copied source
checkpoints are published.

## Coordinator stop

Reconcile the exact patch digest and before/after test hashes with the pending nine-path
placement plan. Adding this one distinct test path makes a proposed **ten-path** selection if
all other accepted bytes remain identical. Freeze that combined selection and verify it before
requesting separate human adoption approval. Do not apply this package to frozen A now.

Human generation and the original complete candidate audit are inherited coordinator evidence;
they were not repeated. No live policy/test installation, canonical artifact placement, source
metadata rewrite, staging, oracle execution, adoption, native run, infrastructure operation,
K1/K2 release, hosted-CI result or sprint closure is asserted. The live real-adoption skip remains
open until the actual authorized lifecycle occurs.
