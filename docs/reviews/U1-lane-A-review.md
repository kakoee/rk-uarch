# U1 · Lane A (U-P1, the contract) — U-REVIEW Stage 1 independent review

- **Date:** 2026-10-06
- **Stage:** 1 (REVIEW). Evidence only. This review does not decide whether U1 is complete, change any ADR's status, or adopt anything.
- **Reviewer independence:** I ran as a fresh session. I did not author either lane's implementation, the coordinator's amendments, or the assembly. This is my first contact with this code.
- **Primary target (read only):** `/tmp/u1-final-integration-84hif1_r`. This is a plain directory, not a Git checkout.
- **Assembly evidence (read only):** `/tmp/u1-final-integration-84hif1_r-evidence/FINAL-VALIDATION.md`, plus `assembly.json`, `conflict-resolutions.json` and the input inventories.
- **Source worktrees (read only):** Lane A at `/home/jjaff/AI-infra-simulation/rk-uarch-u1-a` (branch `u1/contract`, HEAD `af3b1bc`). Lane B at `/home/jjaff/AI-infra-simulation/rk-uarch-u1-b`.
- **Baseline:** coordinator `89313eef20e6b252d235b40a680a1464c52c636a`. rk-sim pin `1e5706e0ebfcc67c1a7333079a35b75f693e9963`, read only from `/home/jjaff/AI-infra-simulation/rk-sim-u1-pin`, which was clean.
- **Where I ran things:** a disposable copy of the target with its own environment (`uv sync --locked --extra dev --offline`, Python 3.12.14, pydantic 2.13.5). Mutation runs used a second, throwaway copy. I did not modify the target, the evidence, the worktrees, the coordinator repository or rk-sim.
- **Supporting artifacts:** `/tmp/u1-independent-reviews/U1-lane-A-review-artifacts/` contains `probe_lane_a.py`, `probes.log`, `mutate.py`, `mutations.log` and the check logs.

Paths below are absolute. `CAND` = `/tmp/u1-final-integration-84hif1_r`.

## Lane A scope as reviewed

I reconstructed Lane A's complete change set from the A worktree's `git status`, `assembly.json` (88 A operations applied, 2 clean three-way merges) and the conflict record:

- `CAND/contract/uarch_contract/*` (13 modules)
- `CAND/contract/schema/*.json` (67 files)
- `CAND/contract/tests/test_u_p1.py` and `CAND/contract/tests/fixtures/{toy_table,model_examples,dram_timing_modes}.json`
- `CAND/docs/decisions/U0001-the-integration-contract.md` and `CAND/docs/reviews/U1-U-P1-handoff.md`
- Lane A's U-P1 text in `CAND/docs/build-spec.md` and `CAND/docs/prompts/U-P1-the-contract.md` (the two conflict regions)
- the `gen` and `gen-check` targets in `CAND/Makefile`

`diff -rq` shows every Lane A contract module, schema, fixture, test, ADR and handoff in CAND is byte-identical to the A worktree. Lane B's tests that consume A's interfaces are reviewed here for cross-lane compatibility only: `vendor_support.py`, `test_vendored_round_trip.py`, `test_committed_snapshot.py` and `parity.py`.

## Summary

- **The reported validation reproduces independently:**
  - strict contract suite: 153 passed, 0 skipped
  - full suite: 157 passed
  - `mypy` clean (42 files with `scripts`; 30 with the configured `files`)
  - `ruff` clean
  - import-linter: 2 contracts kept
  - schema freshness: fresh
  - vendor `--check`: passes

  The handoff's counts also hold: 106 U-P1 tests, 67 schemas, 240 legal level combinations, 12 optional-SRAM cases and 22 DRAM-mode cases. The copied `ModelSpec` class is AST-identical to the pinned rk-sim source.
- **Two BLOCKING findings, both decisions for the contract freeze (G1):**
  - **F1:** the table cannot carry the stipulations it is required to record.
  - **F2:** the table has no hardware spec hash, so rk-sim's spec-hash check (§6.5, §7.4, U-P19) cannot be performed from a table file.
- **Twelve NON-BLOCKING findings (F3–F14).** The most consequential:
  - **F3:** 19 of 26 contract validators survive deletion. This includes the guards for badge evidence, declared omissions and `conditional_on`.
  - **F4:** what the JSON Schema accepts differs from what Pydantic accepts.
  - **F5:** MoE `d_ff` is unconstrained by the parity identity.
  - **F12:** Lane B's replica-to-rank projection contradicts Lane A's accepted KV-replication shard. I reproduced a 7.07% miss against the 5% ceiling.
- **Verified sound:**
  - the composite rule and sync monotonicity (exhaustive, and killed by mutation)
  - C2 roofline-floor enforcement (one ulp below the floor is refused)
  - explicit direct/preset DRAM timing modes (no string heuristics remain; mutation killed)
  - reference-stipulation refusal with full path
  - the name-only Channel mapping
  - hash stability across processes and `PYTHONHASHSEED`
  - U0019 ownership: recorded without adding any U2 payload fields
- **Not established by this review:** a cold clone on the Linux box, hosted CI, and human acceptance of U0001. See "Pending".

## Findings index

| ID | Severity | Classification | Title | Primary location |
|---|---|---|---|---|
| F1 | **BLOCKING** | Implementation defect; remedy is a human decision | `conditional_on` cannot carry stipulated `*_cycles` / `*_per_cycle` hardware leaves | `CAND/contract/uarch_contract/common.py:23-37`, `CAND/contract/uarch_contract/table.py:199-207,244` |
| F2 | **BLOCKING** | Unresolved human decision (the spec sources disagree) | `UarchCostTable` carries no hardware spec hash, but §6.5, §7.4 and U-P19 require one | `CAND/contract/uarch_contract/table.py:222-240` |
| F3 | NON-BLOCKING (invariant-bearing items recommended before G1) | Implementation defect (tests) | 19 of 26 contract validators survive deletion | `CAND/contract/tests/test_u_p1.py` |
| F4 | NON-BLOCKING | Implementation defect | JSON Schema and Pydantic accept different inputs: explicit-null `shared_sram`; booleans and strings coerced into integers and numbers | `CAND/contract/uarch_contract/fidelity.py:16-29`, `CAND/contract/uarch_contract/common.py:19-20` |
| F5 | NON-BLOCKING (settle before U-P3) | Human decision plus validator gap | MoE `ModelShape.d_ff` is unconstrained by `check_parity`, and its meaning is contradictory | `CAND/contract/uarch_contract/model_shape.py:95-99`, `CAND/contract/uarch_contract/request.py:115` |
| F6 | NON-BLOCKING | Human decision (limitation declared in the handoff) | A hardware `unit` string may contradict the unit in the field name | `CAND/contract/uarch_contract/sourced.py:38-43`, `CAND/contract/uarch_contract/hardware.py:39-41` |
| F7 | NON-BLOCKING | Implementation defect plus doc drift | `clock_domains.core.scales_with_core` is required and may be `false` | `CAND/contract/uarch_contract/hardware.py:45-53` |
| F8 | NON-BLOCKING | Doc drift | The build-spec §2.3.3 example request does not validate | `CAND/docs/build-spec.md:313` |
| F9 | NON-BLOCKING | Later sprint (U-P3) plus human decision | The MoE declared omission is defined but enforceable nowhere | `CAND/contract/uarch_contract/table.py:33,259` |
| F10 | NON-BLOCKING | Implementation defect | Zero-width `validated_error_band` accepted; empty `energy_verification` maps accepted | `CAND/contract/uarch_contract/model_card.py:41-58` |
| F11 | NON-BLOCKING | README truthfulness (human-owned path) | `contract/README.md` says no field carries cycles; `HardwareSpec` does by design | `CAND/contract/README.md:11` |
| F12 | NON-BLOCKING (latent; owner Lane B / U-P3) | Cross-lane incompatibility; projection is a human decision | Parity projection `value / tp` contradicts A's replicated-KV and padded-vocabulary shard | `CAND/contract/tests/parity.py:71-75`, `CAND/contract/uarch_contract/request.py:118-123` |
| F13 | NON-BLOCKING (low) | Implementation defect | Canonicalization edges: `-0.0`, grid axis order, duplicate float-spelled keys | `CAND/contract/uarch_contract/hashing.py:18-23`, `CAND/contract/uarch_contract/request.py:53-69`, `CAND/contract/uarch_contract/hardware.py:228` |
| F14 | NON-BLOCKING (low) | Dependency declaration (human decision) | `Field(exclude_if=...)` is used while `pyproject.toml` declares `pydantic>=2` | `CAND/contract/uarch_contract/fidelity.py:16-18`, `CAND/pyproject.toml:6` |

