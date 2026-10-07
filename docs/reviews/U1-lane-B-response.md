# U1 · Lane B — U-REVIEW Stage 2 RESPONSE

Author response, 2026-10-06. This is **not reviewer adjudication**. Findings refer to
`/tmp/u1-independent-reviews/U1-lane-B-review.md`; cross-lane A-F12 refers to the adjacent
Lane A review. Both reports, their inline reproducers, A's saved probe artifact and the
reviewed candidate's U-REVIEW instructions were read. Neither report was rewritten.

## Pending gates and human scope decisions first

- **Current candidate incompatibility blocks strict validation/adoption.** Both preserved
  snapshots pass historical integrity/identity checks, but the revised generator fingerprint
  differs and required oracle-environment metadata is absent. Strict tests and CLI fail;
  they are not bypassed, skipped or reported as passing. Finish review of all generator
  fixes before any human replacement generation. Complete U0002 acceptance remains pending.
- **F8: APPLIED after A's implementation became available.** Javid approved revision
  before G1. A independently implemented the [interface handoff](U1-lane-B-flop-parity-interface.md).
  B captured that exact proposal, added its adapter and seven cross-lane tests. All pass,
  including explicit self-test classification and all four quantities. Code/interface review
  and complete ADR acceptance remain pending; this is not a reviewer verdict.
- **A-F12: APPLIED under Javid's approved interim policy.** Replication/padding that uniform
  /tp cannot represent is explicitly unsupported before numerical comparison. Complete coverage
  is retained; supported tp>1 cases remain comparable. This neither certifies physical
  correctness nor relabels workload results as aggregate compatibility. Embedding accounting
  remains a separate pending decision; ordinary numerical failures remain failures.
- **F1's blocking policy question is now answered by Javid**, not adjudicated by this
  author. The approved total-absolute policy is implemented/tested. It does not settle the
  separate embedding-accounting scope or accept all U0002. The narrow stub-source exception remains
  proposed, and hosted CI, Linux-box cold-clone validation, human adoption/publication and
  full U0001/U0002 acceptance remain outside this response's completed work.

## Inputs and evidence

Authoring worktree: `/home/jjaff/AI-infra-simulation/rk-uarch-u1-b`, branch `u1/parity`,
HEAD `af3b1bc3df3171d196394a58f62202ad50845dfa`, retaining its uncommitted proposal.
Disposable copies: `/tmp/u1-b-response-r14129fi/baseline` and
`/tmp/u1-b-response-r14129fi/integration`. Evidence is in their parent directory.

The first integration copied the frozen reviewed combination
`/tmp/u1-final-integration-84hif1_r` (original A content identity
`fc9522cc8daad2a8f21128657d9f3bfcab01e2154495d8fe9bf1c8076dae7b8f`), retaining that
before-evidence. During work A independently implemented the requested carrier. The **earlier carrier**
disposable integration is `/tmp/u1-b-response-carrier-9sinndh2`, using a fresh captured complete
A proposal from `../rk-uarch-u1-a` on the same HEAD. Its full content identity is
`aa568a839e401047a242f24b176274fc144ac364e8d9924ca4880480b1a03258` (sorted path→SHA256/mode
map). All input bytes/status are retained in `carrier-integration/A-input/` and `input.json`
under `/tmp/u1-b-response-r14129fi`. This validates that captured proposal, not subsequent
mutable A edits. Coordinator base remains `89313eef20e6b252d235b40a680a1464c52c636a`.

New A changes were applied only to the fresh disposable copy. Two repeated U-P3 documentation
conflicts in build-spec and the prompt were resolved by retaining coordinator U0019's
preparation/replay paragraph and appending A's producer omission/shared-SRAM/shard-scope
notes. Both contributions survive; prompt-sync passes. `assembly.json`, original merge
inputs and `resolutions.json` record this. The earlier A/B overlap resolutions and combined
Makefile remain intact. A's production models/schemas/toy are copied unchanged from that
captured A proposal. No A or coordinator source edits were performed by this session.

