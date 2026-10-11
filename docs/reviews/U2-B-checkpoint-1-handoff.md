# U2 Lane B — checkpoint B1 handoff

Status: **READY FOR COORDINATOR DECISIONS AND A1 API RECONCILIATION.** This is B1 preparation and independent acceptance work, not runtime completion or fresh U-REVIEW. Stop here before dependent runtime work.

Javid (@jjaffari) has accepted U2-U0003-acceptance-v1, all six recommendations and D1–D12/R1–R2. Those policies are settled; this report does not reopen them or assert Reza approval.

## Baseline and preservation

Worktree: /home/jjaff/AI-infra-simulation/rk-uarch-u2-b. Branch u2/honesty; HEAD `1e9e794a84c5173812c23a1cf2fc04b85e6f6831`. Entry state before B1 was only the four untracked earlier reports. After an interrupted authoring command, continuation inspection found only the five completed hardware drafts beyond those reports; neither ADR nor fixtures had been partially written. No tracked modifications or staged changes now exist. All B1 files remain untracked/uncommitted.

Read-only common baseline: ../rk-uarch-u2-integration/docs/reviews/U2-common-baseline-v1. Manifest `8ce7b0d6ee152df698543d5be98dc2f2733533a7ed679bcbfa53335303e8370e`, all **262 entries verified**. Embedded accepted proposal manifest `8def4c6d2c275010719525bc7f39b463675284791122def8c38001889c0ea4d6`, all **116 entries verified**. Accepted U0003/acceptance record, current U-P4, relevant build-spec sections and CLAUDE.md/CODEOWNERS govern over historical worker-local public documents.

Earlier reports remain byte-identical:

- `docs/reviews/U2-B-preparation.md` — `12c38ea9f9ae6d64ff59b69aab6e5ee4e1e5761414d1a94daba037e0efa58dbf`
- `docs/reviews/U2-B-U0003-compatibility.md` — `a4ef227c7ac563d6b02e4197137e30cef773dd8565aa1b14f00c7904a8099fb8`
- `docs/reviews/U2-B-S-revision-check.md` — `20863fb6c5e90753f4c637db672d9c330f95b683048ff4ae10293c25661218a3`
- `docs/reviews/U2-B-R1-R2-recheck.md` — `8dea4be31d5baf548fa26fbede7fcf81768ee73355f10f80f5b29a30c4675178`

## Concrete decisions for Javid

1. **U0004 exact text:** approve docs/decisions/U0004-stipulated-values-and-the-estimated-ceiling.md, or identify a wording correction against settled U0003. It records stipulations as conditions, claims plus model evidence, L0–L2 stub, null empty-claim summary, proposed estimated ceiling, total-empty ineligibility, purpose/scope closure and accepted hidden/labelled STUB opt-in. No dependent implementation was made.
2. **H1, npu-l4:** approve or revise the exact stipulated design: 2×2 large cores, 256×256 array, BF16-only 65536 MAC/cycle/core at 1 GHz, 16 MiB SRAM/core, 32 GB HBM and 1 TB/s. All 59 sourced leaves are stipulations with rationales. The inventory includes every DMA/buffer/NoC/controller/timing/energy/power choice; approval must cover those consequential values, not just the headline. Nominal 1.0 efficiency is separately accepted and is not a hardware measurement.
3. **H2, npu-m256:** approve or revise the exact 16×16 small-core design, 16×16 arrays, BF16/FP8 256/512 MAC/cycle at 1.2 GHz, 1 MiB SRAM/core, two counter-directed tori, 32 GB GDDR6 and 512 GB/s. All 67 sourced leaves are stipulations. SRAM capacity and energy coefficient are explicitly coupled design choices, not empirical validation.
4. **H3, incomplete reference inputs:** accept these as quarantined sourcing/loader proposals, or keep them only as incomplete drafts until replacement facts are available. TPU v5e has 46 stub leaves out of 50 claims; Blackhole p100a has 47 of 50. Every stub is enumerated in its YAML header and inventory; categorical stand-ins are also listed. Rev-2 requires positive numeric carriers for many unpublished fields: conspicuous 1-unit stub placeholders are not estimates or useful performance inputs. Recommendation: do not use these templates for physical reference runs or L3 evidence until each consumed unknown has a reviewed replacement or explicitly reviewed fidelity limitation. Schema validity does not establish physical plausibility.
5. **H4, source/unit/operating-point decisions:** review the inventory's exact vendor sources and interpretation limits (printed capacity units/usable capacity, max vs sustained clock, logical vs physical grid). Obtain missing chip-level timing, layout, SRAM/DMA/vector/energy/power information if reference execution is desired. No inverse fitting from aggregate peak, BLOCKFP8→FP8 substitution, board→chip power conversion or unnamed DRAM preset was introduced. Source acquisition remains open and has no bounded validation estimate.