### Common reproducer preamble

Run from the root of a **disposable copy** of CAND after `uv sync --locked --extra dev --offline`:

```bash
uv run --no-sync python -B - <<'EOF'
import sys; sys.path[:0] = ["contract", "."]
from contract.tests.test_u_p1 import hardware, request_data, sv, toy
# ... snippet from the finding ...
EOF
```

All observed outputs quoted below come from `U1-lane-A-review-artifacts/probes.log` or `mutations.log`.

---

## F1 — BLOCKING — `conditional_on` cannot carry stipulated per-cycle or cycle hardware leaves

**Where:**
- `CAND/contract/uarch_contract/common.py:30-33`: `reject_cycles` refuses any dict whose key is `unit` and whose value contains `"cycle"`.
- `CAND/contract/uarch_contract/table.py:244`: it is applied to the whole table.
- `CAND/contract/uarch_contract/table.py:199-207`: `Condition = {path, value: SourcedValue}` and requires `kind="stipulation"`.

**Defect.** These requirements together say a proposed design's stipulations must reach the table unchanged:
- Build-spec §2.6 rule 1 (`CAND/docs/build-spec.md:602-603`): "Stipulations are excluded and recorded in `conditional_on`".
- U0001 records `conditional_on` as `{path, value: stipulation}`.
- U-P3 (`CAND/docs/prompts/U-P3-hardware-workload-and-the-analytic-engine.md:42-43`) expects stipulated MACs/cycle.
- The U2 joint exit criterion requires `uarch report` to show "conditional · N stipulations" for `hw/designs/npu-l4.yaml`.

For a proposed chip, stipulated leaves are typically `macs_per_cycle`, `link_bytes_per_cycle`, `bytes_per_cycle_per_bank`, `job_overhead_cycles` and `router_latency_cycles`. Their units contain "cycle", and §6.1 explicitly allows `_per_cycle` and `HardwareSpec` `_cycles` names. Yet the table validator refuses every one of them. The cycle rule exists to keep computed results free of cycles (CLAUDE.md invariant 3). As written, it also blocks the table's echo of the input design.

**Reproducer:**
```python
from uarch_contract.table import UarchCostTable
from uarch_contract.hardware import HardwareSpec
t = toy()
t["provenance"]["conditional_on"] = [{"path": "nocs[0].link_bytes_per_cycle",
    "value": sv(64, "byte/cycle", kind="stipulation", provenance=None, rationale="design choice")}]
UarchCostTable.model_validate(t)          # refused
hw = hardware(); hw["design_status"] = "proposed"
hw["nocs"][0]["link_bytes_per_cycle"] = t["provenance"]["conditional_on"][0]["value"]
HardwareSpec.model_validate(hw)           # accepted: the same leaf is legal in the spec
```

**Observed:**
```text
[REFUSED ] conditional_on nocs[0].link_bytes_per_cycle unit='byte/cycle' -> Value error, provenance.conditional_on[0].value.unit: cycles cannot cross the request/table boundary.
[REFUSED ] conditional_on cores.core_type.job_overhead_cycles unit='cycle' -> ... cycles cannot cross the request/table boundary.
[REFUSED ] conditional_on cores.core_type.matrix_engine.macs_per_cycle.fp8 unit='MAC/cycle' -> ... cycles cannot cross the request/table boundary.
[ACCEPTED] conditional_on clock_domains.core.freq_hz unit='Hz'
[ACCEPTED] proposed spec with stipulated link_bytes_per_cycle
```

**Why BLOCKING.** G1 freezes the table shape. If frozen like this, U-P3/U-P4 cannot satisfy §2.6 for any realistic proposed design without a contract revision. Execution-plan G1: "A contract that is not frozen is the rework that grows".

**Classification.** An implementation defect in human-owned `contract/`. The remedy is a founders' decision. Options:
- (a) Exempt `provenance.conditional_on[*].value` (an input echo bound to a spec path) from the unit test, while keeping keys, rows and `params` checked. **Recommended.**
- (b) Carry conditions as `{path}` plus a spec binding and no value. This depends on F2.
- (c) Make producers convert stipulations to time units. Not recommended: it changes the stipulated value.

**Proposed regression tests (`CAND/contract/tests/test_u_p1.py`):**
- `test_conditional_on_carries_stipulated_per_cycle_leaf`: a toy table whose `conditional_on` holds `nocs[0].link_bytes_per_cycle` (unit `byte/cycle`) and `cores.core_type.job_overhead_cycles` (unit `cycle`) validates and round-trips.
- Keep `test_cycle_unit_cannot_hide_in_table_provenance`, so a cycle unit in `provenance.params` still fails.
- Add `test_row_cycle_key_still_refused`: a `*_cycles` key injected into a row fails.

## F2 — BLOCKING (human decision) — the table carries no hardware spec hash

**Where:** `CAND/contract/uarch_contract/table.py:222-240`. `UarchCostTable` fields are `contract, uarch_version, request_hash, table_hash, tp, initial_state, kv_layout, rows, interpolation, measured_error, flop_parity, composite_fidelity, fidelity_detail, provenance, warnings`.

**Defect.**
- Build-spec §6.5 (`CAND/docs/build-spec.md:1362-1363`): "Every table carries the spec, request and table hashes."
- §7.2 rule 6 (`:1430-1432`): "the spec hash matches".
- §7.4 (`:1462`): "Table spec hash ≠ component's → `SpecHashMismatch`".
- U-P19 (`CAND/docs/prompts/U-P19-rk-sim-P18-characterized-C2-cost.md:33-34,56-57`): the loader "checks the table's spec_hash against the component's characterization.spec_hash".
- `CAND/rk-sim-side/decisions/DRAFT-admit-characterized-c2-tables.md:50` defines `Characterization = {table_path, table_hash, spec_hash, ...}`.
- U0001 rule 6 says "Verify the referenced hardware hash".

The table references no hardware hash. It carries `request_hash`, which is a one-way digest of a request that contains `hardware_spec_hash`. rk-sim's loader is file-based, so it cannot recover the spec hash from the table. The cross-artifact check U0001 assigns to later integration (`HardwareSpec` declares a shared SRAM, so `fidelity_detail` must not omit it) also needs a table-to-spec binding. U0019 item 5 ("traceable from results and tables") points the same way.

