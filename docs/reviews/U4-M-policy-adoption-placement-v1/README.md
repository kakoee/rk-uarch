# Exact ten-path adoption — accepted, human placement pending

Javid replied **yes** to the reconciled U4-M-policy-artifact-adoption-v1 decision at
`eb99399b96b1271a097aa9f635510f84622bf8dc`. [Acceptance](acceptance.json) binds the exact
[ten-path plan](../U4-AD-M1-and-K1-reconciliation-v1/placement-plan.json), candidate manifest,
source and human approval. It grants no local commit, push, K1 acceptance or K2 release.

[human_place.py](human_place.py) has a read-only `--check` mode and a separately guarded
human placement mode. Both require a full published helper commit, the reviewed Python
interpreter with `-I -B`, no optimization, and no ambient source/Git overrides. The helper
checks its own committed bytes, the exact reviewed plan/audit/freeze and both patches,
the actual acceptance, clean frozen A source and import origins, symlinks, every candidate
member, unchanged human execution receipts and the old canonical artifact. Both patches
are reconstructed in a private directory and every approved postimage is checked before
any live write. The exact ten-path delta is required.

The source remains `0cf24d91eeca5cc45182eb6fb03202677fd97dcb`; candidate manifest remains
`b19016be07307ed987037d8a079f85af0366eab018b1132c2668394acd756bcc`. All 1,008 nominal results,
four precision refusals and 44 unchanged artifact members remain intact. Existing U2/U3
review records and reviewer evidence remain unchanged.

The original oracle venv in /tmp is absent. Placement performs no oracle call, input
staging, dependency installation or environment reconstruction. Recorded generation
metadata and lock, immutable receipts, exact saved inputs, source bindings and strict
candidate compatibility supply the evidence already approved for this adoption. It does
not represent a fresh environment or generator execution.

Only after complete preflight and a human-supplied UARCH_HUMAN=1 does the helper write the
approved files to A, leaving HEAD/index unchanged. It verifies exact live scope, all 49
candidate members, strict new-policy currentness and the approved administrative review.
The receipt goes outside A into `tables/U4-M-policy-adoption-v1/placement.json`. Existing
output refuses rerun. If interrupted or refused, preserve the state for coordinator audit;
do not reset or rerun blindly.

The result remains **unstaged and uncommitted**. Branch history does not protect these
changes until the separately reviewed commit. No full suite, native execution, K1/K2
acceptance, hosted CI, infrastructure action or closure occurs in this helper. A's live
adoption-dependent test gate will be checked by the coordinator after receiving the receipt.

The coordinator will run commit-pinned read-only preflight and refusal checks before
providing the actual human command. The earlier 313-pass conditional selection and AD-M1
revert/restoration remain documented in the reconciliation; no redundant full-suite run is
claimed for this helper preparation.
