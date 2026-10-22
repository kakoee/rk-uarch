# U4 closeout reconciliation

Date: 2026-10-22. Baseline: `85e7552f3ab0784f8f8bb6f7beccb7843e299ce8`.
This is the finite closeout pass requested by Javid. It adds no model, suite unit, native
campaign, review cycle, authority service or qualification requirement. U4 is not tagged
closed by this record.

## Human L1 acceptance and matching evidence

Javid accepted the [GEMM](../../../validation/L1_limits/hand/H-L1-GEMM-01.md) and
[DMA](../../../validation/L1_limits/hand/H-L1-DMA-01.md) calculations as human-validated
work using AI assistance: “Human review was beyond just a review. It validated them too.
Used AI as assistant.” The records disclose who calculated and who reviewed each part.
This supersedes the earlier assisted-only pending classification for these two workings;
it does not describe unaided human derivation or physical validation.

The coordinator discovered an error in its earlier two-credit DMA explanation during
reconciliation. NoC0 traversal is latency-only, not a contended route. Correct completions
are 60/62 ns rather than 60/64 ns. Javid explicitly approved the corrected result. The
worksheet records the mistake, explanation and approval. No engine change was needed.

| Working | Applicable independent expectation | Existing native witness / limit |
| --- | --- | --- |
| Resident GEMM 16×256×256 | 1,048,576 MACs; 139,264 input bytes; 8,192 output bytes; 16,384 accumulator bytes; 702,000 ps | Arithmetic `test_resident_literals`; historical C01 evidence is retained. No new C01 native run in this closeout |
| Partial GEMM 3×5×7 | 105 MACs; 210 useful vs 393,216 issued ops; 100/42 read/write bytes; 84 accumulator bytes; 547,000 ps | Native `synthetic_compute_literals` pins C02; existing native test receipts are inherited |
| One 256-byte DMA | 60,000 ps; exact channel service 159744/71 ps; credit releases at SRAM commit | Native `synthetic_dma_literals`, `synthetic_exact_channel_carry_and_refresh` |
| One vs two credits | Issues 0/60,000 vs 0/0; completions 60,000/120,000 vs 60,000/62,000 | Native `synthetic_credit_and_shared_port_literals` pins D05-one/D05-two |
| Sustained one-credit rate | 256 B/60 ns = approximately 4.267 GB/s; finite-window counting excludes the initial completion when counting inter-completion arrivals | Independent arithmetic/window and synthetic credit tests; no physical throughput or stationary multi-credit saturation claim |

Sources: [independent arithmetic tests](../../../validation/component/test_arithmetic.py),
[finite-window and credit tests](../../../validation/component/test_checks.py),
[native literals](../../../native/crates/uarch-engine/src/component_tests.rs).
The two presence checks now pass because the accepted worksheets exist; those checks
alone do not verify their arithmetic. Current focused Python checks and inherited native
execution are deliberately distinguished.

## Existing readiness requirements

| Existing requirement | Disposition |
| --- | --- |
| M/K1/K2, bounded components, ordinary runtime | Installed; historical accepted evidence retained. No revival of retired deployment/startup/attestation machinery |
| Actual U5 reference workload coverage | Reviewed installed /5 model and all 52 selected units; original campaign retained. No new workload or full-grid run |
| Sourced hardware and uncertainty | Nine published facts, 17 numeric STUBs, original unknowns and staging limitations preserved |
| Applicable correctness, replay, determinism and priming | Reuse the author/reviewer evidence identified in the benchmark plan. Small fresh checks only; no summing overlapping pass counts |
| Human L1 | Accepted with explicit assistance and corrected DMA comparison; numerical and native evidence reconciled above |
| Characterization instruction | Concrete existing-API route documented below; no claim to have run the incompatible legacy command |
| Prediction/order infrastructure | Implemented original Git ancestry requirement in the existing CI job, including immutable evidence and result-without-prediction refusals. Empty current history is not a prediction pass |
| Benchmark agreement/measurement observability | All 52 proposed envelopes are specified, but final A/B signatures and actual compiler/event/retention correspondence remain absent. No signature or device evidence fabricated |
| Diagnostics relied on by G4 | F3/F6 gaps remain. Duration comparisons are distinct from unsupported causal attribution. Any attribution actually relied on by G4 needs the already-required verification or an explicit scope decision |
| Remote correctness/nightly/performance | U0024 remains in force. No polling, job activation, measurement or qualification in this pass |