The final human snapshot was copied only for validation; no actual snapshot was generated,
edited or adopted. Synthetic regression bytes are not rk-sim artifacts. No commits were
made, including in scratch probes. Source preservation auditing observes A's independent
changes rather than falsely claiming that its moving worktree remained byte-identical.

## Finding dispositions

All claims were investigated; no finding is rejected. APPLIED describes author changes
with regressions, not reviewer acceptance. All named regressions are in
`contract/tests/test_u_p2_review.py` unless specified otherwise. The baseline run of its
50 cases gave **47 failed, 3 passed**; the revised run gives **50 passed**. The three
already-passing cases concern existing correct boundary/mode behavior; the associated
new policy/report/documentation regressions failed before the fixes.

| Finding | Disposition | Change / evidence / next action |
| --- | --- | --- |
| F1 | **APPLIED** | Reproduced the original doubled count with twenty +5% declarations: `kind=workload parity, max_rel=1.0`. Javid approved total absolute ≤5% per fixture/channel, residual ≤0.5%, rejecting unnecessary and zero/null adjustments. `test_f1_stacking_is_capped_per_fixture_channel`, parameterized unnecessary/null/zero/cancellation cases, boundaries/four quantities, zero denominator and negative/unadjusted boundary tests cover the fix. Before: stacking/unneeded/report tests fail; after: all pass. No embedding/KV exception or threshold change. |
| F2 | **APPLIED** | Original unmarked oracle echo returns `workload parity`. Default `self_test=True` now yields the explicit self-test label; output also states that authenticity is caller-declared. `test_f2_default_cannot_claim_workload_parity` fails before/passes after. Explicit `self_test=False` remains a caller assertion, never automated proof. |
| F3 | **APPLIED** | Original CLI exits 0 after actual oracle-program `tp=tp→tp=1` drift in a disposable code copy. Added distinct manifest, recorded identity and strict current-compatibility checks; Javid approved exact full-script/oracle equality. Metadata tampering, implementation drift and missing environment regressions fail before (missing verification API) and pass after. `test_current_snapshot_generator_compatibility` intentionally fails against both unchanged old candidates. Human adoption instructions now invoke the target tree's checker on the candidate before adoption. |
| F4 | **APPLIED** | Reproduced original `--check` exit 0 for missing/renamed U0001 and wrong RK_SCHEMA_SNAPSHOT. Default checks now require both; only explicit `--pre-contract` permits absence, never disagreement. Pytest rejects combining preparation with `--require-vendor`. `test_f4_absent_adr_requires_explicit_preparation` and all three strict seam cases fail before/pass after. Existing upstream-reference/history tests remain. No A code changed. |
| F5 | **APPLIED** | Added snapshot-inventory-derived matrix checks, exact sidecar-id set, row→component digest and row→sidecar content/attribution checks. Orphan component/model, wrong digest and changed source tests fail before (missing inventory verifier), pass after. `check_snapshot_inputs` is called by CLI and snapshot acceptance tests. Required scope is U1 correctness of complete optional inputs, not future precision selection. |
| F6 | **APPLIED** | Independently cloned existing Git history into throwaway repos without commits: actual clean status hid modified skip-worktree/assume-unchanged sources and an ignored shadow file. Old check accepted all three; revised check refuses flags/ignored files. Real-index regressions fail before/pass after. External environment plus isolated Python/fresh pycache prefix avoids importing ignored checkout/cache code; source checker requires pristine input. Existing pinned checkout is unaffected. |
| F7 | **APPLIED** | Oracle environment is checked against its lock before/after and recorded (Python/implementation, installed package versions, lock digest); the pinned lock is included in future output. Tests cover stale environment rejection, required/malformed metadata, package/lock tampering and CI runtime independence. Existing synthetic bridge self-test verifies both collections check before/after and record metadata/lock. Old snapshots lack these records and deliberately fail strict checks; no historical environment is invented. |
| F8 | **APPLIED** | Javid approved before-G1 revision; A independently supplied the actual carrier. B's `contract_payload` adapter uses structured classification and same-run actual/reference data, preserving fixture/channel/unit, declarations and all four quantities. Seven `test_parity_carrier.py` cases give 6 failed/1 passed before B adapter, 7 passed after; they cover all representative kinds, no callable rerun, missing classification refusal, zero/null, cancellation spend, explicit workload identity requirements, and serialization of 864×3 oracle-echo comparisons as self-tests. A's models were never replaced/edited by B. Review/ADR acceptance remains pending. |
| F9 | **APPLIED** | Confirmed nominal and shape-implied differences with A's actual implied_params. Javid approved preserving unchanged nominal inputs. Machine-readable six-value offset record and formula reference added; `test_f9_nominal_parameter_offsets_are_recorded_without_correction` fails before (record absent), passes after against real A models and original consistency rule. No new threshold, automatic deviation, shape correction or oracle edit. |
| F10 | **APPLIED** | `check_manifest` now refuses a symlinked root and ancestors, in addition to entries. Both root/parent synthetic regressions fail before (accepted), pass after. No actual snapshot was moved/replaced to test this. |
| F11 | **APPLIED** | `publish_snapshot` returns `created` versus `verified-identical`; CLI prints that result and no longer calls an arbitrary tree committed. Publication/rerun and CLI-label tests fail before/pass after. The existing human double-run claim remains attributed to Javid; new messages provide better evidence for future runs, not retroactive proof. |
| F12 | **APPLIED** | CI now invokes `uv run mypy src contract scripts`; `test_f12_ci_typechecks_b_deliverables` fails before/pass after. Final same command checks 46 files including both lanes' regression additions. |
| F13 | **APPLIED** | Import-linter also forbids scripts; an AST guard covers dynamic import aliases, __import__, exec/path loading and vendor path references in production roots. Five injected-source regressions and clean-source guard fail before (absent guard), pass after. A's exact `importlib.import_module(f"uarch_contract.{name}")` schema-discovery call is a narrow documented exception; no A edit. This is layered detection, not proof against arbitrary obfuscation. |
| F14 | **APPLIED** | Reproduced Git index 100644 and reconstructed mode0644 from a 0444 synthetic file. Javid approved chmod as local precaution, not portable immutability. Prompt/build-spec/U0002 synchronized. Documentation regression fails before/pass after. Two permission/content tests confirm both 0444/0644 integrity passes and modified bytes fail in either mode. No hooks or rejection solely for mode0644. |
| F15 | **APPLIED** | README covers complete revised layout and human generation/review/adoption; its regression fails before/pass after. U0002 rewritten as durable decisions, with transient validation evidence in handoff/response; both reference accepted U0019/89313ee. Historical counts remain explicitly dated in the handoff only and are superseded by current evidence. No reviewer document edited. |
| F16 | **DEFERRED** | Confirmed `component_precisions('npu-l4.yaml')` offers only FP16/FP16 and FP16/FP8. Required U1 components/approved coverage remain unchanged. U0003/U-P3 owners must define per-component precision selection and prepared/imported-bundle parity adapter under U0019. Next: BF16-only PARAMS fixture + declared peak validation and a prepared-bundle adapter test in U2. No future generator, prepared schema or replacement oracle implemented in U1. |
| A-F12 | **APPLIED** | Javid approved refusal of unsupported uniform-/tp projections pending a reviewed component-aware rule. `test_projection_scope.py` covers replicated KV (including the +7.07130967% 70B/tp16 probe), padding, supported tp1/2/4/8, all 864 fixtures, mixed complete coverage, and adapter refusal of incomplete/nonpassing reports. A's legitimate shapes remain accepted; no oracle or budget changes. Embedding accounting remains separately pending. |