Exact decision input byte hashes:

- `docs/decisions/U0004-stipulated-values-and-the-estimated-ceiling.md` — `090482a0f71cb2af9a8d4d5d813e6602e20a62d1dfcb7d1288e600ec0d023cdc`
- `hw/designs/npu-l4.yaml` — `41731f6ac7fe99aaf221edaf917ffdd03cd0fcdd8149ee5f5110bfe42a5911c0`
- `hw/designs/npu-m256.yaml` — `e12d08d40e7b3c0e7ab1443141745a6c082ee544ecfc43c5609c8cd289a35d9e`
- `hw/references/tpu-v5e.yaml` — `acea41f651a5f63e1697937f3879364e5f4342249efeaff1dcc6b6b4345a898d`
- `hw/references/blackhole-p100a.yaml` — `cdd1a51cc9c181b2c9062e8c46ad79989f6873734602152059b05ca363ef3371`
- `hw/U2-sourcing-inventory.md` — `6cfe2e0441bc125e10b065f925edd03b8f18417d1d0af78495867b95a8b5bc01`

## Independent cases and actual verification

See [fixture README](../../tests/fixtures/u2_b/README.md) and [API/matrix plan](U2-B-B1-api-and-matrix-plan.md). The 64 semantic cases cover badge ceilings/monotonicity; no-band and complete purpose/model/scope requirements; all twelve numeric surfaces; R1 genuine vector/decode-write omissions and invented matrix omission rejection; independent refusal/evidence/gate reductions; R2 rehashed/reviewed missing dependencies, indirect cycles, source-model inheritance and count-only zero timing error; rank/export/accounting/isolation/report completeness. These are explicit **pending runtime expectations**, not 64 passed tests.

Actually executed on 2026-10-07:

- Existing HardwareSpec validation: all four YAMLs pass. Runnable input tests also check complete exact-value inventory/header coverage and rejection of a nested reference stipulation.
- Targeted pytest command documented in the fixture README: **14 passed, 0 skipped, 0 failed** (final run 0.62 s). Uses the existing main-worktree venv interpreter with -B, no pytest cache and --require-vendor. Existing APIs only: hardware prerequisites, independent canonical/review/source/pointer bindings, adopted manifest bytes, explicit retained pairs/.55 inputs, planned matrix enumeration and actual frozen omissions/refusal inventory.
- Standalone read-only schema check with system Python's already installed jsonschema: **15 typed objects** validate against exact accepted proposed.schema.json (11 B evidence/assumption/review/registry/dependency objects, two ExecutionModelInput and two ComponentPrecision objects). This is structural validation, not execution of A1 semantic guards. No dependency was added.
- Ruff on the four new Python test files: passes after import-format fixes. Untracked text whitespace check passes. Earlier report hashes, branch/HEAD and absence of tracked/staged changes verified. Baseline/package manifests verified as above.

No full suite, nominal candidate, physical replay, B renderer/evaluator, real expanded bridge, new direct precision probe or artifact generation was executed. Independent fixture hashes and synthetic accepted-review fields are not silicon evidence or human decisions. Supplied no-band L3 fixtures intentionally lack bundle/ordering/verification and cannot upgrade a model; the positive complete S01 context is pending. The toy dependency graph tests pointer integrity only; complete physical/oracle dependency mutation tests await A1.

Final delivery's report-context.json, render-default.json and render-opt-in.json remain pending actual complete bindings. No table/result/export artifact or replacement private type was fabricated to fill them. Current component-precisions.json contains only two genuinely bound retained inputs; npu-l4 waits for the real A export. These are explicit B1 limitations, with final required test paths and setup steps in the README.

## B-F16 and source/input ownership

B-F16 is **OPEN**. Same pin is verified through the adopted manifest and every listed file; no upstream checkout mutation/read beyond the permitted preserved inputs occurred. Adopted MANIFEST.json SHA256 is `b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d`; recorded generator source digest is `4d2304002b262f2ee03dfe4f8fb338b350aacd80ea2488952849c416ee135317`. That historical identity is not claimed to certify a future generator.

Observed adopted inventory: 864 successes in six groups of 144, absent vector channel throughout, 432 null decode writes, positive matrix/read counts and known positive prefill writes. There are two recorded placeholder precision refusals. Proposed matrix enumerates seven unique pairs × three models × two tp × 24 queries = **1008 planned successes**, plus **four direct peak refusal obligations**; optional BF16/FP8 +144 excluded. Enumeration is not oracle execution. Keep retained .55 stub efficiency and accepted new labelled nominal1.0; no calibration fitting.

