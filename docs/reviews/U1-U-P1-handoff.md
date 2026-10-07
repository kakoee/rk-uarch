# U1 · U-P1 — Lane A contract proposal handoff

> **Current publication status — Lane B integration note, 2026-10-06.**
> Both independent lane Stage 3 reviews are ACCEPTED; see [Lane A](U1-lane-A-review.md)
> and [Lane B](U1-lane-B-review.md). A-F12's guard and full-coverage regressions are
> implemented and accepted in the combined proposal; B-F8 is integrated. The replacement
> snapshot has passed real human double-generation and strict validation. Earlier pending
> integration/generation statements below are historical and superseded, not rewritten.
> U0001/U0002 remain proposed; the strict stub-source exception still needs whole-ADR
> acceptance. Snapshot adoption/publication, hosted CI, Linux-box cold-clone validation
> and G1/U1 remain pending. Embedding accounting and B-F16 retain their U2 scope.
> Use [the final publication handoff](U1-publication-handoff.md) for exact files and gates.

**Date:** 2026-10-04; revised 2026-10-06. **State:** implemented proposal, local and uncommitted;
Remaining Javid decisions and final integrated validation remain outstanding.
The coordinator has combined A with B's actual snapshot and tests; see the attributed
update below. **U1/G1 are not complete.**

Javid (@jjaffari) is acting owner and human approver for **both U1 lanes** while
Reza is off duty. This arrangement comes from the session's explicit instruction.
No Reza approval is claimed. U0001 as a whole is **PROPOSED**, not accepted;
its exact Channel mapping is **approved by Javid**. On 2026-10-06 Javid approved
revising composite fidelity and timing-origin policies before final acceptance. The
complete revised ADR and concrete schema proposal still await final review. Lane A performed no commit,
merge, push, tag, UARCH_HUMAN=1, engine, or U-P3 work.

## Stage 2 approved follow-up — current delivery

Javid explicitly approved **A-F1**, **A-F2**, **A-F12** and the cross-lane **B-F8** carrier
revision before G1. A-F1/A-F2 are now applied; they are no longer unanswered human choices.
A-F12's interim refusal policy is settled, with B's guard/tests still pending. B-F8 is
tracked separately from A-F8; A's carrier implementation is delivered, while B's adapter
and cross-lane tests remain dependencies. The [Stage 2 response](U1-lane-A-response.md)
retains one disposition for each original A-F1–F14; A-F9 remains a U-P3 producer dependency.
Specific approvals do not accept the complete proposed U0001 or close Stage 3/G1/U1.

**A-F1:** table cycle quantities are allowed only as hardware stipulations inside
provenance.conditional_on[*].value. The carrier enforces stipulation kind and the explicit
hardware path/unit vocabulary. Execution rows, diagnostics, params and other fields retain
cycle refusal. **U-P3 owns verifying the actual referenced proposed HardwareSpec and each
condition's path/complete value.** U1 does not receive that artifact, so it cannot establish
existence of a resource index or the actual design's value. No producer is implemented.

**A-F2:** required table.hardware_spec_hash uses the existing sha256: + 64 lowercase hex
format, survives round-trip and participates in table_hash. The synthetic toy now includes
it and has a recomputed digest. U-P3 must enforce table/request/spec identity equality;
U-P19 compares table.hardware_spec_hash to characterization.spec_hash and checks table
identity. Field syntax is not authentication or validation of an unavailable spec. Missing
identities and the old parity shape are invalid in this unfrozen pre-G1 revision.

