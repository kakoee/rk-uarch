# U3 closeout checklist — historical preparation and current status

Current status: [U3-closeout-v1 accepted](../U3-closeout-acceptance.json) after
[publication and same-commit validation](../U3-published-validation-v1/README.md) of `390ec9a`.
The preparation checklist below is retained as its original record. Its commit, publication
and validation actions are completed; final closeout record publication and tagging remain
separate. [Current dispositions](../U3-closeout.md) are authoritative for status. U4 is not authorized.

Authority: execution-plan U3 and G2, §5 per-sprint checklist, U0023 and U-REVIEW.
Javid's design/policy decision is [recorded](acceptance.md); U4 is not authorized.

| Step | Status / exact scope |
| --- | --- |
| A response adjudication | ACCEPTED at a7f4acb; original reviewer records preserved |
| B response and O1/O2 adjudication | ACCEPTED at40fab28 and7afba9b respectively; original records preserved |
| Human design/policy decisions | Accepted for closeout only; explicit exclusions preserved |
| Durable normative records | Prepare U0011 acceptance scope and prospective U0002 addendum; exact H-DMA/H-CLOCK/shared text aligned across build-spec, prompts and execution-plan; exact five human-installed postimages verified; commit pending |
| Publishable evidence | Select review reports/necessary evidence and coordinator receipts; check paths, links, lint, attribution and publication scope. Do not copy whole scratch exports or publish interpreter caches. Reviewer text must stay unchanged |
| Fresh documentation refresh | Fresh session completed and its exact proposal installed; see ../U3-final-documentation-refresh/handoff.md and ../U3-final-local-checkpoint-v1/documentation-reconciliation.json. No U4 implementation |
| Final closeout record | Dispose each U3/G2 requirement; map later work to first consumer. Record analytic partial/not_run outcomes, actual executed checks, deferred toolchain/schema/host/corpus items, estimates versus unreported actual hours/retro |
| Exact final source validation/publication | Run appropriate integrated checks on the selected final source; commit reviewed contents and separately publish main. Do not push the unapplied repair or claim migration happened |
| Same-commit closure checks | Fresh hosted Linux checkout and separate fresh local clone on the identical published revision; strict vendor currentness, applicable tests/types/lint/import/schema checks. Explicitly identify empty native/golden/performance/ordering CI jobs as no-ops |
| Human closure/tag | After evidence passes, present G2/U3 closeout for human authorization and tag u03-end on the approved tested main revision; verify published commit/tag. Not performed here |

U3 closure requires the design and explicit implementation/evidence dispositions. Exact
toolchain/licence closure belongs before K1, protected schema installation before K2,
actual M dependency audit before protected M installation, and native execution in U4.
Full tables are U7; reference campaign work, host performance and nightly remain at their
accepted downstream gates. None becomes a new blanket U3 prerequisite.

Recording the prospective dependency policy is closeout work. Applying its code,
freezing/generating/adopting a new artifact is a separate transition, excluded here.
Current published source/adopted artifact can and must pass existing strict verification.

Precommit local suite: 1,701 passed, 29 skipped, zero failures/errors; see [scope and receipt](../U3-final-local-checkpoint-v1/README.md). No hosted CI or published cold-clone result is claimed. Both review loops are
finished; only the final closeout packaging, normative record, documentation and
publication/validation steps remain. No new general adversarial review is requested.
