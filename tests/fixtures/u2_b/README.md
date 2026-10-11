# U2 B acceptance inputs and execution status

Current status at reviewed commit `769a1fef2320430386888bf450af579ea26cf664`: v2
oracle adoption and the complete analytic comparison/report capture are committed.
See [adoption execution](../../../docs/reviews/U2-adoption-v2-execution/README.md) and
[Stage 2 response](../../../docs/reviews/U2-lane-B-response.md). The original B26,
B64, proof77, revision42 and PR3-nine namespaces remain distinct; no bulk ledger
promotion follows from carrier tests or an administrative acceptance receipt.
B05/S10 production-card semantics and R202 complete contributor enforcement are
under Stage 2 correction, with required A adapters tested separately in scratch.
Real positive measurement/history/energy eligibility remains unsupported.

## Historical B1 preparation (preserved below as historical statements)

These files were authored by B before B report/comparison runtime implementation. No A fixture was copied. They are proposals and synthetic unit inputs, not generated engine results, adopted oracle rows, validation evidence or Javid decisions. At B1 submission all 64 semantic cases were pending; its 14 runnable checks covered carrier/input integrity and inventory only. These are historical counts, not the current suite or a claim that later execution never occurred.

## Exact fixture roles

- hardware-input.json: existing HardwareSpec, independently adapted from the B design question with a genuine synthetic stub bandwidth claim. It is not an accepted chip specification.
- source-literals.json: hand-authored count/duration test literals (12 vs 8 counts, 250 ps vs 2.5e-10 s); no engine computation is asserted. Raw file hash is bound by evidence-source.json. No expected oracle duration is generated.
- actual-assumptions.json / reference-assumptions.json: accepted AssumptionSet shapes with distinct physical-resolved and nominal-rk-compatibility identities. Implementation hashes identify synthetic labels only, not executable implementations. A1 tests must replace these with real bound implementations for execution.
- evidence-no-band.json / reference-evidence-no-band.json, actual-evidence-review.json / reference-evidence-review.json: exact EvidenceRecord/ReviewRecord shapes; synthetic L3, matrix-count-only, null band. Deliberately no prepared bundle, prediction ordering or verification records. They are **ineligible negative inputs**, not a complete L3 context. S01 specifies the positive no-band case to assemble independently with A1. A synthetic accepted review field is not a human approval.
- family-registry.json / registry-review.json: reviewed synthetic hash-to-family association, not a silicon family assertion.
- metric-dependencies.json / dependencies-review.json: separate actual/reference source recipes with exact purposes and pointers. The toy source assumption is supplied literals; it does not purport to be the full physical or adopted nominal computation recipe. The actual timing recipe retains a real stub claim for dependency propagation testing. No raw-value display recipes are supplied. R201/R202 require a complete A1 physical/oracle context before mutation; deleting a token from this toy recipe cannot prove full computation completeness.
- badge-cases.json, evidence-scope-cases.json, display-cases.json, r1-omission-cases.json, r2-mutation-cases.json, report-context-cases.json: test-case specifications, **not** runtime schemas or a private ledger. IDs specify setup and expected result; acceptance-cases.json indexes them and the twelve numeric surfaces. matrix-plan.json is a selection test specification, not ComponentPrecision or generated output.
- contract/tests/fixtures/u2_b/component-precisions.json: array of two exact accepted ComponentPrecision objects bound to actual retained upstream-only descriptors and the adopted manifest. Companion asic_placeholder-execution.json and nvidia_h100_sxm-execution.json retain the actual .55 stub scalar inputs. Supported KV selections come from the accepted retained matrix, not new silicon evidence. This is deliberately the retained subset; it is **not** the completed seven-pair generation inventory. Real npu-l4 ExportBinding waits for accepted hardware and A1's actual export.

## Historical B1 executable command

Run from the B root with the existing interpreter, no installation or cache writes:

```sh
/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/unit/test_u2_b_badges.py tests/unit/test_u2_b_evidence_closure.py contract/tests/test_u2_precision_matrix.py contract/tests/test_u2_parity_channels.py --require-vendor
```

No skip substitutes for a pending implementation. The badge-named file tests hardware prerequisites, not badge behavior. Fixture closure tests bind canonical bodies, review subjects and pointers, not eligibility. Matrix tests enumerate selections, not successful oracle execution. All B typed fixture objects were additionally checked read-only with the system's existing jsonschema against the preserved accepted proposed.schema.json; jsonschema is not added to project dependencies.

## Historical B1 planned runtime tests

Use the following existing delivery paths; no parallel types or fallback adapters:

| Test file | Cases and required execution |
| --- | --- |
| tests/unit/test_u2_b_badges.py | B01–B08; real badge evaluator, model/claim ceilings, monotonicity property test, explicit total-empty vs empty-claims distinction. |
| tests/unit/test_u2_b_applicability.py | S01–S12; positive no-band evidence assembled from independently authored full bundle/registry/review/order/verification inputs; independent model/purpose/granularity/scope. |
| tests/unit/test_u2_b_evidence_closure.py | C01–C06, R201–R210; real loader then B recursive evaluator, mutate one complete input at a time, rehash all descendants/review subjects unless testing stale review, assert named refusal/no numeric output. Indirect A→B→C→A graph cycles must be tested separately from shared DAG nodes. |
| tests/unit/test_u2_b_display_permissions.py | D01–D07 on all twelve surfaces; require real RenderSpec permissions, synthetic permission independent of opt-in. Parse rendered markup and inspect attributes, accessible names, axes and geometry, not only a text search. Vary hidden magnitude and require output/geometry invariance. |
| tests/unit/test_u2_b_report.py | D08, C07–C08; render HTML and Markdown with template lint forbidding raw floats, compare moved-directory/wall-clock/order-invariant bytes. Enforce isolated per-op plot labelling and all error/null/energy surfaces. |
| contract/tests/test_u2_precision_matrix.py | C09–C10; full actual ComponentPrecision inventory and real loader/export round trip, explicit role support and precision check boundary tests. |
| contract/tests/test_u2_parity_channels.py | R101–R106, R113–R115; execute real comparator with actual frozen omissions and independent missing-matrix counterexamples. |
| contract/tests/test_u2_comparison_inventory.py | R107–R112; expected/source/observation bijections, validation order, all execution and precision statuses before reduction. |
| contract/tests/test_u2_nominal_compatibility.py | All 1008 adopted fixtures and four real direct checks, unchanged thresholds, isolated candidate with expected-access traps (C11). |
| contract/tests/test_u2_physical_discrepancy_reporting.py | Complete captured/imported-bundle attempts, A-F12, selected-rank conservation (C03–C04/C11), all failures/unknowns recorded; no physical accuracy assertion from recording completeness. |

Delivery's final report-context.json, render-default.json and render-opt-in.json are intentionally pending complete table/bundle closure and executable A1 APIs. There are no invented hashes for nonexistent results/tables and no synthetic stand-in npu-l4 export. The supplied report-context-cases.json states their acceptance requirements. This is a B1 readiness limit, not a change to final delivery scope.

The final paragraph above records the B1 readiness limit. Current A interfaces,
actual H1 export, full table/comparison capture, v2 adoption and HTML/Markdown reports
now exist. Their validation limits and newly found blockers are recorded separately
in the Stage 2 response; the original synthetic fixture bodies remain unchanged.
