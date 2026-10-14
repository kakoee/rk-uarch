# U3-closeout-v1 — human technical closeout decision

## Requested decision

Accept the completed U3 technical/design exits and explicitly retained limitations on
published commit `390ec9aa06eef33da6274eb28ae6ca1c3ae3d623`, tree `a8dbdba71af3b43390bfa5e9fc98784d474211af`. This records G2 design readiness under the
accepted U0005/U0011/U0023 scope; it does not claim that native implementation ran.

Both lane response reviews and B's bounded bootstrap recheck are accepted on their original
pins. The accepted design/policy records and fresh narrative are published. A separate
fresh GitHub clone passes 1,701 tests with 29 explicit skips, plus required
static/currentness/schema checks. Hosted CI passes on the identical revision. See
[verification](README.md), [local execution](fresh-clone-receipt.json),
[hosted scope](ci-summary.json), and [existing closeout dispositions](../U3-closeout.md).

## Retained scope

- Analytic/RoPE runtime is delivered; the progressive Rust engine remains an accepted design.
- Historical analytic reports retain partial/not_run and 22/24 clock coverage, on their exact
  bound implementation. V2 has raw capture/replay, not a public table/report path.
- STUB, unknown error, unverified energy, reference unknowns and later validation duties remain.
- The narrower artifact policy is accepted prospectively; its code/migration remains unapplied.
- Exact M/toolchain/licence/corpus/fixture work belongs to its stated future first-use gates.
  Full tables remain U7; production rk-sim integration remains U10.
- Empty CI jobs are no-ops; no native/performance/nightly/silicon result is inferred.
- Actual engineering/review hours and retrospective remain unreported.

This decision is separate from the earlier design/policy and push approvals. It accepts the
technical closeout record only. Final record commit/push, the human `u03-end` tag, cleanup
and U4 authorization remain separate. No such action has been performed by this proposal.
