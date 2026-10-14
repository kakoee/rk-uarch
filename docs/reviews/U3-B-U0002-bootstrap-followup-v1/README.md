# Separate U0002 O1/O2 proposal follow-up

Both scoped U-REVIEW Stage 3 responses remain **ACCEPTED**. This author follow-up addresses
separate policy observations before Javid's decision; it does not reopen B-F1–B-F8 or A's
review, accept a new patch, install policy, authorize migration or release native work.
The accepted response, all earlier receipts and reviewer/coordinator files are unchanged.

Started clean and normally integrated origin/main at
`40fab28bc73ed1f7898a0950979607cfd0368c12` (already current). Read CLAUDE.md, CODEOWNERS,
U0002, the existing migration proposal, and these files read-only under the **primary**
`/home/jjaff/AI-infra-simulation/rk-uarch/docs/reviews/`:
`U3-lane-B-review.md`, `U3-independent-review-B-stage3-v1/receipts.json`,
`U3-stage3-coordination-v1/B-verdict-receipt.md` and `B-future-observation.json` in that
last directory. [Evidence](evidence.json) binds their exact full-file hashes before/after;
no reviewer scripts or trees were copied into this handoff.

## Exact proposed change

The [full unapplied repair](../U3-B-artifact-dependency-audit-v1/repair.patch) now has SHA256
`c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b`.
Its reviewed predecessor at `40fab28` remains in Git, SHA256
`4c73d73d1c7ec1e1453e7ef7ccf1bd3de55238a4469069dcaa75e89bc764fa81`.
The [exact three-file delta](proposal-delta.patch) applies **after** that predecessor,
SHA256 `eac5a0e20d01a2a6a2987665825a731da2b636517a4f342a1c4a1bbfc785426e`.
It is a review diff, not a second installed source tree. Applying this delta to the old
private proposal produced byte-identical source to the new full patch. Full-patch
`git apply --check` passed against current unchanged main. Neither patch was installed live.

- `scripts/vendor_rk.py`: remove the leading future import; explicitly quote the return
  annotation on `validate_u2_component_inputs`, whose ComponentPrecision is type-checking-
  only at module scope. No function body, CLI operation or oracle constant changes.
- `scripts/u2_inputs.py`: remove the leading future import. All runtime annotation names
  are already imported/defined before their use; no additional imports are necessary.
- `tests/unit/test_u2_support_policy.py`: extract the existing denial hook into a context
  manager with explicit root, retaining the autouse fixture. Add `resolved.parent == root`
  to its refusal condition, preserve named source/data protections and the existing
  interpreter-cache exclusion, and disable each hook on context exit. Add two root-file
  probes, twelve future-shadow cases, one annotation control and the guard-module origin
  assertion. All mutations stay in temporary roots; no new runtime enforcement is proposed
  by this test-only audit hook.

The full repair still has its original six-file scope. Import guard and support-policy
modules themselves are unchanged; no inventory exclusion, public-loader dispatch, legacy
validation, fingerprint check, dependency, contract or accepted policy is altered here.

## O1: prevention before the shadow body, with explicit annotation consequences

Reproduced the observation with a harmless stderr marker and `annotations = None` in both
`scripts/__future__.py` and `scripts/__future__/__init__.py`, in per-test private roots.
Both direct scripts printed the marker and only then refused under the old proposal.
Eventual refusal is insufficient. Module/library entry already guarded package imports;
those positive refusal controls passed before the correction and remain required.

A future statement is also a runtime import. On the locked CPython 3.12 interpreter its
compiler flag postpones annotation evaluation, but its IMPORT_NAME/IMPORT_FROM still
resolves `__future__`. Moving it after the guard is not a valid fix: Python requires future
statements before ordinary executable statements/imports. Removing it eliminates this
pre-guard search; only the unchanged builtin-sys/frozen-os bootstrap precedes the guard.
No name-specific exemption, trusted shadow execution or post-execution detection is used.

This deliberately changes raw annotation storage on the tested interpreter: ordinary
function/class annotations now evaluate after guarded imports; Inputs' entries annotation
becomes the actual tuple generic instead of a ForwardRef. `get_type_hints(ui.load_inputs)`
and `get_type_hints(vendor.validate_u2_component_inputs, localns=...)` resolve the intended
same types. The quoted vendor return avoids evaluating its type-checking-only name; it
adds no eager contract import. These consequences are tested and presented for review,
not hidden as an annotation-preserving reorder. No consumer/carrier schema is changed.

