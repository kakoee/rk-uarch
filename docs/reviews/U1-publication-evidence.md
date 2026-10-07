# U1 publication evidence — proposed, not published

> **Coordinator update, 2026-10-06:** Javid accepted complete U0001/U0002 and
> authorized adoption and integration of this exact proposal. It is now integrated
> locally; commit and push remain separate pending steps. See the
> [acceptance/adoption record](U1-acceptance-and-adoption.md). The original
> pre-acceptance proposal, validation and instructions below are retained as history.

Lane B publication-integration summary, 2026-10-06, prepared for Javid (@jjaffari), acting
human owner/approver for both U1 lanes while Reza is off duty. No Reza approval is claimed.
This summary attributes reviewer verdicts and human generation evidence; it does not itself
adjudicate findings, accept ADRs, adopt artifacts or close G1/U1.

## Exact inputs and artifact

| Input | Identity |
| --- | --- |
| Coordinator baseline | `89313eef20e6b252d235b40a680a1464c52c636a` |
| Accepted combined code source | `/tmp/u1-b-scope-integration-3d8bfs06` |
| Captured complete A proposal | `3f408194c6e26165770e35675b72939469dfe74d660b7e5d6b778bad18a3f773` |
| Captured complete B proposal | `85abc9638a94c708aab154699e9f32548c1945e39ba6f7c24eb5c6732eedc919` |
| Reviewed replacement source | `/tmp/u1-replacement-fzin2pif/staging` |
| Replacement manifest SHA256 | `b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d` |
| Full generator SHA256 | `4d2304002b262f2ee03dfe4f8fb338b350aacd80ea2488952849c416ee135317` |
| Oracle-program SHA256 | `9dd67d4883206f14b8a5a00fa3d0ced95bddaa395ba634d80e08a39813ea04fb` |
| Upstream pin | `1e5706e0ebfcc67c1a7333079a35b75f693e9963` |
| Pinned oracle lock SHA256 | `d984e55723326751ac3f888712f98462a525315ad4693691dbc3f2f5dc7f577c` |
| Verified oracle-environment record SHA256 | `02ffc090d0411265faa165cb60b6cfc7db24e7ed5697b746bcfda72528c5308b` |
| Generation-staging manifest SHA256 | `cb19332e9c1c3c88ad90bf6c0b8cdcf2d8f991b302d472fd5bfac2e497e0e8b0` |
| Accepted U1-lane-A-review.md SHA256 | `6bca5ad174d7902b49f272493687800bff817d4f821c2cd38f78682e4631cd66` |
| Accepted U1-lane-B-review.md SHA256 | `30b51fa71f222f0efb6c7e05ceb817e74dbfde75ca3920e9d74554ad800c0246` |

The [generation staging manifest](U1-publication-records/staging-manifest.json) records
exact sidecar/component hashes and empty PARAMS. The oracle environment is CPython 3.12.14,
uv 0.12.9, with 27 base-selection packages and no extras/default development groups.
Its [inventory](U1-publication-records/oracle-environment.json) and
[locked-check log](U1-publication-records/oracle-locked-check.log) are retained verbatim.
The reviewed verification code passed; the check exited 0 with no changes needed. rk-sim
was pristine before and after setup/generation. CI uses its independently locked environment.

## Attributed review and human-generation evidence

The complete [Lane A review](U1-lane-A-review.md) and [Lane B review](U1-lane-B-review.md)
are copied byte-for-byte from `/tmp/u1-independent-reviews/`. Both final verdicts are
ACCEPTED. Their original earlier findings, stale-artifact observations and adjudication
history remain intact. Lane B's later F3/F7 re-adjudication covers the real replacement.
Those verdicts precede this small publication housekeeping delta; they are not represented
as a review of edits made afterward. This author has not rewritten reviewer text.

Javid ran generation; the saved [first log](U1-publication-records/generation-first.log)
records `created: 20 files`, and the [second](U1-publication-records/generation-second.log)
records `verified-identical: 20 files`. Strict staging and reviewed-target checks passed.
The agent verified artifacts/evidence without executing generation. The complete artifact
has 20 files, 864 oracle records and two UnsupportedPrecision refusals.

