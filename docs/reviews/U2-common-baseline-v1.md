# U2 common baseline v1

Status: **ACCEPTED for implementation** under
[the human record](U2-U0003-acceptance-record.md).
The original accepted brief and proposal remain unchanged as historical evidence.

Frozen repository-relative baseline directory:
`/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-common-baseline-v1/`.
Its `SHA256SUMS` binds every included file; the digest is embedded in each A/B handoff and
recorded in U2-kickoff-SHA256SUMS. No executable runtime is claimed by this baseline.

Contents include the integrated public documents and acceptance annotations, accepted U0003,
CLAUDE.md/CODEOWNERS, exact approval/brief, integration delta and all preserved proposal/B
report inputs. Original snapshot manifests remain valid relative to their own snapshot roots.
Public-document final hashes include coordinator edits that A's original patch index omitted.

## How both lanes use it

Read the frozen baseline as the common authority. Verify `sha256sum -c SHA256SUMS` from its
root. Read active accepted U0003 and approval record before historical proposed ADR text.
Do not modify the baseline. The main and worker worktrees have NOT received file overlays,
commits or cherry-picks. Worker-local public docs still reflect U1; for U2 decisions this
accepted baseline supersedes them. Preserve worker proposal bytes and avoid false manifest
breakage from rewriting A's old ADR. The coordinator owns active public-doc integration.

A implements assigned shared Python types from the accepted specification; B independently
prepares tests against those same fields. Neither creates private alternate types. At A1/B1,
the coordinator reviews exact changed file lists, preserves checkpoints and reconciles callable
dependencies. Transfer reviewed executable shared files only through an explicit, documented
file-level integration step with before/after identities; no whole-directory overlays or
assumed uncommitted branch transfer. Prepare local commits separately when requested.

## First implementation handoffs

- [A checkpoint 1](U2-A-implementation-checkpoint-1.txt): executable shared contract/protocol
  types, semantic validators at A's boundary, generated schemas and independent test fixtures.
  Return APIs and exact schema inventory before expanding to producer/engine/CLI.
- [B checkpoint 1](U2-B-implementation-checkpoint-1.txt): concrete U0004 and hardware/source
  proposals, independent evidence/display/comparison tests and matrix lifecycle preparation.
  Work can proceed while A1 is built; no private schema and no invented source data.

This staging is a delivery dependency, not renewed approval of already accepted U0003 policy.
A1/B1 are coordinator integration checkpoints, not the final fresh independent U-REVIEW.
Runtime implementation within approved scope is authorized; actual hardware inputs, U0004,
new policy deviations and complete generated artifacts retain their stated decisions.

## Verification and publication boundaries

Applied the exact accepted 16-file public patch, then prospective acceptance/status/ownership
annotations. U1 historical approvals and original U0021 host authorization are retained.
U0020 unchanged. Delta JSON records before/exact-patch/final document hashes.
Prompt sync: four tests passed using the existing main virtual environment in integration.
Hash and whitespace checks cover the delivered baseline; no full runtime suite is claimed.

No runtime source, public Python contract/schema, vendor, hardware or dependency changes were
made during baseline assembly. No generation/adoption, commit/push/tag or main transfer.
All files are local and uncommitted; a manifest identifies bytes, not Git protection or an
off-machine backup. Preserve A/B/integration and old U1 worktrees.
