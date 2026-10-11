# U2 · Lane B · U-REVIEW Stage 1 (adversarial review)

Status: **Stage 1 complete — awaiting Stage 2 author response.** Stage 1 evidence only; no verdict,
no fixes, no Stage 3 adjudication, no sprint closure.

Reviewer independence: fresh Claude Code session (Opus 5.5) launched by Javid from
`docs/reviews/U2-final-review-launch/lane-B-stage-1.txt`. I did not author any of the
reviewed code in this conversation. No agents were spawned.

## Summary

Reviewed commit `769a1fef2320430386888bf450af579ea26cf664` (tree `926e3651…`), the full U2 diff from
`1e9e794`, lane-B scope plus A carriers and CLI where they reach users.

| # | Severity | One line |
| --- | --- | --- |
| F1 | BLOCKING | `uarch table` embeds a caller-supplied model card: a proposed design's verified table carries `measured`, a stub card carries a "validated" band, and a non-null `energy_verification` is accepted |
| F2 | BLOCKING | R202 executed on the complete adopted package: adopted-oracle recipes may drop peak, bandwidth, efficiency, precision, tp and input fingerprint after rehash + re-review and still verify and render |
| F3 | BLOCKING | Hosted CI on this exact commit will fail: `ruff check .` (141 errors in committed review scripts/historical fixtures) and `mypy src contract scripts` (duplicate module) |
| F4 | BLOCKING | The default report hides N in "conditional · N stipulations", contrary to the joint exit text |
| F5 | NON-BLOCKING | `safe_prose` redacts identifiers: the model name, tp, mapping policy, op IDs and all 1,008 fixture labels become indistinguishable; fixture coordinates are hidden even in opt-in |
| F6 | NON-BLOCKING | README quickstart fails; reviewed contexts can only be authored by test helpers with synthetic reviews; `uarch table` needs the spec file beside the bundle |
| F7 | NON-BLOCKING | 16 authoritative doc links (U0003's normative design, the execution plan's U2 authority) resolve only to untracked archives; U0004 cites a missing file; B indices are stale |
| F8 | NON-BLOCKING | `uarch characterize` prints unbadged STUB durations, beyond its specified content |

Confirmed good, by my own execution: 1019/1019 tests; CI test, contract and licence commands; RR-C1 (public
CLI fresh-YAML = saved-canonical bytes, and full-matrix `sha256:0202c04d…`); a complete adopted full-matrix
run on 769a1fe reproducing the committed 9,962-member manifest `e0ef6e34…` byte for byte; nominal 1,008/1,008
exact (duration rel 0); physical 96 executed (all `failed`) / 48 `execution_failed` / 864 `not_run` retained
and rendered; default hides all 40,320 ratios, opt-in shows 18,768 labelled; no `±0`, timestamps or scripts;
B05/S10 fail closed; numeric proof rules and badge combination hold under independent oracles and fuzzing.
Pending: the U0021 GitHub cold clone and hosted CI on the same published commit.

## 0. Target identity and environment

| Item | Observed |
| --- | --- |
| Integration worktree | `/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration`, branch `u2/integration` |
| HEAD | `769a1fef2320430386888bf450af579ea26cf664` (matches prompt) |
| Tree | `926e3651b1a5f88a5b6d54e19453ce7d206482e8` (matches prompt) |
| Sprint base | `1e9e794a84c5173812c23a1cf2fc04b85e6f6831` (peeled u01-end); 7 commits, 670 files, +217259/−533 |
| Tracked status at start | clean (`git status --porcelain --untracked-files=no` empty); 87,456 untracked archive files present and ignored for review purposes |
| Scratch checkout | `git clone --no-checkout` of the integration repo + `git checkout 769a1fe` into my session scratchpad (`…/scratchpad/u2b-review`), verified HEAD/tree identical, clean |
| Interpreter | `/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python`, CPython 3.12.14, jinja2 3.1.6, pydantic 2.13.5 |
| Host | ElfinKidsLaptop, Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39, 16 CPUs, 15 GiB RAM |
| Env for every run | `PYTHONPATH=.:contract:src PYTHONDONTWRITEBYTECODE=1`, `python -B`, pytest `-p no:cacheprovider`, private `XDG_CACHE_HOME` under my scratchpad. Verified `rkuarch.__file__`/`uarch_contract.__file__` resolve inside the scratch checkout, not the main worktree's editable install |

Nothing was installed, no network was used, no oracle generation was run, `UARCH_HUMAN` was
never set, no hooks were bypassed, and no tracked integration file was modified. Reviewer
outputs are this file plus `docs/reviews/U2-final-review-B/` (both new, uncommitted). At the end:
integration HEAD/tree unchanged (`769a1fe`/`926e3651`), 0 tracked or staged changes. Concurrent change
outside this session: the `rk-uarch-u2-a` worktree's `u2/analytic` moved from `8b35302` (at my start) to
`769a1fe` during the review. I only cloned read-only from the integration repo, and the review target did
not change. Large generated outputs (1.9 GB full-matrix run, R202 copy) remain only in my session
scratchpad.

## 1. Executed checks (all on the scratch clone of 769a1fe unless stated)

Logs copied (scratch path replaced by `$SCR`) to `docs/reviews/U2-final-review-B/logs/`.

