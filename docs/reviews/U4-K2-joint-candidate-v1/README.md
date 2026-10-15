# U4 K2 joint candidate — coordinator reconciliation

**B's correction is reproduced and incorporated into an exact unapplied candidate.**
No further semantic contradiction was found in this bounded check. This is coordinator
reconciliation, not an independent U-REVIEW verdict or native qualification.

Source base: `0718955cc0656e5bac4688d4696abbd547cb4186`. A's full proposal and B's
notification-order guard are preserved at their original paths and hashes. The
[combined patch](combined.proposed.patch) changes the same ten proposed paths, with
[exact before/after identities](candidate.json). SHA256:
`775e93b92931ff48b3e5bf9a0de98c7b6d38026f1ff25f9b83db3d56a6f6e7cf`.

## What changed and why

A's proposed validator checked that dependency notifications had the right target, time,
phase and multiplicity, but allowed a notification to precede the zero-duration completion
that enables it. B's guard requires an earlier available completion for each notification
within each indistinguishable target/time/phase group. Pairing sorted ordinals preserves
multiplicity without inventing an unrecorded sender field. It does not alter timing laws.

The coordinator additionally extended A's **proposed permanent contract test**, rather than
relying solely on a test in a review directory. The [small test-only delta](durable-test.proposed.patch)
uses A's existing literal four-job fixture and B's counterexample. It tests the first and
second notification in a two-completion group. Both formerly passed malformed traces are
refused with the guard, while the unchanged valid trace passes. The inputs are synthetic
partial subrecords, not an EngineResult, native execution or a scheduler oracle.

Attribution: A owns the original ten-path semantic patch; B owns the exact 20-line guard;
the coordinator owns this small permanent-test amendment. All other nine final postimages
match B's combined-postimage receipt; the mapped.py hash remains
`dee6903c221078ae4add28a88f6a0af679a40f92bb1069c8e250352cffa1dd7b`.
No original package or live protected file was edited.

## Newly executed checks

[Verification receipt](verification.json) contains exact commands, outputs, origins and
preservation records. The coordinator reran B's inspected harness on fresh exports:

- Exact A proposal: 30 structural controls pass; B's notification refusal test fails with
  DID NOT RAISE. Corrected: 31 pass. Guard removal reproduces the failure; restoration passes.
- Preserved B controls: 55 pass. Record/construction-plan controls: 9 pass.
- B's guarded candidate: 123 affected regressions pass; schema freshness, selected support,
  strict currentness, lint and both CI-form type checks pass (83/33 files).
- New permanent controls: 2 fail without the guard, 2 pass with it; then 2 fail on reversion
  and 2 pass after restoration. Failures are DID NOT RAISE, not setup failures.
- Final candidate: **124 affected regressions pass**, full-tree Ruff passes, contract types
  pass (33 files), strict currentness passes. The source-type result applies to identical
  source bytes; only the proposed test differs from B's candidate.
- A second fresh export of the stated base accepts the combined patch and reproduces all
  ten postimages. Prompt sync is included in the affected selection; no execution-plan
  schedule change is proposed.

Counts overlap. No full suite, native command, dependency resolution, image construction,
hosted CI, generation/adoption or performance measurement was run. The actual loader
closure remains 26 and selected support remains 56 in the three audited exports. Those
are observations, not quotas. This exact candidate does not stale the adopted artifact;
later dependency changes require recomputation. The coordinator live checkout's previously
recorded ignored tables import-name refusal is not bypassed by these export checks.

## Remaining decisions and work

[Two separate decisions](next-decision.md) are ready for Javid:

1. Accept the exact corrected semantic/schema proposal for guarded human installation.
2. Authorize C1 only: resolve/fetch the proposed dependency set in isolation and return
   real candidate metadata, archive/licence checks and offline-cache evidence.

C1 can proceed independently of installation once authorized. It does not accept the
resulting dependency graph or release compilation. [A's bounded task](lane-A-C1-after-approval.txt)
is prepared but must wait for recorded C1 approval. B can remain at its current handoff.
After approval, the coordinator prepares the guarded human protected-file installation;
no agent applies contract/ or ADR changes. Actual finite profile/registry freeze, C2 probes,
K2 implementation/build and final binary/host authority remain separately controlled.
Existing K1 approvals and U0024 deferrals are unchanged. No G3a/U4 closure follows.