## Approved F1 policy, alternatives and remaining numerical scope

The literal per-entry cap was faithful to the old words but unbounded after stacking.
Three concrete alternatives were considered:

1. Keep per-entry ≤5%: twenty entries permit 100%; rejected by the approved replacement.
2. Bound `abs(sum(d)) ≤5%`: cancellation can conceal large total adjustments, e.g. +5%/−4%
   gives net +1% but spends 9%; a residual-only report hides that distinction.
3. **Approved:** `sum(abs(d)) ≤5%` per fixture/channel, with `abs(raw - sum(d)) ≤0.5%`.
   Both signs spend budget; raw/signed/absolute/residual are separate report fields.

Ratios use **positive projected reference** as denominator: `(actual-reference)/reference`.
Positive means more actual work. Unadjusted error within ±0.5% passes and declarations there
are refused as unnecessary. Zero reference requires exact zero, null requires null; both
forbid adjustments and use null raw/residual ratios, with zero known adjustment. No undefined
ratio is manufactured as zero. Duplicate/unknown declarations fail. +3%/+2% can explain +5.5%
at the boundary; twenty +5%, +5%/−5%, or any absolute spend above5% fails. Opposing legitimate
+3%/−2% can explain +1% while spending5%; it is not free cancellation.

Legitimate accounting pressure is visible: 128256×4096 / 8.03e9 ≈6.54% for the 8B untied
embedding parameter share. An embedding gather need not be a dense matrix multiply even
though rk-sim's nominal-parameter approximation includes those parameters. This share is not
itself a measured operation/duration offset; the discrepancy depends on query and accounting.
A real above-cap numerical discrepancy remains a reported failure unless there is a documented
scope incompatibility. No embedding-specific incompatibility or new accounting rule is approved.

