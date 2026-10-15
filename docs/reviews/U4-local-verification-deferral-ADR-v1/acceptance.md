# Recorded direction — U0024 local-verification deferral

Javid requested an ADR recording Reza's deferred runner and compilation-image registry
work, its purpose and setup steps. The delay may span several sprints with local tests
providing native correctness evidence in the interim.

In response to the specific question about existing Linux-CI development prerequisites,
Javid explicitly answered:

> Yes—local checks permit interim development; remote and final qualification remain pending.

The exact proposed ADR implements that direction prospectively. Local checks plus independent
review may support development; other task/contract authorizations remain necessary.
Full G5, U9 entry, performance claims and final project closure retain their gates.
Ordinary hosted Python/contract/licence checks remain active. No workflow is changed here.

The accompanying eight-path documentation patch adds U0024 and synchronizes the plan,
build-spec, three native prompts, CLAUDE.md and the previous deferral note. Identity and
postimage hashes are in identity.json. No runtime, schemas, accepted artifact bytes,
numerical thresholds, credentials or host/registry state change.

## Installation boundary

[CLAUDE.md](../../../CLAUDE.md), Workflow: “Agents propose and stop on contract/,
tests/golden/expected/, CLAUDE.md, docs/decisions/.” The human-owned ADR and CLAUDE changes
therefore remain unapplied until Javid runs the exact guarded helper. This is an installation
step for the already approved direction, not another pin/licence/infrastructure vote.
The helper requires the caller's UARCH_HUMAN=1, retains normal hooks, commits the eight paths
locally and does not push. It preserves unrelated untracked reviewer files.

No independent review of this new ADR is claimed. Earlier K1/local infrastructure evidence
is inherited, and this documentation change does not accept K1 or release K2.
