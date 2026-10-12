# U3 artifact candidate audit and adoption proposal

**Candidate audit passed; adoption is pending Javid's separate decision.**
The human ran the approved two-process generation and returned manifest
`1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a`.
The coordinator verified that exact complete 48-file candidate, both successful process
receipts and all source/input/environment preflights. A remains clean at local `187fe3b`;
its existing canonical artifact is unchanged. No source-bound commits were pushed.

## Exact reviewed artifact

| Binding | Identity |
| --- | --- |
| Source commit | `187fe3b035bee9cbeae13b03c8b4ac6ef0ee276f` |
| Source tree | `fe10c7d4b08a6910f165da9b92f8e13a2a37c107` |
| Approved freeze proposal | `70adf0988b218aed895fcf5d2d8b039ca2ba0566` |
| Input digest | `27c6238d42e57dc4f2b1baf0c8846c11f1eec2968176dcefcdc463beb64bc80f` |
| Prior adopted manifest | `20eee19b0e864ad07a7b122da7544e385116fdd50d279e1fac1bfbbf03a697ad` |
| Proposed new manifest | `1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a` |

Candidate location: `rk-uarch-u3-a/tables/U3-rope-generation-v1/candidate`.
Canonical destination after separate approval: A's
`contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963`.

The complete [audit](audit.json) and [human receipts](human-generation-receipts.json) record:

- First process: created 48 files; second process: verified-identical, both exit 0, empty
  stderr, identical commands and manifest. Source/input/environment identity is unchanged
  before, between and after the two runs, and matches a fresh coordinator preflight.
- Strict manifest, required input support, generator/environment, source attribution and
  precision-refusal audit passed. Raw `audit_candidate` correctly returns adopted=false.
- All **1,008 rows** retain their unique identities, with 504 decode and 504 prefill.
  All **four real precision refusals** are retained. The full fixture and refusal files
  are byte-identical, including counts, durations, queries, source attribution and nulls.
  Vector channels remain absent and decode writes remain null.
- Exact artifact delta: only `MANIFEST.json`, `u2-inputs/SHA256SUMS` and
  `u2-inputs/support-files.json`. Inventory, generator metadata/environment, upstream code,
  lock, schemas, component descriptors, model sidecars and all other files are unchanged.
  Support grows 87 to 97 as approved; old entries are unchanged.

[audit.py](audit.py) reproduces the read-only audit using A's isolated interpreter and exact
frozen import paths. It invokes no oracle. Its first receipt comparison needed JSON
normalization of in-memory matrix tuples; the corrected comparison passed and no receipt
or candidate byte was changed. Full semantic/byte comparison is retained in audit.json.

## Exact placement and binding proposal

[placement-plan.json](placement-plan.json) binds the complete candidate and exact
[adoption-bindings.patch](adoption-bindings.patch). This patch:

1. Updates only CURRENT_MANIFEST, REVIEW_SHA256 and the new review-file path in protected
   `contract/tests/test_u2_historical_snapshot.py`; all assertions remain.
2. Updates only the current manifest constants in two existing B reference/R202 tests.
3. Adds `tests/fixtures/u3_rope/received-adoption-review.json` after actual approval,
   preserving the old U2 review, prior manifests and historical fixtures.

[Proposed review bytes](proposed-adoption-review.json.txt) are a **draft only**. Their
accepted/independent fields describe the proposed human administrative artifact-adoption
record. They have no live authority until Javid explicitly approves the named decision.
They do not assert that Javid independently tested or validated physical predictions.
Do not install or use the draft to consume the candidate before approval.

Zero-context patch formatting avoids whitespace-only context lines; use `git apply
--unidiff-zero`. Its applied bytes were verified equal to the three-context patch used
in the scratch tests below. No test or source content changed during normalization.

Complete placement plus this patch would change seven Git paths: the three artifact
metadata files, three current-binding tests and the new administrative record. All 48
candidate members must be verified as one unit; this is not a partial artifact selection.

## Executed conditional checks

[check_proposal.py](check_proposal.py) exported A's exact Git revision into a disposable
directory, placed the complete candidate there, applied the exact binding patch, and used
the draft review only as a conditional test premise. No live protected file was changed.

- Strict vendor check passed in that export ([output](scratch-strict-check.txt)).
- Full contract selection plus the two affected B reference/R202 modules:
  **784 passed, 28 skipped**, zero failures, 55.93s ([log](scratch-tests.log),
  [scope receipt](scratch-results.json)). This is not a full-repository suite.
- The 28 skips are the unchanged protected rotary runtime-admission tests; activation
  remains a separate decision. The previously stale-support contract tests pass in this
  conditional placement. They remain open in A's live checkout until actual adoption.
- Scoped Ruff and exact patch application passed. No production/support bytes changed,
  no new generation ran, and no report evidence, hardware accuracy or U3 completion follows.

## Decision and remaining steps

[U3-artifact-adoption-v1](next-decision.md) asks Javid to adopt this exact complete candidate
and its required pin/review binding updates. Under U0002, explicit human approval of a
complete candidate is separate from permission to generate it. CLAUDE.md reserves protected
contract installation to the human. After approval, prepare/verify the human placement and
local commit procedure; no agent installs protected paths or sets the human-only flag.

Protected-test activation, final integration with published coordination commits, both
version routes and schemas, static/import checks, strict currentness and the full suite,
then a separately verified normal main push remain pending. Old physical discrepancies,
B report limitations and RoPE's lack of a pinned-oracle channel remain explicit. No runner,
nightly, fork selection, independent-review verdict, tagging or sprint closure is granted.
