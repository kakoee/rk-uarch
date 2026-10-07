# U1 — Human acceptance and local snapshot adoption

**Date:** 2026-10-06 (America/Los_Angeles); recorded at 2026-10-07 06:52 UTC.
**Approver:** Javid (@jjaffari), already-authorized acting owner of both U1 lanes.
No Reza approval is claimed.

## Authorization

Javid explicitly instructed the coordinator in this session:

> I accept the complete U0001 and U0002 proposals, including the stub-source exception,
> approve adoption of the identified snapshot, and authorize integration of the final
> publication proposal. Keep commit and push as separate steps, with commit comments
> covering them.

This accepts the complete proposed contents identified below, not only individual
Stage 2 policies. The blank-stub-source compatibility exception is accepted: rk-uarch
requires source=None while the pinned upstream also accepts blank/whitespace strings.
There is no automatic blank-to-null conversion or claim of exact validator parity.

## Approved inputs

Publication proposal: `/tmp/u1-publication-proposal-ns9fp_nu`.
Coordinator base: `89313eef20e6b252d235b40a680a1464c52c636a`.

| Input | Approved SHA256 |
| --- | --- |
| U0001 complete proposal, before acceptance annotation | `a4ddff1ec26e46f53e31f1221022d4361d3aee3d45f76a381a174f6a958951be` |
| U0002 complete proposal, before acceptance annotation | `66eedb5ce47774c58de5a2d69b62a0828f3f55dd4e8dc999f87b464e7951804c` |
| Complete publication patch | `4c73a75e8fe548fe59919e76faa0179badd9554ad0a36b0753ed978cc5aacead` |
| Reviewed generator script | `4d2304002b262f2ee03dfe4f8fb338b350aacd80ea2488952849c416ee135317` |
| Oracle program | `9dd67d4883206f14b8a5a00fa3d0ced95bddaa395ba634d80e08a39813ea04fb` |
| Adopted snapshot manifest | `b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d` |

The ADR hashes identify the exact accepted proposal texts. Recording acceptance changes
their file hashes; it does not change their approved implementation or policies. Those
original texts and the original publication patch remain in the preserved proposal.

## Adoption

Adopted the entire directory
`contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963/`
into the clean coordinator working tree, together with its exact reviewed generator.
The artifact has 20 files, 864 oracle records and two unsupported-precision refusals.
No vendor generation, metadata patching or selective mixing accompanied integration.

This selects the artifact for first publication: no snapshot previously existed in the
coordinator base. There is no prior publication commit. Earlier uncommitted artifacts
remain at their original review locations:

| Prior artifact | Manifest SHA256 |
| --- | --- |
| Lane B original: `/home/jjaff/AI-infra-simulation/rk-uarch-u1-b/contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963` | `4caea65f3c217bbb2030409833be6c67c15561552f8d9c9e179ac3ff82883284` |
| Earlier candidate: `/tmp/u1-vendor-final-f96kn1fp/contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963` | `6b0d69c5737ba2b4cdbd8bce13ec860e4750f4008d9f4ee4fb8dc6db456d8304` |

The reason for the revision is the reviewed generator fixes and verified locked oracle
environment evidence. Compared with both prior artifacts, only GENERATOR.json and
MANIFEST.json changed and uv.lock was added; oracle records and refusals are byte-identical.
See [classified comparison](U1-publication-records/snapshot-comparison.json),
[artifact identity](U1-publication-records/new-artifact-identity.json) and
[environment evidence](U1-publication-records/oracle-environment.json).

## Integration and validation

The coordinator verified a clean main at the exact base, checked the patch hash and all
165 proposed changed-file hashes, applied the complete patch, and checked every resulting
changed file and executable mode against the reviewed proposal: 139 added, 26 modified,
zero deleted paths. No independent lane overlays were reapplied. Source worktrees and
review candidates remain preserved.

Additional coordinator edits record this authorization, accepted ADR status and current
execution-plan/handoff status only. Implementation, schemas, fixtures, generator and
snapshot bytes remain those of the approved proposal. Review reports are unchanged.

The pre-integration publication proposal passed 379 strict contract and 385 full-suite
tests, all static checks, schema freshness and four prompt synchronization checks.
Coordinator integrated-tree validation completed successfully after the acceptance/status
edits. All commands below ran from the coordinator root; none generated vendor artifacts.

| Command | Result |
| --- | --- |
| `uv sync --locked --extra dev --offline` | Passed; local development environment synchronized |
| `uv run --no-sync python -B scripts/vendor_rk.py --check` | Manifest, coverage and strict current compatibility passed |
| `uv run --no-sync pytest -q -rs contract/tests --require-vendor` | 379 passed, no failures or skips |
| `uv run --no-sync pytest -q -rs` | 385 passed, no failures or skips |
| `uv run --no-sync mypy src contract scripts` | Passed, 47 source files |
| `uv run --no-sync ruff check .` | Passed |
| `uv run --no-sync lint-imports` | Two contracts kept, none broken |
| `uv run --no-sync python -B -m uarch_contract.generate --check` | Schemas fresh |
| `uv run --no-sync pytest -q tests/unit/test_prompt_sync.py` | Four passed |
| `git diff --check` | Passed |

These are local integrated checks, not hosted CI or Linux-box cold-clone evidence.

## Remaining gates

- Local publication commit: pending separate instruction; comprehensive message prepared.
- Push and hosted CI: pending separate instruction and actual results.
- Linux-box cold-clone validation of the committed revision: pending.
- Sprint-end how-it-works refresh and closeout record: pending.
- Final human G1/U1 decision and u01-end tag: pending.

Both independent lane review verdicts are ACCEPTED. B-F16, A-F9 and embedding-accounting
obligations remain assigned to U2 in [the kickoff record](U2-kickoff-obligations.md).
Acceptance and adoption do not establish U2 workload parity or close G1/U1.
