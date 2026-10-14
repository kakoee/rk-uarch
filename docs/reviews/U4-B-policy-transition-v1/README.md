# U4 B concrete policy transition preparation

Status: reviewed repair carried forward unchanged, actual first M patch audited in scratch;
**no live policy installation, input staging, oracle generation or adoption**.
D2's policy choice is already accepted. This package asks for release of a concrete future
transition once exact installation inputs are final, not another vote on the selected policy.

The repair remains [the original six-file patch](../U3-B-artifact-dependency-audit-v1/repair.patch),
SHA256 `c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b`.
No copy, redesign or policy exemption is introduced. Its scope is exactly:

- scripts/__init__.py: run the namespace guard before package consumer imports.
- scripts/vendor_rk.py: guarded direct/module/library bootstrap, no pre-guard future import;
  quoted type-only return annotation; full fingerprint changes, oracle program unchanged.
- scripts/u2_inputs.py: guarded bootstrap and explicit policy/legacy public-loader dispatch;
  eager annotation behavior remains the reviewed O1 change.
- scripts/u2_import_guard.py: reviewed normal CPython≥3.12/builtin-sys/frozen-os namespace
  guard, including file/package shadows in root/scripts/src/contract.
- scripts/u2_support.py: conservative import/initializer closure, complete scripts Python
  set, reserved initializers and explicit non-import data families; exact policy matching.
- tests/unit/test_u2_support_policy.py: public-loader, legacy, relevant/unrelated drift,
  shadow-before-body, annotation, origin, synthetic isolated inputs and source-write denial.

[Exact closure delta](closure-delta.json) and [M audit](m-audit.md) bind the observed
published A proposal. [Transition sequence](transition.md) specifies human actions,
expected refusals and recovery. [Handoff](handoff.md) records remaining decisions/checks.
The old source/adopted pair remains intact. Historical U3 receipts and reports are unchanged.

## Actual checks and provenance

Initial export origin: Git archive of `f58e07828fa7a953b06800b227b948d7e9e71a88`.
Combined export origin: Git archive of A's published
`bad9a125d82bbf723675465c9291fb37fa82f799`, then only the exact repair and M patches.
All scratch work stays under this package's disposable scratch/ directory, removed before
publication. No checkpoint tree is retained. In-memory snapshots compare bytes and mtimes;
no whole-tree manifest is published. Relevant support inventory is retained only as artifact
policy provenance in [repair-2.log](repair-2.log) and [m-1.log](m-1.log).

Interpreter: existing `/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python`,
CPython3.12.14. PYTHONPATH/MYPYPATH/UARCH_HUMAN removed; bytecode writes disabled;
pytest cache disabled. Pytest config inserts the scratch root/src/contract; origin tests
and receipts confirm exported modules, not ambient editable modules. No dependencies added.
[Initial command receipts](checks.json), [combined receipts](m-checks.json) and logs retain
exact commands/statuses. [probe.py](probe.py) reproduces initial checks after creating the
named exports; it does not stage inputs or invoke an oracle.

| Check | Observed result |
| --- | --- |
| Required u03-end ancestry, clean main, normal fetch | PASS at baseline; A integrated fast-forward |
| Repair hash and applicability | Exact authorized hash; six paths; applies cleanly in export |
| Pristine strict vendor check | PASS, current source/adopted pair |
| Repair-only strict vendor check | Expected exit1 `vendor-rk: input support inventory changed` |
| All repair-policy plus vendor-entry tests | 108 passed / 1 skipped,44.21s |
| M + repair + vendor-entry tests | 130 passed / 1 skipped,46.84s; includes A's22 prototype tests |
| Combined strict vendor check | Same expected exit1; no historical-mode substitution |
| Whole export bytes/mtime before/after | Unchanged:1685 pristine,1688 repair; combined count in m-checks.json |
| Proposed closure with/without exact M | 56 identical path/digest pairs; not a permanent target |

The one skip is the absent **real human-generated/adopted new-policy positive**. Synthetic
public-loader controls never supply that provenance. U2's current adopted pair is valid;
this is a future migration prerequisite, not an unfinished U2 adoption.

The controls exercise drift after rehashing synthetic input manifests, stripped/unknown
policy, inventory substitution, legacy full enumeration, direct/module/library entry,
transitive and __future__ file/package shadows before marker execution, eager/resolved
annotations, frozen-os/old-Python refusal and root/nested source-write denial. Mutations
remain in throwaway roots; source/export bytes and mtimes are compared. The reviewed U3
fault/restored runs remain historical; this task reruns their normal controls, not those
fault campaigns or any native fault. This is an author audit, not independent adjudication.

Reproduction detail: when exports live inside the clone, set GIT_CEILING_DIRECTORIES to
their scratch parent before `git apply`; otherwise Git-format new-file patches may be
silently skipped because Git discovers the outer repository. The first M apply did that;
inspection caught missing mapped.py, the guarded apply created all19 files, and only that
real combined export was tested/credited. No live source was touched or false first pass
credited. For future reproduction assert expected patch paths exist before any test.
