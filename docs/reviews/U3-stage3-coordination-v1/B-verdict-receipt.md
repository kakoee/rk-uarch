# Lane B Stage 3 verdict and coordinator disposition

Verified **ACCEPTED**, no rows at fault, for B-F1–B-F8 response adjudication at
`40fab28bc73ed1f7898a0950979607cfd0368c12`, tree
`4f7c6ca6a8af0c9a6b76768c8f497a035686a62d`. Exact unapplied repair SHA256:
`4c73d73d1c7ec1e1453e7ef7ccf1bd3de55238a4469069dcaa75e89bc764fa81`.
The first 27,533 report bytes retain SHA256
`550fe94a69e8a9ae53071ebc0928a55af0a3c1d1f88020119e6211b3ac55c820`;
the appended report is 37,472 bytes. Reviewer text and evidence are unchanged.

Reviewer-executed evidence: 136 passed including one added origin test, one genuine
adoption-dependent skip, eight deselections; guard fault32, loader fault4, restored38;
random B-F7 bounded revert/restore; static checks; all 1,516 export files unchanged by
the selected tests, in bytes and mtimes. These are inherited here, not rerun for receipt.
Coordinator's own earlier bounded results are in B-reconciliation.md. Neither result
makes migration current: pristine support passes, proposed patched support refuses.

Both lane responses have now passed scoped Stage 3. This closes that response-review
step, not the human decisions, G2/U3, installation, migration or implementation release.

## Separate policy observations

O1 is material to the proposed early-import guarantee. Coordinator independently
reproduced it in the restored private patch export: add a harmless marker to
scripts/__future__.py; both direct --help commands print the marker before refusing
unreviewed import name. Removing the file restores both valid controls. No staging or
oracle command ran. See B-future-observation.json. This is not a reopening or relabeling
of B-F1; its two reported shadow names are guarded as adjudicated.

Recommendation: correct this bootstrap gap before requesting approval of the proposed
policy. Do not silently narrow its guarantee or treat late hash refusal as prevention.
Retaining current U0002 remains an explicit alternative. Current policy stays installed.

O2 is a defence-in-depth coverage gap in the write-denial hook; the reviewer proved actual
per-test isolation works. Ask B to extend the hook to new root-level paths or document a
concrete equivalent protection, with a discriminating test. Do not call it evidence that
normal tests modified live files. Coordinator has not independently rerun the isolation
fault; the reviewer receipt is the source of this observation.

Use the existing B author session for a bounded proposal follow-up, preserving the accepted
reports. Review the resulting exact delta separately; no second full Stage 1, A redo or
runtime implementation is required. The acceptance of this exact old response does not
automatically accept a future patch. Same B reviewer can check only the bounded delta.

## Work that can proceed independently

A's reviewed stage/U0011 proposal remains ready for a concrete human semantic decision.
M work would first prepare exact carriers/fixtures for review, not install them. K1 still
requires exact toolchain/licence decisions; B CI, corpus identities, two human L1 fixtures
and later reference/performance/product tasks retain their stated first-use deadlines.
B's E4 arithmetic is delivered; frozen corpus and human fixtures are not. Do not attach
later full-table, silicon or nightly gates to this proposal decision.

All receipts/prompts here remain local and uncommitted. No author/reviewer file, protected
file, index, source, adopted artifact or published history changed by this recording.
