# U4 C1 publication — receipt of already approved human source

The coordinator verified remote main at
`1aae27b298f3a051cc80fe94f4889da260633a0b`. Javid separately approved its push after returning
the human local-commit receipt. Its parent is `b02bf4981e38d6903fbaded38d9488fe1e302138`;
its tree is `7165dedeb3c47f74f8fadc44f328b64dc8a9b7cd`. All ten committed postimages match
the accepted semantic candidate. Thus the older local-commit record's `push_authorized:
false` describes that earlier boundary; it is not the current publication status.

A's pending commits `fa2d269dd4616571c530e1672477b8a43a6c4c66` and
`72be3d655ed0c20e16561c86c9552f822f67e08d` change only
`docs/reviews/U4-A-K2-C1-resolution-v1/`. A's tracked/index state is clean. These evidence
paths are disjoint from the human source installation and coordinator publication records.

## Narrow task clarification

The C1 task's statement “The combined semantic candidate remains uninstalled” described
its starting state and prohibited A from independently applying a protected proposal.
The human has since installed, committed and authorized publication of that exact source.
Receiving this already published human commit through normal Git integration is permitted
under the existing parallel-main workflow. The stale starting-state sentence must not be
used to require a new protected installation vote or to prohibit receiving human history.
No permission is added for authoring protected changes or resolving protected-file conflicts.

A may fetch and normally merge current origin/main, preserving the human commit and both
local evidence commits, then push its evidence normally. No force push or history rewrite.
If unexpected source conflicts arise, stop and return the conflict instead of changing
protected files. Verify the human source ancestry and resulting bytes. Commit and push
remain separate normal operations; do not wait/poll hosted CI.

Keep all C1 experiment and uninstalled-preimage checks pinned to the actual old export
`0718955cc0656e5bac4688d4696abbd547cb4186`. Do not rewrite those receipts to describe the
newly integrated source or rerun old-preimage assertions against moving main. Record any
new publication-state check separately. The actual rejected lock remains rejected.

This resolves integration/publication only. No further resolution, version widening,
archive fetching, C2, build, native execution, image distribution or qualification is
released. The first resolver result does not establish unsatisfiability of the approved
pins. Any next bounded dependency action will be reconciled separately.

## Reported automatic-review block

A reports that automatic approval review rejected its normal merge because receiving the
protected files conflicted with the C1 task's “remain uninstalled” restriction. This note
clarifies the already-authorized source integration after the human installation and
separate push approval; it does not bypass that review or claim the rejected merge ran.
