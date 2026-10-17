# Same component reviewer — focused F5 Stage 3 recheck

Continue your existing component reviewer session. Your prior Stage 3 verdict found only
F5 at fault; F1–F4 and F6–F11 passed. Review this correction independently and append a
bounded recheck. This is not a new full review or a repeat of F6.

## Immutable subject

- B publication: `354420fb8c75cb6fb922db82b9eec6bca644fefc`.
- Author package: `docs/reviews/U4-B-component-F5-correction-v1/` at that commit.
- Read its README, proposal.json, matrix-addendum.json, obligations.json, restoration.json
  and evidence manifest. Coordinator reconciliation is in this directory's checks.json.
- Preparation base: `414a94c35c1588cf13b6fcddc3739203c7f5ec6e`.
- First apply the original `U4-A-component-stage2-v1/combined.unapplied.patch`, SHA256
  `81b81c6c2680a17e7d106dedb4a11dc07891b331f3323319fb0192b852bdebe3`.
- Then apply the additive `U4-B-component-F5-correction-v1/test-only.unapplied.patch`,
  SHA256 `23724b209c73fcfb55c62836570a296817936137111a00dfd2f51862ea0757f3`.
- Original manifest SHA256:
  `5d1010aac38f7d04a2935ff48072e418e1e8e9a88d1933758fca4581e2acc845`.
- Added `validation/component/test_f5_mechanism_duration.py` SHA256:
  `e4f9f8693f20031ccf8b97d24a141b0aa63725e220fb6a754d2275cb5c6b0f8a`.
- Matrix addendum SHA256:
  `2c5733da9074f28d13ffbb274d94a1b802b9d1ed6cadd89368f947ec44ebc941`.

The effective subject has 24 postimages: the unchanged original 23 plus this test.
The original 106-case selection remains `sha256:4b9e73cf9ef11456e216acba58c9496c242169e2a40efcf0aa9e3f36bf0dbbc0`.
It does not bind the new test; the additive proposal binds that test and patch order.
Verify those distinctions, activation inputs and supplemental first-use binding.

## Bounded work

1. Verify exact subject identities and reconstruct in a fresh private export. Inspect
   the supplied reconstruction helper before using it. Never apply to moving main or
   overwrite current U0011/K2 clauses. Confirm imported project modules come from the
   private export; use explicit pytest config/root and the existing pinned environment.
2. Independently verify the new positive and forged D01 carriers. In the forgery the
   four-cycle work count stays truthful, while response completion becomes 58,500 ps
   instead of the lawful 59,000 ps. Joined receiving alignment absorbs the difference;
   the remaining work and makespan are unchanged. Require structural validation to pass
   outside the asserted refusal, then the exact independent `mechanism duration` failure.
3. Remove **only** that mechanism-duration check in scratch. Confirm the new forgery is
   accepted through both layers, its test fails with `DID NOT RAISE`, and the positive
   control passes. Restore exact source bytes and rerun the focused controls. Reuse your
   original F5 probe where useful. A setup exception, different refusal or hash mismatch
   is not credit for a behavioral kill. This F5-specific removal is the required recheck;
   do not draw another row or repeat the completed F6 random revert.
4. Verify the corrected F5 disposition retracts the joint-defense claim. Check O1 wording
   is honest and O2 is assigned with its first-use boundary; neither is a new finding or
   a requirement to run their experiments now. Preserve the earlier row verdicts unless
   the actual delta supplies concrete contradictory evidence.
5. Confirm the new test is ordinarily discoverable. Use the two new tests and your focused
   probe; the 49-test affected selection is available if needed to resolve a concrete
   concern. Do not repeat all guard sweeps, broad tests/unit runs, full suite, native
   builds/execution, campaign/replay, server work or CI polling. Broaden only if a specific
   newly observed issue requires it, explaining the reason before a long run.

B reports 49 affected passes (47 behavioral, two identity), two restored controls and
single-guard unsafe acceptance. These are inherited until you reproduce them; counts
from different runs overlap and must not be added. Coordinator ran identity and private
reconstruction checks only, not behavioral tests.

## Preserve and return

Append to `docs/reviews/U4-component-independent-review-v1/README.md`; preserve the current
34,826-byte prefix (SHA256 `fbf1efbcf74b07bb3df33e852d8f5ecaa07d40856d7f0d6349971b83504af23f`)
and all earlier evidence. Put new probes/receipts under a new `stage3-f5/` directory.
If the prefix differs, investigate before writing; do not overwrite another session's work.
Write only reviewer-owned files, leave them unstaged/uncommitted, and stop with your verdict.
Record exact pins, commands, import origins, failure reasons, restoration hashes, executed
versus inherited evidence and remaining limitations. State whether F5's criterion (c) is
resolved and consequently whether the original response now passes Stage 3.

Acceptance is limited to the response checks. It grants no NoC/profile/semantic decision,
protected installation, component native implementation or authority, human L1 credit,
qualification, G3a or U4 closure. The completed K2 campaign and U0024 deferrals are unchanged.
