# U3 preparation

Archived coordination record, committed on 2026-10-12 before the architecture-direction
amendment. The entries and prompts below describe their dated scope; they are not current
implementation instructions. RoPE runtime/adoption and hosted CI subsequently completed; see
[publication receipt](../U3-runtime-publication-v1/receipt.json). The source-only fork
investigation is [published separately](../U3-fork-feasibility-v2/README.md).

## Historical preparation status — 2026-10-11

This update supersedes the historical preparation milestones below. A/B sessions have
published bounded analytic tests and planning supplements; primary main is 7f5d93b.
Javid reports Reza installed the container packages. Rootless Podman 4.3.1 and user
namespaces pass the prepared check ([receipt](host-podman-result.json)); no image has run.
Runner registration and a real manual nightly remain unverified; schedule is paused.
Follow [runner setup](host-next-steps.md#runner-registration). Native remains a no-op;
B's ten nightly mutant cases now exist and must actually execute. Fork semantic
feasibility and the proposed next direction remain unresolved, separately from host setup.

The following entries describe earlier milestones, not the current next action.

Preparation only: no U-P5/U-P6 implementation has started, no workflow has been changed,
and no developer session has been launched. U2 is closed at `u02-end` / `79bc1f0`.

## Host prerequisite

Javid identified `javid@152.53.209.203` as the project Linux server used by Reza and for
Javid's cold testing. A read-only SSH preflight attempt was refused at authentication
(`Permission denied (publickey,password)`); no remote commands or changes ran. The earlier
`agentic-cpu-dev` alias is not the selected server. See [host access record](host-access.json).
GitHub runner inventory returned HTTP 403 with current credentials; no runner state is
inferred. The nightly schedule is still commented out on main.

Javid returned the [host inventory](host-preflight-reported.json). Follow the
[host setup sequence](host-next-steps.md); the next action is user-local Python setup. Current repository
policy requires human runner registration with label `uarch`. Re-enable the schedule only
once that runner is online; trigger and verify a manual nightly run before U-P5 starts.
A green bootstrap with no tests collected is a runner check, not completed U3 verification.
No fork build or performance measurement on WSL2/laptop. No rootful privilege changes.

## Working folders and Git

Use two independent clones (each with its own `.git`) on local `main`, not two linked
worktrees sharing a checked-out branch. Javid clarified these should be separate local folders on this laptop:
`rk-uarch-u3-a` and `rk-uarch-u3-b`. Their setup does not depend on the simulator host decision. One GitHub identity is sufficient.
Keep the primary `rk-uarch` clone as a convenient view of published main. Each lane fetches,
integrates and tests before a normal main-only push. Rebase only unpublished commits, never
force-push. No mandatory PRs or copied checkpoint trees. This is Javid's standing instruction;
the old implementation template's blanket uncommitted stop is superseded for owned paths.
Human-owned files, artifact generation/adoption and consequential policy decisions retain
their existing rules. Do not copy hook bypass flags or credentials into clones.

## Prepared prompts

- [Lane A](lane-A-kickoff.txt): preregister U0005/G2 before candidate measurements, then fork/container/adapter.
- [Lane B](lane-B-kickoff.txt): capability-aware L0/L0m design, U0006 and discriminating mutants.

These prompts are drafts pending host/readiness resolution; do not present them as launched
implementation. A and B can work in parallel once prerequisites and protected decisions are
settled. Use fresh sessions supplied by Javid; the coordinator does not spawn agents.

Hours/retro for U2 remain unreported. U3 estimates must be refreshed; old plan numbers are
not measured engineering time. Cleanup approval is a separate concrete worktree-removal
plan after verified preservation of uncommitted U2 files.

## U2 cleanup completed

The approved U2 worktrees have been removed after archive revalidation; local branch refs
and the verified archive remain. See [cleanup receipt](../U2-cleanup-v1/execution.json).
This does not start U3 implementation.

## Local clones ready

Both local development clones now exist: `../rk-uarch-u3-a` and `../rk-uarch-u3-b`,
each with its own `.git`, local main tracking origin/main, normal commit hooks and the
clean U2 baseline79bc1f0. [Clone receipt](local-clones.json). No implementation or push
has occurred. Server setup remains separate from these local development folders.

## Work available while the administrator is away

Javid reports Reza is the root administrator and unavailable. Defer system container
installation. No host requirement is waived and no privileged workaround is proposed.
Use [A planning now](lane-A-planning-now.txt) for preregistration/interface planning,
and [B analytic preparation now](lane-B-analytic-now.txt) for capability design and a
bounded local test/mutant selection. These replace the broader kickoff prompts for now.
They do not launch fork work or satisfy self-hosted nightly requirements. Javid opens
the fresh sessions; the coordinator has launched none.