The two remaining readiness decisions are therefore the final benchmark agreement
(including the preparation route below) and which diagnostics G4 will actually rely on.
Device observations and access belong to the existing U5 boundary; if absence of those
observations prevents the claimed G3a readiness, that condition must stay open or receive
an explicit scope decision. It must not disappear through a documentation edit.

## Reconcile the older characterize instruction

U-P9's `uarch characterize` wording targets the legacy HardwareSpec/analytic capture API.
The installed reference instead uses `TpuV5eReference`. Passing invented physical fields
or an npu-l4 spec to the legacy command would characterize a different subject.

Use the existing 52 IDs and count-only `shape-regimes.json` for selection. Its 12 matrix
and 28 decoder-projection rows use the U0001 OI/ridge and array-underfill bins; low, middle
and high intensity coverage exists across the matrix anchors. This is useful-work scope,
not measured saturation, physical HBM traffic or a NoC/DRAM load claim. Keep unknown load
bins unknown.

The concrete **proposed U-P9 preparation route**, with no new CLI feature, is:

1. Assemble each agreed high-level input using `workload.reference.suite_source`, with the
   unchanged supplied RoPE coefficients and gather indices.
2. Use `mapping.reference.map_reference` and `workload.reference.nominal_hardware`, then
   `workload.reference.prepare_job`. Save the prepared input; never regenerate it in replay.
3. Use `engines.analytic.reference.resolve_reference` for the existing aggregate/per-op
   U-C0 values on the same bundle. Preserve useful counts and the explicitly omitted laws.
4. Execute via the ordinary run path and retain its job/result plus the existing basic
   provenance, conditions and unknowns in the U5 prediction record. This step is not run
   by this closeout and does not reuse an implementation-test receipt as a frozen prediction.
5. Freeze before measurements using U-P9's existing commit discipline. Compiler-chosen
   mapping, state, full envelopes and the staging limitation travel with each comparison.

These are the existing APIs used by the retained campaign, not a new engine or alternate
workload IR. The small reference baseline tests are rerun; the full campaign is not.
Final agreement must accept this route as the reference-specific replacement for the old
command instruction before claiming the characterization prerequisite is fulfilled.

## Boundaries and next decision

The [benchmark plan](../../../validation/L3_silicon/tpu-v5e/BENCHMARK-PLAN.md) is the exact
52-unit agreement text for final sign-off. Existing author implementation and independent
correctness review are not substituted for measurement-owner agreement. No new broad
review is requested by this record.

No `u04-end` tag is created while G3a's remaining agreement/attribution disposition is
open. Once those existing decisions are recorded, publish the final U4 status/tag without
repeating unchanged engine tests. Hardware access, measurement execution, U0024 catch-up
and final project qualification remain separate.

Deferred follow-ups requested earlier remain separate: assess active legacy-format
support before removing any parser or fixture; improve Python CI/runtime hotspots; and
consider optional trace detail/output controls. None is a new U4 closure prerequisite.

## Checks executed for this closeout

- Clean tracked-source export plus only these closeout changes: **99 passed** across the
  ordering, CI classification/collection-partition, prompt, L1 arithmetic/presence,
  credit/window, phase-law and small reference selections. No native execution.
- The new ordering check's isolated typecheck initially found a reused variable name with
  incompatible types. Renaming it changed no logic. Final scoped mypy and whole-export
  Ruff pass; the affected **15 ordering tests** pass after that correction.
- In the disposable export only, removing the strict-ancestry guard makes the before,
  same-commit and independent-branch tests fail; the missing-prediction control still
  passes. Exact restoration returns all 15 tests to passing.
- Existing package/model checks reproduce the 70 dispositions, 52 units, 12 matrix and
  28 projection rows, nine fact leaves and 17 STUBs. Historical inputs were not rewritten.
- Strict vendor currentness passes on the clean export; selected support remains 56 files.
  62 local documentation links resolve. No protected path, native source, schema,
  artifact, model, lockfile or historical review was edited.
- The live-checkout CI collection-partition test initially refused the existing local
  `tables` directory through the import guard. That directory and guard are unchanged;
  the same test passes in the clean export. This is not labelled a live-checkout pass.
- Existing native builds, complete campaigns and independent review remain inherited,
  with their original scope. No hosted CI result, new device result or performance result
  is claimed. The full Python suite was not repeated for this bounded change.
