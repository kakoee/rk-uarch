# U1 Lane A — Stage 2 RESPONSE

Author response to `/tmp/u1-independent-reviews/U1-lane-A-review.md`, including its
reproducers/mutation evidence and the frozen candidate's U-REVIEW instructions.
This is **not reviewer adjudication**. The review was not edited.

Javid (@jjaffari) remains the authorized acting owner/approver for both U1 lanes while
Reza is off duty. No Reza approval is claimed. During this response Javid specifically
approved F4's copied-carrier compatibility boundary, F5's per-expert MoE width meaning,
and F6's explicit hardware unit validation. In this continuation Javid also approved
A-F1's narrow cycle-valued input echoes, A-F2's required table hardware identity,
A-F12's interim projection refusal, and cross-lane **B-F8**'s revised parity carrier before G1. **Complete U0001 acceptance and G1/U1 remain
pending.** Changes are local and uncommitted in `../rk-uarch-u1-a`, `u1/contract`, still
at `af3b1bc3df3171d196394a58f62202ad50845dfa` (parent `fa16aeb...`). Coordinator `89313ee`
remains a later U0019 coordination reference, not a replacement implementation base.

## Approved follow-up — A-F1/A-F2 applied; B integration still pending

The earlier A-F1/A-F2 policy deferrals are superseded by Javid's explicit approval in
this continuation. Both are implemented with failing-before/passing-after regressions.
No unresolved human choice was inferred accepted. U0001 as a whole remains proposed.

- **A-F1:** only provenance.conditional_on[*].value may echo cycle-valued hardware
  stipulations. Condition checks stipulation kind and the explicit hardware path/unit
  vocabulary. All execution fields and provenance.params retain cycle refusal. **U-P3**
  must resolve each path and compare the complete value against the referenced proposed
  HardwareSpec. U1 receives no such artifact and does not prove existence or equality.
- **A-F2:** UarchCostTable requires hardware_spec_hash (`sha256:` + 64 lowercase hex),
  included in table_hash, preserved by round-trip. The synthetic toy and its digest are
  updated. U-P3 must require table/request/spec identity equality when all are available;
  U-P19 compares table.hardware_spec_hash with characterization.spec_hash and verifies
  table digest. Field validation alone is not verification of actual HardwareSpec contents.
- **A-F12:** the interim **policy is approved**: B must explicitly refuse comparisons
  where uniform /tp cannot represent replication/padding. A's supported shapes remain
  valid and are regression-tested. B owns the guard; no oracle, tolerance or deviations
  may disguise the scope mismatch. The eventual component-aware projection is still
  a separate approval, not implemented here.
- **B-F8 (distinct from A-F8):** precise B proposal available and consumed. A's carrier,
  schema, fixtures and tests are implemented; B's actual harness adapter and cross-lane
  tests remain pending. The exact interface is below and in U0001. No proposal is missing.

The frozen candidate, coordinator main, B's worktree, snapshots and rk-sim remain untouched.
Historical implementation base af3b1bc/fa16aeb and coordinator U0019 milestone 89313ee are
preserved. This is Stage 2 response, not Stage 3 adjudication or human ADR acceptance.

## Findings dispositions