## Approved A-F12 scope follow-up

**A-F12 interim scope policy approved by Javid:** uniform division by tp is eligible
only for the declared unreplicated, unpadded shard scope. Known KV replication or
nondivisible vocabulary/head/FFN shard dimensions produce `unsupported_projection`
before the candidate is called or numerical agreement is considered. Missing required
scope dimensions also fail closed. This guard neither rejects all tp>1 nor certifies
physical correctness; A's broader legitimate request shapes remain valid contracts.
A component-aware projection remains future reviewed work for U-P3.

The frozen oracle is evidence of rk-sim's aggregate calculation. No existing workload
result is relabelled aggregate compatibility, and no new physical-correctness certification
is introduced. `rank_counts` is diagnostic arithmetic only, not an eligibility check.
The harness implements no diagnostic bypass that can satisfy the workload-parity gate.

`run_parity` retains every requested fixture in `coverage`, with `passed`, `failed`, or
`unsupported_projection` and explicit reasons. Any nonpassing entry raises `ParityFailure`
carrying the complete report; later fixtures are still evaluated. Supported numerical or
candidate implementation failures remain `failed`, never relabelled unsupported. Reports
retain available actual/reference values and all four adjustment quantities even for an
over-budget numerical failure. No partial run can enter A's successful FlopParity carrier:
B's adapter requires complete passing coverage and preserves the caller's explicit kind.
Default oracle echoes remain harness self-tests. All 864 baseline fixtures are eligible;
no frozen value, nominal input, fixture or approved tolerance changes.

**Embedding accounting is separately pending.** The approximately 6.54% nominal 8B
embedding parameter share is not an observed operation/duration offset. Preserve nominal
U1 inputs and report actual discrepancies explicitly under the approved budget. An ordinary
above-budget numerical error remains a visible failure. Only a documented scope incompatibility
can justify unsupported status; the replication/padding decision is not an embedding exception.

## Approved fingerprint/environment policy and artifact consequences

Javid approved exact current full-script and oracle-program equality for strict integration/CI,
required environment metadata, and a separate historical integrity path. Alternative historical
fingerprints alone would not catch current drift; a compatibility-attestation system would need
its own reviewed format and policy and was not selected. No old candidate exemption was added.

| Identity | SHA256 |
| --- | --- |
| Revised scripts/vendor_rk.py | `4d2304002b262f2ee03dfe4f8fb338b350aacd80ea2488952849c416ee135317` |
| Previous final-candidate script | `69a3e31f5db3b99bcf251f63ee87eb4dc84ddf4f99fccf9aa48c56843ad186bd` |
| Unchanged oracle program | `9dd67d4883206f14b8a5a00fa3d0ced95bddaa395ba634d80e08a39813ea04fb` |
| Preserved B snapshot manifest | `4caea65f3c217bbb2030409833be6c67c15561552f8d9c9e179ac3ff82883284` |
| Preserved final candidate manifest | `6b0d69c5737ba2b4cdbd8bce13ec860e4750f4008d9f4ee4fb8dc6db456d8304` |

