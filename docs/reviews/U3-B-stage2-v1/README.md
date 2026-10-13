# Lane B Stage 2 bounded handoff

Author response to [B-F1–B-F8](../U3-lane-B-response.md), not reviewer adjudication.
The Stage 1 target is `184d2c2b08c28a01673be143b086ef223ba6706a`; private execution used
`git archive` of that exact target plus the revised unapplied patch. B integrated
published main normally through `d7b00b8`. No coordinator/reviewer tree was copied or
modified. [Exact receipts](evidence.json) distinguish executed work from future gates.

## Patch identity and source scope

[Unapplied repair](../U3-B-artifact-dependency-audit-v1/repair.patch), SHA256:
`4c73d73d1c7ec1e1453e7ef7ccf1bd3de55238a4469069dcaa75e89bc764fa81`.
This supersedes Stage 1's `97d0ec…` proposal, not its receipts. The earlier 30/44-test
results, 52-entry delta, reports and reviewer evidence remain unchanged history in Git.

Only the following source changes are proposed inside the diff, not installed:

- `scripts/u2_import_guard.py`: closed top-level import names/types under ROOT, scripts,
  src and contract. Unknown importable `.py`, `.pyc`, native-extension modules or namespace
  directories refuse, even if only transitively imported by a dependency. The explicit
  reserved repository namespaces are visible in the patch; new names need policy review.
- `scripts/__init__.py`, `scripts/vendor_rk.py`, `scripts/u2_inputs.py`: guard before
  non-bootstrap imports, including fresh direct scripts. Direct scripts establish their
  own package root early; module/library entry does not rewrite sys.path. Guard rechecks
  happen in support inventory validation as well. Direct staging tests use `--help` or
  pre-import refusals only: no input staging is run.
- `scripts/u2_support.py`: retain conservative static closure/data families; additionally
  bind all scripts Python files, reserved module files and existing namespace initializers.
  This is reviewer option 1 plus the small early-bootstrap plumbing needed to prevent a
  shadow body executing before verification. It is not the weaker direct-import guarantee.
- `tests/unit/test_u2_support_policy.py`: explicit isolated roots for every source/data/
  shadow mutation and direct subprocess; actual source/data write denial; public loader,
  fresh-command, origin, legacy/currentness, unrelated-addition and drift controls.

The [new delta](support-delta.json) is **97→56**: 39 retained, 58 removed, 17 added relative
to the unchanged adopted baseline. Four additions over Stage 1: `scripts/u2_import_guard.py`,
`contract/__init__.py`, `contract/tests/__init__.py`, `tests/__init__.py`. There are **no**
Stage 1 inventory removals. Three retained files now change: scripts initializer, input
loader and vendor script. Future M or new script changes may expand the inventory.
No goal of preserving 52 entries influenced this correction.

Nested unrelated report/native/contract consumer files and non-importable Markdown have
positive unchanged-inventory/strict-load controls. An extra `scripts/hooks/*.py` is bound
and refuses the old inventory. A new top-level script name is intentionally refused until
reviewed, even if its author considers it unrelated. This conservative restriction is an
explicit proposed tradeoff, not an accepted policy or a hidden exemption.

## Bootstrap limits and migration effects

The proposed guard uses only normal CPython startup's builtin sys and frozen os before
other imports and refuses an unsupported bootstrap. The current locked CPython 3.12.14
satisfies that premise. Reserved local namespaces are trusted reviewed repository names;
their initializers bind when present. Arbitrary interpreter/startup hooks, hostile external
sys.path/environment, dependency/plugin installation changes, reflection and concurrent
source races are not made safe by this guard. External environment limitations remain
explicit; lock and existing recorded environment checks are preserved. No dependencies
are installed, import guarantee narrowed or environment authority invented.

The embedded `ORACLE_PROGRAM` literal was compared to Stage 1 and is byte-identical.
The **whole vendor script fingerprint changes** because of the proposed bootstrap;
new input/support identities and separately authorized human two-process generation,
complete currentness/semantic audit and adoption are mandatory before real compatibility
can pass. No historical fingerprint can substitute. The [prospective migration text](../U3-B-artifact-dependency-audit-v1/migration.md)
now names the guard/bootstrap, 56-entry delta and vendor-fingerprint effect explicitly.
The unchanged live source/adopted pair still passes strict verification.

## Executed controls and faults