Tests below are in `contract/tests/test_u_p1_review.py` unless noted. Evidence directory:
`/tmp/u1-lane-a-response-artifacts/` (separate from the reviewer's artifacts). APPLIED
means an author fix supported by tests; it does not declare the finding adjudicated.

| Finding | Disposition | Verified evidence, action and regression/dependency |
|---|---|---|
| **F1** | **APPLIED — specifically approved** | Previously reproduced cycle-echo refusal. New `test_cycle_hardware_conditions_round_trip` accepts byte/cycle, cycle and MAC/cycle; leakage tests first validate the legitimate echo, then reject cycles in params/rows/diagnostics/top-level/extra condition fields. Stipulation/unit refusals remain. Follow-up red run failed these tests; all pass after the narrow exclusion. U-P3 path/value/spec verification is explicit, not claimed by U1. |
| **F2** | **APPLIED — specifically approved** | Required hardware_spec_hash added to model/schema/toy/digest. Missing hash test failed before; valid field/round-trip/schema/digest test failed before and passes after. Malformed hashes refused, changing identity changes table digest. Build-spec, U-P1/U-P3/U-P19 and draft boundary prose aligned. No actual unavailable spec is verified. |
| **F3** | **APPLIED** | Reproduced mutation survivors in isolated A copies; added evidence/promotion, omission, condition, named-error, KV-balance and arithmetic/scope regressions; fixed reference-following unit walker; removed redundant request cycle scan. `mutations-before.log`: 6 killed, 20 survived (19 meaningful guards plus redundant M26). `mutations-after.log`: M01–M25 killed; M26 no longer exists. Unit-walker regression failed before, passes after. Details below. |
| **F4** | **APPLIED; compatibility boundary approved** | Generated schemas now forbid explicit shared_sram=null while allowing omission. A-owned numeric fields refuse boolean/string coercion, including tp/seed/rows, shape/operator/card fields, hardware coordinates and byte widths. Pinned ModelSpec/SourcedValue retain coercions standalone and embedded, as Javid explicitly approved. Schema checks, `test_request_wire_numbers_reject_boolean_and_string`, row and other-A-owned tests fail before/pass after. Compatibility/hash test proves equal normalized inputs hash equally and documents schema/Pydantic acceptance differences. `coercion-before.log`: 6 failed/1 passed; after: 7 passed. |
| **F5** | **APPLIED; meaning approved** | Javid approved d_ff == expert_d_ff for MoE: both name one expert's intermediate width. Enforced at implied_params/check_parity boundary. Mismatched 8, 24 and 1e9 widths failed their refusal tests before; now refused. Independent hand counts distinguish total/active multipliers and shared/router terms. `compatibility-current.log` checks all three unchanged B sidecars, including Mixtral, with A's functions; no B file adopted/edited. Updated U0001, build-spec and U-P1/U-P3 copies. Dense semantics unchanged; entire parameter formula/ADR not inferred accepted. |
| **F6** | **APPLIED; unit policy approved** | Explicit 54-pattern full-path unit map checks every sourced HardwareSpec leaf, including stubs/stipulations. Errors report path, supplied label and allowed labels. byte/B preserved without conversion; other aliases not invented. 28 category/provenance cases plus exhaustive populated-leaf wrong-unit test failed before and pass after. Map documented in U0001 and schema metadata; generic SourcedValue and DRAM modes unchanged. This intentionally tightens hardware-input compatibility. |
| **F7** | **APPLIED** | CoreClockDomain fixes scales_with_core=true and defaults it when omitted, matching the existing core-always-scales rule. `test_core_domain_always_scales_and_omitted_flag_defaults_true` failed before/pass after; full round-trip inventory covers new class. NoC/DRAM flags remain explicit. One new generated schema; no clock executor. |
| **F8** | **APPLIED** | Added sync=exact and layer_reuse=true to the build-spec request fidelity fragment, preserving no-SRAM C2. `test_build_spec_fidelity_fragments_validate` parses the actual request/table fidelity fragments: missing fields failed before; both now validate as C2. Remaining ellipsized illustrative YAML is not claimed to be a complete executable fixture. |
| **F9** | **DEFERRED — U-P3 producer dependency** | Reproduced unused MOE_OMISSION and absent model identity on table. U-P3 must inspect request.model.n_experts and emit the existing MOE_OMISSION alongside common warnings; add a Mixtral producer regression. This exact follow-up is now in build-spec/U-P3 and its synchronized prompt. Recommend no new U1 payload field. A reader-verifiable model/MoE indicator would require Javid's separate schema decision; U0003 owns future prepared-input revisions. Owner: U-P3/Lane A producer; Javid decides if an extra public field is wanted. No producer exists to fix in U1. |
| **F10** | **APPLIED** | Present validated bands require high_rel>0; unknown remains null. L0/L2 energy maps must each name a family. Zero-band/empty-map tests failed before/pass after. A positive point band remains legal; the substantiated zero-error problem is fixed. Partial maps/null hashes remain unverified for uncovered families; U-P4 must check all used families' L2 evidence, never merely object presence. |
| **F11** | **APPLIED** | README distinguishes permitted HardwareSpec inputs from prohibited execution results; now records approved A-F1 echo exception and U-P3 artifact check. Documentation regression originally failed before and remains green; embedded build-spec wording agrees. Javid acting ownership preserved. |
| **F12** | **DEFERRED — B implementation; interim policy approved** | Reproduced +7.0713% memory-read discrepancy remains evidence. Javid now requires explicit refusal when uniform /tp cannot represent replication/padding. B owns guard/tests; A retains legitimate shapes (`test_a_f12_oracle_scope_does_not_restrict_legitimate_shapes`). Producer prompt/ADR record the settled policy and aggregate-versus-physical distinction. No B implementation, oracle, tolerance or deviations changed; next action is B guard plus new combined validation. |
| **F13** | **APPLIED (a,c); REJECTED (b's required sorting)** | Normalize signed floating zero in canonical JSON without mutating inputs; reject voltage keys colliding after numeric parsing. Both regressions failed before/pass after. Grid-order repro is real but intentional: U0001 preserves list order, build-spec uses frequency [1.0,0.6], and interpolation can order evaluation coordinates separately. `test_grid_order_is_preserved_in_request_identity` verifies legal reversed axes retain different hashes. Same *ordered* input still yields the same bytes. Imposing ascending order would break documented inputs without establishing an existing invariant. |
| **F14** | **APPLIED — no dependency change** | Removed Field(exclude_if) dependency in favor of Pydantic 2 wrap serialization. Test emulating an absent keyword fails before/pass after. Independently installed existing dependency Pydantic 2.10.6 only under /tmp: actual Field lacks exclude_if, old round trip fails, revised round trip passes (`compatibility-2.10.log`). No pyproject/lockfile change or added dependency. This is not a claim of testing the absolute lowest declared version or hosted CI. |

## Cross-lane B-F8 — APPLIED in A; B adapter/integration pending

This is a separate finding from original **A-F8**, whose single disposition remains in
the table above. The approved comparison semantics were read before implementation from:

- `../rk-uarch-u1-b/docs/reviews/U1-lane-B-flop-parity-interface.md`, SHA256
  `b64fa1e44917dd6b309885bc4f10e2da4b9a5e1202bb1b3d96f64fb649e1b3fc`.
- `../rk-uarch-u1-b/docs/reviews/U1-lane-B-flop-parity-payloads.json`, SHA256
  `f7c7566b0656fb8c175c3258259b8243ebee94ea57fffedd9b6f1d588e5c9580`.
- B's U0002 deviation policy and Stage 2 handoff. Their older pending-Javid A-F12 wording
  is superseded by the current explicit approval, not copied as an unresolved decision.

**Exact A interface for B:** import `FlopParity`, `ParityChannelComparison`, `FlopDeviation`
from `uarch_contract.table`. Generated schemas are `contract/schema/<ClassName>.json`.
All fields are required; nullable fields must still be supplied. No adapter/substitute
carrier is implemented by A.

| Carrier | Fields |
|---|---|
| FlopParity | kind, reference_basis, fixture_set_id, oracle_manifest_sha256, candidate_identity, n_fixtures, max_rel, comparisons |
| ParityChannelComparison | fixture_id, channel, unit, actual, reference, reference_state, raw_rel, signed_adjustment_rel, absolute_adjustment_rel, residual_rel, declared_deviations |
| FlopDeviation | id, deviation_rel, reason |

- kind = **not_run / harness_self_test / workload_parity**, explicitly required.
  reference_basis = **rk_sim_aggregate_divided_by_tp**. not_run requires null identities/
  max_rel, zero n_fixtures and empty comparisons. Run identities are nonblank strings.
  Workload parity requires oracle_manifest_sha256, a **raw 64 lowercase hex digest**
  (no `sha256:` prefix); synthetic self-tests may use null. The toy is explicitly not_run.
- Fixture/channel pairs are unique; deviation IDs are unique within each comparison.
  Channel uses all four approved Row.counts names. unit is op for matrix/vector or byte
  for memory; actual/reference are finite nonnegative numbers or null. The current oracle
  provides three channels; allowing the vector name never invents vector evidence.
- For positive reference R: raw=(actual-R)/R; signed=fsum(deviations); absolute=fsum(abs
  deviations); residual=raw-signed. Dimensionless ratios, positive means extra actual work.
  Enforce each comparison's absolute<=0.05, abs(residual)<=0.005 and reject declarations
  when abs(raw)<=0.005. No pooling or cancellation refund. Preserve full binary64 precision,
  matching B's arithmetic, with no tolerance widening or rounded percent substitution.
- For zero/null reference, actual must match, declarations empty, raw/residual null,
  signed/absolute adjustments zero. Count null never becomes count zero. State must match
  reference; all reported arithmetic must match recomputation. n_fixtures counts distinct
  ids; max_rel is max(abs(raw)) over positive-reference comparisons, otherwise null.
- External checks remain **B/U-P3-owned**: oracle/manifest authenticity, fixture completeness,
  approved projection scope, actual count provenance and physical reasons, reviewed callable
  identity. A manifest string does not authenticate a callable. Removing self-test kind
  fails; a manually asserted workload kind is still not independent proof of real parity.

**Regression evidence:** `contract/tests/test_u_p1_followup.py` written first: **51 failed,
5 passed** before implementation; **56 passed** after. Three additional checks preserve
replication/padding support and explicitly demonstrate unavailable-spec limits; the final
file has **59 passing tests**. Coverage includes all kinds, raw/max semantics, fixture/
channel/deviation duplicates, wrong units, arithmetic tampering, exact 5%/0.5% boundaries,
just-outside residual, cancellation/split-budget violations, unnecessary adjustments,
zero/null refusals and table serialization. B's three unchanged sample payloads round-trip
exactly in A (`b-payloads.log`); the workload sample is hypothetical, not a reported result.

**B next actions:** consume these exact types/schema; flatten the existing comparisons map;
collect actual/reference/units in the same run (do not rerun the candidate); explicitly map
kind and attach identities; retain declarations and all four quantities; add real harness
round-trip/boundary tests. Add A-F12 scope refusal before comparison, preserving all oracle
values/tolerances and A's legitimate shape support. Update B tests expecting the old table
hash/schema/carrier: hardware_spec_hash is now required and hash-covered; top-level parity
`declared_deviations` moved into comparisons. Coordinator must retain B's independently
edited U-P2/build-spec portions when merging A's U-P1/U-P3/U-P19 changes. No vendor regeneration
or adoption is required for these A carrier edits or performed by A. B's separately reported
artifact-compatibility failures are not resolved or revalidated by this A-only delivery.

## F3 evidence and coverage rationale

The reviewer harness was copied only to the response scratch directory and adapted to
set PYTHONPATH to each disposable copy (preventing editable-install imports from hiding
mutations). Each mutation's output is preserved as `mutant-{before,after}-Mxx.log`.
The initial count is **20** survivors including M26, rather than the report's headline
19; the substantive invariant gaps are confirmed, not dismissed over that count.

| Mutants | New public-guarantee tests that detect deletion |
|---|---|
| M01, M02 | Out-of-grid request raises EnvelopeExceedsGrid; negative/nonfinite nested count raises **NonFiniteRow**, checking Pydantic ctx.error, not just generic rejection. |
| M03 | Remove each required warning independently and require refusal. Synthetic-table annotation is not mistaken for a required omission. |
| M04–M07 | Nondivisible decode total; repeated grid point; balanced heads/FFN but unbalanced KV replication (24 heads, 8 KV, tp12); controller attached outside grid. |
| M08–M12 | Inverted band; median greater than max; composition sample total mismatch; both priming presence mismatches; duplicate parameter names. |
| M13–M15 | Claims refused as conditions; both card carriers require evidence above stub; L0/L0m/L1/L2 hashes do not replace ledger entries. |
| M16, M17, M23, M25 | Paged operand missing page size; undefined reduction axis; MHA with fewer KV heads; each missing residency resource key. |
| M18–M22, M24 | Existing roofline/composite/exact-sync/preset/reference/fused-operand tests continue detecting deletion. |
| M26 | No request field carries a unit, and extra cycle/unit keys are refused structurally. Removed redundant traversal; explicit extra-key regressions preserve the boundary. No unreachable-condition test fabricated. |

The schema walker now resolves local `$ref` definitions. A synthetic referenced foreign
`latency: number` was invisible before and is found after. Explicit SourcedValue.value
is exempted only where its parent schema requires a string unit. This does not certify
hardware unit compatibility; F6's separate validator/tests do that.

## Policy and interface limits

- **F4:** copied carriers' numeric strings are accepted by Pydantic and normalized for
  hashing; their JSON Schemas still require JSON numbers. This difference is explicitly
  approved and tested. A-owned numeric fields reject boolean/string conversion. Integral
  numbers such as tp=8.0 remain valid as JSON integers. Hardware unit checks still apply.
- **F5:** B's Mixtral widths stay 14336/14336. Redundant fields are not independent
  dimensions; active expert work uses experts_per_token once, total expert parameters
  use n_experts once, and shared terms stay separate. No runtime workload built here.
- **F6:** standalone SourcedValue remains generic. HardwareSpec's schema publishes the
  unit map as semantic metadata, not executable JSON-Schema unit enforcement. Core
  scales_with_core=false is now rejected and omitted core flags normalize to true.
- **F12:** the mismatch is replica-to-rank projection, separate from Javid's approved
  four-entry Channel mapping. That mapping remains name-only, with no scaling or null
  conversion. Current B fixtures do not exercise replication/padding; their prior green
  result cannot establish these scopes. A's broader shard rules remain proposals where
  previously proposed, not retroactively accepted by the review's wording.
- Optional SRAM semantics and exact→approximate non-promotion are unchanged. A producer
  must cross-check HardwareSpec and never omit an existing SRAM from fidelity_detail.
  Accepted U0019 direction is preserved: standalone preparation, resolved engine inputs,
  authoritative supported imported shapes/mappings, U0003 schema ownership, no U2 payloads.
- Stale founder wording remains in authoring execution-plan U1/G1 (lines 123/125/260),
  U-P1's historical approval/ADR instructions and their build-spec copy. The frozen
  combined plan also has the newer “recorded human ownership” wording. These do not
  revoke Javid's already-authorized acting role. Coordinator can reconcile historical
  governance prose when integrating; no request for repeated role authorization or
  Reza approval is made. Historical acceptance of other revisions is not relabeled.

## Validation — Lane A only (current follow-up)

Executed from `/home/jjaff/AI-infra-simulation/rk-uarch-u1-a` with its local environment.
All final commands below exited 0; earlier deliberately failing runs are listed separately.

| Exact command | Result |
|---|---|
| `make gen` | Generated **69 schemas** (68 concrete models plus PrecisionFormat); ParityChannelComparison is new in this follow-up. |
| `uv run --no-sync pytest -q contract/tests/test_u_p1.py contract/tests/test_u_p1_review.py contract/tests/test_u_p1_followup.py` | **257 passed**. |
| `uv run --no-sync pytest -q` | **261 passed**, no skips. |
| `uv run --no-sync mypy src contract` | No issues, **33 source files**. |
| `uv run --no-sync ruff check` | All checks passed. |
| `uv run --no-sync lint-imports` | **2 kept, 0 broken**. |
| `make gen-check` | Schemas fresh. |
| `uv run --no-sync pytest -q tests/unit/test_prompt_sync.py` | **2 passed**. |
| `git diff --check` | No whitespace errors. |

Current follow-up evidence is in `/tmp/u1-lane-a-followup-artifacts/`: `red.log`,
`green.log`, `acceptance.log`, `full.log`, `mypy.log`, `ruff.log`, `imports.log`,
`schema.log`, `prompt-sync.log`, `b-payloads.log`. Targeted command:
`uv run --no-sync pytest -q contract/tests/test_u_p1_followup.py`; B-payload command:
`uv run --no-sync python -B /tmp/u1-lane-a-followup-artifacts/check_b_payloads.py`.

Historical first-response reproduction / failing-before evidence (retained, not rerun):

```sh
REPO=/home/jjaff/AI-infra-simulation/rk-uarch-u1-a .venv/bin/python -B /tmp/u1-lane-a-response-artifacts/probe.py
.venv/bin/python -B /tmp/u1-lane-a-response-artifacts/extra_probes.py
.venv/bin/python -B -m pytest -q contract/tests/test_u_p1_review.py
# Tests written before fixes: 50 failed, 31 passed (regressions-before.log).
.venv/bin/python -B -m pytest -q contract/tests/test_u_p1_review.py -k unit_walk
# 1 failed, 81 deselected before reference-walker fix.
uv run --no-sync pytest -q contract/tests/test_u_p1_review.py -k 'pinned_numeric or other_a_owned'
# Before: 6 failed / 1 passed; after: 7 passed.
python3 -B /tmp/u1-lane-a-response-artifacts/mutate.py /tmp/u1-lane-a-response-artifacts/before /tmp/u1-lane-a-response-artifacts/mutant-before
python3 -B /tmp/u1-lane-a-response-artifacts/mutate.py /home/jjaff/AI-infra-simulation/rk-uarch-u1-a /tmp/u1-lane-a-response-artifacts/mutant-after
PYTHONPATH=/tmp/u1-lane-a-response-artifacts/pydantic-2.10 .venv/bin/python -B /tmp/u1-lane-a-response-artifacts/compatibility.py
.venv/bin/python -B /tmp/u1-lane-a-response-artifacts/compatibility.py
```

The sidecar checks and F12 probe read B files from the frozen candidate but execute A
contract functions/read-only B comparison code. They are **not a later full combined
A+B validation**. No combined rerun, cold clone or hosted CI success is claimed.
Schemas remain structural; provenance truth, producer/spec equality, ledger applicability
and reader checks are not proved by these tests. No engine or U-P3 implementation added.
The rk-sim pin remains clean at `1e5706e0ebfcc67c1a7333079a35b75f693e9963`.
Coordinator main, frozen candidate, B's worktree, snapshots and rk-sim were not modified.
No artifact adoption, commit, merge, rebase, tag, human-approval environment setting,
ADR acceptance, reviewer adjudication or U1 closure was performed.
