# U3 lane B — independent Stage 1 review

## 2026-10-12 — Stage 1 review of target `184d2c2b08c28a01673be143b086ef223ba6706a`

Target tree `6f74542bf5fc85997e044a135293db95297e3e20`. Corrected repair patch SHA256
`97d0ec302606838a7055ec3d43ce1d3b759e8e015ecb796eed154ce4b0915e55` (verified).
Later coordinator commits `606d247`/`d7b00b8` change only coordinator review documents and
do not change this target; `git diff 184d2c2 d7b00b8` has no source, test, lock or B-package change.

**Scope:** this is a bounded design, readiness and prototype review of Lane B. It is not a
sprint exit, an implementation release, a G2 closure, Stage 3 adjudication or a human decision.
Its findings are evidence, not a verdict. A different reviewer handles Lane A.

**Authorship disclosure:** this session authored none of the reviewed proposals, tests or
patches. It has no memory of the author sessions, and the project memory directory was empty.
The authoring commits were made under the human account and may have used an AI assistant
from the same model family in other sessions. I had no access to those sessions; I am
recording this as an independence limit, not as prior authorship.

### Subjects reviewed

- `docs/reviews/U3-B-verification-readiness-v1/` (README, native-checklist, worked-examples).
- `docs/reviews/U3-B-readiness-supplement-v1/` (README, consumer-conformance).
- `docs/reviews/U3-B-artifact-dependency-audit-v1/` (README, migration, support-delta, evidence, repair.patch).
- `docs/reviews/U3-B-dependency-audit-correction-v1/` (README, evidence).
- `docs/reviews/U3-design-audit-reconciliation-v1/README.md`, read as claims to verify.
- `docs/reviews/U3-native-stage-design-v2/` (all eight files), read for cross-lane reconciliation only.
  This review does not adjudicate A's design.
- Governing context: CLAUDE.md, U0005, U0006, U0019, U0022, U0023, execution-plan
  U3/U4/G2/G3a/G3b/G5, build-spec §7.2, and the U-P5, U-P6, U-P8, U-P11a–c, U-P12 and U-REVIEW prompts.

### Summary

| ID | Severity | Subject | One line |
| --- | --- | --- | --- |
| B-F1 | **BLOCKING** for accepting the exact policy text or patch | Dependency policy | The stated rule rejects shadowed imports, but the mechanism misses transitive ones. A new `scripts/typing_extensions.py` is not inventoried, yet the documented `vendor_rk.py --check` executes it. Current U0002 would catch it. |
| B-F2 | NON-BLOCKING | Clock premises | The per_op premise is false because of **two** memory-only ops (`head/embed`, `layers/kv`), not only the embedding. C2's "memory-dominated" needs its clock stated. |
| B-F3 | NON-BLOCKING (cross-lane) | First consumers | The "native B matched U-C0 floor" consumer has no admitted analytic component path. A makes component `u_c0_duration_ps` null. |
| B-F4 | NON-BLOCKING | Stale requirements | The v1 checklist and README still carry the pre-U0023 runner prerequisite and full-grid/U4b rows, with no row-level supersession note. |
| B-F5 | NON-BLOCKING (cross-lane) | Ownership | A assigns B "real Linux CI" and CI-tool pinning for K1. B's schedule neither accepts nor schedules it. |
| B-F6 | NON-BLOCKING (cross-lane) | Observations | The checkpoint for V21's Little's-law ≤1% check differs between A (B/R/U6, minimal observations at B) and B (first claim, normally U6). |
| B-F7 | NON-BLOCKING | Decisions | The proposed replacements of two U-P6 prompt identities are not in B's human-decision list. These are the DMA "in = consumed + written back" identity and the clock relation's "less than k" wording. |
| B-F8 | NON-BLOCKING for the proposal; required before installing the test patch | Test design | The proposed permanent tests mutate tracked live sources and create root-level shadow modules during an ordinary `pytest` run. |

The coordinator's B-C1 and B-C2 are resolved in the corrected patch, and I reproduced both.
I found no fabricated pass, rescheduled historical shortfall or reintroduced full-table
prerequisite in B's current (supplement) schedule.

---

### Findings

#### B-F1 — BLOCKING (exact policy/patch acceptance only): transitive external-import shadows escape the proposed inventory

**Where:**
- Policy text, `U3-B-artifact-dependency-audit-v1/migration.md:20-21`: "reject … ambiguous or shadowed imports".
- Mechanism description, `README.md:101-104`.
- Code, `repair.patch:84-87` and `:113-119` (applied: `scripts/u2_support.py:45`, `:72-77`).
- The shadow check runs only for each **directly imported** top-level external name.
- `scripts/vendor_rk.py:1056-1059` puts `ROOT`, and the script directory `scripts/`, ahead of
  stdlib and site-packages when run as the documented CLI.
- The current rule enumerates `scripts/**/*.py` (`scripts/u2_inputs.py:47-48`).

**Consequence:** a new committed file in `scripts/` named after a module that pydantic or the
stdlib imports transitively runs inside staging and strict verification. Two examples are
`typing_extensions` and `annotated_types`. The proposed inventory does not change, so a
new-policy artifact would keep verifying as current. Current U0002 enforcement refuses the
same change, so this is a coverage regression against today's rule. It also contradicts the
stated rule, and needs no arbitrary-code or obfuscation assumption: it is a plain file with a
common dependency name. (`ROOT/*.py` transitive shadows are missed by both rules; under
pytest, `src/` and `contract/` are also prepended.)