All tests ran in private sources with ambient PYTHONPATH/MYPYPATH removed and explicit
`-c pyproject.toml --rootdir .`. Origin assertions cover scripts, contracts and hardware
imports; fresh subprocesses replace ambient paths with their own src/contract roots.
No fault overlapped a static reader. Existing B environment was reused without installation.

| Check | Actual result |
| --- | --- |
| Tests first on Stage 1 mechanism with isolated roots | 28 failed / 44 passed / 1 skipped: transitive-shadow and complete-script gaps reproduced, plus three deliberately stronger diagnostic assertions |
| Both reported names, public loader | Modules/packages under all four roots refuse `unreviewed import name` before any body import |
| Both reported names, fresh vendor and input-tool commands | Both tools refuse at pre-import guard; no shadow marker body executes on repaired runs |
| Remove only guard body | **32 failed / 53 deselected**; 16 public and 16 command controls discriminate |
| Remove only loader verification call (B-C1) | **4 failed / 81 deselected**, original four drift attacks accepted |
| Restore exact source (before two bootstrap-premise cases) | **82 passed / 1 skipped** |
| Final-code guard/loader/bootstrap fault controls restored | **38 passed / 47 deselected** |
| Final policy, vendor-entry and bounded contract regressions | **135 passed / 1 skipped / 8 deselected** |
| Ruff / mypy production+scripts / mypy contract tests / import-linter | passed / 80 files / 31 files / 2 contracts kept |
| Live strict vendor | passed |
| Prose/math/source checks | current correction passes; Stage 1 and removed correction each fail B-F2/B-F4/B-F7 checks; fixed decode/prefill show both memory-only ops |

When the guard is disabled, complete scripts binding can still refuse scripts inventory
drift **after** imports; that does not prevent body execution in fresh processes. Other
unknown-root public loads can succeed. The 32 test failures must not all be described as
accepted strict loads. The loader-call fault independently preserves its four exact
accepted-attack/DID-NOT-RAISE failures.

Valid fresh controls verify private import origins, vendor `--help`, input-tool `--help`
and `--check --historical`; strict vendor `--check` refuses the unmigrated input inventory.
Historical success is labelled historical, never new-policy currentness. The single skip
is still the real policy-marked human-adoption positive. It becomes a required strict
library success when such an adoption exists; unconditional strict CI also prevents a
legacy artifact silently satisfying the migration. Eight contract cases were deselected
by the exact bounded selection in evidence.json, not passed or waived.

The test fixture copies only scoped support files and required artifact/read inputs into
pytest temporary roots. All fault writes, shadow creation and finally cleanup occur there.
An audit hook refuses write opens/renames/removal/creation/chmod against the actual
source/data trees (interpreter caches excluded); its deliberate write-open control is
refused before mutation. Safety does not depend on finally restoring tracked source.
The live Git source diff is empty. Reviewer files retain their receipt bytes.

Import-linter resolves the existing editable B src/contract roots; they were individually
checked byte-identical to the export. Mypy uses explicit CI targets and repository config.
The authored checker passes all-tree Ruff; no reviewer script was published, altered or
exempted from lint. Early scratch setup/style corrections are disclosed in the receipts.

## Outstanding reconciliation

[Current supplement](../U3-B-readiness-supplement-v1/README.md) now names both memory-only
operators, base-clock C2 premise, row-level U0023 supersessions, exact H-DMA/H-CLOCK text,
independent component bounds, B's proposed CI assignment/effort and distinct finite versus
stationary queue checkpoints. Those shared/human decisions remain pending, as enumerated
in the response; no A-owned text was edited. The original two-op reason code and 22/24
clock result are unchanged. No new corpus, native interface or analytic component API.

Before protected M installation: exact policy/migration review or an explicit decision
to retain U0002 and budget source-bound cycles. A's actual import/initializer/data patch
still needs recomputation, not this conditional note alone. If repair is later authorized,
complete the real two-run human generation, 1008-row/four-refusal complete query/count/
duration/null/attribution comparison, candidate currentness, complete adoption and separate
protected-test activation, then integrated schema/contracts/replay/CI/full-suite checks.
None occurred here. No full-suite, hosted Linux/native job, nightly or performance claim.

Stop for coordinator reconciliation before reviewer Stage 3. These author dispositions
close no finding and imply no installation, human policy, G2 or sprint acceptance.
