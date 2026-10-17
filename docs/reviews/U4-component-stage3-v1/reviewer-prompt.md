# Component Stage 3 — return to the same independent reviewer

Continue the session that wrote `docs/reviews/U4-component-independent-review-v1/README.md`.
You are adjudicating the authors' responses to your F1–F11, under U-REVIEW Stage 3. You did
not author these corrections. This is a bounded response adjudication, not final U4 review,
semantic approval, native qualification or permission to install. Do not reopen Stage 1 or
introduce new findings; record any out-of-scope observations separately for coordinator triage.

Read `docs/prompts/U-REVIEW-adversarial-review.md`, your original report, both lane response
files, and these immutable packages:

- A response publication: `941e882d76419aee0dd297ffd6b997c9807fc49e`;
  `docs/reviews/U4-A-component-stage2-v1/README.md` and
  `docs/reviews/U4-component-lane-A-response.md`.
- B response publication: `9678d492d01efeeaced007aa69e1d01d01269963`;
  `docs/reviews/U4-B-component-stage2-v1/README.md` and
  `docs/reviews/U4-component-lane-B-response.md`.
- Combined unapplied patch, in A's package:
  `81b81c6c2680a17e7d106dedb4a11dc07891b331f3323319fb0192b852bdebe3`.
- `combined-postimages.json` byte SHA256:
  `5d1010aac38f7d04a2935ff48072e418e1e8e9a88d1933758fca4581e2acc845`.
- Reconstruct from `414a94c35c1588cf13b6fcddc3739203c7f5ec6e` plus that patch, with all
  23 postimages, nine immutable activation inputs and the additional first-use consumer
  sidecar verified. Do not apply to moving main or either author's live clone.
- Immutable selection identity:
  `sha256:4b9e73cf9ef11456e216acba58c9496c242169e2a40efcf0aa9e3f36bf0dbbc0`;
  execution-selection.json byte SHA256:
  `a8b94f0d83f429e5101b2b62ba5ed91d9b98d0d228330f5185acc37aab29319c`.

Use `checks.json` beside this prompt for coordinator-verified identities, provenance and
preservation. These checks are not an independent verdict. A's `reproduce.md` and
`reconstruct.py` provide a reconstruction recipe; verify it before use. The final behavioral
run used `7b972d05a2e351375902cc6553a9c03a77aa8101`; the later preparation base has identical
23 postimages and nine activation inputs. The sidecar is additional future-consumer input,
not a claim that it ran in that earlier behavioral selection. B's shared-final-evidence.tar.gz
retains the logs. B's peer_files manifest hash refers to its named earlier A publication
5b2db59, not the final manifest above; the later manifest records the preparation base and
sidecar. The coordinator independently checked the identical 23 postimages and activation
inputs across both bases. The shared 488 passed / 2 human-work skips / 1 native deselection is one
A-executed run whose bytes B checked. Do not add overlapping counts or call it two runs.

Perform exactly the Stage 3 checks:

1. Every F1–F11 has a disposition across the A/B responses. Identify the owner and concrete
   correction, or a precisely stated deferral. No row may disappear through cross-references.
2. Evaluate any rejection/deferral against the finding. F11 is prepared with a proposed
   profile/2 choice and a bounded alternative; Javid has not selected either. NoC occupancy
   and exact /2 semantics likewise remain proposed. Judge the response honestly without
   granting these human decisions or representing the legacy profile promise as stronger.
3. For each applied correction, verify a meaningful regression fails without the correction.
   Randomly choose one applied finding, record the draw, revert only that correction in a
   private reconstruction, run its discriminating check, restore exact bytes and rerun.
   Use your original probes and targeted checks where useful. Do not count incidental import,
   hash, missing-file, setup, or alternative-refusal failures as unsafe-acceptance detection.
   Explicitly grouped redundant guards and documented redundancy are not per-line kills.

Keep the checks directed at the original defects:

- F1: channel and port service occupancy/laws cannot be bypassed; distinguish the proposed
  noncontending NoC bookkeeping convention from shared-resource service evidence.
- F2/F3/F5: complete real cause sets, structural category/owner/sequence constraints and B's
  independent checker. Evaluate the consistent forgeries and genuine multi-node cycle;
  distinguish essential checks from redundant/totality defenses.
- F4/F7: equal-footprint, unmasked producer/order/partial-terminal-reader cases, their valid
  controls, and the retained historical refusal-order cases.
- F6: all new tests/helpers are in the actual 23-file candidate and ordinarily discovered;
  no doc-only copy, missing-file skip or fingerprint-only behavior claim.
- F8/F9: exact declared job/event fields and explicitly unrepresented fields; independently
  discriminating tied-ready port ordering, not makespan or repeated-byte equality alone.
- F10/F11: honest @2 offset changes and proposed exact profile-policy binding, preserving
  historical @1 and profile/1 meanings and identifying the unmade human choice.

Use private exports with explicit pytest configuration/root and export-only project imports.
Confirm origins inside counted runs. Run the affected selection as needed for your own
adjudication, but avoid repeated full suites, unrelated K2 replay, or duplicate broad campaigns.
Preserve your old report/probes, both authors' packages, indexes and historical outputs.

The original report prefix is 22,848 bytes, SHA256
`3cc7e9111dd2f4863e11f346c7a8717e0be3a2ab30d3280a91e7588402c592f9`.
Append your dated Stage 3 verdict to that README, preserving all earlier bytes. Put new probes,
random-revert receipts and logs in a new stage3 subdirectory. Mark executed versus inherited
results, overlapping counts, skipped actual human workings and native deselection explicitly.
Leave review changes unstaged/uncommitted for coordinator preservation.

Important integration boundary: main now includes the separately human-installed K2 U0011
runtime-coexistence clauses. Only that file's installation preimage differs from this
component proposal's recorded base. Review the exact pinned component candidate; do not
replace the live ADR or silently rebase this review. Any later installation must reconcile
both approved text streams. Canonical and both sealed K2 copies still bind old mapped.py
`dee6903c221078ae4add28a88f6a0af679a40f92bb1069c8e250352cffa1dd7b`.
The component candidate requires distinct future runtime/build/host authority. No native
implementation/build/execution, root placement, current runtime launch, oracle lifecycle,
server contact, human worksheet fabrication or semantic acceptance is authorized here.

Return ACCEPTED or NOT ACCEPTED with the original rows at fault and the exact subject you
adjudicated. Acceptance concerns the software/preparation response only. Human NoC/profile
choices, protected installation, H-L1-GEMM-01/H-L1-DMA-01, future native identities and real
first-use authority, component execution, U0024 qualifications and U4 closure remain separate.