F3/F4/F5/F6/F7/F10/F11 modify the script fingerprint. None modifies ORACLE_PROGRAM.
Future output includes the pinned upstream uv.lock and environment record. Generation uses
an external existing environment; before and after, `uv sync --locked --check --offline
--no-default-groups` verifies exact base selection without syncing it. That interpreter
records CPython version, implementation and normalized distribution versions; lock and
inventory must remain unchanged. All versions must occur in the pinned lock, whose SHA256
is bound in the current generator. CI checks recorded metadata/lock consistency and required
keys but does not recreate the oracle environment or require its own runtime to match it.
This is evidence about software identity, not cryptographic authentication of runtime behavior
or proof against modified installed package files; human input/review controls still apply.

No oracle metadata was backfilled. Both candidates retain historical identity/integrity but
are incompatible with current code. A new human candidate is required **after fixes/policies
and review settle**. The handoff contains the exact staging, external-environment, double-run,
strict validation, classification/comparison and target-checker procedure. Future expected
baseline: 20 files, 864 records, two refusals; unchanged nominal sidecars. Existing values must
be compared and any changes explicitly reviewed, not assumed unchanged or silently adopted.

## Nominal inputs and permission policy approvals

Javid approved preserving nominal inputs, without a new threshold or automatic correction.
Full-precision ratios are in [the machine-readable record](U1-U-P2-nominal-parameters.json).
Formula: A's `model_shape.implied_params` (U0001 formula proposal). Signed differences are
**nominal minus implied**; relative denominator is **implied**. The existing consistency
check remains unchanged. Rows for both total and active are intentionally explicit:

| Model / parameters | Nominal | Shape-implied | Signed difference | Relative difference (approximately) |
| --- | ---: | ---: | ---: | ---: |
| 70B total | 70,600,000,000 | 70,553,706,496 | +46,293,504 | +0.06561456% |
| 70B active | 70,600,000,000 | 70,553,706,496 | +46,293,504 | +0.06561456% |
| 8B total | 8,030,000,000 | 8,030,261,248 | −261,248 | −0.00325329% |
| 8B active | 8,030,000,000 | 8,030,261,248 | −261,248 | −0.00325329% |
| Mixtral total | 46,700,000,000 | 46,702,792,704 | −2,792,704 | −0.00597974% |
| Mixtral active | 12,900,000,000 | 12,879,925,248 | +20,074,752 | +0.15586078% |

Exact implied inputs would require formula approval and regeneration; a nominal source citation
would be a different attribution choice. Javid instead selected explicitly documented nominal
test inputs. U2 must report shape-based count differences under the approved policy; neither
operation counts nor durations may be automatically corrected by these parameter ratios.

For F14 Javid approved the existing local chmod precaution with truthful enforcement layers:
manifests detect edits, strict compatibility binds current generator/oracle/environment identity,
humans approve complete revisions, and Git history preserves published revisions. Alternative
checkout permission hooks were not selected. Writable mode0644 neither proves invalidity nor
approval. Manifest equality does not prevent edits or prove a human approved them.

## Validation commands and results

Earlier carrier commands below ran in `/tmp/u1-b-response-carrier-9sinndh2`, with UARCH_HUMAN unset.
Setup: `uv sync --locked --extra dev --offline` passed. Exact outputs/exit codes are in
`carrier-integration/tests-results.json`, `static-results.json`, per-command logs and JUnit XML
under `/tmp/u1-b-response-r14129fi`. Earlier frozen-A runs are retained separately.
The command runner is `run_checks.py`; reproduction scripts and original outputs are retained.