**Evidence:** private patched export, origin-checked.
`docs/reviews/U3-independent-review-B-v1/test_reviewer_boundaries.py::test_transitive_external_shadow_is_not_inventoried`
passed for both names:

- `policy.inventory()` is unchanged.
- `ui.load_inputs(..., check_support=True)` accepts a synthetic new-policy input set.
- The old-rule inventory gains exactly the new file.
- `python scripts/vendor_rk.py --check` exits 1 with
  `ImportError: REVIEWER-SHADOW-EXECUTED …/scripts/typing_extensions.py` (likewise `annotated_types.py`).

All files were restored, and the tree hash was identical before and after.

**Minimal correction (choose one), then add a public-`load_inputs` control for a transitive shadow:**

1. Bind or refuse every importable top-level name under each sys.path root that the documented
   entry points prepend (`ROOT`, `scripts/`, and the pytest roots), unless it is in the reached
   closure. For `scripts/`, retaining the current complete rule is enough.
2. Run the entry points with safe-path semantics, and stop prepending `ROOT`/`scripts` before
   external imports resolve.
3. Narrow the policy text to "direct external imports only", and have Javid explicitly accept
   the regression against U0002.

This blocks only acceptance of the exact policy and patch. It does not block continued review,
nor Javid's alternative decision to retain current U0002.

#### B-F2 — NON-BLOCKING: the per_op premise cause is understated, and C2's premise clock is implicit

**Where:**
- `U3-B-verification-readiness-v1/README.md:120-121` ("inapplicable to the existing memory-only embedding").
- `U3-B-readiness-supplement-v1/README.md:39` and `:151-153`.
- C2 wording, `README.md:90-95`.
- Same phrase in A's text (for the coordinator): `U3-native-stage-design-v2/verification.md:294`,
  `handoff.md:86`, `proposed-U0011.md:131-132`.

**Consequence:** the inapplicability conclusion is correct. But the fixture has **two**
memory-only operators in both decode and prefill: `head/embed` (16 bytes) and `layers/kv`
(32 bytes, zero matrix and zero vector ops). A future "true-premise per_op domain" that removes
or neutralizes only the embedding would still have a false premise. Separately, "a
memory-dominated aggregate has T'=T" holds only if memory dominates at the **base (slower)**
clock. If it dominates only after the speed-up, then T'<T.

**Evidence:** `premise_probe.py`, which uses exact rationals from the per-op counts and checks
them against the L0 literal totals:

- Memory-only ops are `['head/embed', 'layers/kv']` in both points.
- At 10^18 B/s, the per_op `T'·k/T − 1` worst case over B's 24 anchors is 1.43e-8, above the
  1e-9 tolerance, which confirms inapplicability.
- B's C1 anchors are compute-dominant at the faster clock for both points, with exact `T'=T/k`.
- B's C2 anchors at 1,000 B/s have every op memory-dominant at the base clock, and `T'=T` holds
  in both modes.

So B's C1 and C2 premises hold as designed.

**Minimal correction:**
- Say "memory-only operators (`head/embed`, `layers/kv`)" in the proposal prose. Keep the
  historical reason code `MEMORY_ONLY_EMBEDDING` and the reports unchanged.
- State "memory-dominated at the base clock (hence also at k·f)" for C2.
- Ask A, via the coordinator, to align the same phrase.

#### B-F3 — NON-BLOCKING (cross-lane): the "native B matched U-C0 floor" consumer has no defined admitted path

**Where:**
- B's supplement row 1, `U3-B-readiness-supplement-v1/README.md:27`: "Native B's matched U-C0
  floor/reference check … no later than B for its matched slice".
- `U3-B-verification-readiness-v1/README.md:34`: "existing analytic baseline can supply a
  matched roofline comparison".
- `worked-examples.md:16-17`: tests must not bypass full-model admission.
- A: `interface.md:31` (`u_c0_duration_ps` is null for components) and `verification.md:306-307`
  (B may use independently derived component bounds).

**Consequence:** at B, the native scope is 1–16 component GEMMs, but the public analytic path
admits only full prepared models. B's deadline therefore either implies an unstated new
analytic component path at B, or names a consumer that does not exist. Either way the
re-execution deadline for the v1 checks is ambiguous.

**Minimal correction:** the coordinator records one of two choices:

- **(a)** B's component checks use independent bounds only. The v1 analytic-check deadline then
  moves to the first actual analytic comparison (R/U-P9 at the latest).
- **(b)** A test-only analytic comparison on component ops is defined. It states its admission
  rule and is labelled as not admitted.

#### B-F4 — NON-BLOCKING: stale pre-U0023 runner and full-grid requirements remain in B's v1 package

