# U0002 dependency audit and unapplied migration proposal

**Stage 2 revision:** [B-F1/B-F8 response](../U3-lane-B-response.md) and
[bounded evidence](../U3-B-stage2-v1/README.md) supersede the mechanism and patch bindings
below. The unapplied patch now proposes closed import namespaces, early command guards,
complete scripts binding and isolated mutation tests. Its baseline inventory is **56**,
not the historical 52; original inventories/results remain unchanged historical evidence.
The current patch also changes the proposed vendor bootstrap and package initializer,
so its full script fingerprint needs the normal separately approved human lifecycle.

**Correction:** [B-C1/B-C2 follow-up](../U3-B-dependency-audit-correction-v1/README.md)
updates only the unapplied patch tests and supplies its new SHA256. The execution receipts
and `evidence.json` below remain historical for the original `a602683` patch; they do not
claim coverage of the later public-loader fault. Policy/inventory proposals are unchanged.

**Author audit/prototype, not independent review or permission to install.** This executes
the bounded task in [proposal v1](../U3-artifact-dependency-repair-proposal-v1/README.md)
and its [v2 deadline](../U3-artifact-dependency-repair-proposal-v2/README.md).
Javid decides the exact policy/migration **before M's protected mapped-carrier installation**.
The live clone still uses unchanged U0002 enforcement and its adopted artifact. No oracle,
input staging, generation, adoption, upstream checkout/fetch, installation or protected edit
was performed. Tests used B's existing interpreter and a disposable Git export of the
published source; no checkpoint copy is retained in this package.

## Bindings and result

- Audited commit: `30812dfc322b742b81521e350d7d5b541221ca0d`; exact tree in [evidence](evidence.json).
- Adopted manifest: `1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a`.
- Input manifest: `27c6238d42e57dc4f2b1baf0c8846c11f1eec2968176dcefcdc463beb64bc80f`.
- Upstream remains `1e5706e0ebfcc67c1a7333079a35b75f693e9963`; upstream lock remains
  `d984e55723326751ac3f888712f98462a525315ad4693691dbc3f2f5dc7f577c`.
- [Exact unapplied code/test patch](repair.patch), [support delta](support-delta.json),
  [executed evidence](evidence.json), [proposed policy/migration](migration.md).

The candidate mechanism reduces this baseline's support inventory from **97 to 52**:
39 retained, 58 removed, 13 added. This is an audited proposed dependency policy, not a
claim that fewer bytes happened to produce equal oracle answers. Only `scripts/u2_inputs.py`
changes among the retained files; the new helper is itself bound. The complete generator
script and embedded oracle-program fingerprints remain enforced without exceptions.

**Migration is required.** The exact patch deliberately refuses current compatibility of
the existing unversioned 97-entry artifact: `input support inventory changed`. Historical
integrity/recorded identity and structured frozen-input checks still pass. No test rewrites
its metadata to fake a new-policy actual-run control. New-policy inventory positives are
in-memory policy controls; a real new-policy generated/adopted artifact does not exist.
Until separate acceptance, current live strict checks continue to pass as before.

## Dependency trace, by purpose

| Path / purpose | Actual behavior and binding |
|---|---|
| `scripts/u2_inputs.py::prepare_inputs` (not executed here) | Reads reviewed component precision declarations, a2 truth/derivation/binding/execution JSON plus oracle YAML, two upstream execution-model inputs, npu-l4 hardware and retained provenance. Replays `hw.export`/`hw.derive` for exact equality, validates shared carriers, creates frozen input files and SHA256SUMS. These are local export formulas, not the oracle. |
| `vendor_rk.main` / `collect_snapshot` (not executed) | Human guard; explicit input root/digest; pin and pristine upstream checks; exact SOURCES/schema/uv.lock capture; request matrix with explicit precision/refusal inventory. Inputs cannot be overridden by PARAMS when explicit U2 inputs are used. |
| Isolated upstream subprocess (not executed) | `ORACLE_PROGRAM` imports pinned loader, F0 compute, orchestrator adapter and schema. Uses actual iteration_cost/count/duration methods, records direct callable-source identity. Whole clean upstream Git pin, locked external environment, isolated `-I -B` process and fresh pycache prefix cover runtime beyond the copied source subset. SOURCES is not represented as a complete upstream import closure. |
| Before/after generation | Existing clone/index/ignored/shadow checks, offline locked-environment check, CPython/package/lock records and repeated source/component/input verification stay unchanged. Exact two-process created/verified-identical execution remains human-only. Runtime traces cannot replace review of the unexecuted branches. |
| Publication/integrity | `snapshot_bytes`/`publish_snapshot`, exact safe-path manifest, no symlink substitutions, no differing overwrite; chmod is not approval. All generated files/retained provenance and the frozen inputs' own inventory/content identities remain checked. |
| Strict consumption | `check_manifest` → `check_snapshot_inputs` → `check_generator(current=True)` → `load_inputs(check_support=True)`. Also ADR/contract pin checks, exact component/sidecar copies, attribution, matrix/refusals and recorded oracle environment. Tests/adoption checks separately bind the accepted manifest/review. |
| Consumer computations and review | Nominal/physical comparison candidates, analytic v1/v2, producer/replay, CLI/report/provenance and review tooling consume committed oracle bytes but do not generate them. Their correctness and exact result/report implementation identities remain independently tested/bound. A code change may invalidate those results without requiring a new nominal oracle execution under the proposed policy. |

