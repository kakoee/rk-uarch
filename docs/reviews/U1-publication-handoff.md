# U1 final publication proposal handoff

> **Coordinator update, 2026-10-06:** Javid accepted complete U0001/U0002 and
> authorized adoption and integration of this exact proposal. It is now integrated
> locally; commit and push remain separate pending steps. See the
> [acceptance/adoption record](U1-acceptance-and-adoption.md). The original
> pre-acceptance proposal, validation and instructions below are retained as history.

Lane B integration handoff, 2026-10-06, for Javid (@jjaffari), the already-authorized acting
human owner/approver of both U1 lanes. **Proposal only: uncommitted, unadopted, ADRs proposed.**
No Reza approval, hosted CI result, cold-clone result or G1/U1 completion is claimed.

Complete proposed tree: `/tmp/u1-publication-proposal-ns9fp_nu`.
Accepted input: `/tmp/u1-replacement-fzin2pif/staging`, with real human generation evidence
in `/tmp/u1-replacement-fzin2pif/evidence`. All source worktrees, coordinator main, prior
reviewed candidates and snapshots are preserved. No vendor operation ran in this preparation.

Read [durable evidence](U1-publication-evidence.md), [accepted A review](U1-lane-A-review.md)
and [accepted B review](U1-lane-B-review.md). Both verdicts are copied verbatim; this separate
publication update does not claim reviewer adjudication of the housekeeping changes.
A-F12 is implemented, tested and accepted in the combined revision. Historical response and
handoff text is retained under attributed superseding status notes.

## Exact human decisions

Accept the **complete files**, including all remaining proposed defaults and qualifications,
not merely the previously approved individual policies:

| ADR | Exact proposed SHA256 |
| --- | --- |
| [U0001 — integration contract](../decisions/U0001-the-integration-contract.md) | `a4ddff1ec26e46f53e31f1221022d4361d3aee3d45f76a381a174f6a958951be` |
| [U0002 — snapshot/parity discipline](../decisions/U0002-the-vendored-snapshot-and-parity-discipline.md) | `66eedb5ce47774c58de5a2d69b62a0828f3f55dd4e8dc999f87b464e7951804c` |

U0001 includes the actual A-F1 narrow hardware-stipulation cycle exception, required and
digest-covered hardware_spec_hash, B-F8 typed parity carrier, contract defaults and parameter
formula proposal. U0002 includes the complete artifact refresh, strict compatibility/environment,
nominal-input, deviation-budget and projection-scope policies.

**Narrow proposed source exception:** pinned rk-sim accepts blank/whitespace source on a stub;
uarch requires source=None and refuses those strings. It is explicitly proposed in U0001's
“Carrier parity versus the pinned stub-source loophole” and U0002's “Isolation and remaining
proposed exception,” with vendored regressions. Whole-ADR acceptance must include that choice;
this is not exact validator parity, automatic blank-to-null conversion or an already accepted
exception. The current files remain proposed for Javid's explicit decision.

Separately approve adopting the entire directory:
`contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963/`
from this proposal, which is byte-identical to the reviewed replacement source. Its manifest
SHA256 is `b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d`.
It contains exactly 20 files, 864 oracle records and two refusals. Keep its generator exactly
`4d2304002b262f2ee03dfe4f8fb338b350aacd80ea2488952849c416ee135317`; no metadata patching
or regeneration accompanies integration. The full file inventory is in the copied
[artifact identity](U1-publication-records/new-artifact-identity.json).

The reason for the artifact revision is reviewed generator identity and verified locked oracle
environment evidence, with no oracle-value change. Record prior manifest(s) → replacement,
approval identity/date/reference and later publication commit. Preserve the uncommitted old
snapshots in their review archives. This is first publication if no snapshot has yet been
committed; published successors subsequently retain predecessors through Git history.
No acceptance/adoption entry is fabricated here.

## Complete delta and lossless integration

Base: coordinator `89313eef20e6b252d235b40a680a1464c52c636a`.
Exact path-by-path before/after hashes and statuses:
`/tmp/u1-publication-evidence-586asqvj/final-delta.json`.
Complete binary-capable patch:
`/tmp/u1-publication-evidence-586asqvj/publication.patch`.
These external files are derived after this handoff is finalized, avoiding self-referential
hashes. The full proposal is the authoritative reviewable result; the patch includes this
handoff, both complete lane implementations, the replacement artifact, review records and
all housekeeping. Delta: **139 added, 26 modified, 0 deleted files** relative to coordinator.

After human review/approval, integrate into a **fresh clean checkout based on that exact
coordinator commit**, preserving existing source worktrees and uncommitted proposals.
Use `git apply --check -p2 /tmp/u1-publication-evidence-586asqvj/publication.patch`, then apply
with the same `-p2`. The patch paths have one extra export-directory component. Do not apply
over a dirty coordinator tree or independently copy lane overlays: that risks losing merged
Makefile, build-spec and prompt edits. If coordinator has advanced, merge this complete delta
in another disposable tree and revalidate conflicts; do not replace newer work wholesale.

The complete patch was checked and applied to a separate exported baseline with no commits.
The result matches every final proposal file byte-for-byte and preserves executable modes;
see `/tmp/u1-publication-evidence-586asqvj/final-rehearsal.json`. Snapshot write-permission
bits may become 0644 under Git, as already permitted by U0002; all artifact digests are exact.

The original accepted combination already resolves A/B/coordinator Makefile and documentation
changes; this proposal retains those resolutions. New housekeeping touches only documentation,
review evidence and prompt-sync tests. Schemas, toy, production models, generator, model sidecars
and all 20 artifact files remain exact. Source preservation and exact delta checks are retained
beside the patch. No integration into a source checkout, adoption or commit happened here.

## Validation and stop point

See the exact commands/results in [durable evidence](U1-publication-evidence.md).
Strict contract: **379 passed**. Full suite: **385 passed**. No failures/skips.
Strict vendor compatibility, mypy (47 files), ruff, import-linter (2 kept), schema freshness
and all four prompt-sync checks pass. Generator and complete snapshot bytes remain unchanged.
These are local integrated checks, not hosted CI or actual workload parity.

The remaining gates are explicit complete ADR acceptance, snapshot adoption approval,
publication, hosted CI, Linux-box cold-clone validation and Javid's human G1 decision.
B-F16 and embedding accounting remain discoverable U2 obligations via U-P3/U0003 kickoff;
U1 self-tests do not satisfy U2 workload parity. Do not tag or declare U1/G1 complete based
on this handoff. All proposed changes remain local and uncommitted.