**Reproducer:**
```python
from uarch_contract.table import UarchCostTable
print(sorted(UarchCostTable.model_fields))
t = toy(); t["hardware_spec_hash"] = "sha256:" + "c" * 64
UarchCostTable.model_validate(t)
```

**Observed:** `has spec hash field: False` and `[REFUSED ] toy + hardware_spec_hash -> Extra inputs are not permitted`.

**Classification.** U-P1 item 7's table-level list (`CAND/docs/prompts/U-P1-the-contract.md:107`) omits a spec hash, so Lane A followed its prompt. The build-spec, U-P19 and the draft boundary ADR require one. That conflict is a founders' decision. It blocks G1 because the first check in U-P19's loader cannot be implemented against the frozen shape.

**Options:**
- (a) Add `hardware_spec_hash: Hash` to `UarchCostTable`, included in `table_hash`. **Recommended.**
- (b) Amend §6.5, §7.4, U-P19 and the draft ADR so rk-sim ships and reads the request beside every table.

**Proposed regression tests:**
- `test_table_requires_hardware_spec_hash`: the toy without the field fails, and with it validates.
- `test_schema_lists_hardware_spec_hash`: `CAND/contract/schema/UarchCostTable.json` lists it as required.
- For U-P3: a producer test asserting `table.hardware_spec_hash == request.hardware_spec_hash`.

## F3 — NON-BLOCKING — 19 of 26 contract validators survive deletion

**Where:** `CAND/contract/tests/test_u_p1.py` (the whole suite), against validators across `CAND/contract/uarch_contract/`.

**Reproducer.** `python3 U1-lane-A-review-artifacts/mutate.py <disposable-copy> <scratch-dir>`. This removes one validator at a time in a fresh copy and runs `pytest -x contract/tests tests`.

**Observed** (`mutations.log`): *killed* = the suite failed when the guard was removed; *survived* = 157 passed anyway.

Invariant-bearing survivors (recommended before G1):

| Mutant | Guard removed | Rule it carries | Result |
|---|---|---|---|
| M14 | `ModelCard` above-stub requires evidence (`model_card.py:69-73`) | CLAUDE.md invariant 7, "Nothing may raise a badge" | survived |
| M15 | `EmbeddedModelCard` above-stub requires evidence (`model_card.py:83-87`) | invariant 7; the badge rk-sim reads | survived |
| M03 | table warnings must include the declared omissions (`table.py:259-260`) | §2.3.4 declared omissions | survived |
| M13 | `conditional_on` only stipulations (`table.py:203-207`) | §2.6 rule 1 | survived |
| M01 | `EnvelopeExceedsGrid` raised by the request (`request.py:137-141`) | §7.4 error; U-P1 acceptance 3 | survived (no failing-input test) |
| M02 | `NonFiniteRow` walker (`table.py:73-88`) | §7.4 error class | survived: rows are still refused by Pydantic, but the error class is never asserted |
| M06 | KV replication balance, `tp % kv_heads` (`request.py:120-123`) | U0001 shard proposal | survived (only accepted cases are tested) |

Other survivors: M04 canonical decode divisibility, M05 grid uniqueness, M07 attach-in-grid, M08 error-band ordering, M09 median ≤ max, M10 composition sample sum, M11 priming null exactly when unsampled, M12 unique params, M16 paged-operand page size, M17 undefined dimensions, M23 mha/gqa consistency, M25 peak-resident keys.

M26 (`reject_cycles` on the request, `request.py:113`) also survived. That code is unreachable: requests carry no units, and `extra="forbid"` stops `*_cycles` keys. It is dead code, not a test gap.

Killed (adequately tested): M18 C2 floor, M19 composite equality, M20 exact-sync prerequisite, M21 preset citation equality, M22 reference-stipulation refusal, M24 fused-attention operands.

A related gap: `test_unit_and_cycle_boundaries` (`test_u_p1.py:450-485`) walks only each request/table class's top-level schema, without following `$ref`. Floats in foreign models are therefore unchecked. Today that is only `SourcedValue.value`, which is acceptable because its unit is explicit, but the docstring's claim of "every float field" is broader than the test.

**Classification.** Implementation defect (tests). Stage 3 requires applied fixes to have failing-without tests, so these should exist.

**Proposed regression tests:** one minimal failing input per survivor, asserting the concrete class or message where the contract raises it:
- `test_badge_above_stub_requires_evidence[ModelCard|EmbeddedModelCard]`
- `test_table_requires_declared_omissions`
- `test_conditional_on_rejects_claim`
- `test_envelope_exceeds_grid_raises_class`
- `test_negative_row_raises_nonfinite_row_class`
- `test_kv_replication_unbalanced_refused` (for example `n_heads=24, kv_heads=8, tp=12`)
- `test_decode_total_not_divisible_by_batch`
- `test_grid_repeat_refused`
- `test_attach_outside_grid`
- `test_error_band_inverted`
- `test_sampled_error_median_above_max`
- `test_composition_sum_mismatch`
- `test_priming_presence_mismatch`
- `test_duplicate_param_names`
- `test_paged_without_page_size`
- `test_undefined_reduction_axis`
- `test_mha_with_fewer_kv_heads`
- `test_peak_resident_missing_key`

## F4 — NON-BLOCKING — JSON Schema and Pydantic accept different inputs

**Where:**
- (a) `CAND/contract/uarch_contract/fidelity.py:16-18,22-29`: the type is `Literal[...] | None`, but a before-validator refuses explicit `null`. The generated schema still permits `null`.
- (b) `CAND/contract/uarch_contract/common.py:19-20`: `FrozenModel` runs in Pydantic's lax mode.

**Defect.** Build-spec §7.1 states that rk-sim validates `UarchCostTable` JSON with the contract's JSON Schema. Two sets of inputs are judged differently:
- **(a)** `shared_sram: null` is valid under `CAND/contract/schema/FidelityDetail.json` and inside `UarchCostTable.json`, but Pydantic refuses it. The handoff records refusing explicit null as a fixed regression; the schema never received that fix. A schema-only consumer could read `null` as "absent", which yields C2 eligibility under the composite rule.
- **(b)** Pydantic coerces values the schema forbids: `tp: true` becomes 1, `tp: "8"` becomes 8, `seed: "7"` becomes 7, a row's `batch: true` becomes 1, and `duration_s: "0.001"` becomes 0.001. The request hash is identical to the normalized request, so a JSON boolean silently becomes a shard degree of 1 with a valid identity.

**Reproducer:**
```python
import json
from uarch_contract.request import CharacterizationRequest
from uarch_contract.fidelity import FidelityDetail
print(CharacterizationRequest.model_validate(request_data() | {"tp": True}).tp)   # 1
print(json.load(open("contract/schema/FidelityDetail.json"))["properties"]["shared_sram"])
FidelityDetail.model_validate({"compute": 2, "noc": 2, "dram": 2, "shared_sram": None,
                               "sync": "exact", "layer_reuse": False})            # refused
```

**Observed:**
```text
[ACCEPTED] request tp=True -> (1, True)
[ACCEPTED] table row batch=true -> 1
[ACCEPTED] table row duration_s='0.001' -> 0.001
schema tp: {'minimum': 1, 'title': 'Tp', 'type': 'integer'}
schema shared_sram: {"anyOf": [{"enum": [0, 1, "1+ts", "unrepresented"]}, {"type": "null"}], "default": null, ...}
[REFUSED ] pydantic shared_sram=None -> Value error, shared_sram requires a legal level; omit absent shared_sram.
```