A read-only live strict-consumption run with `run_oracle`, `collect_snapshot` and
`prepare_inputs` replaced by rejecting sentinels passed. It loaded **30 local modules**;
their exact names are in evidence.json. The conservative AST closure also contains those
30 before the new helper. It includes function-local/TYPE_CHECKING imports and parent
package initializers, not just the observed path. It is not a trace of generation, and
no generation branch or external package-file authenticity is claimed tested here.

### Retained, removed and additional groups

The support delta lists every path, only for this artifact-provenance question.

- **Retain 21 contract Python modules** reached via explicit imports and
  `uarch_contract/__init__.py`. This includes evidence/model-card/report-context carriers
  even though the generator does not call their main behavior: their initialization and
  validators execute through package import. No blanket “report files are irrelevant” rule.
- **Retain 9 other Python modules:** scripts initializer/u2_inputs/vendor_rk; rkuarch,
  engines and hw initializers; `engines/protocol.py`, `hw/derive.py`, `hw/export.py`.
  Protocol imports arise through ResolvedHardware. Retain full files, not function hashes.
- **Retain 9 non-Python entries:** pyproject/uv.lock, npu-l4 YAML, and all six retained
  provenance subset members including its immutable historical manifest and model attribution.
- **Remove 45 unimported src modules** (CLI, producer/analytic versions, table/report/
  provenance/study/mapping, native/fork placeholders), **3 unimported contract modules**
  (schema generators and rotary_v2), **6 comparison/adoption test/tool Python files**,
  and **4 refresh-only pinned-source test copies**. None is reached from the generation/
  strict-verification roots. They remain Git-versioned and subject to their own tests and
  exact result/evidence identities; the actual upstream bytes remain in the artifact.
  The old v2 adoption is not called unnecessary retroactively: it followed accepted policy.
- **Add 12 explicit staging/mirror data entries:** a2-export's four JSON values, YAML and
  PIN; two execution-model JSON values and component-precisions.json; three canonical
  model-shape JSON mirrors. Some are conservatively retained integrity companions (PIN,
  canonical mirrors) rather than direct expanded-generation reads. Current old support
  hashes omit these source paths; frozen input bytes already have their own manifest.
  The proposed additions also detect changed current source inputs, without replacing
  frozen-input checks. **Add the new helper** as the thirteenth addition.

New mapped/rotary/native files are not categorically excluded: an import from any reached
module, including an initializer, brings their closure into the policy. A must identify
new generator/export/data relationships in its revision. If M changes a reached contract
initializer/common carrier, the proposed repair still requires refreshed source binding;
it is not a promise of zero M/K2/B adoption cycles.

## Mechanism and limits of the exact patch

`support-policy.json` is proposed tooling metadata inside the frozen input manifest,
with exact `{format: "uarch-input-support/2", selection: "generator-imports-and-data/1"}`.
Unversioned inputs retain the old complete `support_files()` rule. Unknown policy values
refuse even in structural input inspection. New staging writes the explicit policy and
new inventory; only future human-generated/adopted artifacts can use it.