**Where (`U3-B-verification-readiness-v1/`):**
- `native-checklist.md:12` ("unsupported required full-grid work blocks G3").
- `native-checklist.md:22` ("U4b workers 1/N, table bytes and complete-work counts").
- `native-checklist.md:68-70` ("The published Linux/runner/schedule/manual-nightly prerequisite
  still applies before native implementation/build/performance work").
- `README.md:165-169`.

The supplement says only generally that U0023 controls (`README.md:11-17`). A says "U0023
supersedes its U4b-full-grid/runner wording" (`verification.md:241`).

**Consequence:** if the checklist is attached to a decision as written, it reintroduces an
unconditional runner prerequisite before native implementation. U0023 removes that
prerequisite (U0023 lines 88-101, 121-123). The prompt for this review specifically excludes it.

**Minimal correction:** add a dated, B-owned supersession note to the supplement. It should
list these rows and their U0023 replacements: correctness on approved Linux; G3a/G3b split;
worker checks at G3b/T; runner and nightly only for G5-performance/automation, U9 and closure.
Leave the historical text unedited.

#### B-F5 — NON-BLOCKING (cross-lane): native Linux CI ownership is unscheduled on B's side

**Where:**
- A: `delivery.md:8` ("K1 / A; B corpus and real Linux CI"), `delivery.md:136` ("B must pin the
  CI tools under that same decision before CI evidence counts"), `decisions.md:49` and `:67`.
- B's ownership section: `U3-B-readiness-supplement-v1/README.md:108-113`.
- U0023 lines 88-91 require real fmt/clippy/tests/license execution.

**Consequence:** K1 acceptance depends on a CI deliverable assigned to B. B has neither accepted
nor estimated it, and has no first-consumer row for it. Either K1 waits on unowned work, or
no-op CI evidence is accepted.

**Minimal correction:** B accepts or declines the CI and pin tasks, stating timing (before
any K1 result is credited) and effort. Otherwise the coordinator reassigns them.

#### B-F6 — NON-BLOCKING (cross-lane): different checkpoints for Little's law

**Where:**
- A: `verification.md:210` (V21 "B/R/U6 … Little's law on declared completed window ≤1%") and
  `:274` ("V21's minimal observations are mandatory at B").
- A's own separation of the two checks: `interface.md:271-274`.
- B: `U3-B-readiness-supplement-v1/README.md:37` ("Before claim, normally U6/G5-correctness";
  premises not yet settled) and `:154-157`.

**Consequence:** it is unclear whether a steady-state ≤1% Little's-law check is a condition of
B acceptance. Required before its stationary-window premise is frozen, it would be either
forced or quietly skipped.

**Minimal correction:** the coordinator records three points:
- At B, only the finite-window clipped-residence identity (V24) and the minimal observations
  are required.
- The steady-state ≤1% check is due at its first claim (U6/G5-correctness, or earlier if relied on).
- That check uses a frozen window, population and boundary premise.

#### B-F7 — NON-BLOCKING: reinterpretations of U-P6 prompt identities are missing from the decision list

**Where:**
- U-P6 L0 states "DMA bytes moved in == bytes consumed by compute plus bytes written back"
  (`docs/prompts/U-P6-…:31`).
- B replaces it with a direction-specific control-volume balance plus a separate allocation
  ledger (`native-checklist.md:37-40`).
- A says this "requires B and coordinator acceptance; it does not edit that prompt silently"
  (`interface.md:263-266`).
- B replaces the L0m wording "changes a DRAM-bound one by less than k" (`U-P6:46-47`) at
  `README.md:90-95`.
- B's decision list (`README.md:158-163`) covers the C2 premise but not the DMA identity.

**Consequence:** the standing prompt still mandates an identity that both lanes call generally
invalid. An implementer could build it, or skip it, without any recorded decision.

**Minimal correction:** add both replacements, with exact text, to the human decision list.
Keep U-P6 unedited until that decision is made.

#### B-F8 — NON-BLOCKING for the proposal; required before installing the test patch: the permanent tests mutate the live tree

**Where:** `repair.patch` test hunks.
- `:216-237` rewrites `scripts/vendor_rk.py`, `src/rkuarch/hw/derive.py`,
  `contract/uarch_contract/hashing.py` (`sort_keys=False`), `__init__.py`, `uv.lock`,
  `pyproject.toml`, `hw/designs/npu-l4.yaml` and the precision fixture.
- `:307-320` creates `yaml.py` at the repo root, `src/pydantic/__init__.py` and `scripts/json.py`.
- `:248-285`, `:334-347`, `:469-511` and `:529-568` create or modify modules and data in tracked
  directories.
- In every case, restoration depends on a `finally` block.

**Consequence:** once installed, an ordinary `uv run pytest` would corrupt a developer's or
CI's checkout if it were killed (timeout, OOM, SIGKILL) between a write and its restore. One
example is hashing with `sort_keys=False`. Concurrent readers would also see mutated sources:
IDE checkers, mypy, a second pytest, or any process importing `yaml` from the root. This review
had to forbid running static readers concurrently for exactly this reason. No existing test
does this; the existing pattern copies to a temporary target
(`tests/unit/test_u2_b_tooling_binding.py:157`).

**Minimal correction:**
- `support_files`, `inventory` and `verify` already take `root=`. Run every mutation and fault
  case against a temporary copy of the bound inventory, monkeypatching `ui.ROOT` for
  `load_inputs`.
- Keep the real `ROOT` read-only, with one positive case against it.
- Re-demonstrate the loader-call fault discrimination after the change.

---

### Primary checks and outcomes

**1. Private-export application.**
- The patch SHA256 matched.
- `git apply --check` passed, then the patch was applied **only** in a scratch `git archive` export.
- Fault tests and static readers ran strictly sequentially.
- The tree hash of every file excluding bytecode, `87a14d13…`, was identical before and after
  each mutating run. Only a `.ruff_cache` appeared, which I removed.
- The live clone stayed clean (`git status --porcelain` empty), apart from this report and the
  evidence directory.

**2. Independent closure trace.**
- An independent stdlib `modulefinder` closure from the three entry points gives exactly the
  31 proposed `.py` entries, with no unresolved local names. This is a separate static method
  from B's AST walker.
- A runtime audit-hook trace of strict consumption, with `run_oracle`, `collect_snapshot` and
  `prepare_inputs` denied, passed on the pristine export with 30 local modules. It refused on
  the patched export with the expected `input support inventory changed`.
- The helper's inventory equals retained(39)+added(13)=52. The pristine old rule equals
  retained+removed=97. The partition counts are 21/9/9 retained and 45/3/6/4 removed, all
  consistent.
- Static reading of `prepare_inputs` and `collect_snapshot` found these non-import reads, all
  inside the proposed data families or the provenance root:
  - component-precisions, the two execution JSON files, `a2-export/*.json` plus the YAML;
  - `npu-l4.yaml` and the provenance root;
  - the model-shape mirrors, conservatively included.

  The input-root path ignores `contract/fixtures/model_shapes`.
- `docs/decisions/U0001` is read at verification as a live regex check against the constant
  PIN. It is unbound under both rules, so this is not a regression.
- Environment keys read are `PYDANTIC_DISABLE_PLUGINS`, `HOME`, `PYTHONUSERBASE` and interpreter
  keys. Pydantic loads entry-point plugins (`pydantic/plugin/_loader.py:27-40`). Neither rule
  binds the rk-uarch environment beyond `uv.lock`. This is consistent with the README's stated
  plugin limit and is recorded as an observation, not a finding.
- A's M note (`interface.md:308-389`) agrees with B's classification table: no installed edge,
  no projected count and no exemption. New mapped re-exports or shared-carrier changes would
  bind under both rules.

**3. Public `load_inputs` controls.**
- Corrected tests: **44 passed, 1 skipped** (plus my origin probe, 45 passed).
- Replacing only the new-policy `u2_support.verify(...)` call with `pass`: **4 failed, 40 passed,
  1 skipped**. The failures are exactly the four `test_public_load_new_policy_drift_refuses`
  attacks (`bound_bytes`, `missing_entry`, `wrong_hash`, `new_dependency`), each
  `DID NOT RAISE ValueError`, so the attacks were accepted.
- Restored exact loader bytes (`f25ce49d…`): **44 passed, 1 skipped**.
- On the historical `bb15bd…` patch, the same fault gives 30/30/30. This reproduces the
  coordinator's blind spot. The corrected loader and helper bytes are identical to the
  historical patch's; only the tests changed.
- Additional boundaries of my choice:
  - Stripping `support-policy.json` and rehashing loads integrity-only, but strict mode refuses
    `input support inventory changed`. Downgrade fails closed.
  - Relabelling a legacy complete inventory with the new policy marker refuses.
  - The transitive-shadow probe produced B-F1.
- Producer denial and synthetic labelling were preserved throughout. No oracle, staging,
  generation or adoption was run, and no actual-provenance claim was made.

**4. Dispatch and the skip.**
- Legacy dispatch keeps the complete old rule, with its sentinel proving the new verifier is
  never called. Its old-rule diagnostics pass.
- The pinned legacy case uses the authenticated 20-file `historical-u1` fixture
  (`contract/tests/historical_snapshot.py`, manifest `b3a575d…`) and never `ui.ADOPTED`.
- The single skip is the real new-policy adoption positive.
- That skip cannot become a silent permanent waiver. Once the patch is installed, any legacy
  adopted artifact fails the complete rule, because the helper itself is a new `scripts/` file.
  CI runs `scripts/vendor_rk.py --check` unconditionally (`.github/workflows/ci.yml:53`).
- The skip is still open. It is not migration success.
- The shadow, dynamic and data limits match the README's stated non-sandbox limits, except B-F1.

**5. Migration plan.**
- Ordering is sound: human acceptance comes before M installation, then tests-first code, then
  freeze, then two human generations, then a complete audit, then a separate adoption.
- The plan forbids publishing a failing suite, using `--historical` as a substitute for
  currentness, selective support-JSON replacement and script-only rollback.
- `compare_snapshots` joins every row on (component, model, precision, tp, query) and diffs
  the full row, so it covers counts, durations and nulls. It returns refusals before and after
  for comparison without computing a verdict, and the plan already requires that audit.
- Generation and adoption stay human-only (`UARCH_HUMAN`, plus test denial).
- No finding beyond B-F1 and B-F8.

### Readiness and mathematics checks

- **Aggregate-only 22/24:** both historical reports show
  `analytic.aggregate_clock/1:aggregate:d4-bf16-v1` `not_run INCOMPLETE_OR_UNDER_BUDGET`, with 24
  bodies. SR-C1 has 22 valid examples (96 discovery and 88 candidate calls); the original has 21.
  The cell exists only in aggregate mode (`validation/reporting/analytic_report.py:248`).
  `build_inputs` overwrites the drawn bandwidth with 1e18 (`:473-474`). That is consistent
  with B's duplicate-pair explanation, although I did not inspect the duplicates in the
  ledger. Neither outcome is rescheduled into a pass. The anchor remedy is a new,
  separately approved profile.
- **Per_op inapplicability** is confirmed, with the B-F2 precision noted.
- **Finite-window conservation:** clipped-residence and in-flight balance are correct and match
  A's ps-scaled 8000/6000 values. Observed work must come from completions, never from echoed
  expectations; A's R20 refusal agrees.
- **Worked examples:** I executed B's block verbatim (passed). I also wrote a separate
  parameterized re-derivation: 28 of 28 values match B, including A's E5 cross-lane values and
  the `next_edge` formula.
- **Budgets:** 96+96 ≤ 240 discovery calls and 96+96 ≤ 240 mutant-ledger calls are correct.
  The anchors stay in range: 1e6..2e9 Hz with the low hardware range-checked only, MACs 1..24,
  vector ops 64..41.
- **Additional verified facts:** `tdp_w` is carried only as a derivation identity
  (`derive.py:131`), consistent with C3. `hw/references/` is empty, consistent with the TPU
  readiness rows.
- **First consumers:**
  - No full-table or unconditional runner requirement appears in the supplement schedule.
  - C1 is due before first reliance, at R/G3a at the latest.
  - C3 is due at its first invariance claim, U-P14 at the latest.
  - C5 is due before the first v2 floor and U-P9.
  - Native observation checks are due at K2/B.

  Ownership and feasibility are consistent with A, except B-F3, B-F5 and B-F6.
- **Consumer conformance:** all vendored claims check out at the pin.
  - `_time_s` divides by `tp` on both of its paths (`compute.py:902-914`).
  - `decode_counts` gives `memory_write_bytes=None` and `vector_ops=None` (`:893-898`).
  - `modelled_memory_bytes` uses `or 0.0` (`:710-711`).
  - The `Channel` literals match `translate_count_names`.
  - `VendorLoader` registers modules only under a private name.

  Real vendored calls (rule 1's literal, rule 5) are correctly separated from scaffolding
  (rules 2-4 and 6-9). C0 fixtures are positive controls for the seam and negative controls for
  C2. No executed C2 positive control exists, and interpolation, serving and orchestrator
  coverage remain not_run until U10. New B test files change neither support rule.

### Environment, runs not performed, and limits

- **Interpreter and tools:** the existing live-clone `.venv` (Python 3.12.14, pytest 9.1.1,
  ruff 0.16.9, mypy 2.3.1, import-linter 2.15). Nothing was installed or synced. WSL2, so no
  performance claim.
- **Import paths:** `PYTHONPATH` and `MYPYPATH` were unset and also removed with `env -u`. The
  venv's editable `.pth` points at the **live** clone. I therefore asserted export origins in
  every credited pytest run. The CLI strict checks used explicit export `src:contract` paths,
  with their origins printed.
- **Discarded run:** one probe run passed only out-of-tree test files to pytest. pytest found no
  ini, `rkuarch` resolved from the live clone, and the origin probe failed. I credited none of
  its results and re-ran with `-c`/`--rootdir`.
- **CI-form statics on the patched export:**
  - Ruff passed.
  - mypy passed on 79 files and on 31 files.
  - `lint-imports`: 2 contracts kept, 0 broken. It resolves the editable live `src`/`contract`,
    which I confirmed are byte-identical to the target (`git diff 184d2c2 HEAD -- src contract`
    is empty and the worktree is clean).
- **Strict CLI check:** passes on the pristine export (exit 0). The patched export refuses with
  the expected migration message (exit 1). I did not run the live strict check; the source is
  identical.
- **Not run:**
  - full suite, hosted CI, native build, nightly or performance;
  - `prepare_inputs` staging, oracle, generation or adoption;
  - historical report validators or regeneration;
  - the A-lane E3/E4 derivations, which belong to the other reviewer.

  No host contact, containers, spending, protected edits or live fixes.
- **Evidence:** probes, traces and receipts are in `docs/reviews/U3-independent-review-B-v1/`.
  They are unstaged and uncommitted.

### Shared-boundary observations for the coordinator

- **A-C1 is resolved:** the aggregate-only C1 scope now appears in A's verification, U0011
  attachment, README, decisions and handoff. B-F2's two-op wording applies to A's text too.
- **B-F3, B-F5 and B-F6** need a coordinator decision rather than a change by either lane alone.
- **A's M dependency note** creates no conflict with B's audit. Exact M edges remain an
  implementation-time recomputation, as both lanes state.
- **A's "proposed model conventions"** (E3 WS law, E4 DRAM-0/credit lifecycle, 1 GHz npu-l4
  stipulations) are design assumptions. B correctly keeps its own examples conditional and
  does not treat A's values as chip facts. A's E2 index formula matches B's edge examples.

### Readiness recommendation (lane B, Stage 1)

- **Verification readiness and first-consumer schedule (v1 plus supplement, consumer
  conformance):** ready for coordinator reconciliation and the human decision once the
  non-blocking clarifications B-F2 to B-F7 are answered. The mathematics, premises and
  historical-outcome preservation hold, and no fabricated pass or early full-grid gate was found.
- **Dependency audit, policy and corrected prototype:** B-C1 and B-C2 are resolved and
  reproduced, and the 97→52 baseline is independently confirmed. The **exact policy text and
  patch are not ready for acceptance** until B-F1 is corrected, or until the narrower guarantee
  is explicitly accepted. B-F8 must be fixed before the test patch is installed. The real
  new-policy adoption positive and the migration audits remain unexecuted and are correctly
  not credited.
- **Javid's documented "retain current U0002" alternative** stays available regardless of B-F1.

This is not Stage 3 acceptance, G2 closure or authority to implement. The authors answer each
finding in their own sessions. This lane's reviewer returns for Stage 3 adjudication under
U-REVIEW, and Javid makes all human decisions.

---

## 2026-10-13 — Stage 3 adjudication of B's Stage 2 response at `40fab28bc73ed1f7898a0950979607cfd0368c12`

**Bindings.**

| Item | Value |
| --- | --- |
| Target commit | `40fab28bc73ed1f7898a0950979607cfd0368c12` |
| Target tree | `4f7c6ca6a8af0c9a6b76768c8f497a035686a62d` |
| Stage 1 target | `184d2c2b08c28a01673be143b086ef223ba6706a` |
| Unapplied patch SHA256 (verified) | `4c73d73d1c7ec1e1453e7ef7ccf1bd3de55238a4469069dcaa75e89bc764fa81` |
| Preserved report prefix (first 27,533 bytes) SHA256 | `550fe94a69e8a9ae53071ebc0928a55af0a3c1d1f88020119e6211b3ac55c820` |

`git diff 184d2c2 40fab28` touches no source, tests, validation, locks, hw, Makefile or
workflows.

I read the following:
- `U3-lane-B-response.md`.
- `U3-B-stage2-v1/` (README, evidence, `shared-inputs.md`, both checkers, `support-delta.json`).
- The audit and migration documents.
- The current readiness supplement.
- The coordinator's `U3-stage3-coordination-v1/B-reconciliation.md` (an untracked
  coordinator file, read-only).

I read A's material only for shared dependencies and did not adjudicate it.

**Scope.** This section applies U-REVIEW Stage 3 checks (a), (b) and (c) only, and raises
no new findings. The observations at the end are recorded for the coordinator. They are
not numbered findings and do not change the verdict.

### Row-by-row check

| Finding | Author disposition | (a) Row present | (b) Reason addresses finding | (c) Discriminating test or check, as executed here |
| --- | --- | --- | --- | --- |
| B-F1 | APPLIED (proposal) | yes | n/a (not REJECTED) | `test_public_load_transitive_shadow_refuses` (16) and `test_fresh_direct_shadow_refuses_before_body` (16). The guard body disabled by a single `return` gives **32 failed**; restored, they pass. |
| B-F2 | APPLIED (supplement prose) | yes | n/a | `check_readiness.py` REQUIRED["B-F2"]. Against the Stage 1 text it fails on `` `head/embed` (16 bytes) ``; the target passes. The existing two-point fixture shows both memory-only ops. |
| B-F3 | DEFERRED (shared) | yes | Waits on: A's component conventions, coordinator disposition, exact cases. Recorded in: supplement S-COMPONENT and B-reconciliation planning alignment. | n/a (no change claimed) |
| B-F4 | APPLIED (supplement rows) | yes | n/a | REQUIRED["B-F4"] fails on the Stage 1 text (`v1 native-checklist “Stage scope and refusal”`); the target passes. |
| B-F5 | DEFERRED (shared; B accepts ownership) | yes | Waits on: coordinator assignment, tool/license pins, A targets/corpus, actual job execution. Recorded in: supplement S-CI and B-reconciliation. | n/a |
| B-F6 | DEFERRED (shared) | yes | Waits on: V21/V24 alignment and a frozen window/population/boundary premise. Recorded in: supplement S-QUEUE and B-reconciliation. | n/a |
| B-F7 | APPLIED (exact proposed text, H-DMA/H-CLOCK rows) | yes | n/a | **Random check, below.** REQUIRED["B-F7"] fails on the Stage 1 text and on the reverted mechanism. |
| B-F8 | APPLIED (test isolation) | yes | n/a | Per-test temporary roots plus an audit hook. Executed: the 136-test run left all 1,516 export files byte- and mtime-identical. With isolation reverted in a throwaway copy, 38 writes were refused before mutation and tests failed. |

No row is REJECTED. The three DEFERRED rows each name what they wait on and where that is
recorded, as U-REVIEW Stage 2 requires. These are explicit shared deferrals. The
coordinator's planning alignment is recorded, while the exact semantic, tool and fixture
decisions and later execution remain pending.

### Random applied-correction check (executed)

**Selection.** `secrets.choice(['B-F1','B-F2','B-F4','B-F7','B-F8'])` at
`2026-10-13T23:27:07+00:00` returned **B-F7** (`random-selection.txt`).

**Mechanism reverted, scratch only.** In the private pristine export I deleted supplement
`README.md` lines 226–253: the "Exact proposed prompt replacements" heading and the DMA and
clock replacement text. I also deleted lines 257–258, the H-DMA and H-CLOCK rows. The table
header and the S-COMPONENT/S-CI/S-QUEUE rows were kept. The exact hunk is in `B-F7-revert.diff`.

**Result.** `check_readiness.py <export> <supplement>` passed B-F2 and B-F4, then exited 1
with `AssertionError: ('B-F7', '**DMA replacement:**')`. That is a failure for the finding's
reason: the replacement text is absent from the decision list.

**Restore.** I restored the exact blob `b94a4cded73fb4c3c3a821441e61d2dbe715e899` (matching
Git) and the checker passed again (exit 0).

### B-F1: public refusal versus fresh-process body execution (executed)

**Guard on.** All 16 public loads refuse `unreviewed import name:` before any body import.
All 16 fresh direct commands (`--check` for both entry points, shadows under `.`, `scripts`,
`src` and `contract`) exit non-zero with the guard message and no shadow marker.

**Guard off (single `return`).** 32 failed:

- **Public loads (16):** 12 were accepted outright (`DID NOT RAISE`, roots `.`, `src`,
  `contract`). The 4 under `scripts` were refused only **late**, `input support inventory
  changed`, by the complete scripts binding after import.
- **Fresh commands (16):** all 16 carried `SHADOW_BODY_MUST_NOT_EXECUTE` in the captured
  stderr, meaning the shadow body executed.

So for the reported names, the prevention of body execution comes from the early guard, not
from late hash refusal. The B-C1 loader fault still gives exactly 4 `DID NOT RAISE` attacks.
The restored selection gives 38 passed / 47 deselected, and export bytes are identical to
pre-fault.

### B-F8: actual isolation, not finally-restoration (executed)

The full 136-test run modified, created, removed or re-touched **no** export file: mtime_ns
and SHA256 were compared for all 1,516 files. Stage 1's tests, by contrast, re-touched
tracked files.

In a separate throwaway copy I pointed `isolated_root` at the real root. The hook refused
38 writes before mutation, and no existing file changed, so tracked source fails closed.

### Executed versus inherited evidence

**Executed here.** All in a private `git archive` export with the exact patch applied:
- `git apply --check` and apply.
- The author's exact selection plus my origin probe: **136 passed (135 + 1) / 1 skipped /
  8 deselected**. The skip is the real policy-marked human adoption, which is absent. The
  deselected cases are not credited.
- Guard fault 32 failed; loader fault 4 failed; restored 38 passed.
- The random B-F7 revert and restore.
- Per-finding prose discrimination for B-F2, B-F4 and B-F7.
- The B-F8 mtime check and the isolation-revert probe.
- `check_readiness.py` and `check_shared_math.py` passed. These are arithmetic, prose and
  existing-fixture checks only.
- Statics: ruff; mypy 80 and 31 files; lint-imports 2 kept (resolving live `src`/`contract`,
  which are byte-identical to the target).
- Strict CLI: the pristine export exits 0 and the patched export exits 1 (`input support
  inventory changed`).

`PYTHONPATH` and `MYPYPATH` were unset for every credited check. Every pytest run used
explicit `-c pyproject.toml --rootdir .`, and export module origins were asserted inside the
credited invocation. The Stage 1 out-of-tree editable-import error did not recur.

**Inherited, not re-executed.**
- The author's tests-first 28/44/1 run and other author receipts.
- The coordinator's matching 135/1/8, 32, 4 and 38 counts. My own executions reproduce
  them; I credit mine.
- The live strict check (the pristine export was used; the source is identical).

**Not run.** Full suite, hosted or native CI, nightly, performance, staging, oracle,
generation, adoption, native build.

### Observations outside Stage 3 (not findings; no effect on the verdict)

These are recorded so they are not lost, without opening Stage 1 again.

- **O1 — pre-guard `__future__` import.** Both patched entry scripts execute `from __future__
  import annotations` before `check_import_roots()`, and `__future__` is not preloaded at
  startup.
  - In a throwaway copy, a `scripts/__future__.py` body ran on `--help` for both
    `vendor_rk.py` and `u2_inputs.py`, before the guard refused it late.
  - This is a residual against the stated "before non-bootstrap imports" premise. It is not
    the reported B-F1 names, which are prevented.
  - It is relevant to the separate human policy decision on the guard's stated guarantee.
- **O2 — audit-hook coverage is defence in depth.** With isolation deliberately reverted,
  the hook protected the named trees and `pyproject.toml`/`uv.lock`. It did not stop
  creation of new repository-root files (`typing_extensions.py`, `annotated_types.py`).
  Actual isolation under the proposed patch is unaffected.
- **O3 — untracked bytecode in my Stage 1 evidence.** `docs/reviews/U3-independent-review-B-v1/`
  now contains a `__pycache__/` of pytest-rewritten bytecode from a later run of those
  probe files. This reviewer did not create it, and it was left untouched.

### Verdict

**ACCEPTED**, scoped to B's Stage 2 author response for B-F1 to B-F8 under U-REVIEW Stage 3
(a), (b) and (c). No rows are at fault.

This acceptance does **not** do any of the following:
- approve the U0002 replacement policy, the guard/bootstrap tradeoff, the 97→56 inventory
  or U0011;
- authorize installation or migration (the patched strict check still refuses; migration
  is not green, and the real new-policy adoption positive remains skipped);
- close G2, release any runtime, or constitute human acceptance.

Retaining current U0002 remains available.

The shared worksheet is independent arithmetic under A's proposed law. It is not native
execution, a hardware measurement, human L1 work or corpus acceptance. The historical 22/24
is unchanged.

Still pending:
- exact variants, profile signing and capacity cases;
- M import/initializer/data closure;
- the H-DMA and H-CLOCK decisions;
- tool and license pins, and budgets.

Javid makes the human decisions; no stage tags the sprint.

---

## 2026-10-13 — Bounded O1/O2 proposal-delta recheck at `7afba9b16d954fd46684711764cb3718170e53aa`

**Scope.** This section checks only the three-file delta (`scripts/vendor_rk.py`,
`scripts/u2_inputs.py`, `tests/unit/test_u2_support_policy.py`) and its direct consequences.
Both accepted Stage 3 verdicts stand. A-F1 to A-F10 and B-F1 to B-F8 are not reopened, and
this is not a whole-plan review.

**Bindings.**

| Item | Value |
| --- | --- |
| Target commit | `7afba9b16d954fd46684711764cb3718170e53aa` |
| Target tree | `a6bd46821714dc698de927c8f2142dfb21877ede` |
| Predecessor | `40fab28bc73ed1f7898a0950979607cfd0368c12` (docs-only change since then) |
| Old full patch SHA256 | `4c73d73d1c7ec1e1453e7ef7ccf1bd3de55238a4469069dcaa75e89bc764fa81` |
| New full patch SHA256 | `c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b` |
| Delta SHA256 | `eac5a0e20d01a2a6a2987665825a731da2b636517a4f342a1c4a1bbfc785426e` |
| Report bytes preserved before this append | 37,472 bytes, SHA256 `39799be3a0849aaa1f005b8fde471965965ffa7d252dadaced49198f649ab454` |

All three digests were verified. Evidence is in
`docs/reviews/U3-independent-review-B-bootstrap-recheck-v1/`.

**Composition.** Applying the old full patch and then the delta to a private export
produces a tree byte-identical to applying the new full patch (`diff -rq` shows no
difference). The six files match the disclosed digests. The guard and support helper are
unchanged.

### O1: `__future__` shadow prevention (executed)

**Prevention.** My own probe (`o1_probe.py`, throwaway copy) ran 12 cases: both entries ×
direct/module/library × file/package shadow. Each shadow body writes a sentinel *file* as
well as a stderr marker, so execution is detected independently of captured output.
- Valid controls passed in 12 of 12, including the exact private library origins.
- The shadow body ran in **0 of 12**.
- The guard refused with a nonzero exit in 12 of 12.

**Discrimination.** I reintroduced only the two leading `from __future__ import annotations`
lines, in scratch (`O1-reintroduce.diff`):
- The body ran in **4 of 12**, exactly the direct file/package cases for both entries. Each
  was refused only *after* executing.
- Module and library forms stayed prevented.
- B's `-k future_shadow` gave 4 failed / 8 passed / 88 deselected, on the same four cases.

So the eventual refusal alone does not prevent the body running; removing the statement
does. After restoring exact bytes (`b82ae570…`/`eb68cb3d…`), the probe showed 0 of 12 and
B's test passed 12 of 12.

**Annotation consequences.**
- Resolved types are unchanged: all 36 annotated objects give identical `get_type_hints`
  before and after.
- Raw storage changes exactly as disclosed: 102 of 109 strings plus 7 `ForwardRef` became
  1 of 109 strings, which is the deliberately quoted, `TYPE_CHECKING`-only
  `validate_u2_component_inputs` return. `Inputs.entries` is now the actual
  `tuple[ComponentPrecision, ...]`.
- No eager contract import is added.
- No repository code other than the new test reads the raw annotations.
- A scan of all 113 eagerly evaluated annotation sites, at every nesting depth, found no
  `TYPE_CHECKING`-only or unresolvable name, so no call-path `NameError` is latent.
- Ruff and mypy cover the scripts: 80 and 31 files, plus both changed scripts checked
  explicitly. The test file stays outside the CI mypy targets, as before.

### O2: immediate-root write denial (executed)

**Denial.** Using B's `source_write_denial` on a throwaway root, my probe tried nine
operations: create-absent, overwrite, append, remove, rename-into-root, mkdir, chmod,
symlink, and a write to a nested protected file.
- Every attempt raised `PermissionError` **before** mutation. Bytes, mtime_ns and the
  directory listing were unchanged.
- Private temporary writes and protected reads kept working.
- B's two `root_file_write` tests passed.

**Discrimination.** Removing only the `resolved.parent == root` predicate, in scratch
(`O2-predicate-removal.diff`), gave **2 B failures** (`DID NOT RAISE PermissionError`) plus
my probe's failure. All writes landed under pytest's temporary roots. After restoring
`65c26ac3…`, all three passed.

**Original observation.** Re-running my Stage 3 scenario (isolation pointed at the real
root, in a throwaway copy) produced 74 refused tests and **zero** files created or changed.
In Stage 3 the same scenario created root-level `typing_extensions.py` and
`annotated_types.py`. This remains test defence in depth, not an OS sandbox.

**Normal runs.** Both normal runs left all 1,519 export files identical in SHA256 and
mtime_ns, with no `__pycache__` created:
- the bounded selection: **151 passed (150 + my origin probe) / 1 skipped / 8 deselected**;
- the restored selection: **53 passed / 47 deselected**.

All deliberate faults ran in throwaway copies, never in the export or any live folder. No
normal test relies on restoring real sources.

### Retained controls and consequences (executed)

**Retained controls.**
- The public-load and fresh-shadow controls run inside both normal selections.
- Origins, including `u2_import_guard`, are asserted from the export.
- The B-C1 loader-call fault (throwaway copy) still gives the 4 `DID NOT RAISE` attacks,
  and restored bytes give `eb68cb3d…`.

**Consequences.**
- Support inventory: **56 → 56** with the same paths. Only `vendor_rk.py` and `u2_inputs.py`
  digests change, matching the disclosed values.
- Embedded `ORACLE_PROGRAM` SHA256 is `bca57950…` in pristine, old and new, equal to the
  adopted GENERATOR.
- The whole vendor-script fingerprint is `787d30d5…` (pristine and adopted), then
  `e18e6fce…` (old proposal), then `b82ae570…` (new). The new value would have to bind any
  future approved generation.
- The 55 vendor/provenance files are identical.
- Strict CLI: the pristine export exits 0. The proposal exits 1 with `input support
  inventory changed`. The one skip is the absent real human adoption. **Migration is not
  green.**

### Inherited, not re-executed

- The author's tests-first runs (6/8/85, annotation 1/99).
- The author's 150/1/8 and 53/47 counts, which were taken before a whitespace-only test
  edit; my own counts are on the final bytes.
- The coordinator's 150/1/8, 4, 2 and 53 counts.

### Not run

Full suite, hosted or native CI, nightly, staging, producers or oracle, generation or
adoption, native execution, host or performance measurement.

### Verdict

**ACCEPTED for this exact bounded O1/O2 delta.** I found no delta-specific issue.

- **O1:** pre-guard `__future__` body execution is eliminated for direct, module and library
  forms, and a scratch reintroduction discriminates it. The annotation change is limited to
  raw storage, with identical resolved types.
- **O2:** absent and existing root files are refused before any mutation, allowed writes and
  reads still work, normal runs preserve bytes and mtimes, and a scratch removal of the
  predicate discriminates it.

This grants no human policy choice, U0002 replacement, installation, migration,
implementation release, G2 or sprint closure. Current U0002 remains installed and retaining
it remains available. Javid makes the human decisions.