| Command | Result |
| --- | --- |
| `uv run --no-sync pytest -q contract/tests/test_parity_carrier.py contract/tests/test_u_p2_review.py --require-vendor` | **57 passed** |
| `uv run --no-sync pytest -q -rs contract/tests --require-vendor --junitxml=/tmp/u1-b-response-r14129fi/carrier-integration/strict-contract.xml` | **360 passed, 1 failed, no skips** |
| `uv run --no-sync pytest -q -rs --junitxml=/tmp/u1-b-response-r14129fi/carrier-integration/full-suite.xml` | **364 passed, 1 failed, no skips** |
| `uv run --no-sync mypy src contract scripts` | Passed, 46 source files |
| `uv run --no-sync ruff check .` | Passed |
| `uv run --no-sync lint-imports` | 2 kept, 0 broken |
| `uv run --no-sync python -B -m uarch_contract.generate --check` | Schemas fresh |
| `uv run --no-sync pytest -q tests/unit/test_prompt_sync.py` | 2 passed |
| `uv run --no-sync python -B scripts/vendor_rk.py --check` | **Exit 1**, stale generator + missing environment metadata |
| `uv run --no-sync python -B scripts/vendor_rk.py --check --historical` | Historical integrity/recorded identity only passed; not current compatibility |

The single failure in each pytest run is `test_current_snapshot_generator_compatibility`:
`GENERATOR current incompatibility: generator script fingerprint differs; locked oracle
environment metadata missing`. This is deliberately retained. No xfail, skip or disabling
flag was used to make the preserved candidate appear current.

Before evidence: `regressions-before-final.log` records 47 failed/3 passed against the reviewed
implementation; `regressions-after.log` records 85 passed including all 50 initial cases against frozen A. `carrier-before.log` then records 6 failed/1 passed
for the adapter against actual new A; `carrier-after.log` records all 57 review/carrier cases passing. The decision
probes reproduce F1/F2/F8/F9/F14/F16/A-F12. `original-behavior-probes.json` also captures actual
original CLI acceptance of oracle drift and missing/renamed/constant mismatches, plus real Git
flag/ignored-file bypasses before and refusals after. Most new verification-API regressions
fail before because those checks do not exist; direct behavioral probes independently confirm
these are real gaps rather than just renamed interfaces.

All comparison self-tests remain synthetic harness evidence. Captured-A round-trip, sidecar, optional-SRAM and explicit DRAM regressions pass,
as do the **seven new F8 carrier tests**. These include hypothetical workload-classification
protocol data, never a claim of a real workload implementation result. Hosted CI and Linux-box cold-clone execution remain pending publication and
human orchestration. The author does not adjudicate findings, accept U0002, adopt a candidate,
or close G1/U1.

## Latest A-F12 follow-up and captured-A validation — 2026-10-06

This section supersedes the earlier scope status and integration totals above. Author
dispositions: **B-F1–F15 APPLIED; A-F12 APPLIED; B-F16 DEFERRED to U2**. These are not
independent reviewer adjudications. Embedding accounting remains the separate unresolved
numerical-scope question; nominal inputs and approved tolerances remain unchanged.

### Exact integration inputs and conflict resolutions

Fresh disposable tree: `/tmp/u1-b-scope-integration-3d8bfs06`.
Evidence, input copies, command logs/JUnit, audit and merge records:
`/tmp/u1-b-scope-evidence-5st8n19o/`.

Coordinator main remains `89313eef20e6b252d235b40a680a1464c52c636a`. The assembly starts
from the previously validated combined tree, preserves its coordinator/A/B overlap resolutions
and combined Makefile, then applies the delta from captured A revision `aa568a83…3258` to
A's newly delivered complete follow-up. Current captured A **content identity** is
`3f408194c6e26165770e35675b72939469dfe74d660b7e5d6b778bad18a3f773`, with HEAD
`af3b1bc3df3171d196394a58f62202ad50845dfa` on `u1/contract`. Identity hashes the sorted
path→SHA256/mode inventory in `A-input.json`; this identifies uncommitted bytes, not a commit.
The captured A handoff includes approved A-F1/A-F2/A-F12 and the exact B-F8 delivery.

B's adapter targets **that revision's** actual `FlopParity`, `ParityChannelComparison`
and `FlopDeviation`. It adds no A field/schema and edits no A worktree. Relative to the
previous A capture, carrier implementation and schemas are unchanged; current A documentation
and additional regression are integrated. Exact SHA256s:

| A interface file | SHA256 |
| --- | --- |
| `contract/schema/FlopDeviation.json` | `7cb60d212136f1f588b369ef9ad1bfe26b4d59bc8886d90dba07c25c4f2a071d` |
| `contract/schema/FlopParity.json` | `7235d5bc4152498dddc076948c674e23a98bee88c1e19ee5fa8710b5d6380118` |
| `contract/schema/ParityChannelComparison.json` | `8f6ba28d16c1ce0afdacafecd801582a3827ccd28c7480530a4c7345d15383dd` |
| `contract/uarch_contract/table.py` | `0ddfdc94d5dcaac9e26e7c27577fa82d9b06feb7fc9da60df5f9ccd594779749` |
| `docs/reviews/U1-U-P1-handoff.md` | `deb1a6c1c36400052d520395f961661ac7ce8da3a2b898f138a5af693467ccc8` |

All 88 captured A production/schema/toy files match the disposable tree byte-for-byte.
The two mirrored documentation conflicts (build-spec and U-P3 prompt, two hunks each)
retain coordinator U0019's validated prepared-graph engine and prepare/import/replay flow,
and append A's typed parity/ratio requirements plus table/request/spec identity and condition
resolution requirements. U-P1 and U-P19 changes merge cleanly. B's new U-P2 wording is
applied to both prompt and build-spec; prompt-sync passes. `assembly.json` and
`resolutions.json` preserve the exact old/new/merged text. Neither source worktree nor
coordinator main was modified to resolve a conflict.

### Scope regressions and exact validation results

`contract/tests/test_projection_scope.py`: **17 passed**. First 15 cases failed before
the scope/report fix (`scope-red.log`); the additional over-budget diagnostic case failed
before its metric-preservation fix, while the added valid-A padding case already passed
(`scope-extra-red.log`). Final targeted evidence: `scope-green-final.log`.

- The reproduced 70B/tp16/kv_heads8 case preserves 9,490,301,952 aggregate/tp versus
  10,161,390,592 rank-local read bytes (+7.07130967%). This arithmetic is the review's
  synthetic reproducer, never replacement oracle generation. A accepts the legitimate
  request; B refuses its projection before calling a candidate, even an exact echo.
- A-valid padded vocabulary and nondivisible FFN/expert widths are unsupported. Supported
  tp1/2/4/8 cases and all 864 preserved baseline fixtures retain passing self-test coverage.
- Mixed coverage reports retain supported, unsupported and numerical failures. A synthetic
  +6.54% count probe stays failed, not an embedding exemption or measured embedding offset.
  A +3%/+3% declaration remains over-budget despite zero residual, preserves all four
  quantities, and does not prevent reporting a later supported fixture.
- Incomplete/nonpassing reports cannot serialize through A's successful carrier. Duplicate
  fixture ids fail before collapsing coverage. All seven carrier tests still pass, preserving
  explicit self-test kind, fixture/channel attribution, units and all four quantities.

Commands ran in `/tmp/u1-b-scope-integration-3d8bfs06` with UARCH_HUMAN unset. Setup:
`uv sync --project /tmp/u1-b-scope-integration-3d8bfs06 --locked --extra dev --offline`.

| Exact command | Result |
| --- | --- |
| `uv run --no-sync pytest -q contract/tests/test_projection_scope.py contract/tests/test_parity_carrier.py contract/tests/test_flop_parity.py contract/tests/test_u_p2_review.py --require-vendor` | **84 passed** |
| `uv run --no-sync pytest -q -rs contract/tests --require-vendor --junitxml=/tmp/u1-b-scope-evidence-5st8n19o/strict-contract.xml` | **378 passed, 1 failed, no skips** |
| `uv run --no-sync pytest -q -rs --junitxml=/tmp/u1-b-scope-evidence-5st8n19o/full-suite.xml` | **382 passed, 1 failed, no skips** |
| `uv run --no-sync mypy src contract scripts` | Passed, **47 files** |
| `uv run --no-sync ruff check .` | Passed |
| `uv run --no-sync lint-imports` | **2 kept, 0 broken** |
| `uv run --no-sync python -B -m uarch_contract.generate --check` | Schemas fresh |
| `uv run --no-sync pytest -q tests/unit/test_prompt_sync.py` | **2 passed** |
| `uv run --no-sync python -B scripts/vendor_rk.py --check` | Expected **exit 1**, stale artifact |
| `PYTHONPATH=. uv run --no-sync python -B /tmp/u1-b-scope-evidence-5st8n19o/audit.py` | Historical integrity/inputs and preservation pass; strict incompatibility explicitly asserted |