The helper walks static imports from u2_inputs, vendor_rk and itself; includes package
initializers; rejects unresolved/ambiguous local imports, symlinks and unknown external
roots; checks source-root and script-directory shadows of external imports. Stdlib plus
pydantic/PyYAML are the only external roots. Known direct dynamic-import/eval/exec forms
are refused. A new ordinary local import changes inventory, so a new helper dependency
cannot disappear merely because a sampled execution did not reach it. Full reached-file
hashes detect changes to functions, branches, serializers and dynamic program strings.
Explicit reviewed data families cover current non-import input reads.

This is **not a Python security sandbox or a proof against obfuscated imports/I/O**.
The vendor's embedded subprocess programs are manually audited exceptions to a simple
local AST view; their entire containing source stays bound. Pydantic/PyYAML/std-library
transitive code and environment behavior remain under the existing lock/environment/
pristine-source policy, not vendored or byte-attested by this helper. It does not prove
installed package bytes untampered. New plugins, native extensions, reflective imports,
resource/config readers or alternative import-search rules require review and explicit
policy work; output equality alone never approves them. Read-only tracing exercised strict
consumption only. The helper is intentionally conservative about unused imports and schemas
reachable through initializers. Splitting the monolithic vendor script is not in this patch.

Before accepting the repair, review these remaining risks: file-level closure can stay broad;
new non-import data reads need explicit review; AST pattern checks are not complete against
aliases/reflection; external-runtime capture retains U0002's existing limitations. If these
limits are unacceptable, retain current enforcement explicitly before M rather than waive
currentness. No automatic policy narrowing or unreviewed inventory allowlist is offered.

## Executed checks and their limits

All scratch executions used B's existing locked interpreter with `PYTHONPATH=.:src:contract`
in the private export; live tests used `uv run --no-sync`. No dependencies were installed.
Exact command selections and before/fault/restored outcomes are in [evidence](evidence.json).

- Tests were written first: expected collection failure on the absent proposed helper.
  First implementation: 20 passes / two test-cleanup failures; the shadow fixture had left
  an empty directory. Cleanup was corrected, not weakened into an allowed shadow.
- Final proposed policy suite: **30 passed**. Controls cover valid inventory; generator,
  formula, serializer, input, initializer and lock changes; new imports and direct dynamic edges; external shadows;
  unimported native/mapped/report additions and existing CLI edit; missing/substituted
  inventory; additional data/symlinks; unknown policies; legacy integrity versus migration.
- Disabling only proposed inventory/byte enforcement in process produced **9 failed /
  21 deselected**; restoring it produced **9 passed / 21 deselected**. No live file or
  historical artifact was changed for the fault. This tests discrimination, not review.
- Fourteen existing synthetic pin/scope/fingerprint/environment refusal controls passed,
  including recorded lock/package substitutions and a valid CI/oracle-version distinction.
  Synthetic fixture metadata is labelled test data, not generated evidence or an adoption.
- Live strict vendor check and strict consumption with generation denied passed. Three
  existing producer-disabled v2/full-count and legacy dispatch/replay controls passed
  in each of the live clone and patched export (separate runs).
  This is bounded software regression, not a v2 verification report or a new corpus.
- Scratch Ruff, both CI-form mypy commands and two import contracts passed. Patch syntax/
  applicability is checked without applying it in B. No full-suite rerun: this is an
  unapplied prototype, and new-policy real-artifact positives require human migration.

No unsupported/no-op test is credited. Current strict check in patched scratch is an
**expected migration refusal**, not a pass; current strict check in the unmodified live
clone passes. Relevant tests and the full integrated suite are required again after an
accepted implementation/migration at the exact source checkpoint, before publication.

## Decision and remaining effort

Request coordinator/A review of dependency reachability and the proposed compatibility
scope, then Javid's exact policy/migration decision. The concrete patch is ready for review,
not installation. Prefer this versioned, conservative repair over a consumer-folder glob
exclusion; do not declare the repair accepted or the M prerequisite discharged here.

Remaining active-work estimate from this prototype: B 8–14 h for adversarial closure/data
review and integration-test completion; A 2–4 h for mapped/export dependency consultation;
independent review 3–5 h; B/human migration preparation/audit 4–8 h (human generation/adoption
and external waits separate). Total 17–31 engineering/review hours, not elapsed time or a
measurement of work already performed. A monolithic generator split or stronger package
sandbox would be a separately estimated scope. If repair is not ready, the decision is
explicit retention plus budgeted M/K2/B source-bound cycles, not unbounded postponement.
