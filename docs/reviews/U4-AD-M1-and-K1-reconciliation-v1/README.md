# Separate adoption and K1 handoff reconciliation

B's AD-M1 correction is ready to join the exact adoption selection. A's K1 response is
reproducible as an unapplied twelve-path tree; its independent Stage 3 and B-owned guard/
inventory reconciliation remain pending. No live implementation or artifact was placed.

## Adoption

The exact B proposal at `3fb34d64359efdd4aa9992f66e19a224c5ab2895` changes only the prospective
policy test. Inspection confirms direct CLI behavior is compared to real strict-library
validation of the same isolated source/artifact. Import errors stay outside compatibility
handling; false successes and wrong reasons are caught. The source-write guard and real
adoption gate stay intact.

In a new export of frozen source `0cf24d91eeca5cc45182eb6fb03202677fd97dcb`, the original
nine-path candidate proposal plus B's one test path gave **313 passed, zero failures/skips,
one deliberate staging-test deselection**. Producers were disabled and imports came from
the export. This reproduces B's 307 selection and adds the six committed-snapshot tests.
The coordinator also reversed the exact B patch: the original `assert 0 == 1` failure
returned. Restoring it passed. All ten resulting paths match the proposal postimages.
B's separate 104-pass/one-skip prior-artifact run is inherited, not rerun here.

The [saved-output audit](audit_saved.py) reverified unchanged receipts, full candidate
integrity, exact frozen inputs/source and strict candidate currentness. All 1,008 nominal
rows and four refusals remain byte-identical to the old artifact. The original temporary
oracle venv is now absent: the earlier full-environment preflight refused today. No attempt
was made to reconstruct or run it. Its historical execution metadata and embedded lock
remain verified. Adoption does not execute the oracle and need not depend on an expired
scratch environment. This distinction must remain in the eventual human placement helper.

[Ten-path adoption decision](next-decision.md) is ready for Javid; its acceptance must be
recorded before preparing the guarded human placement. Both exact patches and postimages
are bound by [placement-plan.json](placement-plan.json). This supersedes the draft held on
AD-M1, not the reviewed candidate or old provenance. Live adoption is still pending.

## K1

A's uncommitted response remains untouched in `../U4-A-K1-stage2-v1/`. The primary patch
and separate B guard patch applied exactly to `9b1408437b6dc08d9b77848f5fffe56c0cf1db72`.
All nine primary postimage hashes verified. A temporary index produced exact combined tree
`6d5263e13e43a5dfb44d8addf93cc47cc814a0ac`, twelve paths. This is a review tree object, not
an installed commit or protection for the author's uncommitted handoff. [identity.json](identity.json)
binds the response and both patches; the original reviewer report remains unchanged.

Twelve available Python licence/README/chain-guard checks passed. The initial attempted
manual linkage test failed because K1_METADATA was not provided; its prerequisite Cargo
metadata is not in the delivered package. Docker is currently unavailable in WSL, so native
runs, graph reconstruction, replay and fault evidence remain inherited from A. No toolchain
or image was installed. The manual input must be reproducible from actual accepted tools,
not invented; [B's reconciliation prompt](lane-B-K1-reconciliation.txt) explicitly covers it.

A's two disclosed reviewer-probe differences require adjudication: retroactive queue
insertions now refuse, and the renamed private predecessor list deliberately is not causal.
The [same-reviewer Stage 3 prompt](K1-reviewer-stage3.txt) binds those questions and all five
original findings to the exact unapplied tree. Prefer B's confirmation of these exact guard
bytes before launching Stage 3; any new B delta requires a revised review tree binding.
B inventory/replay publication is separate from a scoped software-review verdict.

The author disclosed a mistaken failed pull in frozen A. Its HEAD/tree and complete clean
state are independently unchanged, and receipt/source checks pass. Fetch metadata is not
source identity; we did not rewrite it to hide the incident. Both lanes must continue to
leave this checkout untouched through the separately approved artifact lifecycle.

[Verification](verification.json) distinguishes current checks, inherited results and failed
launches. No full suite, hosted CI, native qualification, K2 release or sprint closure follows.