Level values are not affected: `compute: 2.0` normalizes to `2`, and `"2"` is refused.

**Proposed regression tests:**
- `test_fidelity_schema_forbids_null_shared_sram`: the generated schema has no `null` branch.
- `test_request_refuses_boolean_and_string_integers`: `tp=True`, `tp="8"` and `seed="7"` are all refused.
- `test_row_refuses_string_numbers`.

A schema-vs-model differential test would need `jsonschema`, which is not a dependency. Adding it requires asking (CLAUDE.md).

## F5 — NON-BLOCKING (settle before U-P3) — MoE `d_ff` is unconstrained and its meaning is contradictory

**Where:**
- `CAND/contract/uarch_contract/model_shape.py:95-99`: the MoE branch never uses `d_ff`.
- `CAND/contract/uarch_contract/request.py:115`: `d_ff` is still checked for tp divisibility.
- `CAND/docs/decisions/U0001-the-integration-contract.md:199-200`: "d_ff remains the mandatory dense-equivalent width in the MoE sidecar".

**Defect.** U-P1 says the parity check exists so that "two sources describing different models" become impossible. For MoE, `d_ff` escapes it: any positive value passes `check_parity`. Its meaning is also inconsistent:
- U0001 calls it the "dense-equivalent width".
- Build-spec §1.3 (`CAND/docs/build-spec.md:124`) scopes MoE as an "active-parameter dense-equivalent". For Mixtral that would be `experts_per_token × expert_d_ff` = 28,672.
- Lane B's sidecar (`CAND/contract/fixtures/model_shapes/mixtral-8x7b.json`) sets `d_ff = 14336 = expert_d_ff`, the per-expert width.

If U-P3 builds the dense-equivalent FFN from `d_ff`, Mixtral's active FFN work halves: roughly −44% `matrix_ops` against rk-sim's `2·P_active`. U2's parity gate would catch that, but only after implementation.

**Reproducer:**
```python
import json
from uarch_contract.model_shape import ModelSpec, ModelShape, check_parity
mix = json.load(open("contract/fixtures/model_shapes/mixtral-8x7b.json"))
for d_ff in (14336, 8, 10**9):
    check_parity(ModelSpec.model_validate(mix["model"]),
                 ModelShape.model_validate(mix["shape"] | {"d_ff": d_ff}))   # all pass
```

**Observed:** `[ACCEPTED] mixtral check_parity with d_ff=8` and `[ACCEPTED] ... d_ff=1000000000`.

**Classification.** A human decision: U0001 open item 3 covers the parameter formula and its MoE interpretation. It also exposes a validator gap.

**Proposed regression test:** `test_moe_d_ff_relation`. For MoE, enforce the decided relation and show that a Mixtral sidecar with `d_ff=8` fails. The decision is one of:
- `d_ff == expert_d_ff`,
- `d_ff == experts_per_token * expert_d_ff`, or
- `d_ff` forbidden, with `expert_d_ff` the only width.

## F6 — NON-BLOCKING (human decision) — a hardware `unit` may contradict the unit in its field name

**Where:** `CAND/contract/uarch_contract/sourced.py:38-43` checks only that `unit` is non-blank. `CAND/contract/uarch_contract/hardware.py:39-41` adds no unit/name consistency check.

**Defect.** CLAUDE.md invariant 3 says "Units live in names". A spec can declare `t_rcd_cycles: {value: 14, unit: "ns"}`, `freq_hz: {value: 1000, unit: "MHz"}` or `capacity_bytes: {value: 16, unit: "GB"}`, and it loads. A U-P3 engine would read 14 cycles, 1000 Hz or 16 bytes. The handoff declares this as a limitation ("U-P3 must enforce derived parameter units").

**Reproducer:** set `hw["memory"]["dram"]["timing"]["t_rcd_cycles"] = sv(14, "ns")` and call `HardwareSpec.model_validate(hw)`.

**Observed:** `[ACCEPTED] t_rcd_cycles with unit 'ns'`, `[ACCEPTED] freq_hz with unit 'MHz'`, `[ACCEPTED] capacity_bytes with unit 'GB'`.

**Proposed regression test:** `test_unit_matches_name_suffix`. Using a per-suffix allow-list, a `_cycles` leaf must have unit `cycle`, `_hz` must have `Hz`, and `_bytes` must have `byte` or `B`. Mismatches are refused, naming the path. The test fixtures already follow this convention.

## F7 — NON-BLOCKING — `clock_domains.core.scales_with_core` is required and may be `false`

**Where:** `CAND/contract/uarch_contract/hardware.py:45-53`, against `CAND/docs/build-spec.md:214-216,262-265`.

**Defect.** §2.3.2 says a frequency ratio scales `clock_domains.core` and every domain whose flag is true; core always scales. The contract requires the flag on core, although the build-spec YAML omits it, and it accepts `false`. An engine that reads the flag uniformly would not scale the core under DVFS. The build-spec's own shape fails to load.

**Observed:** `[ACCEPTED] core scales_with_core=False` and `[REFUSED ] core without scales_with_core (build-spec §2.3.2 YAML shape) -> Field required`.

**Proposed regression test:** `test_core_domain_always_scales`. Either `core.scales_with_core=False` is refused, or core uses a model without the flag and the build-spec shape validates.

## F8 — NON-BLOCKING — the build-spec §2.3.3 example request does not validate

**Where:** `CAND/docs/build-spec.md:313` has `uarch_fidelity: {compute: 2, noc: "1+ts", dram: 2}`. `FidelityDetail` (`CAND/contract/uarch_contract/fidelity.py:19-20`) requires `sync` and `layer_reuse`.

**Observed:** `[REFUSED ] request uarch_fidelity as in build-spec §2.3.3 -> Field required`.

**Classification.** Doc drift. U-P1 item 6 asks for "the fidelity_detail keys and values", so the contract is right and the example is stale.

**Proposed regression test:** `test_build_spec_examples_validate`. Parse the §2.3.3 request and table YAML fragments, after fixing them, through the contract models.

## F9 — NON-BLOCKING (later sprint plus human decision) — the MoE declared omission is enforceable nowhere

**Where:** `CAND/contract/uarch_contract/table.py:33` defines `MOE_OMISSION`, which is never referenced. `table.py:259` enforces only the four dense omissions.

**Defect.** §2.3.4 requires MoE routing, imbalance and all-to-all as table warnings. Tables carry no model identity or `n_experts`, so neither the contract nor rk-sim's reader can tell that an MoE table omitted them.

**Observed:** `MOE_OMISSION referenced outside its definition: False`.

**Classification.** Producer enforcement belongs to U-P3. Whether the table should carry an MoE indicator, so a reader can check, is a human decision.

**Proposed regression test:** for U-P3, `test_moe_table_carries_moe_omission` using the Mixtral sidecar. If a field is added to the table, add a contract-level test.

## F10 — NON-BLOCKING — zero-width error band and empty energy-verification maps are accepted

**Where:** `CAND/contract/uarch_contract/model_card.py:41-50` and `:56-58`.

**Defect.**
- CLAUDE.md invariant 8 and U-REVIEW check 6 ("Any error band of zero?"): `ValidatedErrorBand{low_rel: 0, high_rel: 0}` validates.
- `energy_verification: {L0: {}, L2: {}}`, an object with no families, also validates. A consumer testing `is not None` could label energy verified.

**Observed:** `[ACCEPTED] ValidatedErrorBand low=high=0` and `[ACCEPTED] EmbeddedModelCard estimated with empty energy maps -> L0={} L2={}`.

