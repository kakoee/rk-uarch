# U0006 — What verification can and cannot establish

**Status: ACCEPTED by Javid (@jjaffari), 2026-10-11**, acting human decision-maker
for both lanes, under `U3-RoPE-and-verification-v1`. Human-owned commit and publication
remain separate from acceptance.

Accepted source: section 1 of `docs/reviews/U3-U0006-report-supplement.md` at
`428b7bb29664b7de2b8c8ef8ce3a8bad2e5245ee`. Javid also accepted that revision's
sections 2–4 source profile/reductions and section 6 standalone implementation/test
scope, including `U3-U0006-report-example.json` at that revision. Section 5 production
integration and section 7 future fork telemetry remain proposals, not implementation
permission. B may begin the standalone task after this human-owned ADR commit.
See [acceptance and authorization scope](../reviews/U3-RoPE-and-verification-v1/README.md).

**Context.** The accepted U2 aggregate/per-op analytic engine exposes resolved
accounting and roofline predictions, not executed telemetry. B's bounded
[preparation](../reviews/U3-U0006-proposal.md) and
[report proposal](../reviews/U3-U0006-report-supplement.md) distinguish those claims.
[U3-next-direction-v1](../reviews/U3-next-direction-v1-acceptance.md) endorses the
conservative direction and requests a bounded revision, not wholesale profile acceptance.

**Decision.**

L0/L0m verification is a scoped statement about executed checks of a declared
model, never silicon validation. Preserve STUB, unknown error and independently
unverified energy under U0003/U0004. Analytic shape accounting is not executed
MAC, DMA, queue, placement or history telemetry. Unsupported observations remain
explicit skips; deferred or unfinished applicable checks remain not-run. Neither
contributes positive verification. An applicable counterexample fails its
relation and dominates every enclosing reduction, even if execution is unfinished.
Partial, empty or skipped-only coverage cannot be summarized as passed.

Freeze relation definitions, premises, domains, modes, case-selection rules and
budgets before execution. Retain every actual engine invocation, input, result
and observed counterexample, including executed shrinking attempts and mutant
controls, with exact implementation, assumptions, suite and input/result bindings.
Separate
engine checks on fixed prepared work, producer-path checks and mutant results.
A mutant rejection demonstrates test discrimination, not an engine failure or
hardware accuracy. Hash identity, an actual test run and independent accepted
review are distinct obligations. Reusing a version string cannot authorize a
report from another implementation. A report must retain omissions and failures;
review cannot erase them or expand their scope.

Freeze concrete admitted inputs before two qualifying replays. Preserve discovery
failures even if a replay passes. Observe generation and engine calls through
supported public APIs and an explicit recording wrapper. Do not retain a second
ledger of framework-internal rejected draws that never invoke the engine; report
unavailable internal counts as unavailable, never as zero. Record all actual
calls even when a framework cannot label which belong to shrinking. Example
budgets, observed generation, retained cases and actual executions are distinct.

Reduce failed applicable relations or failed required mutant discrimination to
failed; otherwise unfinished, skipped, empty or under-budget coverage reduces to
not_run; only nonempty complete passing coverage reduces to passed. Rich relation
states remain in canonical source bytes. The three VerificationRecord outcomes
can carry conservative reductions only after separately authorized integration.

**Consequences.** The proposed first implementation is standalone analytic report
generation and validation under B-owned validation paths. Bind exact implementation,
assumptions, suite, concrete inputs and results; refuse missing/tampered cases and
changed implementations even with unchanged version strings. Git retains source
history; retain only report-relevant artifacts and existing content identities.
Stable report bytes exclude operational timing/host/nightly receipts, which refer
to their report hash. No circular dependency on a later publication commit.

**Does not do.** This decision supplies no measurement authority and accepts no
test run or review. Production provenance dispatch, A loader changes, card
attachment and evidence eligibility are deferred; initial L0/L0m references stay
null. It does not accept a fork, change U0003/U0004, alter U2 historical evidence,
waive U0002, discharge nightly/U-P6 gates, authorize private Hypothesis hooks or
modify protected carriers. Concrete profile review and implementation authorization
remain separate from this proposal's publication.
