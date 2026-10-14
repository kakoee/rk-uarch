# U3 final documentation refresh — proposal handoff

Fresh standing-documentation session, separate from both A/B author and reviewer sessions.
This is execution-plan §5 documentation work, not U4, an adversarial review or a closure
verdict. No subagents, network/host contact, oracle generation, artifact adoption, native
execution, runtime/source edits, staging, commit, push or tag occurred.

## Exact target and proposal

Implementation: `7afba9b16d954fd46684711764cb3718170e53aa`.
Accepted documentation: [five-file review identity](../U3-closeout-documents-v1/review.json)
and [closeout.patch](../U3-closeout-documents-v1/closeout.patch), SHA256
`2b0bc1934020e1d0da2d21ab3514d26c1595a780d3d539b300f79a05286d9416`.
The helper's `--verify` succeeded: all five exact postimages are already installed locally,
although the original package and closeout records retain their earlier pending wording.
They were not changed here. Javid's design/policy acceptance excludes U4; prospective code
and migration remain unapplied, with current strict source/artifact enforcement intact.

Installed accepted postimages (SHA256):

| Path | SHA256 |
| --- | --- |
| `docs/build-spec.md` | `2abf7454e6495f849f5a55bdaf3723c9fdbb045e6464d1f80112d8a1c554fb7f` |
| `docs/decisions/U0002-the-vendored-snapshot-and-parity-discipline.md` | `4f904507383c7e22b8e14eda2424bc7c716597d1846b7d878353a84de1b5a31f` |
| `docs/decisions/U0011-the-native-engine-core.md` | `de9efa167268b97075b521d59c3bdbb9e92e3ed5dd6ddb111caad2a65d843364` |
| `docs/execution-plan.md` | `afeec8e6b2e930ba26dc9c4ac3c221cfa85c76b7d9b067fa95d02f232ab36a93` |
| `docs/prompts/U-P6-L0-invariants-and-L0m-metamorphic.md` | `8ca3647e67f4bd8a7d9df85248a2b98bab5391413f2e49f2431b900bcf31be3b` |

The replacement [proposed-how-it-works.md](proposed-how-it-works.md) is written for installation
at `docs/how-it-works.md`; its relative links are resolved from that intended destination.
[how-it-works.patch](how-it-works.patch) is an **unapplied, zero-context patch** against the
preserved live narrative. Check with:

```sh
git apply --check --unidiff-zero docs/reviews/U3-final-documentation-refresh/how-it-works.patch
```

No final tag exists or is claimed. The coordinator must select the full publication content,
bind its exact final commit/tree and arrange same-published-revision validation before human
closure. These proposal bytes deliberately identify implementation plus reviewed documents;
they do not assert `u03-end` or final published validation.

## What was executed here

Existing CPython 3.12.14 `.venv` was reused without dependency installation or synchronization.
Installed packages that occur in the lock matched their pinned versions. This is a local
WSL2 documentation check, not a fresh environment or controlled-host qualification.
The sandbox initially could not launch commands because of its `/mnt/wslg/distro` mount
configuration; approved local commands ran outside that broken sandbox, with no network use.

- Exact five-file installed-postimage verification and strict `scripts/vendor_rk.py --check`
  passed. Manifest `1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a`,
  frozen-input digest `27c6238d42e57dc4f2b1baf0c8846c11f1eec2968176dcefcdc463beb64bc80f`,
  current complete support inventory 97 files. No historical-mode substitution.
- Public analytic v1 demonstration: reconstructed its existing input bytes, checked the
  original capture receipt and actual AI review bindings, then ran assembly/table/report
  twice plus saved replay with producers disabled. All three output sets were identical:
  61 files / 36,707,563 bytes each. Default/opt-in reports and negative producer controls
  passed. Table/row hashes exactly reproduce the proposal. No review was issued here.
- Existing v2 contract literals: both aggregate and per_op, decode and prefill, authenticated
  capture/replay and public subprocess dispatch agreed byte-for-byte. This is real analytic
  execution on explicit synthetic test inputs, not a new producer, named-model coefficient
  inference, public v2 product artifact, independent physical oracle or silicon evidence.
- Retained B SR-C1 L0/L0m decompressed source hashes matched. Reductions remained partial /
  not_run, including aggregate clock 22/24. **Both current-checkout public validations
  refused with exit 1, `Implementation bytes changed`**, using the historical implementation
  pin. The exact changed bound paths and command errors are recorded in checks.json.
- Existing focused runtime/contract/arithmetic/display/card selection: **328 passed,
  zero skipped/failed/errors**. Existing report selection: **14 passed, 33 deselected,
  zero skipped/failed/errors**. These two selections are distinct, not a full suite.
- Proposal links, quoted result/inventory/report numbers and hashes, clean patch applicability,
  scratch-applied exact postimage and workspace preservation passed. Probe field-name and
  placeholder assumptions were corrected during development; an actual-data check corrected
  the draft synthetic-d4 head dimension to 2. No production or fixture change was needed.

