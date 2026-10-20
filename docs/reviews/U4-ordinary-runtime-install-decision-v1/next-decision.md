# Install the reviewed ordinary-runtime simplification

Status: approved by Javid in this session; nothing installed.

Approval: Javid replied “yes” to “Approve installing this exact transition,
committing it normally, and publishing after receipt verification?”

## Exact change

Install the complete successor transition from published commit
`808076a8f1786f00ef9e3cd0de6ab8f2adea83ad`:
[transition.patch](../U4-ordinary-runtime-correction-v2/transition.patch).
Do not apply the earlier v1 patch first.

- Patch SHA-256: `b0de563bc3a6433b205649b3ed4db2861856636629dc715a18ff264f6eda4da4`.
- Recorded base: `12be87558c5a3312068ab1c5aa147fd95df232da`.
- Reconstructed source tree on that base:
  `9a86cab622504e68746534c94e93b659cacf794d`.
- Complete transition: 150 paths, including the original ordinary interface,
  protected schemas/documentation, corrections and bounded obsolete-code cleanup.
- Coordinator HEAD is the published successor package. The patch applies there;
  the additional proposal files remain intact.

The result uses an installed package, the native executable and ordinary inputs,
with basic software/model provenance, semantic validation, independent checking,
replay and normal process limits. The superseded authority, deployment, startup
assurance and construction-attestation machinery is retired. This does not
broaden the engine's admitted model or hardware capabilities.

## Review disposition

The [independent review](../U4-ordinary-runtime-independent-review-v1/README.md)
and its `recheck-808076a-independent/` evidence report F1–F3 resolved,
A1–A2 handled, no blocking finding and no concrete cleanup regression.

R1 is a non-blocking, pre-existing regression-coverage suggestion. It is not an
installation prerequisite and is not represented as fixed. The package-version
restriction remains documented: version `0.0.1`, without cross-version replay.
The two archival-only helpers remain documented; no additional cleanup is
required by this decision.

The implementation author appended a section and `recheck-808076a/` evidence
inside the review directory before the independent recheck. That is an author
contribution, not independent evidence. Preserve it with that attribution.
Only the original reviewer’s Stage 1 and later independent recheck receive
independent-review credit. No reviewer text was edited during this preparation.

## Evidence and bounded checks

The author reports 1,285 affected Python passes with two human-L1 skips,
87 native passes and installed execution/replay with 26 negative controls.
The reviewer independently exercised the corrected behaviors, normal native
workflow, cleanup/import/static checks and relevant removal controls, reusing
unchanged installed-runtime evidence explicitly.

The coordinator did not repeat those suites. [checks.json](checks.json)
records exact patch verification, independent temporary-index reconstruction,
current-checkout applicability and preservation of the report's prior prefix.
The working tree and real index were not changed by those checks.

## Approved action

Approve this exact protected source/documentation installation, a normal local
commit, and subsequent normal publication after receipt verification. Preserve
peer history and publish the review and this decision with accurate attribution.
The human performs the protected application and commit; the coordinator may
verify the receipt and publish. Do not bypass hooks or set the human flag in an
agent session.

Use ordinary Git application/staging/commit commands for the exact patch,
starting with a clean tracked worktree and index. Stop on conflicts, changed
preimages or hook failures. Do not reset unrelated work. No new installation
helper or runtime authorization framework is needed.

This is source installation, not a dependency/environment installation, root
deployment, artifact regeneration, hosted-native setup or U4/G3a closure.
Existing human L1, U4b/reference readiness and U0024 obligations remain.
No full historical campaign or new assurance requirement is added.

The remaining human installation step comes from the repository's existing
`CLAUDE.md` rule: “Agents propose and stop on contract/,
tests/golden/expected/, CLAUDE.md, docs/decisions/.”

## Publication preparation

The review report and all executed probe/receipt files are preserved unchanged.
Coordinator-added `ruff.toml` inside the review directory records only the existing
lint diagnostics for 21 exact archived probe paths, so publication does not
rewrite executed evidence or change production lint checks. This file is
publication metadata, not independent reviewer evidence.