Each shadow case first runs a fresh valid control, then requires **absence of the marker**
in both output streams and the intended `unreviewed import name: scripts/__future__...`
refusal. Covers two scripts × direct/module/library × file/package shadows. Fresh library
controls assert exact private module paths; prior direct/module vendor tests also preserve
library sys.path/root behavior. `--help` is the only new CLI action; no staging/producer runs.

Bootstrap limits remain the existing proposed normal CPython >=3.12, builtin sys/frozen os,
trusted startup/environment and reviewed local namespaces, without concurrent source races.
Executed interpreter: CPython 3.12.14, existing locked environment. Unsupported-bootstrap
refusal controls still pass. This is not an expanded interpreter support claim or protection
against hostile startup hooks, arbitrary code/reflection, modified trusted bootstrap code
or external dependency installation. No new environment assumption substitutes for a check.

## O2: additional test defence, not a finding of normal source mutation

Original per-test isolation worked, as the accepted review records. The new tests configure
that same hook for a throwaway root, created outside the real export, and attempt creation
of an absent root file or overwrite of an existing root file. Both must raise before the
write: absence remains absence, or original bytes **and mtime_ns** remain identical. While
the hook is active, writes/reads/deletion in a different private temporary root still work;
read-only access to protected data remains allowed. Previous nested source-write and
source/data/shadow-isolation controls are retained.

Disabling only the new immediate-root predicate makes these two tests fail with
DID NOT RAISE; the deliberate writes land only in their throwaway roots. No isolation fault
points at the author's or coordinator's checkout. The hook still is test defence in depth,
not an OS sandbox against pre-opened descriptors, native syscalls or arbitrary hostile
code. No normal test now depends on finally restoring a real source file.

## Executed checks, before/fault/restored

All credited tests/statics ran sequentially in disposable `git archive` exports with only
the proposed patch applied. No fault overlapped static readers. Command executable prefix:
`/home/jjaff/AI-infra-simulation/rk-uarch-u3-b/.venv/bin/`; reproduction environment prefix:
`env -u PYTHONPATH -u MYPYPATH -u UARCH_HUMAN PYTHONDONTWRITEBYTECODE=1`.
Pytest prefix: `python -B -m pytest -c pyproject.toml --rootdir . -p no:cacheprovider -q --tb=short`.
PYTHONPATH/MYPYPATH were cleared in every run; UARCH_HUMAN was never set and was also
explicitly removed by the regression/static orchestrators. Exact selections and result
summaries are retained in evidence.json.

| Execution | Actual result |
| --- | --- |
| Tests first, old mechanisms: `-k 'future_shadow or root_file_write'` | 6 failed / 8 passed / 85 deselected: four direct marker executions and two missed root denials |
| Annotation control before removal | 1 failed / 99 deselected: original ForwardRef storage, explicit proposed change |
| Initial correction/origin controls | 16 passed / 84 deselected |
| Policy + vendor-entry + bounded U-P2 regression selection | **150 passed / 1 skipped / 8 deselected**, 37.57 s |
| Reinsert future statements before os in both entry scripts; `-k future_shadow` | **4 failed / 8 passed / 88 deselected**; direct file/package markers execute; module/library remain protected |
| Remove only immediate-root predicate; `-k root_file_write` | **2 failed / 98 deselected**, both DID NOT RAISE in throwaway roots |
| Remove only public `load_inputs` new-policy verify call | **4 failed / 96 deselected**, retained drift attacks accepted |
| Restore exact bytes; new controls + previous public/fresh shadows + loader attacks/origins/write guard | **53 passed / 47 deselected**, 17.44 s |
| `ruff check .` | PASS |
| `mypy src contract/uarch_contract scripts` | PASS, 80 files |
| `mypy --no-explicit-package-bases contract/tests` | PASS, 31 files |
| `lint-imports` | PASS, 101 files/600 dependencies, 2 kept/0 broken |
| Pristine private export `python -B scripts/vendor_rk.py --check` | PASS, current unchanged source/artifact pair |
| Proposed private export, same strict command | Expected exit1: `vendor-rk: input support inventory changed` |

