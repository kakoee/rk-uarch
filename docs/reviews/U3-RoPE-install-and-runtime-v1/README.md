# U3-RoPE-install-and-runtime-v1 — accepted

Javid (@jjaffari), acting human decision-maker for both lanes, approved this decision on
2026-10-11 by replying **yes** to the named decision. This accepts the exact
[proposal](../U3-schema-report-reconciliation-v1/next-decision.md) published at
`7454ececbdc03cddd83194ac756a41cd06d99392`; that historical proposal remains unchanged.
No independent-review verdict or Reza approval is inferred.

## Accepted scope

Human installation and a local protected commit of A's exact 17-path patch published at
`53435927497eb3e4552e32e2c5e887e0bcb05ddc` are approved. Patch path:
`docs/reviews/U3-RoPE-protected-patch-v1/protected.patch`; SHA256:
`8a02ed6cf56846c6f688d195b068aadd19bb2bab11fe751a8af36d8408e04169`.
It contains two contract modules, eleven mirrors, three tests and the U0022 schema addendum.
The [coordinator reconciliation](../U3-schema-report-reconciliation-v1/README.md) records
138 passing tests, 28 pending runtime tests and expected strict-support refusal in scratch.

After the human installation/commit, A may implement the already accepted design sections
2–5: additive v2 protocol/generator, strict prepared/job/result admission, coefficient-input
preparation, RoPE counts/traffic, analytic v2, dispatch and capture, with tests first.
The [implementation handoff](lane-A-implementation.txt) binds the exact scope and stop point.
This does not authorize agents to edit protected tests: A proposes their required updates
for human installation, including activation of the 28 pending admission cases.

Preserve all accepted U0022 semantics and legacy v1 bytes/identity. No automatic upgrade,
coefficient guessing, public v2 table/report attachment, B eligibility change, simulator
selection, U0005/200-second timing, host waiver or nightly completion is granted.

## Human installation

The [helper](human-install.sh) targets only the existing `rk-uarch-u3-a` clone's local main.
It checks a clean clone/index, accepted ancestry, exact patch, unchanged destinations and
normal hooks. It prepares the expected patched files only in a disposable scratch directory,
then compares every staged blob before committing. `--check` changes no repository files,
index, branch or Git objects. The non-check invocation is **for Javid only** and sets the
human-owned hook flag only for its exact local commit. No push, generation or adoption occurs.

```sh
bash /home/jjaff/AI-infra-simulation/rk-uarch/docs/reviews/U3-RoPE-install-and-runtime-v1/human-install.sh
```

Return the printed commit receipt before sending the implementation handoff to A. Coordinator
verification will bind that human commit to this acceptance and the reviewed patch; approval
alone is not a claim that installation has happened. The helper refuses reruns after installation.

## Local development and publication

A continues normal local Git commits in its existing independent clone. B's standalone-v1
correction remains authorized independently and can publish changes outside the support set.
The schema commit makes A's support inventory stale locally. Until one combined reviewed
freeze/human generation/audit/exact adoption and final checks, **do not push A's source-bound
commits or merge them into published main**. Fetch and integrate peer main as needed, preserving
those local commits; do not blindly pull with ff-only once histories diverge or force-push.
Primary `rk-uarch` continues to track published main. No integration branch, checkpoint copies
or per-checkpoint oracle refresh is introduced.

Candidate adoption, protected adoption commit and main publication remain separate. Final
checks include both schema families, CI-form types/lint/imports, strict vendor/contract checks,
new rotary/replay and legacy table/report checks, then the full suite. Any support-code change
after freeze requires a new lifecycle. Existing reports retain their original implementation
bindings; changed support does not become current through historical validation.

## Coordinator preparation checks

Shell and embedded Python syntax and local document links passed. The clean Lane A clone
was fast-forwarded to published main; no protected installation occurred. The helper's
`--check` passed all 17 paths, exact patch digest, scratch application and index applicability.
Its initial hooks-path check was too strict about the existing explicit `.git/hooks` setting;
it now compares the effective path to the normal clone hook location. The hook configuration
and hook files were not changed. A final read-only preflight follows publication of this helper.

## Human installation verified; A implementation released

Javid returned the human receipt for local A commit
`eeb2f4d74d4c751c55edec1b5ee40f7a40162562`, parent
`df4caf81969c5aafa90ea183dfc8d9e69334d9f0`, tree
`cb0d7fd650426706a7cdadf2058bf49637c1ec4d`. The coordinator independently reconstructed
the approved patch from that parent in disposable scratch and verified all 17 committed
paths, bytes, modes and live contents, with a clean index/worktree. The
[verification receipt](installation-verification.json) binds this human commit to the approval.

Installed new carrier tests: **74 passed, 28 skipped**; new schema freshness passed. The
28 skips are still the pending runtime-admission tests. Strict vendor check refused with
`input support inventory changed`, as expected. No full suite or runtime implementation
is claimed. These checks do not grant support currentness. Do not rerun the installer.

The [Lane A implementation handoff](lane-A-implementation.txt) is now released. The human
schema commit remains only in A's clone; the primary clone publishes this coordination
record without incorporating the schema change. A preserves its local human commit while
integrating subsequent published coordination/B work through normal Git. The source-bound
push remains gated on the combined U0002 lifecycle.