The **only** failing test in strict/full runs is
`test_current_snapshot_generator_compatibility`: `GENERATOR current incompatibility:
generator script fingerprint differs; locked oracle environment metadata missing`.
No skips, xfails, metadata edits or relaxed check flags conceal it. The integrated suite
is **not green**. No unexpected implementation failure remains. Optional-SRAM, explicit
DRAM mode, revised table hardware identity/conditions, ModelShape and vendored round trips
are included in these runs. Synthetic harness probes/echoes establish no actual U2 workload
parity, hosted CI result or Linux-box cold-clone result.

### Preserved artifacts and readiness for human review/freezing

Read-only audit verifies both historical manifests, complete 864-record/two-refusal coverage,
and identical oracle/refusal values. The two historical snapshots still differ only in
GENERATOR.json and MANIFEST.json. Final human candidate manifest remains
`6b0d69c5737ba2b4cdbd8bce13ec860e4750f4008d9f4ee4fb8dc6db456d8304`; the prior B manifest
remains `4caea65f3c217bbb2030409833be6c67c15561552f8d9c9e179ac3ff82883284`. Javid's
reported two identical successful runs remain attributed human evidence, not agent execution.
The disposable integration uses an exact copy of the final human candidate. Both originals
remain **historically intact, strictly incompatible and unadopted**; rk-sim remains clean
at its exact pin. A/coordinator contents are unchanged since capture.

The scope fix and alignment against the delivered A revision are complete. No known pending
B implementation work requires another generator edit. The script fingerprint is unchanged
by this follow-up: `4d2304002b262f2ee03dfe4f8fb338b350aacd80ea2488952849c416ee135317`;
ORACLE_PROGRAM remains `9dd67d4883206f14b8a5a00fa3d0ced95bddaa395ba634d80e08a39813ea04fb`.
Inputs are **ready for review and an explicit freeze, not declared frozen or approved**.
Review-driven script changes would change the full fingerprint and must precede the human
candidate step. Preserve approved nominal sidecar inputs, exact upstream pin and PARAMS=''.
Embedding accounting remains a U-P3 workload-parity decision; it grants no permission to
alter these inputs, adjust oracle outputs or turn an ordinary failure into unsupported scope.

After review/freezing, Javid can use the handoff's future-human recipe, now pointing at this
captured combined tree: separate staging; verified external locked environment; two identical
human generations; manifest/matrix/strict integration checks; classified comparison against
both preserved artifacts; explicit review of changed existing values; then separate approval
for complete adoption/publication. Expected revised baseline is 20 files (including uv.lock),
864 records and two refusals. No replacement manifest is invented. No generation, artifact
patching, adoption or UARCH_HUMAN setting occurred here. Strict tests must actually pass with
the human-generated compatible revision before an integrated-green claim.

**B-F16 remains deferred to U2.** Lane B's vendor/parity maintainer owns the deferred matrix
change; Lane A's U-P3 preparation/workload owner implements the prepared/imported-bundle
adapter; the U0003 author owns the component-precision interface. Javid receives this concrete
handoff as acting U1 owner/approver. Acceptance requires a BF16-only npu-l4 PARAMS fixture,
validation against its declared supported compute peak (no substitute), and parity adapter
coverage of the actual prepared bundle under U0019. Review any later generator change and
refresh at the same upstream SHA through the approved artifact lifecycle. No successor work
is implemented now.

Complete ADR acceptance, reviewer adjudication, embedding-accounting scope, human candidate
review/generation/adoption/publication and G1/U1 acceptance remain outstanding. All proposals
remain uncommitted. No Reza approval or physical-correctness certification is claimed.