**Proposed regression tests:**
- `test_error_band_cannot_be_zero`: `high_rel == 0` is refused.
- `test_energy_verification_requires_families`: empty maps are refused, or null is the only "unverified" spelling.

## F11 — NON-BLOCKING — `contract/README.md` describes a rule that is no longer true

**Where:** `CAND/contract/README.md:11`: "Units live in names; no field carries cycles."

**Defect.** `HardwareSpec`, inside `contract/`, has `*_cycles` leaves by design (§6.1, `CAND/contract/uarch_contract/hardware.py:94,104,108,116,155-159`). The README rule should say that requests and tables carry no cycles. U-REVIEW check 11 applies; `contract/` is human-owned.

**Proposed regression test:** documentation only. Fix the wording in Stage 2. Optionally add `test_contract_readme_states_hardware_cycle_exception`.

## F12 — NON-BLOCKING (latent; owner Lane B / U-P3) — parity projection contradicts Lane A's accepted shard

**Where:**
- `CAND/contract/tests/parity.py:71-75` (Lane B): projects every replica count by `value / tp`.
- `CAND/contract/uarch_contract/request.py:118-123` (Lane A): accepts `kv_heads < tp` with replicated KV.
- `CAND/contract/tests/test_u_p1.py:532-534`: explicitly accepts tp=16 for the 70B shape.
- U0001 also proposes vocabulary padding when `V % tp ≠ 0`.

**Defect.** Under replication, each rank reads `KV / kv_heads`, not `KV / tp`. The harness's expected per-rank counts are then wrong by more than its 5% maximum declared deviation. A correct implementation would fail parity, or be pushed to be wrong. Every current fixture has `kv_heads = 8`, `tp ∈ {1, 8}` and `V % tp = 0`, so nothing fails today. U2 fixture additions are explicitly anticipated, though: FINAL-VALIDATION step 4.

**Reproducer:** 70B shape, tp=16, decode B=1, T=32768, fp16, using rk-sim's roofline terms.
```python
from contract.tests.parity import compare_counts
from uarch_contract.request import CharacterizationRequest
m = CharacterizationRequest.model_validate(request_data() | {"tp": 16}).model
w = m.active_params * 2; k = 2 * m.n_layers * m.kv_heads * m.head_dim * 2; T = 32768
compare_counts("70b/tp16", {"memory_read_bytes": w / 16 + k * T / m.kv_heads},
               {"memory_read_bytes": (w + k * T) / 16})
```

**Observed:** `A contract accepts 70B-shaped tp=16 with kv_heads=8 (replicated KV): 16 8`, then `compare: FAIL 70b/tp16/decode: memory_read_bytes: actual=10161390592.0, expected=9490301952.0; delta=0.0707...`.

**Classification.** Cross-lane incompatibility. The projection rule is a human decision. I record it here for the Lane B reviewer.

**Proposed regression test:** `test_parity_refuses_unprojectable_fixtures`. The harness refuses fixtures with `tp > kv_heads` or `vocab_size % tp ≠ 0` until an approved projection exists. Alternatively, it projects the KV terms by `kv_heads` and tests that case.

## F13 — NON-BLOCKING (low) — canonicalization edges

**Where:** `CAND/contract/uarch_contract/hashing.py:18-23`, `CAND/contract/uarch_contract/request.py:53-69`, `CAND/contract/uarch_contract/hardware.py:228`.

**Defect.** These bear on CLAUDE.md invariant 4 (same inputs, same bytes):
- **(a)** `-0.0` passes the row checks but hashes differently from `0.0`. Both are produced by ordinary arithmetic, and the result can depend on summation order.
- **(b)** Grid axes are order-sensitive: `[1,2]` and `[2,1]` give different `request_hash`. U0001 says list order is meaningful, but interpolation "bilinear in (log B, log T)" presumes monotone axes. Requiring strictly increasing axes would remove the ambiguity.
- **(c)** `voltage_ratio` keys `"0.6"` and `"0.60"` both parse to 0.6 and silently collapse; the last one wins.

**Observed:**
```text
[ACCEPTED] row with attribution noc=-0.0
table_hash equal for 0.0 vs -0.0: False
request_hash equal for batch [1,2] vs [2,1]: False
[ACCEPTED] voltage_ratio with '0.6' and '0.60' (duplicate after parse) -> {0.6: SourcedValue(value=0.9, ...)}
```

**Proposed regression tests:**
- `test_canonical_json_normalizes_negative_zero`, or rows refuse `-0.0`.
- `test_grid_axes_strictly_increasing`.
- `test_duplicate_keys_after_parse_refused`.

## F14 — NON-BLOCKING (low) — dependency floor versus API used

**Where:** `CAND/contract/uarch_contract/fidelity.py:16-18` uses `Field(exclude_if=...)`. `CAND/pyproject.toml:6` declares `pydantic>=2`. Both lockfiles, uarch and rk-sim, pin 2.13.5, so CI is unaffected.

**Defect.** `exclude_if` is not available in early Pydantic 2.x releases. I could not verify the exact minimum version offline. The draft boundary ADR §5 says rk-sim will adopt these models, and rk-sim's own floor is `pydantic>=2`.

**Classification.** Changing a dependency floor needs human approval (CLAUDE.md).

**Proposed regression test:** a CI variant `uv sync --resolution lowest-direct` that runs `contract/tests`, or an explicit floor matching the first release that provides `exclude_if`.

---

## U-REVIEW checklist (Stage 1, in order)

1. **Joint exit criterion (G1) from a cold clone on the Linux box. PARTIAL; key parts PENDING.**
   - I ran the `contract` CI job's three commands (`CAND/.github/workflows/ci.yml`) in a fresh copy with no caches and no virtual environment, then `uv sync --locked --extra dev --offline`:
     ```text
     $ uv run --no-sync python scripts/vendor_rk.py --check
     committed snapshot manifest and matrix verified: .../contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963
     $ uv run --no-sync pytest -q -rs contract/tests --require-vendor
     153 passed in 1.41s
     $ uv run --no-sync python -B -m uarch_contract.generate --check
     Contract schemas are fresh.
     ```
   - Parity fixtures: 864 records, 24 queries for each of `llama-3.1-70b`, `llama-3.1-8b` and `mixtral-8x7b`.
   - **A cold clone on the Linux box is PENDING.** No published revision exists; the target is not a Git checkout.
   - **Hosted CI is PENDING.**
   - **U0001 is PROPOSED, not accepted.** That is a human gate.
   - G1's wording differs between documents. Execution plan §3 (`CAND/docs/execution-plan.md:138`) says "ADR U0001 accepted by both". §4 G1 (`:273`) says "accepted under the recorded human ownership". With Reza off duty, which one governs is an unresolved human decision.