| # | Command (env as in §0) | Result |
| --- | --- | --- |
| E1 | `python -B -m pytest -p no:cacheprovider -q --tb=short` | **1019 passed**, 0 failed/skipped, 215.99 s; tree still clean (`logs/full-suite.log`) |
| E2 | CI `python` job test step: `pytest -q -m "not nightly and not silicon and not native and not golden and not determinism"` | 1019 passed, 220.19 s (`logs/ci-pytest-markers.log`) |
| E3 | CI `python` job lint step: `ruff check .` | **exit 1, 141 errors** (`logs/ci-ruff-u2b-review.log`); same command on base `1e9e794`: exit 0 |
| E4 | CI `python` job typecheck step: `mypy src contract scripts` | **exit 2**: "Source file found twice under different module names: tests.u2_comparison and contract.tests.u2_comparison"; base: exit 0, 47 files. `mypy src contract/uarch_contract scripts` and `mypy` (pyproject `files`) both pass (65/62 files) |
| E5 | CI `lint-imports` | 2 kept, 0 broken (target and base) |
| E6 | CI `contract` job: `scripts/vendor_rk.py --check`; `pytest -q -rs contract/tests --require-vendor`; `python -m uarch_contract.generate --check` | all exit 0; 579 contract tests passed |
| E7 | CI licences step `pytest tests/unit/test_third_party.py` | 2 passed |
| E8 | README quickstart `uarch table hw/designs/npu-l4.yaml --model llama-3.1-8b --precision bf16 --engine analytic` | **exit 2**: requires `--output --assumptions --context --model-card --artifact-dir` |
| E9 | Public CLI chain `e2e_cli.sh` (H1, llama-3.1-8b, bf16, tp 8, synthetic assignment, 6 rows): `uarch prepare` → reviewer-authored context (`author_context.py`, production `table_recipes` + explicitly synthetic reviews, because no product command authors one) → `uarch table` (YAML; `PYTHONHASHSEED/OMP=4` variant; canonical saved input) → `uarch report` default + `--show-unvalidated-predictions`, twice, plus from the saved-input table | YAML vs saved-canonical table **byte-identical** (`5a9e7351…`); thread/hash-seed variant byte-identical; `--workers 4` refused `UnsupportedWorkers` with no output; both report modes byte-identical on repeat and from the saved-input table (`logs/e2e3.log`). First attempt needed the H1 spec JSON added to `--artifact-dir` (`ArtifactMissing: sha256:3b7186…`) although the bundle embeds it |
| E10 | Independent serialized scan `scan_report.py` (does not import rkuarch) over E9 HTML/MD | default: only visible digit outside hashes/paths is `Producer version: 1`; no `±`, no timestamps, no `<script>`/`src=`, no SVG; opt-in: 6 SVGs, labelled values, `n_samples` still hidden. Stipulation count default **hidden**; model name renders `llama[numeric text withheld][numeric text withheld]b` (`logs/scan-e2e3.json`) |
| E11 | Forged model-card probe `forge_card_probe.py` via public `uarch table`/`uarch report` | **accepted**: see F1 (`logs/forge-card.log`, `logs/forge-band.log`) |
| E12 | `b05_s10_probe.py` (B's committed fixture builder + production evaluator) | B05/S10 fail closed with discriminating controls (§4) (`logs/b05-s10.log`) |
| E13 | `numeric_probe.py`: independent Decimal/struct oracle for the accepted proof numeric rules | 0 failures over 2,000 binary64 conversions, 3,000 terminating round trips, 3,000 outward roundings (§3) (`logs/numeric.log`) |
| E14 | Adapted full adopted-matrix driver `runtime_driver_adapted.py` (§7) | exit 0, 25/25 phases, 2,140 s; output manifest `e0ef6e34…` = committed receipt (`logs/runtime-adapted.log`) |
| E15 | `r202_probe.py` on a private copy of my fresh complete package | see F2 / §7a (`logs/r202.log`, `logs/r202-results.json`) |
| E16 | `uarch characterize hw/designs/npu-l4.yaml --model llama-3.1-8b --precision bf16 --tp 8 --synthetic-assignment` | exit 0; Markdown inspected (F8) (`logs/characterize-h1-llama8b.md`) |
| E17 | Focused case tests (A-F12, selected rank, padding, capability refusals, split efficiency, precision matrix, export consumer, R2 report tests, proof never-promote) | 56 passed (`logs/focused-cases.log`); plus `c04_padded_probe.py` padded-vocab pre-engine refusal (`logs/c04-padded.log`) |
| E18 | `badge_fuzz.py` randomized worst-of/ceiling/combine | 20,000 cases, 0 violations (`logs/badge-fuzz.log`) |
| E19 | Option-A guard mutation (comment-only edit to `proof_raw.py` in a `git archive` export) | isolation suite errors on the exact hash pin; unmodified export: 35 passed |
| E20 | `link_check.py` over committed authoritative docs | 16 untracked-only links, 1 missing-everywhere mention (`logs/link-check.log`) |
| E21 | Independent nominal threshold recomputation from captured `nominal.json`; physical outcome census from `physical.json` | §7 |

## 2. Findings

Severity is my Stage-1 judgement. "Category" = code / unmet test coverage / human-policy
choice / future work. Reproductions use the scripts in `docs/reviews/U2-final-review-B/`
with the §0 environment and the scratch clone as CWD.

### F1 — BLOCKING (code) — The table embeds a caller-supplied model card badge and error band that the honesty layer never derives or caps: a proposed design ships `measured`

- **Symptom.** `uarch table --model-card card.json` validates the card only structurally
  (`src/rkuarch/cli.py:237`), embeds it in the hash-bound table (`src/rkuarch/table/build.py:258,307-309`),
  and the offline verifier checks only that the embedded summary equals the card and that
  card evidence IDs appear in the context index (`src/rkuarch/table/artifacts.py:416-420,468-469`).
  The contract only requires a non-stub badge to list *some* evidence ID
  (`contract/uarch_contract/model_card.py:71-75`). B's `build_model_card`
  (`src/rkuarch/provenance/model_card.py:19`) is never called outside one unit test, and no code applies
  the proposed-design ceiling, scope applicability, synthetic exclusion or band derivation to the
  embedded card. `badge_for`'s ceiling (`src/rkuarch/provenance/badge.py:60-61`) applies only to
  report-local assessments.
- **Reproduction.** `bash e2e_cli.sh $SCR/e2e3`, then
  `python -B forge_card_probe.py $SCR/e2e3 $SCR/forge-measured measured`. The card is the probe's
  stub card with `badge: measured` and `evidence: ["b1-actual-no-band-incomplete-scope"]`. That is the
  committed **synthetic L3 counts** fixture `tests/fixtures/u2_b/evidence-no-band.json`, whose scope names
  another model and no bundle, added to the context's `evidence_index`.
- **Observed.** `uarch table` exit 0; the table for H1 (`design_status: proposed`) contains
  `provenance.model_card.badge = "measured"`; `load_verified_report_inputs`/`uarch report` accept it;
  the report prints `Supplied card badge (not eligibility): measured` next to
  `Model badge: STUB — …`. Same with `estimated`. Variant (`logs/forge-band.log`): a **stub** card with
  **no evidence** and `validated_error_band {low_rel: 0.0, high_rel: 0.02, scope: …}` is accepted and the
  band is embedded in the table; the report hard-codes `Validated model error: unknown`, so the table
  and its own report disagree. Third variant, lower certainty because it depends on consumer reading
  (`logs/forge-energy.log`): a card with `energy_verification = {L0: {all five families: null}, L2:
  {…: null}}` is accepted and embedded as a non-null object, although build-spec §2 defines
  `energy_verification` as `None` ("unverified") until every used family has an L2 reference. The
  report still prints "energy unverified".
- **Expected.** CLAUDE.md invariant 7 ("Nothing may raise a badge. A proposed design is never above
  estimated"); U0004 ("A proposed design never exceeds estimated … L0–L2 … the model remains stub");
  U-P4 1.c ("capped at estimated … Enforced in code, with a test") and 2 ("validated_error_band is None
  unless ledger entries whose scope covers this request supply it"). Build-spec §8 U-P19 item 4 makes
  rk-sim take the uarch model's badge **from the table's model_card badge**, so the product artifact,
  not only the report, must be capped and derived. The table should refuse, or store only an
  honesty-layer-derived card: stub here, no band.
- **Impact.** A hash-verified U2 table can carry a better-than-allowed calibration and a fabricated
  "validated" band into the C2 consumer, while the report is silent apart from a text field. This is not
  a pending-case label: it executes through the public CLI today.

### F2 — BLOCKING (code + unmet test coverage; resolves the R202 question) — Adopted-oracle (reference) recipes may drop the original peak, bandwidth, efficiency, precision, tp and input fingerprint after rehash + re-review; the complete package still verifies and renders

- **Symptom.** For reference-side source recipes the only structural requirements are: the ratio's
  reference pointer is reachable with the reference model identity
  (`contract/uarch_contract/report_context.py:246-266`), and each source recipe contains at least one
  `prepared_content`, one `model_assumption` and one `model_evidence` leaf (`:351-354`). The required
  timing-input set exists **only** for `physical-resolved` duration recipes (`:360-375`), and the
  computation-source check covers only actual engine results (`src/rkuarch/table/artifacts.py:270-333`).
  Nothing binds the adopted-oracle duration recipe to its component peak, bandwidth, execution-model
  efficiency, precision, tp or input fingerprint. The review record is an administrative, content-addressed
  artifact anyone can re-issue, so it cannot carry that guarantee.
- **Reproduction (executed).** `r202_probe.py <copy of my fresh complete adopted package> …`
  (`logs/r202.log`, `logs/r202-results.json`). For one adopted-oracle duration source recipe
  (`/fixtures/864/values/duration_s/value` of the reference inventory, fixture
  `llama-3.1-70b/bf16/bf16/tp1/npu-l4.yaml/0`, a `uarch_projection` binding), delete **one** selector at a time. Then rehash `MetricDependencies`, issue a fresh synthetic
  `accepted`/`independent` review over the new subject, rebind `ReportContext` and the table identity, and
  call the public `verify_report_inputs`.
- **Observed** (`uarch_projection` recipe; the retained-component `.55` recipe result is in §7a):

  | Deleted selector | Result |
  | --- | --- |
  | `prepared_content /model`, `/model_shape`, `/query` (input fingerprint) | **ACCEPTED** |
  | `prepared_content /precision` | **ACCEPTED** |
  | `prepared_content /tp` | **ACCEPTED** |
  | `model_assumption /reference_model` | **ACCEPTED** |
  | `hardware_leaf /params/0/value` (original BF16 peak) | **ACCEPTED** |
  | `hardware_leaf /params/1/value` (original `hbm_bw`) | **ACCEPTED** |
  | `model_assumption …/compute` (npu-l4 nominal efficiency 1.0, `6121a063…`) | **ACCEPTED**; full default report then rendered (136 MB, 268 s), e.g. `/comparisons/0/fixtures/864/channels/4/raw_rel → magnitude hidden · STUB …` |
  | `model_evidence /reference_model` | refused `IncompleteMetricContributors …/model/workload` |

- **Expected.** R202 (`tests/fixtures/u2_b/r2-mutation-cases.json`): "Delete reference model or original
  component peak/bandwidth/.55 efficiency/precision/tp/input fingerprint from complete adopted-oracle
  recipe; rehash and re-review → IncompleteMetricContributors; cannot borrow actual model or value-only
  provenance." U0004: "R2 numeric ratios inherit the complete actual, reference and adjustment
  dependencies recursively. Rehashing and reviewing a recipe cannot authorize omitted required computation
  inputs." The existing tests (`tests/unit/test_u2_b_report.py:59-109,126-151`) cover cycles, ambiguity,
  purpose, physical timing hardware, reference-model removal and ratio-level reference removal, but not
  this reference-recipe completeness. The ledger's own note ("positive closure alone does not promote it")
  was correct. **R202 is genuinely missing required behavior**, not a pending label.
- **Impact.** A comparison ratio can present a reference duration as fully contributed while its declared
  contributors omit the hardware and efficiency that produced it. Because every ratio is STUB and hidden by
  default, today's numeric exposure is limited to opt-in, but the contributor list (the honesty claim
  itself) becomes forgeable for the oracle side.

### F3 — BLOCKING (code; publication gate) — The exact commit will fail the hosted `ci` python job at lint and typecheck

- **Symptom.** `.github/workflows/ci.yml:13-16` runs `uv run ruff check .` and
  `uv run mypy src contract scripts`. At 769a1fe, `ruff check .` exits 1 with 141 errors, all in committed
  evidence scripts under `docs/reviews/**.py` (e.g. `U2-adoption-v2-execution/runtime_driver.py` ×41,
  `final_verify.py` ×11, `U2-artifact-adoption-v2/audit.py` ×15, `U2-adoption-v1-execution/prepared-replay.py` ×14)
  and in `tests/fixtures/u2_b/historical-u1/rk/schema/*.py`. `pyproject.toml [tool.ruff]` excludes only
  `contract/vendor`. `mypy src contract scripts` exits 2 before checking anything, because
  `contract/tests/u2_comparison.py` and `tests/u2_comparison.py` map to the same module name.
- **Reproduction.** `ruff check .` and `mypy src contract scripts` in the scratch clone (E3/E4).
  Control: the same commands on base `1e9e794` pass (ruff "All checks passed!", mypy 47 files). The narrowed
  `mypy src contract/uarch_contract scripts` passes, so there is no underlying type error.
- **Expected.** U0021 requires hosted Ubuntu CI on the exact published commit; check 1 requires the
  joint exit from a cold clone. The adoption README says "modified-test lint passed" and "type checks
  were not rerun", so the receipts never ran the CI commands as CI runs them. When this commit is
  published, the `python` job fails at `lint`, so its test step never runs in CI.
- **Lane.** `.github/workflows/` and `scripts/` are lane B; the offending evidence scripts are review
  records; the duplicate module name spans contract/tests (both lanes) and tests/.

### F4 — BLOCKING (code; exit criterion) — The default report hides N in "conditional · N stipulations"

- **Symptom.** `Document.provenance` renders the stipulation count through `badged` with a stub
  combination of the stipulated inputs (`src/rkuarch/report/complete.py:251-270`), and `badged` hides every
  stub magnitude by default (`src/rkuarch/report/badged.py:43-44`).
- **Reproduction.** E9 `r1/default.md` line 177, and the full adopted default report from my run:
  `**Stipulation inventory count**: magnitude hidden · STUB — input inventory; not a prediction; …`.
  Only the opt-in mode shows `59.0 stipulations · STUB — input inventory …`. The 59 stipulated hardware
  values themselves are also hidden by default.
- **Expected.** Execution-plan §3 U2 joint exit: "`uarch report` defaults to hidden STUB magnitudes …,
  shows "conditional · N stipulations""; U-P4 item 4 "conditional: if built as specified (N
  stipulations)"; `src/rkuarch/report/README.md:5`. A count of declared stipulations is a property of the
  input spec, not a model prediction. U0001's addendum and U0003 item 5 scope the default-hidden rule to
  "STUB computed predictions". The only test of the count
  (`tests/unit/test_u2_b_report_surfaces.py:137-170`) renders with `show_unvalidated_predictions=True`, so
  no test covers the default exit wording. **Category:** code plus unmet test coverage. If Javid prefers
  hiding stipulated input values by default, that is a human-policy choice; the explicit count in the
  exit text still needs a decision.

### F5 — NON-BLOCKING (code; human-policy input) — Numeric-prose redaction destroys categorical identities, so model, tp, mapping policy and fixtures are unreadable

- **Symptom.** `safe_prose` (`src/rkuarch/report/prose.py:18-27`) replaces every digit run outside a small
  allow-list. It is applied to identity text: model name (via `fields`, `complete.py:341`), mapping policy
  (`:315`), operator IDs (`:537`), comparison fixture IDs (`:575`), reviewer names, hardware rationales and
  refusal reasons (`:589`).
- **Observed.** `/request/model/name: llama[numeric text withheld][numeric text withheld]b`, the same text
  for llama-3.1-8b and llama-3.1-70b; `Mapping policy: analytic-ops@[numeric text withheld]`; every decoder
  operator is `decoder[numeric text withheld]/…`. In my full adopted report, the 672 llama fixture
  entries of the physical section collapse to **7 distinct labels** (e.g. all 72 executed llama/npu-l4
  fixtures read identically `llama[…][…]b/bf16/bf16/tp[…]/npu-l[…].yaml/[…]: executed; failed`). Each fixture's `query/batch`,
  `total_context_tokens`, `global_kv_heads` and `global_vocab` render "magnitude hidden … no reviewed numeric
  recipe" **even with `--show-unvalidated-predictions`**. The 48 capacity failures read
  `WeightCapacityExceeded: [numeric text withheld] > [numeric text withheld]`.
- **Expected.** U-P4 requires "separately named nominal compatibility and complete physical comparison
  failures/unassessed/refusals" and that the report distinguish producer/mapping interpretation. Nothing
  false is shown and every row stays hash-bound, but a human cannot tell which workload a discrepancy or
  capacity failure belongs to, which defeats inspecting the 96/48/864 inventory. Declared query
  coordinates and identifiers are not predictions. Low-risk direction: do not redact identifier fields;
  give declared fixture coordinates the existing `declared_input` treatment.

### F6 — NON-BLOCKING (docs/usability; human-policy for exit wording) — The documented table→report path is not runnable as written; reviewed contexts can only be authored by test helpers

- **Symptom.** `README.md:11-12` documents `uv run uarch table hw/designs/npu-l4.yaml --model llama-3.1-8b
  --precision bf16 --engine analytic` and `uv run uarch report tables/<hash>.json`. The first exits 2 (E8):
  `--output --assumptions --context --model-card --artifact-dir` are required (`src/rkuarch/cli.py:170-178`).
  The `--context` must be a reviewed `ReportContext` whose `MetricDependencies` name the result hashes of
  this capture. No product command or `scripts/` tool authors one. Every end-to-end table→report path in
  the repo and in the receipts uses test helpers with synthetic reviews (`tests/u2_comparison.py:697`,
  `tests/integration/test_u2_a_replay.py:27-28`: "Production must receive actual reviewed context from B"),
  as does my E9 (`author_context.py`). Additionally, `uarch table` resolves the registry's
  `hardware_spec_hash` only from `--artifact-dir` (`src/rkuarch/cli.py:238-241`), so a fresh YAML run
  fails `ArtifactMissing: sha256:3b7186…` unless the spec JSON is copied there, although the bundle embeds it.
- **Expected.** The joint exit's first step is `uarch table hw/designs/npu-l4.yaml … --engine analytic →
  uarch report`; check 11 requires READMEs to be true. Whether "…" may include a context authored by test
  scaffolding with synthetic reviews, or B owes a production context-authoring path in U2, is a human
  decision. I recommend recording it explicitly before the cold-clone exit rather than letting the
  validator improvise.

### F7 — NON-BLOCKING (docs/publication; human-policy) — Authoritative committed docs point at unpublished archives, and B-owned indices describe superseded state

- **Unpublished authority.** A link check over the committed ADRs, execution plan, how-it-works, lane-B
  READMEs/indices and U2 acceptance records found **16 links whose targets exist only as untracked
  local archives**. A GitHub cold clone will 404 on them. They include
  `docs/decisions/U0003-one-chip-one-set-of-facts.md`, whose "normative design" is the untracked
  `docs/reviews/U2-inputs/A-R1-R2-proposal-8def4c6d2c27/` package, and its common baseline;
  `docs/execution-plan.md` ("Current U2 authority: … common baseline" → untracked
  `U2-common-baseline-v1.md`, plus kickoff/A1/A2/B2 records); and `hw/U2-sourcing-inventory.md`
  (→ the B1 snapshot). `docs/decisions/U0004…md` cites `docs/reviews/U2-B-checkpoint-1-handoff.md`,
  which exists **nowhere**, tracked or untracked. Reproduce: `link_check.py` (E20); the full list is in
  `logs/link-check.log`.
- **Superseded B-owned status text (check 11).** `tests/fixtures/u2_b/README.md:3` ("All 64 semantic cases
  … remain **pending execution**"; "The 14 runnable tests …"; report-context deliverables "intentionally
  pending") and `acceptance-cases.json` `limitation` contradict the current 56/8 ledger.
  `hw/U2-sourcing-inventory.md` (last paragraph) still says export/bridge/oracle generation/adoption
  "remain outstanding", but the v2 adoption is committed. `src/rkuarch/provenance/README.md`
  says `validated_error_band is None ("unknown") unless in-scope ledger entries supply it`, which F1
  falsifies at the table. `docs/how-it-works.md:13` says "No U2 producer or engine is implemented yet".
  That one is expected to be refreshed by the standing how-it-works session, so I note it only.
- **Not a new code defect.** The prompt already acknowledges preserved archives; the point is
  that publication of 769a1fe as-is leaves the accepted normative design unreachable from the published
  repository. Committing (or manifest-binding) the referenced packages versus amending the links is a
  human choice.

### F8 — NON-BLOCKING (code; check 2; uncertainty: medium) — `uarch characterize` writes unbadged STUB duration magnitudes for humans by default

- **Symptom.** The joint-exit demo command `uarch characterize hw/designs/npu-l4.yaml --model llama-3.1-8b
  --precision bf16 --tp 8 --synthetic-assignment --output …` writes a Markdown twin
  (`logs/characterize-h1-llama8b.md`) whose tables print `Duration ps 1882111296.0 | U-C0 ps 1882111296.0`
  and per-op `Duration ps`. The word "STUB" appears nowhere, and there is no permission check or opt-in.
  The same row and per-op durations render `magnitude hidden · STUB — unvalidated model prediction` in the
  default `uarch report`.
- **Expected.** Check 2 ("Does any number reach a human without its badge? … check CLI output paths");
  `src/rkuarch/report/README.md` ("the only way a number reaches a human"); U0003 item 5 / U0004
  Presentation (default-hidden STUB magnitudes, adjacent STUB labels on every numeric surface).
  Build-spec U-P3 item 8 specifies characterize as "FLOPs, bytes, operational intensity, op class and shape
  regime". **Durations are outside its specified content**; counts are inside it.
- **Uncertainty.** The page is headed "unvalidated physical predictions … no evidence or accuracy claim",
  and characterize is lane A's selection tool. Whether it is a governed numeric surface is a human-policy
  call. Durations are not needed for its stated purpose either way.

## 3. Three formulas re-derived independently (lane-B scope)

1. **Badge combination** (`src/rkuarch/provenance/badge.py:48-64`, `report/evaluation.py:19-42`). From U-P4 1.a–e
   and U0004: badge = min over (claim provenances ∪ model-evidence rungs); stipulations excluded and recorded;
   both empty → stub; proposed → ≤ estimated; combination never above any nonempty part. The code matches.
   `badge_fuzz.py`: 20,000 random multi-claim/stipulation/model cases, 0 violations (worst-of, ceiling,
   empty→stub, `conditional_on` preserved, combine monotone) (`logs/badge-fuzz.log`). Limits: the
   report-local ceiling does not reach the table's embedded card (F1). A non-input recipe with only claims
   and no model gets `complete=False` (hidden) but its label would show the claim badge. That is
   unreachable with `table_recipes`-generated dependencies, so I record it as residual risk only.
2. **Proof numbers** (`src/rkuarch/provenance/proof_raw.py:253-333`). Re-derived from recommendation 2 of the
   accepted proof decision: exact rational of the captured binary64; `ps` ÷ 10¹² exactly, `s` unchanged;
   canonical terminating decimals, nonterminating relative error → `UNSUPPORTED_NONTERMINATING_ERROR` *before*
   the null-band shortcut; band high = least binary64 ≥ exact max; all-zero max → null; overflow unsupported.
   Code matches; `numeric_probe.py` with an independent Decimal/struct oracle found 0 failures. Observation
   only: a JSON *integer* capture above 2⁵³ is rounded through `float()` (2⁵³+1 → 2⁵³). Captured counts are
   serialized as binary64 floats, so the accepted rule ("captured binary64 value") is not violated.
3. **Roofline quantities the report plots** (`complete.py:515-523`, captured A fields). Operational intensity =
   matrix_ops/(read+write bytes); achieved = matrix_ops/(duration_ps·10⁻¹²); ridge = matrix_peak/dram_bw;
   per-op duration = max(compute, memory), with compute = matrix/peak + vector/vpeak (serialized, D6). My E9
   table: 102 ops, **0 mismatches** against my independent recomputation; no row faster than its U-C0; row
   duration = Σ per-op durations (per_op mode) ≥ U-C0 = max(ΣC, ΣM). SVG coordinates
   x = 40+500·v/max, y = 300−260·v/max use only permitted values (head/embedding (0,0) → (40,300); ridge
   524.288 op/B at x = 540).

## 4. Case reconciliation (B64 namespace only; ledger unchanged by me)

Namespaces: the B64 ledger (`acceptance-cases.json` B/S/D/R1/R2/C ids) is distinct from the original
26-case preparation namespace (`original_preparation_26`, which **also** uses B01–B26) and from the
proof namespaces original77 (which **also** uses S01–S05) / revision42 / PR3nine. All ids below are B64 ids.
I do not change any count. The 56 executed / 8 pending ledger stands until the author and Javid act.

| Case | Evidence I executed / identified | Recommended disposition |
| --- | --- | --- |
| **B05** (reference design, measured claims, matching target L4 → measured only within full covered scope) | E12: synthetic L4 control reaches `measured` (reference) / `estimated` (proposed) only in explicit evaluator test mode; the same record as `real` → stub with "real measurement/order protocol verification not delivered at B2"; 20k-case badge fuzz. **But** F1: the table's supplied card reaches `measured` with no in-scope evidence at all | Positive real path: **accepted unsupported** (proof decision). Negative "not measured without full scope": **genuinely missing at the table/card boundary (F1)**; do not close B05 until F1 is fixed and has a regression |
| **S10** (four energy families covered, static missing → unverified) | E12: all five families → stub/"energy unverified"; every report prints "energy unverified; no energy quantity produced"; `build_table` refuses context `used_energy_families` ≠ consumed (known-empty) (`table/build.py` `ReportContextMismatch`) | Positive nonempty-family verification: **accepted unsupported**. Negative: **executed now (fail-closed)**. F1's non-null `energy_verification` variant should be closed with F1 |
| **R202** (delete reference model / original peak / bandwidth / .55 efficiency / precision / tp / input fingerprint from the complete adopted-oracle recipe; rehash + re-review → IncompleteMetricContributors) | **Executed now** on my complete adopted package (`r202_probe.py`); see F2 | **Genuinely missing required behavior** except the reference-model deletion. Not satisfiable by positive closure checks |
| **C04** (uniform-rank comparison with replicated/padded/uneven counts → A-F12 pre-call refusal) | Executed focused tests: replicated KV pre-call for nominal (`test_af12_refuses_before_candidate`) and physical (`test_real_physical_af12_refuses_before_engine`); conserved explicit/synthetic selected-rank embedding (`test_selected_rank…`, `test_d7…`). **New probe** `c04_padded_probe.py`: padded vocabulary (V=7, tp 2) refused before the engine. Nominal nonuniform-context refusal exists (`nominal_candidate.py:88`) | **Covered by identified tests + executed probe.** Reporting half: pre-call refusals render as `refused` with no fabricated values (`complete.py:627`). Recommend promotion once a padded-vocab regression is committed |
| **C06** (split/unknown efficiency, zero clock, nonbase scalable DRAM, unsupported block scale → named refusal, no silent conversion) | `test_capability_refusals` (zero-rounded clock, scalable DRAM, width, block scale, peak, KV) executed. Split efficiency is refused at the adopted-input boundary (`scripts/vendor_rk.py:877` "accepted scalar input required") and is explicitly modelled, not silently converted, in the isolated nominal candidate (`test_split_memory_and_retained_point55`). Unknown efficiency is unrepresentable (required `SourcedValue` in (0,1]) | **Covered by identified tests**, except a split-efficiency `export_component` → loader round trip (lane A). Recommend promotion after A confirms the split export path is intended to be supported rather than refused |
| **C07** (physical conventions, all discrepancies exposed, partial residency unknown) | My full run: physical track 96 executed / 48 `WeightCapacityExceeded` / 864 not_run + 4 direct refusals, gate `not_assessed`, evidence `execution_failed`; all channels rendered with their status; `peak_resident_bytes` render "unknown / not modelled", never 0. E9: attention `full_square`, all-token head and paged KV visible in `characterize` | Reporting half **executed now**, subject to F5 (fixtures not identifiable). Physical-convention half is lane A, outside this report |
| **C09** (invalid/unsupported format, unsupported chip KV, duplicate pairs, missing key) | `test_B2_explicit_bindings_reject_missing_duplicate_and_inferred_inputs`, `test_AB2_C1_unsupported_KV_and_changed_pair_refuse`, strict `vendor_rk.py --check`, plus the 1008-unique-selection test; all executed | **Covered by identified tests** except an out-of-vocabulary format string at the descriptor boundary; small gap, recommend one literal negative |
| **C10** (truth export with stipulations; mismatched spec/projection/bytes/execution binding → refuse; round trip at the pinned loader) | `test_AB2_C1_rehashed_inconsistent_source_projection_refuses` (6 rehashed mutations), `…wrong_execution_input_refuses` (7), `test_rehashed_wrong_derivation_and_wrong_execution_are_refused`; the loader re-exports and re-projects every bound export (`table/artifacts.py:201-235`) | Mismatch refusal: **covered by identified tests**. "Round-trip real emitted bytes at pinned upstream loader": only the human-generated adopted outputs evidence it; no test executes `contract/vendor/…/rk/components/loader.py` on emitted bytes. **Unresolved decision** whether received human generation discharges it |

RR-C1 (claimed fixed): **verified.** Public CLI fresh-YAML vs canonical saved-input tables are byte-identical
(E9, 59 conditions sorted by path). My full adopted run's `rebuild_saved_canonical_table_producers_disabled`
phase asserted `replay == package`, and `tests/integration/test_u2_a_condition_order.py` passes. Side
note for the separate original-26 namespace: its B20 ("fresh-to-saved identity blocked by RR-C1") now has
supporting evidence. I do not re-disposition it.

## 5. U-REVIEW rubric (checks 1–11), lane-B view

| # | Check | What I did | Result |
| --- | --- | --- | --- |
| 1 | Joint exit on the designated host from a cold clone | Fresh clone of the **local** integration repo at 769a1fe (not GitHub); full suite, the CI job commands, the public CLI chain (E9), `uarch characterize`, and my adapted full adopted-matrix driver (§7) | Local exit elements run, with F4 (default N hidden), F6 (context authoring only via test scaffolding; README command fails) and F3 (CI commands fail). **The GitHub cold clone on ElfinKidsLaptop WSL2 and same-published-commit hosted Ubuntu CI are PENDING** (commit unpublished); per F3 the hosted `python` job is predicted to fail as committed. Not called the final gate |
| 2 | Any number reaching a human without its badge | Template lint read (`render.py:22-54`); independent serialized scan of default/opt-in HTML+MD (E10, full-matrix surface phase); CLI outputs `report`, `characterize`, `validate` | `uarch report`: no unbadged magnitude in default; opt-in labels every number; no `±`; no timestamps; no scripts/fetches; nulls "unknown / not modelled". **F8**: `characterize` prints unbadged durations. `validate` prints source inputs with kind/rationale (input listing, not a prediction; acceptable) |
| 3 | Golden changes | `git diff --stat 1e9e794 HEAD -- tests/golden` | none; `tests/golden/{expected,scenarios}` empty, so CI golden/determinism jobs are conditional no-ops |
| 4 | Numerical smells (lane-B code) | Read provenance/report for unordered iteration, units, null-as-zero; PYTHONHASHSEED/thread variation (E9) | Ordered: `sorted`/`dict.fromkeys` throughout; byte-identical under hash-seed/thread variation; diagnostics/energy never 0; units carried per field; no cycles/time conversion in lane-B code. Three formulas: §3 |
| 5 | Provenance | `git grep` for stipulations outside `hw/designs/`; H1/H2 hashes vs B1 acceptance; draft references location; reference loader refusal test | Stipulations elsewhere only in the npu-l4 export/derivation records that U0004 requires to carry them. H1 `41731f6a…`, H2 `e12d08d4…` exact; `hw/references/` empty (`.keep`), drafts only under `tests/fixtures/u2_b/hardware-review/`; `test_reference_deep_stipulation_is_refused` passes. Derived kind/provenance never better than inputs (`badge_for`, fuzz) **except the embedded model card (F1)** |
| 6 | Evidence | Card promotion, band zero, frozen predictions, `check_ordering` | Zero-width bands refused by `EvidenceRecord`/`ModelCard` (`high_rel > 0`). **F1**: an unpromoted, out-of-scope card is embedded. No `validation/L3_silicon/*/predictions/` exist and `check_ordering.py` does not exist at base or target, so check_ordering could not be run (CI `ordering` job is a conditional no-op). Not applicable at U2 |
| 7 | Fidelity / C2 rule | Table `composite_fidelity` and `fidelity_detail`; rows vs U-C0 | C0 with levels 0/0/0 exact; no C2 row; no row faster than its U-C0 (E9: 6 rows) |
| 8 | Determinism 1 vs N workers | `uarch table --workers 4` | **Not applicable as N>1**: refused `UnsupportedWorkers` with no output (fail-closed, consistent with invariant 4). Substitute: PYTHONHASHSEED/OMP 1 vs 4 byte-identical; report repeat byte-identical; full-matrix repeat/replay stream-identical (§7). Threads 1 vs 4 exact mode is U9 scope |
| 9 | Native-vs-fork harness | — | U6+ scope; no native sources (`native/crates` has no `.rs`); not applicable |
| 10 | Out-of-scope builds (build-spec §1.3) | Read lane-B diff | None found in lane B (no web UI, studies, mapping search, new IR). `src/rkuarch/study/` is README-only |
| 11 | READMEs still true | Read changed READMEs/indices | **F7** (fixtures README, hw inventory, provenance README vs F1), **F6** (root README quickstart); `docs/how-it-works.md` stale but owned by the standing refresh |

## 6. Pending publication checks (not executed, not claimed)

- U0021 fresh **GitHub** cold clone on ElfinKidsLaptop Ubuntu/WSL2 at the exact published commit, plus
  hosted Ubuntu CI run URLs on the same commit, distinguishing executed jobs from conditional no-ops
  (`golden`, `determinism`, `native`, `perf`, `ordering` and the `patches` step are no-ops at 769a1fe because
  their inputs are absent). The `python` job is predicted to fail as committed (F3).
- Reviewed local commit of any Stage-2 changes, separately authorized publication to main, tag, cleanup.
  None performed by me.
- U3 self-hosted runner, nightly re-enable and performance-host requirements remain (no WSL2 benchmark).
- Link targets in F7 must be published or the links amended before a cold clone can read the accepted
  normative design.

## 7. Complete adopted full-matrix run, executed by me (not inherited)

- **Harness.** `docs/reviews/U2-final-review-B/runtime_driver_adapted.py`, a copy of the committed
  `docs/reviews/U2-adoption-v2-execution/runtime_driver.py` with the four-line delta documented in its
  header. The committed driver writes `runtime-progress.json` and `output-location.json` into its own
  committed evidence directory and pins HEAD `14fa0ed` plus an uncommitted 5-path delta, so it must not run
  in place. Its helpers (`U2-B-real-report-exits-v1/real_report_driver.py`, `serialized_surface_check.py`)
  were loaded unchanged from the scratch clone. Outputs went only to my scratchpad.
- **Command.** CWD = scratch clone, `PYTHONPATH=.:contract:src PYTHONDONTWRITEBYTECODE=1
  REVIEW_ROOT=<clone> REVIEW_EVIDENCE=<scratch> python -B runtime_driver_adapted.py`. **exit 0**, 25/25
  phases passed, 2,140 s, with the R202 probe running concurrently (`logs/runtime-adapted.log`,
  `logs/runtime-progress-adapted.json`).
- **What it executed.** Adoption authority and strict audit of the canonical vendor path (manifest
  `f8220c94…`, inputs `9a30b290…`, review `5ab5192e…`); fresh 1,008 nominal-candidate calls, 96 H1 physical
  point calls and 6 H1 preparations (no oracle generation). Then, with preparation, physical point, nominal
  candidate, capture and analytic producers trapped: package (3,310 files, 24 rows, 59 conditions, 46,296
  recipes, 14,904 sources), public disk and memory load, both render modes, independent serialized
  HTML/Markdown check (default 0 of 40,320 ratios visible; opt-in 18,768 visible, 21,552 withheld, HTML ==
  Markdown), repeat byte equality, saved physical result verification, canonical saved-input rebuild
  (**RR-C1: fresh and replayed table both `sha256:0202c04d…`**), replay package and report stream
  equality (3,316 files), and three rehashed RenderSpec capability refusals
  (`RenderIdentityBindingMismatch`).
- **Independent corroboration.** My 9,962-member output manifest digest is
  **`e0ef6e3424681a010a0f4e9b3b02f3aad2564e224c35cdddeea09498f0c2f6af`, identical to the committed
  `final-verification.json`**. Render file hashes, coverage counters, RR-C1 identity and refusals equal
  `runtime-progress.json`. The only use I made of the optional `/tmp/u2-adoption-v2-runtime-rxh7iex5/outputs`
  was to compare its `SHA256SUMS` with mine (identical). All other evidence above is from my own run.
- **Independent of the driver's assertions.** From my captured `nominal.json`: 1,008/1,008 executed,
  max |duration rel| = **0** exactly, no declared count adjustments, residual 0; the gate is
  `compatibility_pass` and evidence `refused` (four direct precision observations). Comparator thresholds
  `contract/uarch_contract/comparison.py:94,328,349,357` are 0.05 / 0.005 / 0.001 with timing adjustments
  refused, matching the accepted budgets. Physical track (`captured/physical.json`): 96 executed, **all
  `failed`** (every executed duration channel differs from nominal; matrix_ops 87 failed / 9 passed;
  vector_ops 96 unassessed; write bytes 48 unassessed), 48 `execution_failed` (24 llama-3.1-70b, 24
  mixtral-8x7b; `WeightCapacityExceeded`), 864 `not_run`; gate `not_assessed`, evidence `execution_failed`.
  Every channel renders its status in both modes. These are retained discrepancies, not defects;
  nominal agreement establishes no physical full-workload accuracy, and the report does not claim it.
- **What this does not show.** It is the same driver logic as the receipts, re-run on the exact target,
  not an independent oracle. Its `save_render` and `serialized_surface_check` assertions check the
  comparison ratios only, not the stipulation count (F4), the redaction (F5) or the embedded card (F1).

## 7a. R202 on the retained-component (.55) adopted-oracle recipe

Same probe, second recipe: `/fixtures/0/values/duration_s/value`, fixture
`llama-3.1-70b/fp16/fp16/tp1/asic_placeholder.yaml/0` (retained upstream descriptor `de3c0032…`, execution
model `bd096f8c…` = `scalar_efficiency 0.55`, `accepted_input`). Each single deletion, then rehash, fresh
synthetic re-review, context and table rebind, then `verify_report_inputs`:

| Deleted selector | Result |
| --- | --- |
| `prepared_content /model`, `/model_shape`, `/query`, `/precision`, `/tp` | **ACCEPTED** (each) |
| `model_assumption /reference_model` | **ACCEPTED** |
| `hardware_leaf /params/fp16_tflops` (original component peak) | **ACCEPTED** |
| `hardware_leaf /params/hbm_bw` (original bandwidth) | **ACCEPTED** |
| `model_assumption …/compute` (**the .55 efficiency**) | **ACCEPTED** |
| `model_evidence /reference_model` | refused `IncompleteMetricContributors …/model/workload` |

Total over both recipes: **16 of 18 single-selector deletions accepted**; only removing the reference
model's `model_evidence` refuses (`logs/r202.log`, `logs/r202-results.json`; 2 × 10 full-package
verifications, about 3–4 min each). The R202 "cannot borrow actual model" half appears enforced
(**source-derived, not executed by me**): the model-identity checks at `report_context.py:340-345`
refuse a substituted model, and the committed R201/R208 tests exercise model removal.

## 8. Source-derived observations (no finding)

- Positive real eligibility cannot arise in the report path: `Evaluator.recipe` always calls
  `assess_evidence(..., allow_synthetic=False)` (`src/rkuarch/report/evaluation.py:118-127`); real records
  stop at "real measurement/order protocol verification not delivered" (`applicability.py:176-179`);
  energy always stops (`:159-163`); `interpret_ordering` and `interpret_measurement` always end
  `ProofUnsupported`; expected sources need synthetic kinds plus explicit test mode (`proof.py:686-691`).
  The model badge line in every report is hard-coded STUB. Executed: E12. The gap is the card (F1), not
  the evaluator.
- Proof `/2` member handling (`proof.py:294-380`): null `source_record_hash` resolves to the *containing*
  member's owner; role names are checked per field; unused optional members are rejected; every member is
  re-hashed against its declared digest and must be in the table's declared closure. I found no
  path-escape or rehash substitution that yields eligibility. Rehashed substitutions produce a different,
  internally consistent closure that still cannot promote (fail-closed by construction).
- Option-A guard: the committed `contract/tests/vendor_support.py` (`f56e666e…`) differs from the accepted
  AD-C2 bytes (`4892004b…`, applied in `a9facbb`) only by a line wrap in `7aab97d`. Behavior verified: a
  comment-only edit to `proof_raw.py` in a throwaway export makes the isolation suite error on the exact
  hash pin (`638f8135… != 9f47439f…`). The byte drift is unrecorded in the AD-C2 record; it is a
  bookkeeping matter only.
- Adopted artifacts: `MANIFEST.json` `f8220c94…`, `u2-inputs/SHA256SUMS` `9a30b290…`, pin `1e5706e…`,
  `parity/fixtures.json` 1,008 rows and `refusals.json` 4 entries, unchanged since `7aab97d` (v1). Strict
  `vendor_rk.py --check` passes.
- H1 stipulation rationales render "B1 hardware proposal, pending Javid: …" in every report. These are the
  exact accepted bytes, so this is historical wording, not a defect, but readers will see "pending" on
  accepted inputs.
- Opt-in renders counts as floats (`59.0 stipulations`, `8.0 ranks`) because of `roundtrip-display/1`. Style only.

## 9. Residual risks

- Report-local assessments are recomputed at render time from supplied recipes. Any recipe class without
  a structural completeness rule (F2) is only as complete as its author made it; reviews do not help.
- The comparison harness and A-F12 guards live in `contract/tests/` and `tests/` support modules, by the
  accepted S design, so their guarantees depend on test code paths being the ones the human runs.
- Full-matrix report generation takes ~2–4 min per render and ~2 min per full verification on this host.
  Mutation coverage of the complete package is therefore expensive; most closure negatives run only on
  small fixtures.
- Hosted CI has never run any U2 commit; the predicted lint/type failure (F3) means the first hosted run
  will not reach the test step.

## 10. Required author response (Stage 2)

Respond to every finding, F1–F8. BLOCKING items: **F1** (embedded card badge/band/energy not derived or
capped), **F2** (R202 reference-recipe completeness), **F3** (CI lint/typecheck on the exact commit),
**F4** (default "N stipulations"). For F5–F8, either fix them or record the human-policy decision
(identifier redaction and declared fixture coordinates; how the joint-exit context is authored; the
publication of normative archives; whether `characterize` is a governed numeric surface). Case
dispositions in §4 need author and Javid confirmation; I changed no counts. Stage 3 needs, for each
APPLIED item, a regression test that fails without it (F1: forged card at `uarch table`; F2: one selector
deletion per R202 category on an adopted-oracle recipe; F4: default-mode count visible).

---

## Stage 3 — adjudication (2026-10-09)

Same independent B reviewer session that wrote Stage 1 above. Stage 1 text is preserved unchanged:
its prefix is the first 49,723 bytes of this file, SHA256
`f121636d0d7b74a940bd52f34e637a7d09d58c366decf9c7999afa3bbb1dfb4b` (equal to the coordinator's
`B_review_sha256`). U-REVIEW Stage 3 checks only: (a) a row for every finding, (b) rejected reasons address
the finding, (c) applied (and here, proposed) resolutions have tests that fail without them, with one
random revert. No new findings, no fixes, no staging/commit/publication/adoption/closure. This is not
Javid's protected-path or config approval.

### Inputs and target (verified)

| Item | Identity |
| --- | --- |
| Author response (read-only) | `rk-uarch-u2-b/docs/reviews/U2-lane-B-response.md` SHA256 `ab3d7f72…a242` ✓ |
| Adapter supplement (read-only) | `…/U2-lane-B-response-adapter-addendum.md` SHA256 `b9cc912f…3d4` ✓ |
| Reviewed baseline | `769a1fef2320430386888bf450af579ea26cf664`; integration HEAD unchanged, 0 tracked changes |
| Overlay tree (accepted A + 19 live B paths, no proposals) | `47b212854f7585b09275e71e098ad54570d8d6bf` |
| **Adjudicated candidate tree** | **`b87187981a83229b8e5055cef39809020cbf0601`** (44 paths vs base; path list identical to `B-stage2-review-paths.txt`) |
| Identity checks I ran | all 19 B paths in the overlay byte-equal the live B worktree; all 10 accepted-A paths equal tree `5c2b7f1d…`; applying the three proposed patches (`A-loader-adapter` `ef5b20e6…`, `A-characterize-adapter` `d77d0b7d…`, `shared-CI-contract-proposal` `b4041e17…`) to a `git archive` of the overlay reproduces a `git archive` of the candidate **byte for byte** |

All tests and reverts below ran in private scratch exports (`git archive`) with
`PYTHONPATH=.:contract:src PYTHONDONTWRITEBYTECODE=1`, `python -B`, pytest `-p no:cacheprovider`, the
same interpreter as Stage 1. Small scripts and logs are in `docs/reviews/U2-final-review-B-stage3/`.
**Executed by me** unless marked "receipt".

### Independently executed checks

| # | Check (candidate tree unless stated) | Result |
| --- | --- | --- |
| S1 | Full suite | **1,203 passed, 2 failed** (`test_current_snapshot_generator_compatibility`, `test_current_canonical_is_exact_adopted_1008_four_real_refusals`, both `input support inventory changed`), 1,205 cases, 302.8 s. Count reconciles with the stated 1,159 + 3 recursive + 5 net adapter + 38 A. Not hosted CI (`logs/cand-full-suite.log`) |
| S2 | The coordinator's nine focused modules | 188 passed, 140.5 s (reproduces receipt) (`logs/cand-focused.log`) |
| S3 | `test_u2_b_stage2_cards.py` on the **overlay** (no A loader adapter) | **56 failed** (7 attacks × 4 boundaries × 2 designs), 18 passed (direct validator + STUB controls) (`logs/overlay-cards.log`) |
| S4 | **R202 at public loaders**, my own Stage 1 complete adopted package (unchanged copy, table `sha256:0202c04d…`), `r202_public_probe.py` | Positive controls: disk load (87.6 s) and memory verify **accepted**. 20 single deletions + 16 distinct wrong-source substitutions × {`verify_report_inputs`, `load_verified_report_inputs`} = **72/72 refused** `IncompleteMetricContributors: adopted reference …`, for projection 1.0 and retained .55 (`logs/r202-public.*`). Four reference-model "substitutions" were skipped because both profiles share that selector; the helper tests cover that case with a distinct model |
| S5 | Public CLI chain from Stage 1 (`e2e_cli.sh`) on candidate + independent `scan_report.py` | Table bytes unchanged (`5a9e7351…`); reports repeat byte-identically and fresh-YAML = saved-canonical. Default: `conditional · 59 stipulations` visible; model `llama-3.1-8b`, mapping `analytic-ops@1`, op IDs `decoder-0/…` exact; 28 declared request/grid inputs visible, each labelled `declared captured input; not a measurement; source=sha256:…`; every computed prediction still `magnitude hidden · STUB`; no `±`, timestamps or scripts (`logs/e2e-cand.log`, `logs/scan-cand.json`) |
| S6 | Full adopted default and opt-in render with candidate code (my package) | Renderer `u2-complete-report/2`. Physical fixture labels **1,008, all distinct** (Stage 1: 672 llama labels collapsed to 7); 3,024 physical coordinates visible as source-bound declared inputs; ratio visibility unchanged: **default 0, opt-in 18,768**; count line visible in both modes (`logs/full-render.log`) |
| S7 | Stale RenderSpec | `renderer_version u2-complete-report/1`, rehashed: **`RenderIdentityBindingMismatch`** in both modes; current specs render (`logs/stale-spec.log`) |
| S8 | `test_u2_b_stage2_display.py` copied onto a base `769a1fe` export | **10 failed** (6 count/mode, 3 identity/escaping, 1 coordinate binding); all pass on candidate (`logs/base-display.log`) |
| S9 | Characterize regression, overlay vs candidate; `uarch characterize` (Stage 1 command) | overlay 1 failed / candidate 2 passed. Candidate Markdown has no `Duration ps`/`U-C0 ps`; counts read `… · STUB`; raw JSON **byte-identical** to Stage 1 (`logs/characterize-*.log`) |
| S10 | Proposed CI commands | `ruff check .` pass; `mypy src contract/uarch_contract scripts` 66 files pass; `mypy --no-explicit-package-bases contract/tests` 28 files pass; old monolithic `mypy src contract scripts` still exit 2; lint-imports 2 kept; schemas fresh; **`vendor_rk.py --check` refuses** `input support inventory changed`; contract tests 577 passed / 2 failed (`logs/ci-*.log`) |
| S11 | Random revert (below) | see next section |

### Random revert (criterion c)

- **Selection.** `random_selection.py`: sorted list of the five implemented behavioral corrections in the
  candidate (B-F1 loader card call, B-F2 loader reference call, B-F4 count, B-F5 identities/coordinates,
  B-F8 characterize), `random.Random(int(candidate_tree_hex, 16)).randrange(5)` → **B-F2 loader call**
  (`validate_reference_contributors` in `src/rkuarch/table/artifacts.py`).
- **Revert.** Only that 15-line hunk removed in a scratch copy (`scratch-revert-F2-loader-call.diff`);
  everything else is identical to the candidate.
- **Original symptom returns** (`r202_revert_subset.py`, my package): positive memory verify accepted;
  retained .55 peak deletion **ACCEPTED** (memory and disk); .55 efficiency deletion, `/tp` deletion and
  projection-1.0 `/precision` wrong-source **ACCEPTED** (`logs/r202-revert.*`). The candidate refuses all
  of these (S4).
- **Committed regressions after the revert:** **209 passed, 0 failed**
  (`test_u2_b_stage2_reference.py`, `test_u2_b_comparison_orchestration.py`, `test_u2_b_refresh.py`,
  `test_u2_b_stage2_cards.py`, `test_u2_b_report.py`, `test_u2_a_stage2_export_loader.py`;
  `logs/revert-f2-committed-tests.log`). **No committed test fails without the proposed loader
  integration.** The R202 helper tests call the helper directly; the orchestration and refresh tests
  load valid packages only (positive controls). Public-boundary refusals exist only in the author's
  evidence drivers (receipt) and in my probe.
- **Supplementary control, not the random pick.** Reverting only the helper's timing requirement
  (`scratch-revert-F2-helper-timing.diff`) makes exactly the **12** peak/bandwidth/efficiency ×
  delete/wrong-source × two-profile helper cases fail and 35 pass (`logs/revert-helper-reference.log`).
  The helper regression is discriminating; its loader integration is not covered.

### Per-finding adjudication

| Finding | Author disposition | (a) row | (b) rejection | (c) discriminating tests / my execution | Live vs proposed status | Stage 3 result |
| --- | --- | --- | --- | --- | --- | --- |
| **B-F1** card badge/band/energy | DEFERRED overall; B helper applied, A loader adapter proposed | ✓ | none | ✓ S3 (56 fail without adapter, pass with); STUB/null controls pass; refusals at build, CLI, memory and disk for reference and proposed designs. Placement covers every original public path: `build_table` and `write_table` call `verify_report_inputs`; `render_verified` re-verifies; `write_report` uses the disk loader. Note: wrong-model and wrong-scope cases share the generic "no applicable real evidence" refusal, because the bounded U2 profile admits no positive card at all | Adapter **unapplied** in live A | Proposed fix **adequate**; deferral concrete (exact patch, owner A). **Finding remains OPEN** until the adapter is installed |
| **B-F2** R202 | DEFERRED overall; helper applied, same A adapter proposed | ✓ | none | Helper ✓ (40 + selected + recursive cases; helper revert bites). Public behavior correct in my S4 (72/72), with full and selected positive controls. Raw-member requirement uses the adopted manifest-listed `parity/fixtures.json` bytes via the existing raw resolver, with no new authority (control/missing-raw/changed-row tests). Original model-evidence omission was already refused at baseline; it is now refused earlier by the new check, and the response keeps it separate. **✗ No committed regression fails when the loader integration is removed (random revert)** | Adapter **unapplied** in live A | **Row at fault under (c)**: the proposed resolution's public-boundary claim rests on driver evidence, not a committed discriminating test. **Finding remains OPEN** |
| **B-F3** CI lint/type | DEFERRED; exact 12-file shared proposal | ✓ | none | ✓ S10: both namespace-separated strict commands pass; the 21 lint exclusions are explicit files (14 review scripts + 7 historical fixtures); no skip/xfail/ignore. Ten contract-test edits are typing refactors; the two changed assertions keep semantics (the physical threshold assertion is preserved; the CI-coverage assertion accepts the exact split commands verbatim). Strict-support tests and `vendor --check` still refuse, as the author states | Proposal **unapplied**; protected-path/config decision not mine | Deferral adequate. **Finding remains OPEN**; hosted CI not green and not claimed green |
| **B-F4** "conditional · N stipulations" | APPLIED (live B) | ✓ | none | ✓ S8 (6 fail on base); S5/S6 serialized: integer count visible in both modes; hardware values and STUB predictions keep their permissions | Live in B; selected for the candidate | **Satisfied** for Stage 3 |
| **B-F5** identifier redaction | APPLIED (live B) | ✓ | none | ✓ S8 (identity/escaping/coordinate tests fail on base); S5/S6: exact model/mapping/op/fixture identities, `<script>` escaped, arbitrary prose still redacted, coordinates bound to inventory/intent (mismatch refuses), predictions still permission-gated; renderer `/2` and stale `/1` refused (S7). Residual: refusal-reason prose (e.g. `WeightCapacityExceeded` magnitudes) stays redacted under the stated prose policy | Live in B | **Satisfied** for Stage 3 |
| **B-F6** public companion workflow | DEFERRED | ✓ | none | Not applicable (no behavior). The proposal has an exact interface, an A/B owner split, refusals, a test plan and an estimate; it keeps the public exit unmet and adds no auto-accepted or synthetic review | Proposed only | Deferral adequate. **Finding remains OPEN** |
| **B-F7** publication/stale docs | DEFERRED overall; live B text corrections APPLIED; subclaim corrected | ✓ | Subclaim correction **valid**: `U2-B-checkpoint-1-handoff.md` exists untracked in the B worktree and in the preserved B1 snapshot `U2-inputs/B1-05daf76bfda1/…`, both SHA256 `27ddb979…`. My Stage 1 "missing everywhere" checked only the integration-root path and was overstated. The clean-clone gap stands | Live B text corrections are accurate and promote no cases. The corrected B docs now link `docs/reviews/U2-lane-B-response.md`, which is outside the selected tree: same publication gap | Corrections live in B; link/publication proposal coordinator-owned | Subclaim correction accepted. **Finding remains OPEN** (publication, U0004 citation repair, how-it-works pending) |
| **B-F8** characterize timing | DEFERRED to A; exact patch proposed | ✓ | none | ✓ S9: regression fails without the patch and passes with it; timing columns removed from the human Markdown, counts labelled STUB, raw JSON durations byte-identical. This resolves the Stage 1 finding as proposed: durations were the out-of-scope part | A patch **unapplied** | Proposal adequate. **Finding remains OPEN** until coordinated A disposition |

**Adapter supplement (A-F2 dependency, not a B finding).** On the candidate, the corrected
`test_u2_b_report_adapter.py` exercises the production `rkuarch.cli.app` registration with
saved-A3 and current-capture positives. The same assertion helpers detect removed and no-output
`report` registrations and missing `report`/`validate` help. All 7 cases pass with the accepted A CLI
(S1/S2). The historical A4 `cli-adapter.json` blob is identical at base and candidate (`4d2eb009…`). Reviewer A's
two adapter failures are corrected **for the candidate configuration I tested**; the two strict-support
failures remain open.

### Verdict

**NOT ACCEPTED — row at fault: B-F2 (criterion c).** The randomly selected correction (the proposed
loader call for R202) can be removed while every committed regression still passes, and the original
exploit returns at both public loaders. Remedy for Stage 2 re-response: add a committed test that drives
`verify_report_inputs` and `load_verified_report_inputs` with an adopted-oracle package (a small selected
inventory suffices). Cover at least one deletion and one wrong-source per R202 category for both the .55
and 1.0 profiles, plus a positive control, and show it fails with the loader call removed.

All other rows meet (a)–(c) for their stated status. B-F4 and B-F5 are satisfied as applied fixes;
the B-F7 live corrections and subclaim correction are accepted. B-F1, B-F3, B-F6 and B-F8 deferrals are
adequately specified, and their proposed fixes passed my discriminating checks. **None of B-F1, B-F2,
B-F3, B-F6, B-F7 or B-F8 is closed or pre-accepted.** They stay open until the proposals are actually
installed and integrated, or the human decisions are recorded.

### Unresolved gates (unchanged by this adjudication)

- A loader adapter, A characterize patch and the shared CI/contract-test proposal are unapplied in live
  A/shared paths; protected-path/config approval belongs to Javid and the shared owners.
- Both strict-support tests and `vendor_rk.py --check` refuse the changed support set. A combined
  source/input freeze and separately authorized human generation/adoption are required; no relabelling
  or `UARCH_HUMAN`.
- Old v2 report/generation hashes bind the old sources and renderer `/1`, not this candidate. My S6
  render is a check, not an artifact.
- U0021 GitHub cold clone and same-published-commit hosted Ubuntu CI have not run. B-F6/A-F3 public
  companion workflow, B-F7 normative publication, how-it-works refresh, and the eventual commit
  selection's own lint verification remain open.

---

## Stage 3 — narrow B-F2 criterion (c) re-adjudication (2026-10-09)

Same independent B reviewer session. Scope: only the B-F2 row that failed the Stage 3 adjudication
above. No new findings, fixes, staging, commit, adoption or closure. All earlier bytes are preserved:
the first 64,619 bytes of this file (Stage 1 + Stage 3) have SHA256
`ff2ee42f947da7950024a1ba64602b31e17bed6f1e041d016d6ace8628bc9326`. Scripts and logs are in
`docs/reviews/U2-final-review-B-stage3-R202/`.

### Target and identity (verified)

- Author correction `rk-uarch-u2-b/docs/reviews/U2-lane-B-response-R202-correction.md`, SHA256
  `70f92a34…0fff` ✓. The original response (`ab3d7f72…`) and supplement (`b9cc912f…`) are unchanged.
- **Tested tree: `b5e530e17d3b7511216a229c56263ca9be3b902c`.** `git diff b8718798… b5e530e1…` shows exactly
  one added path, `tests/integration/test_u2_b_r202_public.py` (330 lines, SHA256 `e6808706…125b` ✓). A
  fresh `git archive` export differs from my prior candidate export only by that file. Production code,
  adapters, CI proposal and earlier tests are byte-identical. This is a review tree, not a live
  installation of the A adapter.

### Evidence class of the new test (from reading + execution)

- **Authentic, committed adopted-oracle inputs.** It authenticates `contract/vendor/rk-sim@1e5706e…/MANIFEST.json`
  = `f8220c94…`, checks every member it reads against that manifest (full `parity/fixtures.json`, component
  descriptors, precision entries, export/execution carriers, `GENERATOR.json`, `refusals.json`,
  `compute.py`), and checks H1 hardware bytes against the frozen support member. The inventory is the
  committed `tests/fixtures/u2_b/stage2/reference-inventory.json`, reduced to fixtures 0 and 864.
  `classification == "adopted_oracle"` is asserted, and the full raw rows member is supplied, as the
  production validator requires for a selection.
- **Actual side:** the committed saved A3 capture (an earlier real analytic computation), via the existing
  `CapturedWork` carrier and `tests/u2_comparison.report_package`. No producer, engine run or invented
  engine output.
- **Constructed declarations:** both comparison tracks are built in the test with fixtures
  `execution: not_run` (no candidate values) and the real captured precision-refusal observations, then
  checked by `validate_comparison`. Administrative dependency/registry reviews are explicitly synthetic.
  No oracle values, hardware claims, review authority or source authority are invented.
- **Portable:** ran from a pure `git archive` export, so no untracked file exists. It reads only tracked
  paths (verified for the manifest, H1 YAML, reference inventory and A3 table). Grep finds no `/tmp`,
  `docs/`, network, subprocess, `UARCH_HUMAN`, generator or `load_inputs` use outside comments.
  `nominal.candidate_identity()` is a constant identity (no candidate execution). Ruff check and format pass.

### Executed checks (mine)

| Step | Configuration | Result |
| --- | --- | --- |
| 1 | Corrected tree, normal pytest discovery, `tests/integration/test_u2_b_r202_public.py` | **84 passed**, 0 failed/errors/skips, 24.5 s (`logs/candidate.*`) |
| 1a | Entry points | Negatives call `verify_report_inputs` (memory) or `load_verified_report_inputs` on a real on-disk package (canonical/raw files, no symlinks). There is no helper call, mock or shortened verifier. My spy probe confirmed the **real** `validate_reference_contributors` runs inside both loaders for the unmodified package (2 calls) (`probe_r202_fixture.py`, `logs/probe-fixture.log`) |
| 1b | Rehash/re-review closure | Each mutation re-reviews the exact changed dependency subject, then rehashes the dependencies, context and table, runs `verify_review` and `verify_declared_artifact_closure` **outside** `pytest.raises`. A stale hash or setup error would therefore error the test, not satisfy it. The revert run (step 3) shows every refusal is hook-caused |
| 2 | Wrong-source semantics (probe) | All 10 category indices map to the intended selector (kind/pointer) in **both** profiles. All 20 substitutions change `artifact_hash` and resolve to an existing valid object. 12 of 20 keep the **same value from a different source**: model, shape, query and tp (both profiles are llama-3.1-70b tp1), plus both reference-model fields. So identity, not value, is what is tested. The reference-model donors are distinct, valid `adopted_oracle` single-selection inventories for the *other* fixture, with an equal `reference_model` value: a genuine wrong-source control, not swapped identical selectors |
| 3 | Scratch copy, **only** my original 15-line `validate_reference_contributors` hook removed (diff equals my Stage 3 `scratch-revert-F2-loader-call.diff`; loader `c3b769fd…` → `c6d79fe6…`; helper `96bbab06…`, card validator `ed9959ed…` and the card hook unchanged) | **76 failed, 8 passed**, 0 errors/skips (`logs/reverted.*`). All 76 failures are `DID NOT RAISE IncompleteMetricContributors`, i.e. accepted forgeries. The 8 passes are the 4 positive controls and the 4 pre-existing `reference-model-evidence` **deletion** refusals (memory/disk × both profiles), which are baseline-enforced and not required to newly fail. My original exploits are among the failures: `original-peak-delete-retained-.55-{memory,disk}` and `precision-wrong-source-projection-1.0-{memory,disk}` |
| 4 | Same scratch copy, exact hook restored (loader SHA back to `c3b769fd…`; tree identical to the export) | **84 passed** (`logs/restored.*`). Identical 84 node IDs across candidate/reverted/restored |

Per boundary and profile with the hook present: each of {retained .55, projection 1.0} × {memory, disk}
refuses all 10 deletions and all 10 wrong-source substitutions (80/80) and accepts its positive control
(4/4). With the hook removed, each combination accepts 19 of the 20 forgeries; only the
model-evidence deletion is still refused. I did not rerun the full suite or adjacent modules (not
required for this single additive test); the earlier 1,203/2 full-suite result binds tree `b8718798…`
only. Received but not re-executed: the author's three-run XML, adjacent 216-pass run and scoped
lint/types; the coordinator's 84-pass run and 84 identical node IDs.

### Verdict

**ACCEPTED — the B-F2 criterion (c) coverage gap is resolved** on tree `b5e530e1…`. An ordinary,
portable, pytest-discovered test now fails (76 accepted forgeries) when the proposed loader integration is
removed, and passes when it is restored. It uses authentic committed adopted-oracle sources and the full
public loaders.

With the sole faulted row cured, my Stage 3 adjudication of the B Stage 2 response (response, adapter
supplement and this correction) is **ACCEPTED for U-REVIEW response checks (a)–(c) only**. That does not
install or approve anything:

- The A loader adapter (and with it the B-F1/B-F2 production protection), the A characterize patch and
  the shared CI/contract-test proposal remain **unapplied proposals**. **B-F1, B-F2, B-F3, B-F6, B-F7 and B-F8
  remain OPEN** as previously adjudicated. B-F4/B-F5 stay satisfied.
- Javid's protected-path/config decision is not granted by this review.
- Both strict-support gates (`input support inventory changed`), the combined source/input freeze,
  human generation/adoption, the public companion workflow, normative publication, how-it-works refresh,
  the eventual commit selection's lint, U0021 GitHub cold clone and same-commit hosted CI, tagging and
  sprint closure all remain pending.

---

## Stage 3 — public companions follow-up (2026-10-10)

Same original independent B reviewer session. U-REVIEW Stage 3 checks only, for the approved
public companion workflow and the now-installed corrections. No new Stage 1 findings, fixes,
author-file edits, ledger changes, generation/adoption, staging, commit or closure. All earlier
bytes are preserved: the first 72,169 bytes of this file (Stage 1 + Stage 3 + R202 recheck) have SHA256
`8e33167e02cd423a335a40981202673013b0d78002bf715cd92c278940cadac6`. New scripts and logs are in
`docs/reviews/U2-final-review-B-companions/`. This review issues no evidence records. Every
accepted review used below is explicitly SYNTHETIC test or probe scaffolding, not the pending actual
external-review demonstration.

### Target and identity (verified)

- **Reviewed target: Git tree `57e975842bf70583680c68e19e80af77bb42d8d0`** (not a commit); installed baseline
  tree `b5e530e17d3b7511216a229c56263ca9be3b902c`; original commit `769a1fef…`. `git diff b5e530e1 57e97584`
  changes exactly the 9 listed paths. B-authored: `src/rkuarch/provenance/companions.py`,
  `tests/unit/test_u2_b_companions.py`, `docs/companion-assembly.md`. A-authored: `cli.py`,
  `table/companions.{py,md}`, two companion test files, `tests/u2_a_companion_inputs.py`.
- Handoffs match the reconciliation hashes: A `b4a29063…`, B `84e8f96a…`, A follow-up `f978fc87…`.
  Approval/install records were read: `U2-final-corrections-v1-acceptance.json` (Javid "approve", exact three patch
  SHA256s), installed baseline, installed checks (receipt: 1,287 passed / 2 failed at `b5e530e1`).
- **Installation verified by me:** the installed tree `b5e530e1` is byte-for-byte the tree I adjudicated
  in the R202 recheck. All 53 target paths (45 installed + 8 new) equal the target blobs in the
  **live** integration, A and B worktrees, uncommitted, with HEAD `769a1fe` and empty indexes. The installed
  F1/F2/F3/F8 files (`table/artifacts.py`, `workload/characterize.py`, `ci.yml`, `pyproject.toml`,
  `model_card.py`, `reference_contributors.py`) have identical blobs in the installed tree, the target and live
  integration.

### Executed checks (mine, on a `git archive` export of the target)

| # | Check | Result |
| --- | --- | --- |
| P1 | Coordinator's exact selection (`test_u2_a_companions`, `test_u2_a_companions_cli`, `test_u2_b_companions`, `test_u2_a_stage2_cli`, `test_u2_a_cli`, `test_u2_b_report_adapter`, `test_u2_b_complete_report`) with `-rs` | **124 passed, 0 failed/errors/skips**, 223 s (no pending-peer skip) (`logs/target-selection.*`) |
| P2 | Static: `ruff check .`; `mypy src contract/uarch_contract scripts`; `mypy --no-explicit-package-bases contract/tests`; `lint-imports`; schema `--check`; `vendor_rk.py --check` | pass; 68 files; 28 files; 2 kept; fresh; **vendor refuses** `input support inventory changed` (`logs/static.log`) |
| P3 | Installed-correction regressions on target: R202 public (84), cards (74), characterize, display, reference helper, `test_u_p2_review.py` | **265 passed, 1 failed: `test_production_isolation`** (`logs/installed-regressions.log`) |
| P4 | **Full suite on target** (not the old baseline count) | **1,380 passed, 3 failed**, 1,383 cases, 667 s: the two strict-support gates **plus** `contract/tests/test_u_p2_review.py::test_production_isolation` (`logs/target-full-suite.*`) |
| P5 | Isolation guard, baseline vs target | `b5e530e1`: **passed**; `57e97584`: **failed**, `production vendor isolation: src/rkuarch/cli.py:[447, 510]`, i.e. the new `import importlib` and `importlib.import_module("rkuarch.provenance.companions")` in A's `companions assemble` adapter (`logs/isolation-guard-baseline-vs-target.log`) |
| P6 | Public CLI chain, my own script `public_chain_probe.sh` (H1, llama-3.1-8b, bf16, tp 8): `assumptions → prepare → capture → companions draft` | Draft README marks UNREVIEWED; no ReviewRecord or registry generated |
| P7 | Refusals via `uarch companions assemble` with my SYNTHETIC records (`author_synthetic_reviews.py`) | not-independent, rejected → `UnacceptedReview`; wrong subject → `ReviewSubjectMismatch`; family missing → `AmbiguousFamily`; family duplicated → registry validation `AmbiguousFamily`; neither intake flag → `ComparisonIntake`. **All exit 2, no `context.json` written** (`logs/public-chain.log`) |
| P8 | Positive synthetic control: `assemble --no-comparisons` → `table --capture-dir` twice → `report` default + opt-in → overwrite attempt | Assemble exit 0; table bytes repeat-identical; context `evidence_index {}`, `verification_hashes []`, `comparison_hashes []`, `used_energy_families []`; table card STUB, empty evidence, null band/energy, C0, `not_attempted`. Default: `conditional · 59 stipulations`, `llama-3.1-8b`, predictions `magnitude hidden · STUB`, energy unverified, no `±`/timestamps/SVG. Opt-in: labelled STUB values. Overwrite refused `OutputConflict` (`logs/public-chain.log`, `logs/chain-scan.json`) |

Covered by P1 (my execution): PC-C1 distinct twins and overwrite refusal; PC-C2 production refusal of the
original wrong-index declaration (`bound comparison identity`) and omitted attempt
(`ComparisonIntakeMismatch`) while the explicitly synthetic canonical-index re-reviewed declaration
works; .55/1.0 original-peak delete and wrong-source refusals through assembly; all supplied comparisons
and precision refusals retained; real analytic `WeightCapacityExceeded` capacity attempt retained
through the public CLI saved table and disk loader, with omission refused; deleted original full-rows
blob refused before table output; relocated producer-disabled replay; card promotions refused;
reversed-intake determinism and caller immutability.

### Random revert (B assembly check)

- **Selection.** `random_selection.py`: sorted list of the seven newly applied checks in B's
  `assemble_stub_context`, `random.Random(int(target_tree_hex, 16))` → **#5 comparison intake must
  enumerate every supplied comparison exactly once** (`companions.py:193-201`).
- **Revert.** Only that 9-line block removed in scratch (`logs/revert-intake.diff`; file
  `7431cd7d…` → `41bb811d…`).
- **Meaningful behavior failure** (`probe_intake_subset.py`, committed actual capacity scenario, SYNTHETIC
  re-review). The caller omits the supplied capacity-failure comparison **and** re-reviews recipes for the
  remaining subset.
  - **Target:** refused `ComparisonIntakeMismatch`.
  - **Reverted:** **ACCEPTED**. Context and table carry 2 comparisons, the capacity comparison is absent from
    the table though its artifact is still supplied, and public verify passes. A supplied failing attempt
    was filtered into a passing subset (`logs/probe-revert.log`).
- **Committed tests after revert:** 3 failed / 68 passed
  (`test_actual_capacity_failure_and_prior_attempts_survive`, `test_real_cli_rejects_wrong_indexes_or_missing_attempts[omit]`,
  `test_real_cli_capacity_failure_prior_comparisons_and_refusals_survive`). These fail because the
  refusal identity becomes the recipe-path check's `IncompleteMetricContributors`; in those scenarios the
  omission is still refused by check #6. No committed test reproduces the re-reviewed-subset case that #5
  alone guards. Criterion (c) is met (tests fail without the check); I record that limitation and recommend
  adding that case, as an observation only (`logs/revert-suites.*`).
- **Restore.** Exact block restored (`7431cd7d…`, tree identical to the export): probe refuses again; the B and A
  companion modules pass 71/71 (`logs/probe-restored.log`, `logs/restored-suites.log`).

### Per-original-finding dispositions (this follow-up)

| Finding | Response set | Stage 3 disposition |
| --- | --- | --- |
| B-F1 card assertions | Exact approved loader adapter **installed** (live, uncommitted) | Installed bytes = adjudicated bytes; card regressions pass on target (P3/P4). **Applied resolution accepted** for local software checks. Commit, publication and hosted CI remain separate |
| B-F2 R202 | Same adapter installed; durable 84-case public test | R202 public module 84/84 and assembly R202 controls pass on target. **Applied resolution accepted** for local software checks; publication and hosted CI separate |
| B-F3 CI | Exact 12-file protected patch **installed with Javid's approval** | Local lint and both strict mypy commands pass (P2). The finding stays **OPEN**: the strict-support gates still fail and `vendor --check` refuses, and the target adds a **third** pytest failure (`test_production_isolation`, P4/P5). The hosted python job would not be green on this tree. Hosted CI not run |
| B-F4 / B-F5 | Unchanged | Satisfied, as previously adjudicated; display/count regressions pass on target |
| **B-F6 public companion workflow** | Applied: B pure assembly + A draft/assemble/table integration; actual external-review demonstration pending | B's helper meets (a)–(c): all listed assembly properties were verified by P1, P7 and P8, and the random revert shows meaningful behavior. **But the applied joint workflow on this exact tree breaks an existing committed safety regression:** `test_production_isolation` passes at `b5e530e1` and fails at `57e97584` on A's new `cli.py:447,510` dynamic peer import. Neither the response selections (A follow-up "30 regressions", coordinator 124 selection) nor any full-suite run on the target exercised it. **Row at fault** |
| B-F7 publication/docs | Deferred | **OPEN** (normative publication/link repair, command/Makefile/how-it-works docs) |
| B-F8 characterize | Exact A patch **installed** | Characterize regressions pass on target. **Applied resolution accepted** for local software checks; publication separate |

### Verdict

**NOT ACCEPTED — row at fault: B-F6.** Criterion (c) / applied-behavior adequacy: on target `57e97584` the
applied public companion workflow fails the existing production-isolation regression
(`contract/tests/test_u_p2_review.py::test_production_isolation`, invariant-1 guard), which passes on the
installed baseline. The response's executed claims omitted that guard. The defect lies in the A-authored
CLI adapter (`src/rkuarch/cli.py:447` `import importlib`; `:510` `importlib.import_module(...)`), so the
remedy owner is A. Two remedy directions exist, neither chosen here: a static guarded import, or a
separately reviewed narrow guard exception (a protected contract test, needing its own human decision).
After that, the guard and the companion selection should be rerun on the corrected tree.

The software portion authored by B, `assemble_stub_context`, is adequate: exact accepted and independent
subject reviews, unique family, intrinsic/recursive source correspondence, complete supplied comparison
recipes at canonical indexes without rewriting, reference identities, no-comparison control, model-card
ceiling through the public builder/loader, purity, immutability and raw-byte retention. The installed
B-F1/B-F2/B-F8 resolutions are accepted for local software checks.

**Remaining scope (not closed):**

- The B-F6 actual external recipe/registry review demonstration. Test and probe reviews are synthetic.
- B-F3 hosted CI and the strict-support gates, which need a combined source/input freeze and human
  generation/adoption.
- B-F7 normative publication and shared docs.
- Command/Makefile/how-it-works docs.
- U0021 GitHub cold clone on WSL2 with same-commit hosted Ubuntu CI.
- Commit/publication, tag and closure.

The P4 full-suite result binds tree `57e97584` only; the old 1,287/2 binds `b5e530e1`.

---

## Stage 3 — CI/isolation recheck (2026-10-10)

Same original independent B reviewer session. Bounded U-REVIEW Stage 3 recheck of the existing response
set; not an author. No new Stage 1 review, live edits, ledger changes, protected policy decisions,
staging, commit, generation/adoption or closure. All earlier bytes are preserved: the first 83,719 bytes
of this file (through the public-companions section) have SHA256
`19727302f43898d2d7aa32de337b59086ef65f081fb58dde0cc68ffb86548420`. Scripts and logs are in
`docs/reviews/U2-final-review-B-ci-isolation-recheck/`.

### Target and identity (verified)

- **Reviewed target: Git tree `53f9f21b7cc3f84c0cbdb5f3f1e74e6e4aeca522`** (not a commit); HEAD `769a1fef…`.
  `git diff 57e97584 53f9f21b` changes exactly the nine stated paths. `git diff 0fb1900a 53f9f21b`
  changes only `scripts/vendor_rk.py` and the new `tests/unit/test_vendor_script_entry.py`.
- All 58 selected paths equal the target blobs in the live integration, A and B worktrees (uncommitted,
  empty indexes). The four handoffs match the receipt's SHA256s (A `1731d974…`, B companion `a798eddd…`,
  vendor `54b7a32f…`, VE-C1 `9b27b059…`).
- The isolation guard is unchanged: `contract/tests/test_u_p2_review.py` SHA256 `856aa220…` and
  `contract/tests/vendor_support.py` `f56e666e…` are identical at `b5e530e1`, `57e97584` and `53f9f21b`.
  No report/badge/applicability source changed since `b5e530e1`.

**Environment.** Static checks ran from the `git archive` export root with **PYTHONPATH and MYPYPATH
unset** and fresh external caches. Runtime checks used **only** `PYTHONPATH=<export>/src:<export>/contract`,
never the repository root. `rkuarch`/`uarch_contract` resolved inside the export, whereas the
interpreter's default editable install resolves to `/home/jjaff/AI-infra-simulation/rk-uarch/src`
(recorded in `logs/static.log`).

**Correction to my own earlier evidence.** My Stage 3 S10 and public-companions P2 rows reported
"`mypy --no-explicit-package-bases contract/tests` passes". Those runs had `PYTHONPATH=.:contract:src`
set. Re-run on the old target `57e97584` with both path variables unset, the same command finds **206
errors in 4 files** (`tests/unit/test_u2_a_shapes.py`, `tests/u2_comparison.py`, `tests/u2_refresh.py`,
`tests/fixtures/u2_b/b2_support.py`). With my old PYTHONPATH it reports success
(`logs/old-target-mypy-contract-unset.log`). My earlier statement did not reproduce CI's environment and
should be read as superseded by this section. It does not change the B-F3 OPEN disposition I gave.

### Executed checks (mine, target export)

| # | Check | Result |
| --- | --- | --- |
| Q1 | `mypy src contract/uarch_contract scripts` (paths unset) | **pass, 68 source files** |
| Q2 | `mypy --no-explicit-package-bases contract/tests` (paths unset) | **pass, 28 source files** (was 206 errors at `57e97584`) |
| Q3 | `ruff check .`; `lint-imports --no-cache --no-logo` (export src/contract) | pass; 2 kept / 0 broken (90 files, 503 dependencies) |
| Q4 | Isolation guard + static-boundary + real-peer controls (`test_production_isolation`, `test_missing_peer_refuses_without_breaking_other_commands` ×2, `test_real_peer_review_and_model_refusals` ×4, `test_real_cli_rejects_wrong_indexes_or_missing_attempts` ×2) | **9 passed** |
| Q5 | Direct/module vendor commands from export root | `python -B scripts/vendor_rk.py --check` → exit 1 `vendor-rk: input support inventory changed` (no import error); `-m scripts.vendor_rk --check` → identical; `--check --historical` → exit 0, "historical integrity and recorded identity ONLY; current compatibility not checked" (`logs/vendor-entry.log`) |
| Q6 | `test_vendor_script_entry.py` (9) + `test_vendor_tooling.py`, `test_u_p2_review.py`, `test_u2_historical_snapshot.py`, `test_committed_snapshot.py` (88) | **95 passed, 2 failed**: the two strict-support gates (`input support inventory changed`); no skips/errors |
| Q7 | B typed helpers (`tests/u2_comparison.py`, `tests/u2_refresh.py`, `tests/fixtures/u2_b/b2_support.py`) diff audit | No assertion or `pytest.raises` removed (2→3, 0→2, 0→0; additions are `assert … is not None` narrowings). Sensitive hunks are semantics-preserving: `kv_replicated = kv_heads < tp`, `padded_vocab = ceil(vocab/tp)*tp` with the three values bound from the same row; the capacity-failure `reason` string is retained (only a `cast` added); explicit `nominal=`/`physical=` replace `**comparisons` over the same two keys; saved comparison bytes use the same canonical writer |
| Q8 | Full suite on target | **1,392 passed, 2 failed, 0 errors/skips**, 1,394 cases, 509 s. Only `test_current_snapshot_generator_compatibility` and `test_current_canonical_is_exact_adopted_1008_four_real_refusals` fail (`input support inventory changed`); `test_production_isolation` passes (`logs/target-full-suite.*`). This is my run on this exact tree, not the inherited `0fb1900a` count |

### Subset hook and random revert

- **Every-supplied-comparison hook (required check).** Removing only the nine-line block
  (`companions.py:193-201`; `logs/hook-removal.diff`) in a scratch copy makes the new durable
  `test_re_reviewed_subset_cannot_erase_supplied_capacity_failure` fail with **`DID NOT RAISE ValueError`**.
  Assembly returned normally, so the re-reviewed omission of the supplied capacity-failure attempt was
  **accepted**, not refused under another message. The same test passes on the target and again after exact
  restoration (`logs/subset-hook-removal.log`). This matches my earlier probe (accepted 2-comparison subset)
  and **resolves my public-companions coverage observation** with a committed regression.
- **Random revert.** `random_selection.py` over this delta's two behavioral changes,
  `random.Random(int(tree_hex,16))`, picked **A's guarded static peer import in `src/rkuarch/cli.py`**. In
  scratch, the `57e97584` blob was reinstated; the only delta is that hunk (`logs/cli-revert.diff`:
  `import importlib` and `importlib.import_module(...)` back). Q4 selection results:
  - **Reverted:** 3 failed / 6 passed. `test_production_isolation` fails with
    `production vendor isolation: src/rkuarch/cli.py:[447, 510]`, my original B-F6 symptom. Both
    static-boundary cases fail with `assert [] == [('assemble_stub_context',)]`. The six real-peer
    review/model/index controls still pass.
  - **Target:** 9 passed. **Restored** (tree identical to the export): 9 passed (`logs/cli-revert-tests.log`).

### Synthetic-declaration display disposition (B-F6)

B's written disposition makes no flag or policy change; badge, report and applicability code is unchanged
since `b5e530e1`. I checked it directly by rendering the same public-chain table opt-in with and without
`--allow-synthetic-presentation` (`logs/synthetic-flag-display.log`):

- Both outputs carry **557 identical labelled STUB numeric lines**.
- They differ **only** in the `RenderSpec` identity.
- The `SYNTHETIC … not an actual independent review` reviewer label is visible in both.

This is consistent with U0004 Presentation and the accepted F6 workflow: synthetic presentation
permission gates synthetic fixtures/comparisons by structured classification, while these are executed
analytic STUB predictions with synthetic *administrative* reviews. No real review authority or evidence
eligibility is claimed. Extending the flag to administrative-review provenance would be a separate human
policy decision; none was made.

### Per-original-row adjudication

| Finding | Stage 3 result on `53f9f21b` |
| --- | --- |
| B-F1, B-F2, B-F8 | Installed software acceptance stands as previously scoped (no production change in this delta) |
| **B-F3** CI | Software response for the defects in scope is adequate. Both CI-equivalent mypy commands now pass without path masking (Q1/Q2); ruff and import contracts pass. The direct `vendor_rk.py --check` entry defect is corrected and its 9 entry tests compare command output with strict library validation. The isolation guard passes (Q4). **The finding stays OPEN** for the artifact/hosted gates: both strict-support tests and `vendor --check` still refuse `input support inventory changed`, and hosted CI on a published commit has not run |
| B-F4, B-F5 | Satisfied, unchanged |
| **B-F6** | **Previously at fault (isolation regression) — now resolved in software:** the unchanged guard passes, the static peer boundary is discriminated by the random revert, and the re-reviewed-subset gap now has a committed accepting-omission regression. Software portion **accepted**. The actual external recipe/registry review demonstration remains **OPEN** |
| B-F7 | **OPEN** (normative publication/link repair, shared command/Makefile/how-it-works docs) |

### Verdict

**ACCEPTED** for the Stage 3 response checks (a)–(c) on tree `53f9f21b7cc3f84c0cbdb5f3f1e74e6e4aeca522`.
No original row is at fault in this recheck.

- **B-F6:** the isolation fault named in my public-companions section is cured in software. The unchanged
  guard passes, the full suite has no third failure, and the randomly reverted static import reproduces the
  original guard failure. The re-reviewed-subset coverage gap is closed by a committed test that fails only
  as an accepted omission when the hook is removed.
- **B-F3:** its typing and vendor-entry corrections are adequate software responses.

This acceptance covers source-level response adequacy only. It does not close any deferred exit gate:

- **B-F3:** strict-support currentness (both gates and `vendor --check` still refuse) and hosted CI.
- **B-F6:** the actual external recipe/registry review and public demonstration (all reviews used here are
  synthetic).
- **B-F7:** normative publication/link repair and shared command/Makefile/how-it-works docs.
- The final combined source/input freeze and human generation/adoption.
- U0021: a fresh GitHub clone on ElfinKidsLaptop WSL2 plus hosted Ubuntu CI on the identical published
  commit. Neither a local archive nor U1 CI satisfies it.
- Separately controlled commit, publication, tag and sprint closure.

This section does not mark publication or the sprint complete.