**Exact B-F8 handoff:** use `uarch_contract.table.{FlopParity,ParityChannelComparison,
FlopDeviation}` and their matching generated schemas. The [response's B-F8 section](U1-lane-A-response.md#cross-lane-b-f8--applied-in-a-b-adapterintegration-pending)
and [U0001](../decisions/U0001-the-integration-contract.md) list every field/type/rule.
The implementation matches B's precise interface proposal, read before implementation:
`../rk-uarch-u1-b/docs/reviews/U1-lane-B-flop-parity-interface.md` and its payload file.
No competing representation or missing-proposal dependency remains.

- FlopParity: **kind, reference_basis, fixture_set_id, oracle_manifest_sha256,
  candidate_identity, n_fixtures, max_rel, comparisons**. All fields required, including
  nullable ones. kind is not_run/harness_self_test/workload_parity; never inferred/defaulted.
- Comparison: **fixture_id, channel, unit, actual, reference, reference_state, raw_rel,
  signed_adjustment_rel, absolute_adjustment_rel, residual_rel, declared_deviations**.
  Declarations remain {id, deviation_rel, reason}, now nested under their comparison.
- Ratios use the positive projected reference denominator. signed=sum(d), absolute=sum(abs(d)),
  residual=raw-signed; absolute<=5%, abs(residual)<=0.5%, with no pooling/cancellation refund.
  Refuse declarations for raw-inside-tolerance and zero/null references. Preserve B's
  binary64/math.fsum arithmetic, not rounded percentages or expanded tolerances.
- Zero/null references require matching actual, no declarations, null raw/residual, zero
  adjustments. Units are op/byte and must match channel. Unique fixture/channel pairs and
  local declaration IDs; n_fixtures/max_rel must agree with contents. max_rel is raw error.
- Workload parity requires a **raw 64-hex manifest digest without sha256: prefix** and run
  identities. not_run requires null identities/max, zero fixtures and no comparisons.
  The toy is not_run. Self-test success never becomes actual workload parity; a caller's
  manifest/implementation name still requires external authentication/review.

**B integration next:** adapt the real harness output using these actual types, capture
counts/units in the same run, flatten comparisons without losing attribution, explicitly
map kind, preserve all ratios/declarations and supply identities. Add cross-lane round-trip
and boundary tests. Incorporate the newly required table identity/toy digest. B must also
refuse uniform-/tp comparisons requiring replication/padding under approved A-F12; keep A's
legitimate shapes and distinguish aggregate oracle approximation from physical rank-local
correctness. No oracle changes, tolerance widening, fixture dropping or deviation camouflage.
Coordinator must preserve B's separate U-P2/build-spec changes while merging A's mirrored
U-P1/U-P3/U-P19 updates. B's separately reported artifact-compatibility limits are not
resolved or revalidated by this A-only delivery; no artifact was regenerated/adopted.

**Tests first and validation:** new regressions produced **51 failed / 5 passed** before
implementation, then **56 passed** after. Three further checks preserve legitimate shapes
and explicitly bound unavailable-spec claims; the file now has **59 tests**. B's three
unchanged example payloads round-trip exactly through A models (the workload example is
hypothetical). These are A-only carrier checks, not a combined harness validation.

| Exact final command | Outcome |
|---|---|
| `make gen` / `make gen-check` | **69 schemas**, fresh (68 models plus PrecisionFormat). |
| `uv run --no-sync pytest -q contract/tests/test_u_p1.py contract/tests/test_u_p1_review.py contract/tests/test_u_p1_followup.py` | **257 passed**. |
| `uv run --no-sync pytest -q` | **261 passed**, no skips. |
| `uv run --no-sync mypy src contract` | No issues in **33 files**. |
| `uv run --no-sync ruff check` | All checks passed. |
| `uv run --no-sync lint-imports` | **2 kept, 0 broken**, 42 files / 87 dependencies. |
| `uv run --no-sync pytest -q tests/unit/test_prompt_sync.py` | **2 passed**. |
| `git diff --check` | Clean. |

Evidence: `/tmp/u1-lane-a-followup-artifacts/` (pre-change snapshot/inventory, red/green,
acceptance/full/static-check logs, B proposal/payload hashes and payload validation log).
Earlier evidence below is historical. Previous uncommitted work and af3b1bc/fa16aeb base,
89313ee/U0019 milestone, approved SRAM/DRAM/Channel/F4/F5/F6 decisions are preserved.
No B worktree, frozen candidate, coordinator main, vendor artifacts or rk-sim was modified.
No engine/U-P3/U2 implementation, commit, merge/rebase, tag, push, UARCH_HUMAN=1, ADR
acceptance or review adjudication was performed. Final U0001 and G1/U1 remain pending.

## First Stage 2 response — retained history and earlier evidence

Full response: [U1-lane-A-response.md](U1-lane-A-response.md). This is the author's
response, **not reviewer adjudication**. All 14 findings were verified; the reviewer
report and frozen combined candidate were not modified. This section supersedes earlier
implementation counts/limits where noted; historical evidence and baseline references
below remain intact.

**Earlier disposition (superseded above for F1/F2/F12):** F3–F8, F10–F11, F13–F14 had
applied fixes; F13 sorting was rejected with evidence. F1/F2 awaited choices at that point;
the continuation explicitly approved and implemented them. F9 still belongs to U-P3;
F12 now has an approved interim policy awaiting B's implementation.
Javid specifically approved F4's pinned-carrier numeric compatibility boundary, F5's
per-expert MoE widths, and F6's explicit hardware unit map during this response. Those
approvals do not accept U0001 as a whole or the other remaining proposals.

- **F1 earlier proposal (now approved/applied):** only provenance.conditional_on[*].value may echo unchanged hardware
  stipulations in cycle/per-cycle units. Execution results and provenance.params remain
  cycle-free. Later producers must check each path/value against the bound proposed
  HardwareSpec. Alternative: path-only conditions plus the spec artifact. At that earlier stop no exception had been implemented; the current follow-up
  above supersedes that parser limitation.
- **F2 earlier proposal (now approved/applied):** require hardware_spec_hash on every table, include it in table_hash,
  verify equality with request/spec identity in U-P3 and characterization.spec_hash in
  U-P19. Required schema, synthetic toy/digest, test and downstream-doc changes are laid
  out in the response. Alternative: mandatory request sidecar. At the earlier stop no field had been added. The current follow-up adds it after
  Javid's explicit approval; artifact-aware producer checks still belong to U-P3.
- **F4 approved:** A-owned numeric fields reject boolean/string coercions. Copied
  ModelSpec and generic SourcedValue preserve pinned coercions, standalone and embedded;
  hashes use normalized validated values. Their schemas still reject numeric strings
  accepted by Pydantic. No identical-acceptance claim. Optional shared_sram schema now
  forbids null while allowing omission; exact/approximate composite rules are unchanged.
- **F5 approved:** MoE d_ff == expert_d_ff, both one expert's width. Total expert
  parameters use n_experts once; active parameters/work use experts_per_token once;
  shared terms are separate. Dense d_ff unchanged. B's Mixtral sidecar remains unchanged
  and passes the A model/shape check. Parameter-formula acceptance remains pending.
- **F6 approved:** 54 explicit hardware field-path patterns define exact units, including
  stubs/stipulations. byte/B aliases preserve labels/values. No implicit conversion,
  generic-carrier narrowing, preset-mode change or citation inference. The schema
  publishes the map as semantic metadata; Pydantic enforces it. U0001 contains the full
  map and unsourced scalar-unit exceptions.
- Core scaling now defaults to and requires true; request fidelity example is complete;
  zero claimed error bands and empty evidence maps are refused; negative floating zero
  has one canonical identity; duplicate normalized voltage keys are refused. The README
  distinguishes hardware inputs from execution results. Optional-resource serialization
  no longer depends on Field(exclude_if); actual Pydantic 2.10.6 reproduces old failure
  and revised success in a temporary environment, with no dependency/lockfile edits.
- **F9 next action:** U-P3 must emit MOE_OMISSION from request.model.n_experts and add a
  Mixtral producer regression. This obligation is now explicit in its synchronized prompt.
- **F12 interface warning:** B's uniform replica-count/tp projection disagrees with the
  A-supported tp16/KV8 shape by **7.0713%** for the reproduced memory-read case. Recommend
  B guard unsupported replicated-KV/padded-vocabulary cases until an approved projection
  exists. B owns that guard and tests; A's request scope is unchanged. No tolerance,
  oracle fixture, snapshot or B file was changed. Name-only Channel mapping stays exact.

**Acceptance evidence:** tests were written before fixes: 50 failures/31 passes in the
first corrected regression run; one additional foreign-schema walker failure; then six
additional numeric-boundary failures with one compatibility pass. Final tests pass.
Mutation reproduction found six killed and 20 survivors (19 meaningful guards plus
redundant M26). Expanded tests kill all 25 retained mutants; redundant request traversal
was removed, with explicit extra-cycle/unit-key refusal tests. Ledger evidence, each
omission, stipulation-only conditions and concrete documented error classes are covered.
All prior SRAM/DRAM regressions remain green.

**Earlier A-only validation (historical)** (local authoring environment, all exit 0):

| Exact command | Outcome |
|---|---|
| `make gen` / `make gen-check` | **68 schemas**, fresh; 67 models plus PrecisionFormat. |
| `uv run --no-sync pytest -q contract/tests/test_u_p1.py contract/tests/test_u_p1_review.py` | **198 passed**. |
| `uv run --no-sync pytest -q` | **202 passed**, no skips. |
| `uv run --no-sync mypy src contract` | No issues in **32 files**. |
| `uv run --no-sync ruff check` | All checks passed. |
| `uv run --no-sync lint-imports` | **2 kept, 0 broken**. |
| `uv run --no-sync pytest -q tests/unit/test_prompt_sync.py` | **2 passed**; U-P1/U-P3 copies synchronized. |
| `git diff --check` | Clean. |

Full commands, before/after logs and disposable mutation outputs are recorded in the
response and `/tmp/u1-lane-a-response-artifacts/`. Read-only checks of B sidecars and
its comparison helper are **not** a later full combined A+B rerun. Coordinator must
integrate these local proposals and rerun combined validation after the blocking choices;
hosted CI/cold-clone evidence and reviewer Stage 3 remain outstanding.

U0019's accepted preparation direction, the approved four-entry Channel mapping, exact
DRAM modes, optional-SRAM semantics and producer HardwareSpec/detail cross-check are
preserved. No future payload fields or engine/U-P3 code were added. Javid's acting role
already governs both lanes; stale “both founders” wording in historical execution-plan
and U-P1 text is identified in the response, not treated as missing Reza approval.
All changes remain local/uncommitted; no adoption, commit, merge, rebase, push, tag,
UARCH_HUMAN=1, final ADR acceptance or G1/U1 closure was performed.

### Stage 2 changed-file scope

The content audit against the preserved pre-response authoring snapshot found these
31 changed/new source documents, tests and schemas, with **no existing file removed**.
Generated caches are excluded. Existing earlier uncommitted changes outside this list
were preserved; in particular this response made no Makefile, vendor or CI change.

```text
contract/README.md
contract/schema/CharacterizationRequest.json
contract/schema/ClockDomains.json
contract/schema/CoreClockDomain.json
contract/schema/EmbeddedModelCard.json
contract/schema/EnergyVerification.json
contract/schema/FidelityDetail.json
contract/schema/HardwareSpec.json
contract/schema/ModelCard.json
contract/schema/ModelId.json
contract/schema/Provenance.json
contract/schema/UarchCostTable.json
contract/schema/ValidatedErrorBand.json
contract/tests/fixtures/model_examples.json
contract/tests/test_u_p1.py
contract/tests/test_u_p1_review.py
contract/uarch_contract/common.py
contract/uarch_contract/fidelity.py
contract/uarch_contract/hardware.py
contract/uarch_contract/hashing.py
contract/uarch_contract/model_card.py
contract/uarch_contract/model_shape.py
contract/uarch_contract/operators.py
contract/uarch_contract/request.py
contract/uarch_contract/table.py
docs/build-spec.md
docs/decisions/U0001-the-integration-contract.md
docs/prompts/U-P1-the-contract.md
docs/prompts/U-P3-hardware-workload-and-the-analytic-engine.md
docs/reviews/U1-U-P1-handoff.md
docs/reviews/U1-lane-A-response.md
```

## Preparation-ownership documentation follow-up — coordinator 89313ee

Read the coordinator's accepted
`../rk-uarch/docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md`
and amended `../rk-uarch/docs/prompts/U-P1-the-contract.md`. Both match coordinator
commit `89313ee` (`89313eef20e6b252d235b40a680a1464c52c636a`), which records Javid's
accepted architectural direction on 2026-10-06. This is a coordination milestone;
Lane A remains on `u1/contract` at its historical `af3b1bc` baseline, with `fa16aeb`
as the parent. No merge, rebase, commit or branch movement was performed.

U0001 now records U0019's accepted preparation ownership:

- Standalone workload/mapping preparation remains supported, without requiring an
  external compiler or rk-sim service.
- Engines consume resolved inputs; imported rank shapes and mappings are authoritative
  within validated, supported scope, with no hidden re-sharding or mapping replacement.
- U0003 owns concrete prepared-input schemas, validation/identity fixtures and public
  contract revisions before U2 implementation. No future payload fields or U2 code
  are added in U1. Explicit fork mapping delegation remains bounded and visible.

**Status distinction:** U0019's direction is accepted; the complete U0001 remains
**PROPOSED pending final review**. Its optional-SRAM semantics, explicit direct/preset
DRAM timing modes, approved four-entry name-only Channel mapping and other proposal
content are preserved. The later producer must still cross-check HardwareSpec: an
existing shared SRAM must never disappear from fidelity_detail; unsupported means
"unrepresented", while omission means physically absent. This follow-up neither
implements that later producer nor accepts future schema fields. No Reza approval,
new integrated implementation result, or G1/U1 completion is claimed.

**Exact changed-file list for this follow-up:**

1. `docs/decisions/U0001-the-integration-contract.md`
2. `docs/reviews/U1-U-P1-handoff.md`

Only these documents were edited. The coordinator's full prompt was not copied over
Lane A's revised prompt: its preparation-boundary instruction is recorded in U0001
without replacing the existing SRAM, DRAM or Channel changes. B's worktree and vendor
artifacts were not changed. No schema, test, executable, build-spec or prompt edit was
made. Existing uncommitted work is preserved.

**Documentation verification:** coordinator ADR/prompt compared against 89313ee; local
prompt-sync checked with `uv run pytest -q tests/unit/test_prompt_sync.py` (2 passed);
`git diff --check` and direct whitespace checks of these untracked documents are clean.
A before/after content-hash inventory of tracked and untracked non-ignored files
confirms the two-file scope; the existing policy sections and historical SHA references
are retained. Earlier implementation test results below are historical, not a new
full-suite run for this documentation-only follow-up.

## Optional shared-SRAM correction — 2026-10-06

The coordinator clarified the ambiguous "missing shared SRAM" wording. The original
optional-resource semantics are restored: **omission means physically absent**, never
unknown or unmodelled. The full revised ADR still awaits final acceptance. The accepted
DRAM-mode implementation and already-approved Channel mapping are unchanged.

For compute=2, noc="1+ts", dram=2 and exact sync:

| shared_sram | Composite |
|---|---|
| omitted (hardware has none) | C2 |
| "unrepresented" | C1 |
| 0 | C1 |
| 1 | C1 |
| "1+ts" | C2 |

Every scenario above becomes C1 with approximate sync. All-zero represented hardware
still stays C0 under exact or approximate sync. Exhaustive classification and monotonicity
checks retain all 240 legal hardware-level combinations, both layer_reuse values and
two approximate quanta. The no-shared-SRAM C2 table is accepted at its roofline; below
its roofline it raises the **roofline-specific** refusal, proving the floor validator
executes rather than being blocked by an incorrect composite mismatch.

**Producer contract:** later integration must compare HardwareSpec with fidelity_detail.
If HardwareSpec declares shared SRAM, the producer must emit a level ("unrepresented"
when unsupported), never omit the key. If hardware has none, omit the key. No producer
or cross-artifact validator is implemented by this narrow correction.

**Tests first:** the explicit scenarios, no-SRAM table/floor checks and corrected
exhaustive expectations produced **5 failed, 9 passed, 92 deselected** before the fix.
The no-SRAM floor regression specifically caught the wrong composite-mismatch error.
After the fix, the same selection gave **14 passed, 92 deselected**.

**Final validation** from `/home/jjaff/AI-infra-simulation/rk-uarch-u1-a` (all exit 0):

| Exact command | Outcome |
|---|---|
| `uv run pytest -q contract/tests/test_u_p1.py` | **106 passed** in 0.94 s. |
| `uv run pytest -q` | **110 passed** in 1.01 s, including prompt-sync; no skips. |
| `uv run mypy src contract` | No issues in **31 source files**. |
| `uv run ruff check` | All checks passed. |
| `uv run lint-imports` | **2 kept, 0 broken**. |
| `make gen-check` | All schemas fresh; no regeneration needed. |
| `git diff --check` | No whitespace errors. |

A SHA-256 comparison against a snapshot taken before this correction confirms hardware.py,
dram_timing_modes.json and all 67 generated schemas are byte-identical. Changes are
limited to fidelity.py, its acceptance tests, U0001, build-spec rules/example, the
synchronized U-P1 prompt and this handoff. The example downgraded solely because shared
SRAM was absent is restored to C2. No B worktree or vendor artifact was changed. Earlier
work, baseline/pin history and all uncommitted changes are preserved; no commit or other
publication action occurred. Final integrated validation and ADR acceptance remain pending.

## Policy revisions — 2026-10-06

**Authority:** Javid approved revising the composite-fidelity branches and replacing
DRAM citation heuristics with explicit timing-origin metadata before final acceptance.
The direction is approved; the complete revised U0001 and this concrete implementation
remain **proposed pending final review**. No Reza approval is claimed. Other open choices
(strict stub source=None, parameter accounting, KV replication/vocabulary padding, etc.)
remain proposed. The exact approved Channel mapping is unchanged.

**Composite:** C0 when compute/noc/dram are all 0 and shared_sram is omitted, 0 or
unrepresented, with either exact or approximate sync. Absent/unrepresented shared SRAM
adds no detail. C2 requires compute=2, noc/dram in {2,"1+ts"}, exact sync in 0.1 and
shared_sram="1+ts" only when hardware has it. Omission means physically absent; an
unrepresented existing resource cannot satisfy C2. All other higher-detail configurations
are C1. The method leaves the detail vector unchanged. This reflects the coordinator's
optional-resource clarification, superseding the earlier mandatory-SRAM interpretation.
The illustrative build-spec table without shared SRAM is restored to C2. Later producers
must emit a level when HardwareSpec declares shared SRAM ("unrepresented" if unsupported)
and omit it only when hardware has none; standalone FidelityDetail cannot cross-check
HardwareSpec. No producer implementation or new evidence carrier was added.

**Exact schema choice:** one required typed field on Dram,
`timing_source: Literal["direct", "preset"]`, retaining existing `timing_preset` and
`timing` fields. No default, no extra wrapper, no per-leaf origin field. Direct requires
null/omitted timing_preset and has no fallback; its citations remain valid regardless of
"@" or .yaml/.yml/.cfg. Preset requires one nonblank file and full pinned 40-hex SHA;
every non-stub timing claim must cite its exact file@sha. Mixed preset/datasheet claims
remain unsupported. Stubs and proposed-design stipulations retain their old rules;
reference stipulations still fail with their full parameter path. A mode declaration
cannot independently prove a citation truthful. The old source-string classifier is gone.

Generated schemas express required mode and conditional preset presence/nullability;
Pydantic also checks exact citations. The 67-schema inventory is unchanged; Dram,
Memory and HardwareSpec schemas carry the new discriminator/conditions. Existing
HardwareSpec inputs must add an explicit timing_source; this is an unfrozen 0.1 proposal
revision, not a claim of backward compatibility with an accepted release.

**Examples:** U0001 shows both modes as timing fragments, with full validated Dram
examples in `contract/tests/fixtures/dram_timing_modes.json`. Direct cites
`synthetic://direct@lab/timing.yaml`; preset names `synthetic/preset.cfg` at a synthetic
40-character SHA and cites that exact file@sha. Values are illustrative, never hardware
evidence. The toy table and B's model-shape/vendor artifacts need no mode field and
were not changed.

**Tests first:** the new policy regressions ran against the old implementation with
19 failed, 10 passed and 64 deselected; they reproduced the C0→C1 sync defect,
unrepresented-resource promotion and the old timing interface. The example test also
failed on the missing new fixture before that fixture was written. After implementation,
all 29 targeted policy regressions passed. Exhaustive branch tests cover all 240 legal
hardware-level combinations, both layer_reuse values and exact plus two approximate
quanta (1 and 1,000,000 ps): 480 vectors, 1,440 evaluations, 960 non-promotion comparisons.
Additional cases exercise missing/unpinned/malformed presets, direct citations resembling
preset filenames, mismatched or mixed citations, reference/proposed provenance, direct
with preset refusal and round trips for both valid modes.

**Validation before the optional-resource correction** (local .venv; all exited 0):

| Exact command | Outcome |
|---|---|
| `make gen` | Regenerated the 67 schemas. |
| `make gen-check` | Schemas fresh. |
| `uv run pytest -q contract/tests/test_u_p1.py` | **94 passed** in 0.91 s. |
| `uv run pytest -q` | **98 passed** in 0.91 s, including prompt-sync; no skips. |
| `uv run mypy src contract` | No issues in **31 source files**. |
| `uv run ruff check` | All checks passed. |
| `uv run lint-imports` | **2 kept, 0 broken**; 42 files, 86 dependencies. |
| `git diff --check` | No whitespace errors. |

**Scope and coordination:** changed hardware.py, fidelity.py, U-P1 acceptance tests,
one synthetic timing-example file, generated schemas, U0001, this handoff, Lane A's
build-spec prose and its U-P1 prompt copy. Read B's U-P1/build-spec wording only to
preserve the already-approved exact four-entry Channel mapping, with no scaling, tp
division or null conversion. B's worktree, vendor artifacts, U0002, tooling, CI and U-P2
prompt were not changed. B's separate U-P2 wording changes still belong in the eventual
combined checkout; this revision touches only the U-P1 prompt block in build-spec §8.

The 2026-10-04 coordinator integration evidence below predates these revisions; it is
not a claim that the combined checkout has been rerun on this schema. Final integrated
validation and Javid's final ADR review remain outstanding. All earlier work and useful
baseline/pin history are preserved; no commit, push, merge, tag or U-P3 work was performed.

## Checkout and preservation evidence

The supplied directory was the clean main checkout at af3b1bc. The existing clean
Lane A worktree was `/home/jjaff/AI-infra-simulation/rk-uarch-u1-a`, on `u1/contract`.
Lane A's local proposal files remain there. The coordinator separately reports
combining them with Lane B; this follow-up does not modify that integration checkout.

- Implementation base: `af3b1bc3df3171d196394a58f62202ad50845dfa`.
- Its immediate parent: `fa16aeb5671f0f0fbfc372d7d57487fddaf65933`.
- Javid explicitly approved retaining af3b1bc, the documentation-only approved pin
  update, rather than resetting to the originally requested fa16aeb.
- Read-only rk-sim path: `../rk-sim-u1-pin`, exactly
  `1e5706e0ebfcc67c1a7333079a35b75f693e9963`; clean at start and final audit.
- No pre-existing local changes were present in main or Lane A. No branch history
  was rewritten. In this follow-up, B's U0002 and U1-U-P2-handoff were read for
  coordination; no Lane B worktree files were changed.
- Read CLAUDE.md, the execution plan (including current STATUS, U1 and G1),
  how-it-works, the historical U0 handoff, implementation template, U-P1 and its
  required build-spec/pinned rk-sim context. Current STATUS takes precedence over
  the U0 handoff's obsolete statements about missing protected files and remote/tag.

The sandbox launcher failed with an unsupported host mount at `/mnt/wslg/distro`.
Commands therefore used approved escalation, including writes to the existing Lane A
worktree outside the initially configured writable root. Early checks used the existing
main .venv with PYTHONPATH selecting Lane A; final checks use Lane A's own .venv,
created offline from existing lockfile/cache. Main's environment registration was
restored to main after those early checks. No dependencies or lockfile were changed.

## Implementation checklist

- [x] SourcedValue, claim/stipulation split, finite values, required evidence or rationale.
- [x] Rev-2 HardwareSpec: sourced counts, clock domains, matrix/vector/SRAM/DMA,
  sync, optional shared SRAM, NoCs, controller queues/credits, DRAM organization,
  named preset/timing, format widths, energy/voltage coefficients, static power/TDP.
- [x] Recursive reference-only-claims validation with exact parameter path;
  integral count checks; preset and SRAM-energy checks.
- [x] P16-aligned operator concepts, named dimensions, per-operand dtype/layout,
  reduction axes; attention_fused admits exactly Q/K/V/O as DRAM operands.
  MAC=two-operations and fused count=sum-of-parts are documented semantics;
  no operator graph or engine count evaluator was added.
- [x] Exact ModelSpec field/default/validator copy, ModelShape, proposed parameter
  accounting, and 1% total/active identity check.
- [x] Exact eight PrecisionFormat members and Precision defaults.
- [x] Request, canonical phase-specific rows/table, error statistics, diagnostics,
  provenance/conditions, model-card carriers and shared fidelity vector.
- [x] All 17 named errors/warning, with user sentences and ErrorRecord schema transport.
- [x] Canonical JSON, SHA-256, normalized spec/request/table hash helpers;
  table digest excludes only its own top-level digest.
- [x] 69 generated JSON Schemas (68 concrete models plus PrecisionFormat; Stage 2 adds CoreClockDomain and ParityChannelComparison).
- [x] make gen; make gen-check; pytest freshness check, including stale/missing/extra
  file regression. Generation raises on duplicate model export names.
- [x] Handwritten synthetic toy table, two decode rows and one prefill; auxiliary
  synthetic carrier examples. Neither is a parity fixture or calibration evidence.
- [x] Full proposed ADR [U0001](../decisions/U0001-the-integration-contract.md),
  including all nine semantic rules and explicit alternatives/recommendations.
- [x] Makefile edit limited to replacing gen's placeholder, adding gen-check and
  its .PHONY entry. vendor-rk and CI remain Worker B's responsibility.

## Acceptance checklist and evidence

Acceptance file: `contract/tests/test_u_p1.py`. Tests were written first: the initial
run failed collection because HardwareSpec did not yet exist. Subsequent targeted
regressions were observed failing before their fixes (nested cycle-unit leakage,
unsampled weighted-error zero, boolean levels, explicit-null shared-SRAM level).
The initial generation check also exposed a nondeterministic duplicate Grid schema
name; hardware now uses HardwareGrid and generation rejects collisions.

| U-P1 item | Evidence |
|---|---|
| 1. Every model round-trips | Round-trip inventory now covers all 68 exported concrete models and nested carriers; asserts frozen=True/extra=forbid. |
| 2. Stable hashes | Two fresh interpreter processes, reversed input key order, model-vs-JSON hash equality, non-finite canonical JSON rejection. |
| 3. Every named error | 17 parametrized class/message/ErrorRecord round-trips; real invalid inputs preserve StipulationOnReference, ClaimWithoutSource, UnnamedPreset, ShardIndivisible, EnvelopeExceedsGrid and NonFiniteRow in Pydantic error context. |
| 4. Carrier refusal rules | Invalid source/rationale combinations, strict null stub source, non-finite value and blank rationale. |
| 5. Deep reference stipulation | cores.core_type.sram.banks named in refusal; same leaf accepted as a proposed design. |
| 6. Unit names | Walks request/table float schemas through local references and mapping/list branches, recognizing explicit-unit carriers; applies unit inheritance and matrix_ops/vector_ops exception. |
| 7. No cycles at boundary | Field/fixture walk, structural request extra-key refusal and recursive table rejection, including a cycle unit hidden in provenance.params. Approved F1 exempts only hardware condition values; U-P3 verifies the actual spec. |
| 8. ModelShape identity | 70B-shaped hand count passes; 10% FFN-width error fails with declared and implied counts; independent tiny MoE arithmetic case. |
| 9. Toy validates | UarchCostTable validates the handwritten toy and its digest; B reports CI wiring, but **hosted contract CI success is not claimed**. |
| 10. Rev-2 fields | Missing/invalid preset SHA, mismatched preset, missing SRAM energy, reference stub bank count; fractional count refusal. |
| 11. Null, not numeric defaults | Every diagnostics and model-card field checked for numeric defaults. |
| 12. Complete toy metadata | tp/state/KV layout, all four errors, embedded stub card and null diagnostics asserted. |
| 13. Legal fidelity values | Illegal values/key-naming errors, boolean levels and explicit null refused. |
| 14. Revised composite branches | Exhaustive legal-level branches and exact→approx monotonicity pass; sync and unrepresented resource metadata are preserved. |

Additional checks cover matching and replicated KV shards, named FFN indivisibility,
duplicate rows, phase key mixing, attribution sums, composite mismatch, C2 below its
own roofline, fused attention score materialization, and negative/non-finite rows.

Original implementation commands (2026-10-04), run from `/home/jjaff/AI-infra-simulation/rk-uarch-u1-a`, without
PYTHONPATH or shared-environment overrides:

| Exact command | Outcome |
|---|---|
| `uv sync --extra dev --offline` | Exit 0; worktree-local Python 3.12.14 environment, existing lockfile/cache, no dependency changes. |
| `make gen` | Exit 0; 67 schemas generated. |
| `make gen-check` | Exit 0; schemas fresh. |
| `uv run pytest -q contract/tests/test_u_p1.py` | Exit 0; **64 passed** (1.40 s). |
| `uv run pytest -q` | Exit 0; **68 passed** (2.04 s), no skips. |
| `uv run mypy src contract` | Exit 0; no issues in **31 source files**. |
| `uv run ruff check` | Exit 0; all checks passed. |
| `uv run lint-imports` | Exit 0; **2 kept, 0 broken**, 42 files/86 dependencies analyzed. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git branch --show-current` | `u1/contract`. |
| `git rev-parse HEAD` | `af3b1bc3df3171d196394a58f62202ad50845dfa`. |
| `git log -1 --format='%H %P'` | Confirms af3b1bc's immediate parent is full fa16aeb SHA above. |
| `git -C ../rk-sim-u1-pin status --porcelain` | Empty; pinned checkout clean. |
| `git -C ../rk-sim-u1-pin rev-parse HEAD` | Exact required full SHA above. |

Native files were untouched, so native-test was not applicable. No hosted CI run is
claimed. B's later handoff records CI wiring; that is not evidence of hosted success
or acceptance of the remaining proposed decisions.

## Coordinator integration update — 2026-10-04

Read B's `docs/decisions/U0002-the-vendored-snapshot-and-parity-discipline.md` and
`docs/reviews/U1-U-P2-handoff.md` from `../rk-uarch-u1-b`, without editing B's
worktree. They record Javid's approved four-entry map, an actual human-generated
snapshot, and CI wiring. Their pending-A statements precede the newer coordinator
results below and are historical for these checks.

The coordinator reports combining A's proposal with B's actual snapshot/tests:

- All three model-shape sidecars pass `check_parity`.
- ModelSpec/PrecisionFormat identity, claim round-trip, stipulation refusal and the
  exact Channel mapping checks pass.
- The only integration failure reported is B's overly broad ADR pin parser; B is
  fixing it. U0001's rk-sim pin and useful af3b1bc/fa16aeb history references are
  preserved, not removed to accommodate the parser.

This evidence is attributed to the coordinator, not a Lane A rerun. It does not
establish real workload FLOP parity or accept strict stub source=None, parameter
accounting, KV replication/vocabulary padding, preset rules, composite-fidelity
completion, or any other remaining proposal. No overall pass count or hosted CI
success is inferred from the report.

The 2026-10-04 documentation follow-up edited only U0001 and this handoff. Documentation checks verify the
exact mapping, preserved history and proposal labels; `git diff --check` is clean.
No executable code, schemas, tests, fixtures or Lane B files were changed, so the
implementation test evidence above is retained rather than presented as a new run.

## Approved Channel mapping

Javid approved preserving Row.counts keys with exactly this name-only translation,
now recorded canonically in [U0001](../decisions/U0001-the-integration-contract.md):

| Row.counts field | rk-sim diagnostic Channel |
|---|---|
| matrix_ops | matrix_ops |
| vector_ops | vector_ops |
| memory_read_bytes | memory_read |
| memory_write_bytes | memory_write |

No scaling, tp division or null conversion occurs. Numeric values are unchanged and
null remains null. Each field has exactly one mapping; destinations are unique and
valid vendored Channel literals; unknown fields fail. The two-operations-per-MAC
convention is not a conversion performed by this mapping. Any parity-harness
replica-to-rank projection is a separate operation. This decision is no longer open.

## Remaining decisions for Javid

All items below remain **proposed**, with alternatives and consequences in U0001.
Passing integration checks do not imply acceptance:

1. Accept the prompt defaults together: build-spec applicability bins, no
   BLOCKFP8→fp8 evidence equivalence, optional shared SRAM, steady default, declared
   omissions, per-row applicability, Megatron-style one-tp shards, clock assignments,
   common fidelity vocabulary, phase-specific keys, embedded card, fused attention.
2. Accept strict stub source=None despite the pinned rk-sim blank-string loophole;
   permit Worker B to record that narrow negative-input exception. Alternative:
   explicitly amend the prompt to mirror the loophole.
3. Accept the documented bias-free norms/router/embedding parameter formula and its
   formula, or select a different formula. F5's per-expert d_ff/expert_d_ff relation is now specifically approved; it is not still an open choice. All three actual sidecars passing
   check_parity demonstrates compatibility, not approval of the formula.
4. Require balanced KV replication; propose vocabulary padding for nondivisible V
   rather than rejecting it or creating unequal ranks. U-P3 must implement the choice.
5. Review the revised required timing_source discriminator and direct/preset schema
   after Javid's approval of the revision direction. Preset mode requires a full pinned
   SHA and exact non-stub claim citations; mixed preset/datasheet claims remain unsupported.
6. Review the revised explicit C0/C1/C2 branches after Javid's approval of the direction:
   sync cannot promote fidelity; omission means physically absent shared SRAM;
   existing shared SRAM must be "1+ts" for C2; contract 0.1 permits C2 only with exact sync.
7. Confirm the named relative visit-weight records, parameter/condition records,
   coefficient-family energy maps, zero-sample/null error representation, proposed
   categorical hardware sets, array-fill endpoint convention and hash normalization.

These are review decisions, not hidden blockers to producing the proposal. No operator
naming conflict requiring the prompt's early-stop rule was found: pinned P16 contains
concept names, not a contradictory implemented wire enum.

## Interfaces Worker B must consume

No message was sent to another person or worker; these interfaces are provided here
for Javid to pass on. Early session updates identified the ownership boundary and the
two pinned-vocabulary discrepancies before implementation proceeded.

| Interface | Producer/consumer contract (proposed unless marked approved) |
|---|---|
| Pin | `RK_SCHEMA_SNAPSHOT` in common.py and U0001 must match Worker B's manifest: exact `1e5706e0ebfcc67c1a7333079a35b75f693e9963`. |
| Claim parity | `uarch_contract.sourced.SourcedValue`; compare value/unit/provenance/source/date on claims. kind defaults claim, rationale null. Five-field projection strips only these uarch additions. Strict blank stub-source difference is proposed, not accepted. |
| Model parity | `uarch_contract.model_shape.ModelSpec`, `ModelShape`, `implied_params(spec,shape)`, `check_parity(spec,shape)`. ModelSpec is the pinned copy; fixtures remain Worker B's independent work. |
| Precision | `uarch_contract.precision.PrecisionFormat` and Precision, also package exports; all eight enum strings and fp16/fp16 defaults. |
| Count seam — approved | Exact four-entry mapping above, name-only: no scaling, tp division or null conversion. Unknown fields fail. Extension counts are outside this map. |
| Revised timing interface | HardwareSpec.memory.dram now requires timing_source="direct" or "preset". No default/inference; direct forbids a preset, preset requires one full-SHA file. This changes the unfrozen proposal; no vendor artifacts change. |
| Revised composite | All-zero represented detail is C0 under either sync mode. Omitted shared_sram means hardware has none; C2 requires "1+ts" only when it exists, plus other resource prerequisites and exact sync. Producers must compare against HardwareSpec and never omit an existing resource. Higher detail otherwise is C1. |
| Requests and tables | `CharacterizationRequest.model_validate(...)`, `UarchCostTable.model_validate(...)`; decode/prefill discriminated rows; `Row` is the shared base, not a union parser. |
| Errors | `ErrorRecord` transports all 17 exception/warning types. Pydantic wraps raising validators as ValidationError, retaining the concrete cause in ctx.error. |
| Hashes | `canonical_json`, `sha256`, `spec_hash`, `request_hash`, `table_hash`. Parse/model normalization precedes identity hashing. Parsing does not verify the supplied digest; compare separately. |
| CI freshness | `make gen-check` or `uv run python -m uarch_contract.generate --check`; checks missing, changed and extra JSON without rewriting. `make gen` is regeneration only. |
| CI toy/acceptance | `uv run pytest -q contract/tests/test_u_p1.py`; full pytest also collects it. Toy path `contract/tests/fixtures/toy_table.json`. |
| Schema paths | `contract/schema/<ClassName>.json`; now 69 files, including UarchCostTable.json, CharacterizationRequest.json, HardwareSpec.json, ModelSpec.json and PrecisionFormat.json. |
| Makefile overlap | Merge only A's gen/gen-check/.PHONY additions with B's vendor target. A has not changed vendor-rk, scripts, CI or U0002. |

## Limitations and remaining blockers

- Human acceptance of U0001 as a whole and the remaining proposed choices is
  outstanding; the Channel mapping and the two revision directions are already approved. All human-owned
  modifications remain uncommitted for Javid's review.
- Worker B owns vendor tooling/snapshot, independently generated parity fixtures and
  tests, model-shape fixture files, U0002 and CI wiring. B's handoff records the actual
  human-generated snapshot and wired CI; the coordinator now reports the combined
  semantic checks passing. Lane A neither regenerated nor independently certified
  B's artifacts. The reported pin-parser failure remains B's fix, followed by final
  integrated validation. G1 and U-P3 remain gated.
- Generated JSON Schema captures structural constraints. Pydantic validation remains
  necessary for cross-field arithmetic and semantic checks; schema alone cannot prove
  attribution sums, parity, preset provenance, evidence applicability or digest identity.
- Explicit timing_source replaces source classification. Declarations cannot independently
  prove a citation truthful. No preset files are opened; preset mode checks exact file@sha
  citations for non-stub claims. No fallback or mixed-source inference is implemented.
- Stage 2 F6 now enforces explicit hardware unit/path compatibility without conversion.
  Generic SourcedValue remains compatible; U-P3 still owns derived parameter units and provenance.
- Frozen Pydantic models do not deeply freeze nested dicts. Treat them as immutable
  values; do not bypass validation with model_construct/model_copy updates.
- Ledger applicability, actual report hashes, model badge ceilings and complete energy
  evidence are future U-P4 work. The carriers do not certify ledger claims.
- The toy's numbers and request/card IDs are explicitly synthetic. There is no measured
  accuracy, real characterization, FLOP parity result or model promotion in this proposal.
- No full table/request consistency validator, interpolation, engine, mapping, timing
  conversion, workload generation or rk-sim reader was built. Those remain their prompts.

**Stop point: U-P1 proposal delivered for review. U1 is not declared complete.**