Both normal runs (150 and restored53) compared **all 1,516 export files** before/after:
no creation/removal, changed bytes or changed mtime_ns. Deliberate fault edits/restores
occurred between those runs and are not described as mtime-preserving. Snapshots were
in-memory comparisons; no whole-tree manifests/checkpoint copies are retained.

In-test origins include scripts ui/policy/vendor/guard, derive and uarch_contract from the
export. Fresh children replace ambient paths with their own src/contract. Import-linter's
editable src/contract roots were verified byte-identical to the export (119 Python files).
The first Ruff attempt found one extra blank in the added origin imports; removing that
blank was the only post-regression formatting edit. Origin test then passed (1/99), followed
by all final statics. No semantic change or unreported suite rerun is implied.

The single skip is the **absent real policy-marked human adoption positive**. The current
completed U2 artifact lifecycle is not pending: pristine strict verification passes. A
new-policy artifact for this uninstalled proposal does not exist. Synthetic rehashed
controls do not supply that provenance, and historical integrity cannot supply currentness.
Eight deselections retain the earlier bounded scope: default parity1, matrix-inventory4,
Git index/ignored-path3; these unchanged tests were not credited. No matching cases exist
for the selection's inherited f7_environment_record/f8 exclusions. Full integration and
real-migration tests remain later. No full suite, hosted CI, native/host/nightly execution,
producer/input staging, oracle, generation/adoption or performance measurement occurred.

## Inventory, fingerprints and remaining decision

Support paths remain **56 → 56**, no addition/removal. Relative to installed complete
support the proposal remains97→56, with the previous review/history untouched. Only two
bound file digests change in this follow-up:

| Bound file | Old proposal SHA256 | Revised proposal SHA256 |
| --- | --- | --- |
| scripts/vendor_rk.py | e18e6fce2dfdaca3cd6a3fd39af9e148797be1c575677c3adaf9128b14e5ae51 | b82ae570dee99466389d609051425c501022d1ebf2efb03a2bc67a27a27c1b76 |
| scripts/u2_inputs.py | 56a4695055dbb1498787c9bdc7824980ee236e058d6daedb992808340be1b9bb | eb68cb3d6e09dae9ff7310c65d767d30785df838e347d3389d531250493a44ff |

The whole vendor-script fingerprint therefore changes again and **must** bind any future
approved generation. Tests are not in that proposed support closure; their changed source
hash is in evidence.json for recheck. Embedded ORACLE_PROGRAM is byte-identical across
pristine, old and revised proposals, SHA256
`bca579505e96e3f105d4442e7b6c52c3cbe87316edde3ea896692abceb90993b`.
All 55 historical artifact/provenance files compared equal. No adopted input digest is
reused, rewritten or claimed current for the new proposal.

Javid's exact alternatives remain:

1. After the same B reviewer checks this **bounded O1/O2 delta**, accept/revise the exact
   narrower U0002 policy and revised patch, including the disclosed annotation behavior
   and existing bootstrap limits. Any installation task is separately released. Before M
   installation reconcile A's actual imports/initializers/data; future source/input freeze,
   human two-process generation, complete old/new semantic/provenance audit and complete
   adoption need separate authorization. No old acceptance approves those actions.
2. Retain current U0002 complete enumeration/enforcement; do not install this repair.
   Budget coherent source-bound human lifecycles at required M/K2/B checkpoints as previously
   proposed. No support/currentness waiver and no assumption of a fixed future M inventory.

If raw postponed annotation storage itself must be retained, simply moving the future
statement is invalid; a separately reviewed guarded-wrapper/implementation split would
need a different exact source/dependency proposal. That broader alternative is neither
implemented nor silently accepted here. The recommended bounded correction needs no new
dependency or interpreter policy. Policy choice remains Javid's, without claiming Reza's approval.

Requested recheck is limited to the exact delta, O1 marker prevention/valid forms/annotation
semantics, O2 denial and normal byte/mtime isolation, retained public/shadow/origin controls,
revert/restore discrimination and fingerprint/currentness consequences. Earlier accepted
responses and A's review need no restart. Stop for coordinator reconciliation; no finding,
human policy, installation/migration, G2 or sprint acceptance is declared by this author.