Exact reproduction commands from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src:contract .venv/bin/python -B \
  docs/reviews/U3-final-documentation-refresh/check-evidence.py.txt \
  --output /tmp/u3-doc-evidence.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:contract .venv/bin/python -B \
  docs/reviews/U3-final-documentation-refresh/reproduce-v1.py.txt \
  /tmp/u3-doc-v1-summary.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/rotary_v2 contract/tests/test_rotary_v2.py \
  contract/tests/test_rotary_v2_runtime_pending.py tests/unit/test_u2_a_stage2_result.py \
  tests/unit/test_u2_b_display_permissions.py tests/unit/test_u2_b_stage2_cards.py \
  --junitxml=/tmp/u3-doc-focused.xml
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  validation/reporting/test_analytic_report.py \
  -k 'catalogue or fixed_replay or skipped_only or discovery_failure or underbudget or malformed_result or invalid_return_full or changed_implementation or rehashed_subset' \
  --junitxml=/tmp/u3-doc-report-tests.xml
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  docs/reviews/U3-final-documentation-refresh/validate-proposal.py.txt
```

The final probe needs the two `/tmp` summaries and JUnit files from those commands plus
this session's `/tmp/u3-doc-refresh-before.json` preservation baseline. A new session must
record its own before-state; it cannot reproduce this session's preservation assertion
without that original baseline. The baseline is a SHA256 inventory, not a copied source
snapshot. Immutable `.py.txt` probe source is intentional; no lint exclusion was added.
The main evidence probe returns success for its completed audit while recording the two
expected historical-report validator refusals; its exit status is not a report-rung pass.

## Evidence and preservation

[checks.json](checks.json) holds current identities, environment, hardware, v2 results,
retained-report hashes/reductions, exact validator commands/refusals and changed bound paths.
[public-workflow.json](public-workflow.json) retains exact public CLI argv, original-review
bindings, repeated-output summary and quoted v1 row projection. Full table/report payloads
remain in its recorded `/tmp` output root. The original driver, capture receipt and actual
AI review records remain untouched; synthetic review records supply no human authority.
[focused.log](focused.log) and [report-tests.log](report-tests.log) are the actual pytest logs;
[proposal-checks.json](proposal-checks.json) binds the proposal/probes, JUnit counts, links,
patch equality and preservation observations. Large generated payloads and full JUnit files
remain under `/tmp`, not this review tree.

All 1,642 pre-existing tracked/untracked nonignored files were hash-checked unchanged,
including the live narrative, local accepted documents, reviewer text, contracts, fixtures,
ADRs and code. HEAD and the actual index digest are unchanged; only this requested directory
is new. Existing local work was neither staged nor cleaned. Preservation scope and the exact
initial status are in proposal-checks.json; it does not claim a hash audit of ignored caches.

## Inherited checks and remaining dependencies

A/B author, coordinator and independent-review outcomes retain their original targets and
attribution. This session read their handoffs and existing evidence; it did not rerun the
full suite, nominal/physical matrix, historical discovery/replays, native fault experiments,
all-tree lint/types/import/schema CI, hosted CI, cold clones, nightly, benchmarks or silicon.
The focused test suite's report fixtures are software tests, not fresh qualifying reports.

A public v2 table cannot currently be constructed through the admitted public product path.
It requires accepted v2 table/report carriers and CLI/build/report integration, model/source/
review eligibility, coefficient/contributor closure and genuine applicable declaration review.
This proposal supplies honest raw v2 execution plus the exact dependency instead of fabricated
product evidence. Existing v1 output remains RoPE-incomplete and C0/STUB. No interpolation,
accuracy band, energy validation, positive card eligibility or completed migration is inferred.

Historical B reports need their compatible historical checkout/environment for historical
validation, or fresh reports at a clean committed current implementation for current coverage.
Even their recorded historical successful validation did not make the partial rung pass.
Their current refusal is a source-binding boundary, not evidence of a candidate arithmetic bug.
No guard was bypassed and no report's identity was relabeled.

Native M/K1/K2/B/R/T is accepted design only. Exact toolchain/license closure, mapped carriers,
independent human-worked expectations, reference/product decisions and implementation remain
future separately authorized work. Full tables first serve U7; rk-sim integration is U10.
Performance/nightly and final same-commit publication checks remain open. STUB, unknown error,
unverified energy, no final tag and no U4 authorization are explicit throughout the narrative.

## Exact file identities

SHA256 of the deliverables and bounded supporting evidence below (handoff and the subsequently
refreshed preservation receipt are not self-hashed):

| File | SHA256 |
| --- | --- |
| [proposed-how-it-works.md](proposed-how-it-works.md) | `f46e96de645f52d260ba575414c0b5f0cbdae752ba0c5e1eebdfda277af167be` |
| [how-it-works.patch](how-it-works.patch) | `d0487b5a706b3713cb7895113aef93619294725cd2b084084e8489f623f03350` |
| [check-evidence.py.txt](check-evidence.py.txt) | `5c5209e4adfa010bb59bf27cc4443581a6e0215d8b810686b1aa6e1c448b6234` |
| [reproduce-v1.py.txt](reproduce-v1.py.txt) | `531b2e21740efc5bd494e0c56fccdb8d31a3c08c45ab16eebfcd0de8ffbccdc8` |
| [validate-proposal.py.txt](validate-proposal.py.txt) | `2933aa109374ee3e4f83c1dc8f2d0357a780124d2a46f93c1b08fe00b1e7342f` |
| [checks.json](checks.json) | `98ef6040ce6c440a8bc48f4b2da47f791dfe7fcd1428e2e726b0d4e31367bdd3` |
| [public-workflow.json](public-workflow.json) | `60d7f387243ccf3d441c8730c012cee2e67033cf235ef1b93647a5bcad6a628a` |
| [focused.log](focused.log) | `3671d1dd5e62a7b4af8593210280973aef74c5f210fdcc48b252f2109c788697` |
| [report-tests.log](report-tests.log) | `43a2574b6129e6a61804c1bfe71531ce4cb8578f60f0f43d0f307194ead5110f` |