Against BOTH prior manifests `4caea65f3c217bbb2030409833be6c67c15561552f8d9c9e179ac3ff82883284`
and `6b0d69c5737ba2b4cdbd8bce13ec860e4750f4008d9f4ee4fb8dc6db456d8304`, only GENERATOR.json
and MANIFEST.json changed, and uv.lock was added. No files were removed. All oracle/refusal
bytes, sidecars, component inputs and upstream sources are unchanged; see the complete
[classified comparison](U1-publication-records/snapshot-comparison.json).

## Publication housekeeping

- P18's shipped block now equals U-P19, including hardware_spec_hash; P19 already equals
  U-P20. A parameterized regression protects both shipped copies. Before repair, prompt
  tests gave 1 failed/3 passed; after repair, all four pass.
- Current handoffs explicitly supersede historical pending A-F12/B-F8 and generation status.
  A-F12 is implemented and accepted; original response/review evidence is preserved.
- Current U1/G1 and U-P1 ownership wording uses Javid's existing acting authority. Historical
  approvals and future-sprint ownership remain unchanged.
- [U2 kickoff obligations](U2-kickoff-obligations.md) are loaded by U-P3 and the execution
  plan's U0003 prerequisite: B-F16 and embedding accounting retain their existing U2 owners,
  budgets and acceptance. No workload/reader/preparation implementation was added.
- U0001's stale integration-status paragraphs are attributed housekeeping updates; its
  semantics and proposed status are unchanged. U0002 is byte-identical to the reviewed input.
  No production model, schema, toy, generator, sidecar or snapshot byte changed.

## Final proposal validation

Proposal: `/tmp/u1-publication-proposal-ns9fp_nu`.
External run/assembly evidence: `/tmp/u1-publication-evidence-586asqvj`.
Setup: `uv sync --locked --extra dev --offline`. UARCH_HUMAN remained unset.

| Exact command | Result |
| --- | --- |
| `uv run --no-sync pytest -q -rs contract/tests --require-vendor --junitxml=/tmp/u1-publication-evidence-586asqvj/strict-contract.xml` | 379 passed; zero failures/skips |
| `uv run --no-sync pytest -q -rs --junitxml=/tmp/u1-publication-evidence-586asqvj/full-suite.xml` | 385 passed; zero failures/skips |
| `uv run --no-sync mypy src contract scripts` | Passed, 47 source files |
| `uv run --no-sync ruff check .` | Passed |
| `uv run --no-sync lint-imports` | 2 kept, 0 broken |
| `uv run --no-sync python -B -m uarch_contract.generate --check` | Schemas fresh |
| `uv run --no-sync pytest -q tests/unit/test_prompt_sync.py` | 4 passed: build-spec and both shipped mirrors |
| `uv run --no-sync python -B scripts/vendor_rk.py --check` | Manifest, matrix and strict current compatibility passed |

Exact outputs/exit codes are retained in [test results](U1-publication-records/tests-results.json)
and [static/vendor results](U1-publication-records/static-results.json). No skip/xfail
was used; strict compatibility now passes against the real replacement.


All parity-harness results are synthetic self-tests, including frozen-oracle echoes.
These runs do not establish actual U2 workload parity, hosted CI or a Linux-box cold clone.
The final strict run includes A-F1/A-F2/B-F8, optional-SRAM and explicit DRAM-mode regressions,
ModelShape/vendored round trips, full coverage and unsupported-projection refusal.

## Remaining gates

Both complete U0001/U0002 ADRs remain proposed, including the narrow strict stub-source
exception. Javid must explicitly accept them and separately approve adopting the complete
replacement directory. Publication/commit, hosted contract CI, Linux-box cold-clone evidence
and the human G1 decision remain pending. No tag or G1/U1 closure is authorized by these
local results. The unresolved embedding obligation and accepted B-F16 deferral belong to U2;
no numeric failure is silently excused. See [the publication handoff](U1-publication-handoff.md).