2. **Numbers reaching a human without a badge. NOT APPLICABLE in U1.** There are no report templates or table producer (U-P3/U-P4). The `uarch` entry point fails with `ImportError: cannot import name 'app' from 'rkuarch.cli'`. That is the unchanged U0 stub (`CAND/src/rkuarch/cli.py`, identical to baseline), not a U1 regression.
3. **Goldens. No change.** `CAND/tests/golden/expected/` holds only `.keep`, the same as the baseline `89313ee` tree.
4. **Numerical smells:**
   - Units in request/table float names pass the walk test; hardware unit strings are unchecked (F6).
   - Cycles: none in requests or rows. The guard is over-broad (F1).
   - `next_edge`, `HashMap`/`HashSet`, `unsafe` Rust and seed plumbing: not applicable. There is no engine or native code, and `seed` is a carrier only.
   - MAC counting: the module docstring states MAC = 2 operations; no counting code is in U1.
   - tp: request and table carry tp, and `ShardIndivisible` covers heads, FFN and experts. The divisor-of-1 and plan-tp rules belong to the U-P19 reader. Cross-lane projection: F12.
   - Unordered iteration: canonical JSON sorts keys. Hashes are identical across two fresh processes and `PYTHONHASHSEED` 0, 1, 12345 and random (`sha256:fbb1b51b...` each time). Order-sensitive grid: F13.
   - Null, not zero: `Diagnostics` and model-card fields have no numeric defaults (read and tested).
   - DRAM presets: an explicit mode is required and has no fallback.
   - **Three formulas re-derived:**
     - `implied_params`. Independent hand formula, against the sidecars' declared counts:

       | Model | Total (implied) | Total (declared) | Δ | Active (implied) | Active (declared) | Δ |
       |---|---|---|---|---|---|---|
       | 70B | 70,553,706,496 | 70,600,000,000 | −0.066% | same | same | same |
       | 8B | 8,030,261,248 | 8,030,000,000 | +0.003% | same | same | same |
       | Mixtral | 46,702,792,704 | 46,700,000,000 | +0.006% | 12,879,925,248 | 12,900,000,000 | −0.156% |

       The code matches its docstring.
     - `conservative_composite`. Matches the revised §2.4 text. Monotone: approximate sync never raises the composite. Mutation M20 was killed.
     - Shard divisibility and replication. Matches U0001's text, but the replication refusal is untested (F3, M06).
5. **Provenance:**
   - No stipulation in `CAND/hw/` (designs and references are empty). Stipulations appear only in contract test fixtures, as synthetic `Condition` and refusal examples.
   - Non-stub claims without a source are refused.
   - A reference spec with a deep stipulation is refused, naming the full path (M22 killed).
   - No derived values exist in U1.
   - The strict `source=None` for stubs is a documented proposed exception; it awaits a human decision.
6. **Evidence. NOT APPLICABLE.** No model cards are promoted, and there is no ledger or prediction. `validation/L3_silicon/check_ordering.py` does not exist in the tree; the CI step runs only when predictions exist, so I could not run it. At carrier level: zero band accepted (F10); above-stub evidence guard untested (F3).
7. **Fidelity:**
   - Composite branches follow §2.4: all 240 legal hardware combinations × both `layer_reuse` values × exact and two approximate quanta pass.
   - Approximate sync is never C2.
   - The C2 floor is enforced: exactly at the floor is accepted, one ulp below is refused, with the roofline-specific message.
   - A C1 row 1,000× faster than its U-C0 floor is accepted. That is consistent with invariant 6's C2-only scope, so it is not a finding.
   - Gaps: schema divergence (F4a), and no spec binding for the later shared-SRAM consistency check (F2).
8. **Determinism. NOT APPLICABLE to tables** (no engine in U1). Hash determinism is verified as in check 4; edge case in F13.
9. **Native vs fork. NOT APPLICABLE** (from U6).
10. **Scope (§1.3).** Nothing out of scope was built. `OpSpec` is a vocabulary with named dimensions, not a workload IR, and there is no ONNX path.
11. **READMEs.** `CAND/contract/README.md:11` is stale (F11). Lane A touched no other README.

## Focus areas requested

| Area | Verdict |
|---|---|
| Contract semantics and provenance | Carrier rules are correct, and `SourcedValue` matches the pinned rk-sim semantics except for the documented strict stub source. Gaps: F1, F2, F6, F10. |
| Parameter formulas, TP/KV scope, declared omissions | Formula re-derived exactly; `ShardIndivisible` correct. Open: F5 (MoE `d_ff`), F12 (projection versus replication), F9 (MoE omission), F3 (replication and omission guards untested). |
| Optional shared SRAM and sync monotonicity | Correct per the revised §2.4. Omission means physically absent; existing hardware must be `"1+ts"` for C2; sync never promotes. The schema permits explicit null (F4a). The `HardwareSpec`/detail consistency check is correctly deferred to producer integration but needs F2's binding. |
| C2 roofline floor | Enforced and tested, including without a shared SRAM. M18 killed. |
| Explicit direct/preset DRAM modes | Correct. Required discriminator, no heuristics, pinned 40-hex SHA, exact `file@sha` citations, direct mode refuses a preset; JSON Schema conditions propagate into `HardwareSpec.json`. M21 killed. |
| Serialization, schema freshness, cross-lane | Schemas fresh. Round-trip covers every exported model. `ModelSpec` AST-identical to the pin. The Channel map is exact and name-only. Issues: F4, F13, F14, F12. |
| U0019 ownership | Consistent. U0001 records the accepted direction, no prepared-input fields were added (no `prepared`, `bundle` or `replay` in contract code), and U0003 owns schemas. Nothing is demanded of U2. F2 also touches U0019 item 5's "traceable from tables". |

## Distinguishing defect, decision and later work

