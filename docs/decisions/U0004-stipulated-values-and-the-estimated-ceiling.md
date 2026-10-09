# U0004 — Stipulated values and the estimated ceiling

Status: PROPOSED B1 text, awaiting Javid (@jjaffari) approval of these exact bytes.
Authority: accepted U2-U0003-acceptance-v1, all six recommendations and D1–D12/R1–R2. This ADR records those settled rules; it does not reopen them. Common baseline manifest: `8ce7b0d6ee152df698543d5be98dc2f2733533a7ed679bcbfa53335303e8370e`.

## Decision

A stipulation defines the question being asked: what would this design do under these explicit conditions? It is not evidence that the hardware exists or performs as predicted. Preserve each consumed stipulation and rationale in conditional_on and in export/report provenance. Stipulations neither raise nor lower the worst real hardware claim. A reference hardware specification contains claims only; unpublished facts remain stub, with source null.

A metric's badge depends on both its actual hardware claims and applicable evidence for its model. L0, L0m, L1 and L2 establish verification, not validation: the model remains stub. Eligible same-class L3 can support estimated within its scope; eligible target L4 can support measured within its scope. A model never becomes spec_derived merely because its inputs are published. Any real consumed stub claim still limits the result to stub.

No hardware claims is an empty claim summary (null), not a phantom stub claim. An all-stipulated design can therefore reach estimated with eligible model evidence. An entirely empty contributor set is different: it is stub and is not eligible for numeric opt-in. A proposed design never exceeds estimated, even with otherwise stronger contributors. A chip that does not exist cannot acquire a measured prediction through precise simulation or persuasive presentation.

Eligibility requires complete verified source/review/ordering/verification/family-registry closure, exact model identity, purpose, granularity and all required scope dimensions. A missing error band does not alone invalidate otherwise applicable evidence; it leaves the band unknown. Compound scope cases do not imply their Cartesian product. Actual and reference models remain independently scoped. A count comparison cannot validate timing, even when timing error is zero. Energy remains unverified until every consumed energy family has its own applicable support. Do not synthesize confidence intervals from deterministic outputs.

R1 numerical evidence outcomes and nominal compatibility or physical recording gates remain separate. Null/absent reference channels remain unknown; only genuinely declared model omissions receive modelled_absence. Expected precision refusals have their own complete, source-bound observations. A complete discrepancy record is not physical accuracy.

R2 numeric ratios inherit the complete actual, reference and adjustment dependencies recursively. Rehashing and reviewing a recipe cannot authorize omitted required computation inputs. Reject missing/ambiguous recipes, cycles, wrong purpose and review mismatches. Source recipes do not themselves grant display permission for raw values.

## Presentation

Default-hidden STUB and explicit labelled opt-in are already accepted U0003 policy. Every numeric surface uses the same permission check, including HTML/Markdown, SVG geometry/axes, tooltips, data attributes, accessibility text, comments and warnings. Opt-in requires a finite executed prediction with complete contributors; unknown stays unknown, not zero. Synthetic presentation requires the separate explicit test permission and an unmistakable synthetic label. No production validation follows from synthetic fixtures. Visible predictions retain STUB/unvalidated labels and conditions; no hidden magnitude may leak through geometry or metadata.

## Consequences and implementation boundary

B consumes A's shared carriers and load_verified_report_inputs closure. No alternate badge ledger, model identity, provenance hierarchy or private report-context schema is introduced. This checkpoint contains no dependent runtime implementation.

Javid's remaining decision is approval of this ADR's exact text, or a specific wording correction to align it with the accepted policy. Hardware choices H1–H4 in hw/U2-sourcing-inventory.md are separate input decisions; schema acceptance did not approve their values. A1 reconciliation concerns executable API signatures and validation behavior, not a fresh policy vote. No Reza approval is asserted.

Acceptance cases and pending execution boundaries are indexed in tests/fixtures/u2_b/acceptance-cases.json and docs/reviews/U2-B-checkpoint-1-handoff.md.