B owns hardware drafts, explicit selections/refusal inventories, generator/comparison tooling and report consumers; A owns exact shared carriers, derivative/export implementation, offline closure loader, nominal candidate and captured-bundle physical adapter. Coordinator owns public/Makefile/CI integration; Javid owns remaining decisions, later two-run whole-revision generation and separate adoption. The API/matrix plan specifies input/source/hash bindings, real loader/bridge checks, exact probe-boundary separation, staging needed because the current writer refuses different existing outputs, complete-byte comparison and whole-revision adoption. No generation flags were set and no artifacts were adopted.

## Scope, estimates and reconciliation stop

No runtime, shared contract/schema, accepted public policy, A package, vendor artifact, main/other worktree or dependency changed. Only B-owned proposal inputs/tests/docs were authored; contract test fixtures are human-review proposals under this task's explicit authorization. No agents, messages to A, reset/cleanup/stash, commit, push or tag. No implementation depends on guessed A1 fields.

Reconcile the actual A1 callable signatures, exports, typed closure return, canonical/review hashes, strict validation/refusal order and required source dependency enforcement against the accepted carriers before B runtime code. Confirm who supplies each missing semantic guard without making a second ledger/model/type. The detailed API requirements are concrete; no new policy decision is requested by them.

No substantiated estimate change. Retain A140–222 hours, B100–154, fresh independent review16–24: **256–400 engineering hours total**. B1 belongs within existing preparation/hardware/tests allocations, not an additive new package. Javid active decisions/generation/adoption2–4 hours remains provisional, with elapsed waits separate and unbounded. Unpublished reference acquisition and independent full physical timing validation are not silently included. No calendar commitment or actual-work-hour claim is made.

After Javid's U0004/hardware dispositions and coordinator A1 reconciliation, implement accepted B behavior and pending tests, then prepare the reviewed tooling/input freeze. Fresh U-REVIEW, generation/adoption and publication are later separate checkpoints.

## Proposed reviewed checkpoint and commit

Proposed commit message (NOT executed): `Prepare U2 B1 hardware, U0004 and independent acceptance cases`.

The following exact paths are proposed for review. All remain uncommitted. SHA256SUMS contains all 37 new B1 payload files including this handoff; it excludes itself to avoid self-reference. The manifest's own digest is returned separately. Earlier reports are preserved, excluded from this new checkpoint payload, and hashed above.

- `contract/tests/fixtures/u2_b/asic_placeholder-execution.json`
- `contract/tests/fixtures/u2_b/component-precisions.json`
- `contract/tests/fixtures/u2_b/nvidia_h100_sxm-execution.json`
- `contract/tests/test_u2_parity_channels.py`
- `contract/tests/test_u2_precision_matrix.py`
- `docs/decisions/U0004-stipulated-values-and-the-estimated-ceiling.md`
- `docs/reviews/U2-B-B1-api-and-matrix-plan.md`
- `docs/reviews/U2-B-checkpoint-1-handoff.md`
- `hw/U2-sourcing-inventory.md`
- `hw/designs/npu-l4.yaml`
- `hw/designs/npu-m256.yaml`
- `hw/references/blackhole-p100a.yaml`
- `hw/references/tpu-v5e.yaml`
- `tests/fixtures/u2_b/README.md`
- `tests/fixtures/u2_b/acceptance-cases.json`
- `tests/fixtures/u2_b/actual-assumptions.json`
- `tests/fixtures/u2_b/actual-evidence-review.json`
- `tests/fixtures/u2_b/badge-cases.json`
- `tests/fixtures/u2_b/dependencies-review.json`
- `tests/fixtures/u2_b/display-cases.json`
- `tests/fixtures/u2_b/evidence-no-band.json`
- `tests/fixtures/u2_b/evidence-scope-cases.json`
- `tests/fixtures/u2_b/evidence-source.json`
- `tests/fixtures/u2_b/family-registry.json`
- `tests/fixtures/u2_b/hardware-input.json`
- `tests/fixtures/u2_b/matrix-plan.json`
- `tests/fixtures/u2_b/metric-dependencies.json`
- `tests/fixtures/u2_b/r1-omission-cases.json`
- `tests/fixtures/u2_b/r2-mutation-cases.json`
- `tests/fixtures/u2_b/reference-assumptions.json`
- `tests/fixtures/u2_b/reference-evidence-no-band.json`
- `tests/fixtures/u2_b/reference-evidence-review.json`
- `tests/fixtures/u2_b/registry-review.json`
- `tests/fixtures/u2_b/report-context-cases.json`
- `tests/fixtures/u2_b/source-literals.json`
- `tests/unit/test_u2_b_badges.py`
- `tests/unit/test_u2_b_evidence_closure.py`
- `docs/reviews/U2-B-checkpoint-1-SHA256SUMS` (manifest envelope; digest returned separately)