- **Implementation defects (Stage 2 can apply):** F1 (once a remedy is chosen), F3, F4, F7, F10, F11, F13.
- **Unresolved human decisions:**
  - F1's remedy shape
  - F2: add a spec hash, or amend §6.5, §7.4 and U-P19
  - F5: MoE `d_ff` meaning
  - F6: contract-level unit enforcement
  - F9: an MoE indicator on the table
  - F12: projection rule
  - F14: dependency floor
  - G1 "accepted by both" versus "recorded human ownership"
  - every U0001 proposed default (the handoff's seven open decisions)
- **Properly assigned to later sprints (not findings):**
  - `derive_rk_params` and producers (U-P3)
  - producer-side `HardwareSpec`/`fidelity_detail` consistency
  - applicability classifier, badge ceilings, ledger (U-P4)
  - reader checks: `table_hash` recomputation, envelope lower bounds, `TpMismatch`, `KvLayoutMismatch`, `InitialStateMismatch`, divisor 1 (U-P19)
  - U0003 prepared-input schemas (U2)
  - interpolation vectors (U-P7)
  - cross-language hash vectors (before another producer)

## Claims verified

- **FINAL-VALIDATION:** all eight check results reproduced. Optional SRAM: 12 cases. DRAM modes: 22 cases. Three stub-source exception cases. Parity fixture counts.
- **Handoff:** 106 U-P1 tests. 67 schemas (66 models plus `PrecisionFormat`). 240-combination enumeration. 17 error classes with `ErrorRecord` round-trip.
- **Lane A file identity:** A's files are byte-identical in CAND.
- **No commits:** Lane A made none (A HEAD equals base `af3b1bc`).

## Commands run (in disposable copies)

```text
uv sync --locked --extra dev --offline
uv run --no-sync pytest -q -rs contract/tests --require-vendor          # 153 passed
uv run --no-sync pytest -q -rs                                           # 157 passed
uv run --no-sync pytest -q contract/tests/test_u_p1.py                   # 106 passed
uv run --no-sync mypy src contract scripts                               # no issues, 42 files
uv run --no-sync mypy                                                    # no issues, 30 files
uv run --no-sync ruff check .                                            # all passed
uv run --no-sync lint-imports                                            # 2 kept, 0 broken
uv run --no-sync python -B -m uarch_contract.generate --check            # fresh
uv run --no-sync python -B scripts/vendor_rk.py --check                  # verified
PYTHONHASHSEED={0,1,12345,random} table_hash/request_hash                # identical
REPO=<copy> python -B probe_lane_a.py                                    # probes.log
python3 -B mutate.py <copy> <scratch>                                    # mutations.log
diff -rq (A worktree vs CAND, Lane A paths); AST compare ModelSpec vs rk-sim pin
```

## Pending (cannot be established by this pre-publication review)

- Cold-clone execution of the G1 criterion on the Linux box.
- Hosted CI (`contract` job and the rest).
- Human acceptance of U0001 (and U0002 for Lane B). The adoption and publication of the vendored snapshot.
- Stage 2 responses to F1–F14, then Stage 3 adjudication.

---

## Stage 3 — ADJUDICATION (appended 2026-10-06)

The reviewing session adjudicates Lane A's Stage 2 response. Per U-REVIEW Stage 3 this checks three things: (a) every finding has a row, (b) each REJECTED reason addresses its finding, and (c) each APPLIED change has a test that fails without it. As you asked, I also assessed the deferrals and the four cross-cutting items. **No new findings are raised.** The few observations below are labelled as integration notes and do not affect the verdict. Nothing was fixed, regenerated, adopted or accepted.

### Inputs adjudicated

- **Response:** `/home/jjaff/AI-infra-simulation/rk-uarch-u1-a/docs/reviews/U1-lane-A-response.md` (sha256 `00b60a5a…92df3`).
- **Updated handoff:** `/home/jjaff/AI-infra-simulation/rk-uarch-u1-a/docs/reviews/U1-U-P1-handoff.md` (sha256 `deb1a6c1…7ccc8`, matching the evidence audit's `A_interface` record).
- **Combined candidate (primary code target):** `/tmp/u1-b-scope-integration-3d8bfs06`. Evidence: `/tmp/u1-b-scope-evidence-5st8n19o`.
- **A proposal identity:** I recomputed `3f408194c6e26165770e35675b72939469dfe74d660b7e5d6b778bad18a3f773` from the A worktree (HEAD still `af3b1bc`, no commits). A's contract modules, 69 schemas, fixtures, the three A test files, `contract/README.md`, U0001, the handoff and the response are byte-identical in the candidate. `docs/prompts/U-P19-…` differs only by the coordinator's U0019 preparation paragraph, which is correctly retained.
- **Where I ran things:** a disposable copy of the candidate (`uv sync --locked --extra dev --offline`). Reverts ran in further throwaway copies with `PYTHONPATH` pinned to each copy. Scripts and logs are in `U1-lane-A-review-artifacts/stage3/`.

### Candidate test state (reproduced; this is NOT green)

| Check | Result |
|---|---|
| `pytest contract/tests --require-vendor` | **378 passed, 1 failed** |
| full `pytest` | **382 passed, 1 failed** |
| `scripts/vendor_rk.py --check` | **exit 1**, "GENERATOR current incompatibility: generator script fingerprint differs; locked oracle environment metadata missing" |
| mypy (47 files), ruff, import-linter (2 kept), schema freshness, prompt-sync | pass |
| A's three test files | 257 passed |

The single failing test is `contract/tests/test_committed_snapshot.py::test_current_snapshot_generator_compatibility`. It comes from the intentionally preserved snapshot predating B's generator changes. This adjudication does not treat regeneration as done and does not count the suite as green. Every revert result below is measured as *new* failures beyond that one known failure.

### (a) Every numbered finding has a row — YES

F1–F14 each have exactly one disposition row in the response's table:

| Disposition | Findings |
|---|---|
| APPLIED | F1, F2, F3, F4, F5, F6, F7, F8, F10, F11, F14 |
| APPLIED (a, c) / REJECTED (b) | F13 |
| DEFERRED | F9, F12 |

Cross-lane B-F8 is tracked separately and not conflated with A-F8.

On F3's count: the response says 20 survivors where my headline said 19. My report counted 19 meaningful guards and listed M26 separately as dead code, so both counts describe the same log.

### (b) REJECTED reasons address the finding — YES

- **F13(b), grid axis order** (`test_grid_order_is_preserved_in_request_identity`). The rejection is substantive, not a restatement of intent:
  - Build-spec's own request example uses a descending axis, `frequency_ratio: [1.0, 0.6]`, so mandatory ascending order would refuse a documented input.
  - Invariant 4 (same inputs → same bytes) still holds for identically ordered input.
  - Interpolation (U-P7) can order its evaluation coordinates independently.

  A stranger can check the build-spec counterexample. I accept the rejection.

### (c) APPLIED changes have tests that fail without them — YES (verified by revert)

**Stage 3 random check.** A random draw over the APPLIED set selected **F4**. Reverting it in a scratch copy:

- **R3a** (JSON-number strictness disabled): **12 new failures**, including `test_request_wire_numbers_reject_boolean_and_string`, `test_row_wire_numbers_…` and `test_other_a_owned_numeric_fields_do_not_coerce[*]`.
- **R3b** (`shared_sram` schema override removed, schemas not regenerated): **detected** by `test_schema_freshness`, which ties the committed schema forbidding null to the code.

**Every other APPLIED row, and both deferred items now implemented in this combination,** reverted one at a time (`stage3/reverts.log`, `reverts2.log`):

| Revert | Result | Regression(s) that caught it |
|---|---|---|
| R1 A-F1: whole-table `reject_cycles(self)` restored | DETECTED, 11 new | `test_cycle_hardware_conditions_round_trip[*]`, `test_condition_carrier_does_not_claim_to_verify_unavailable_hardware`, … |
| R1b A-F1 made over-broad (exempt all `provenance`) | DETECTED, 2 new | `test_cycle_unit_cannot_hide_in_table_provenance`, `test_cycle_exception_cannot_escape_condition_value[params]` |
| R1c A-F1: `Condition` unit/path vocabulary check dropped | DETECTED, 1 new | `test_condition_exception_preserves_stipulation_and_unit_rules[wrong_unit]` |
| R2 A-F2: `hardware_spec_hash` removed | DETECTED, 34 new | `test_table_requires_hardware_identity`, schema/round-trip/hash tests |
| F3: original 26-mutant sweep, rerun on new code (`mutations-after.log`) | M01–M25 all DETECTED; M26 not applicable | dead code removed, as the response states |
| R4 B-F8 (A carrier): raw/residual recomputation dropped | DETECTED, 1 new | `test_comparison_refuses_inconsistent_evidence[residual_rel-0]` |
| R6 F5: MoE `d_ff == expert_d_ff` dropped | DETECTED, 3 new | `test_moe_widths_are_redundant_compatibility_fields[8, 24, 1e9]` |
| R7 F10: zero band allowed | DETECTED, 2 new | `test_error_band_cannot_claim_zero_error`, freshness |
| R8 F6: unit/path check disabled | DETECTED, 30 new | `test_hardware_units_match_explicit_field_meaning[*]`, `test_every_sourced_hardware_leaf_has_a_unit_rule` |
| R9 F7: core back to plain `ClockDomain` | DETECTED, 3 new | `test_core_domain_always_scales_and_omitted_flag_defaults_true`, round-trip, freshness |
| R10 F13(a): `-0.0` normalization removed | DETECTED, 1 new | `test_negative_zero_has_one_canonical_identity` |
| R11 F13(c): duplicate voltage keys allowed | DETECTED, 1 new | `test_voltage_keys_cannot_collapse_after_parsing` |
| R12 F14: `Field(exclude_if)` restored | DETECTED, 1 new | `test_fidelity_round_trip_without_exclude_if_api` |
| R13 F8: build-spec fragment reverted | DETECTED, 1 new | `test_build_spec_fidelity_fragments_validate` |
| R14 F11: README sentence reverted | DETECTED, 1 new | `test_readme_cycle_rule_distinguishes_hardware_from_results` |
| R5b B's A-F12 guard disabled | DETECTED, 9 new | `test_replicated_kv_refused_before_even_an_exact_echo[*]`, `test_padding_cannot_pass_via_aggregate_echo[*]`, … |
| R5 B's replication branch only | not detected; behaviorally redundant | `kv_heads < tp` still fails the divisibility branch with a reason naming `kv_heads=8` and `tp=16`. Refusal is preserved. |
| R0 baseline | no new failures | only the known snapshot failure |

### Deferrals — properly recorded

- **F9 (U-P3 producer).** Scope, owner and acceptance are recorded:
  - The producer copies `MOE_OMISSION` when `request.model.n_experts > 0`.
  - The test uses the Mixtral sidecar.
  - Whether to add a reader-verifiable MoE indicator is left to Javid.

  The recording is in `CAND/docs/prompts/U-P3-hardware-workload-and-the-analytic-engine.md:93-97` and its build-spec copy (`:2009`); prompt-sync passes. This is a plan, not "later". It stays **open until U-P3**.
- **F12 (Lane B guard; interim refusal policy approved by Javid).** The deferred action is **discharged in this combined revision**:
  - `contract/tests/parity.py::projection_incompatibilities` refuses replicated KV and any non-divisible head, FFN, expert or vocabulary dimension. It does so *before* the candidate is called, keeps every fixture in `coverage`, and lets no partial run reach A's success carrier.
  - All 864 preserved fixtures stay eligible.
  - My original 7.07% case now reports `unsupported_projection`.
  - A's legitimate tp=16 and padded-vocabulary requests remain valid contracts (`test_a_f12_oracle_scope_does_not_restrict_legitimate_shapes`).
  - The component-aware projection remains future reviewed U-P3 work, recorded in U0002 (`:83-89`) and U-P3 (`:99-103`).

### The four cross-cutting items, in this combined revision

- **A-F1 cycle exception — sound and narrow.**
  - `UarchCostTable` drops only `provenance.conditional_on[*].value` before `reject_cycles` (`CAND/contract/uarch_contract/table.py:379-382`).
  - `Condition` still requires `kind="stipulation"` and a path-matched unit (`:328-337`).
  - Params, rows, diagnostics and top-level fields keep cycle refusal (R1b).
  - Verifying that each path exists and its value matches the referenced proposed spec is explicitly U-P3's job (U-P3 `:89-92`), and a test pins that U1 does not claim it.
- **A-F2 hardware identity — sound.**
  - `hardware_spec_hash` is required, uses the `sha256:` format, is covered by `table_hash` and preserved by round-trip.
  - The toy table's digest was recomputed.
  - Build-spec §6.5, §7.2 rule 6 and §7.4, U-P1, U-P3 (equality of table, request and spec) and U-P19 are aligned. Syntax alone does not authenticate contents, as stated.
- **B-F8 agreed parity carrier — consistent across lanes.**
  - A implements `FlopParity`, `ParityChannelComparison` and `FlopDeviation`. B's `contract_payload` serializes through A's real class.
  - `test_parity_carrier.py` covers B's adapter, including the 864-fixture oracle echo staying `harness_self_test`. All B payloads round-trip; the payload file sha256 `f7c7566b…` matches what A read.
  - B's interface document changed after A read it, but only in A-F12 and embedding-policy text and identity references. The carrier field definitions did not change. B's separate embedding-accounting question remains B's and Javid's.
- **B's A-F12 projection refusal — sound** (see F12 above).

### Integration notes (observations, not new findings; they do not affect the verdict)

1. **Mirror drift.** `CAND/rk-sim-side/prompts/P18-characterized-c2-cost.md` still reads "checks the table's spec_hash", while U-P19 now reads `hardware_spec_hash`. Their code blocks were identical at baseline `89313ee`. U0019 says the shipped rk-sim-side prompts mirror U-P19/U-P20, and no sync test covers them. The coordinator should reconcile this when integrating.
2. **Stale wording.** A's handoff and response say B's A-F12 guard is "still pending". In this combined revision it exists and is tested. The wording predates integration and is superseded here.
3. **Coarse path vocabulary.** The `Condition` path check is a pattern match: `*` matches any suffix, and `nocs[999]` is accepted. Existence and equality are explicitly deferred to U-P3, as the response states.

### Verdict

**ACCEPTED** — Lane A's Stage 2 response satisfies U-REVIEW Stage 3:
- all 14 findings have a row;
- the one REJECTED item addresses its finding;
- every APPLIED change has a regression that fails when the fix is reverted. This covers the random check (F4) and all other APPLIED rows.

The deferrals are recorded with owner, scope and acceptance. F12's is discharged in this combined revision.

**Open by recorded deferral (not unresolved defects):**
- F9: U-P3 MoE omission.
- Producer and reader verification for A-F1 and A-F2: U-P3 path/value and identity equality; U-P19 spec-hash comparison and `table_hash` recomputation.
- The component-aware projection: future U-P3.

None of A's findings is left unanswered or improperly closed.

### Separate from this verdict — still required before G1/U1 can close

This verdict adjudicates A's findings only. It does **not** make the candidate green, accept any ADR, or close G1/U1.

1. **Snapshot.** The preserved vendored snapshot intentionally fails current generator compatibility (1 failing strict/full test; vendor `--check` exit 1). Regeneration, review and human adoption under U0002 are outstanding. No regeneration evidence exists or is implied.
2. **Hosted CI and cold clone.** Hosted CI has not run, and the G1 criterion has not been run from a cold clone on the Linux box. Neither can be established pre-publication.
3. **Human acceptance.** U0001 remains PROPOSED: its remaining proposed defaults, strict stub source, parameter formula and the rest. U0002 is Lane B's. B's embedding-accounting decision is pending. The specific approvals Javid gave (A-F1, A-F2, A-F12 policy, B-F8, F4/F5/F6) do not accept U0001 as a whole.
4. **G1 wording.** Execution plan §3 (`:138`) still says "ADR U0001 accepted by both", while §4 (`:273`) says "accepted under the recorded human ownership". Reconciling them is a human or coordinator action.
5. **Lane B's own U-REVIEW Stage 3** belongs to its reviewer and is not covered here.
6. **No closure.** No stage tags the sprint. U1 is **not** declared complete.

### Stage 3 commands run (disposable copies only)

```text
rsync candidate -> scratch (no caches/venv); uv sync --locked --extra dev --offline
uv run --no-sync pytest -q -rs contract/tests --require-vendor     # 378 passed, 1 failed (known snapshot)
uv run --no-sync pytest -q -rs                                      # 382 passed, 1 failed (known snapshot)
uv run --no-sync pytest -q contract/tests/test_u_p1{,_review,_followup}.py   # 257 passed
uv run --no-sync python -B scripts/vendor_rk.py --check             # exit 1 (current incompatibility)
uv run --no-sync python -B -m uarch_contract.generate --check       # fresh
uv run --no-sync mypy src contract scripts / ruff check . / lint-imports   # pass
python3 -B stage3/revert.py <copy> <scratch>; python3 -B stage3/revert2.py ...; python3 -B stage3/mutate2.py ...
A identity recomputation; diff -rq A worktree vs candidate; sha256 of B-F8 interface/payload files
```
