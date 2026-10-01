# rk-uarch on the Linux box — server runbook

The accounts, SSH access and system packages already exist from rk-sim's setup
(rk-sim's `docs/server/RUNBOOK-server.md`, steps 1–3). rk-uarch adds one clone per account,
next to rk-sim's, and one setup script that each of you runs in your own home directory.

The same two rules hold as for rk-sim: **two accounts, two clones, never a shared working
tree**, and **Javid stays a normal user with no sudo**, which matters again at U3 (the
container runtime, below).

| | Ray | Javid |
|---|---|---|
| Server account | `kakoe` | `javid` |
| GitHub handle | `kakoee` | `jjaffari` |
| rk-uarch clone | `~/AI-infra-simulation/rk-uarch` | `~/AI-infra-simulation/rk-uarch` |
| rk-sim clone (read-only from rk-uarch) | `~/AI-infra-simulation/rk-sim` | `~/AI-infra-simulation/rk-sim` |
| Lane | A — engine | B — evidence & product |

---

## Step 1 · Before the script (once)

- **System packages** (admin, once). The script installs none and stops if `git` or `curl`
  is missing; it warns about the rest:

  ```bash
  sudo apt-get install -y git curl build-essential cmake tmux gh
  ```

  `build-essential` gives Rust a linker and, from U-P13b, compiles the C++ bridge to
  Ramulator 2. `cmake` builds the fork, BookSim 2 and Ramulator 2 from U3. `gh` is optional
  but makes GitHub sign-in a one-liner.
- **Javid accepts the GitHub collaborator invite** to `kakoee/rk-uarch`. Without it, the clone
  fails with "not found".

## Step 2 · Each of you runs the setup script

Same script, both accounts, no sudo. The repo is private, so fetch the script with your own
GitHub sign-in (`gh` is probably signed in already from rk-sim's setup):

```bash
gh api repos/kakoee/rk-uarch/contents/docs/server/setup-dev.sh \
  -H "Accept: application/vnd.github.raw" > ~/setup-uarch.sh
bash ~/setup-uarch.sh
```

Or copy it from your laptop: `scp docs/server/setup-dev.sh kakoe@server_ip:~/setup-uarch.sh`.
After the first run, re-run it from the clone: `bash ~/AI-infra-simulation/rk-uarch/docs/server/setup-dev.sh`.

It checks what's installed, puts `uv` and Claude Code in `~/.local` and Rust (rustup, with
clippy and rustfmt) in `~/.cargo`, signs you in to GitHub, clones to
`~/AI-infra-simulation/rk-uarch`, sets your git identity, checks that rk-sim sits next door,
installs the Python dependencies, installs the repo's pre-commit hook, reports your
container runtime, and runs the gates:

```
pytest       : 4 passed
ruff         : All checks passed!
mypy         : Success: no issues found in 27 source files
import-linter: Contracts: 2 kept, 0 broken.
native       : nothing yet (the engine arrives in U-P11a)
```

Flags: `--no-claude`, `--no-rust`, `--no-hooks`, `--no-gates`, and `--with-measure` (adds
JAX on CPU for U-P10's dry run; large, so off by default). It's idempotent: re-running is
also how you pull and re-verify.

## Step 3 · Work in tmux

A dropped SSH connection kills a foreground agent session mid-task.

```bash
tmux new -s uarch
cd ~/AI-infra-simulation/rk-uarch && claude
# detach: Ctrl-b then d        reattach: tmux attach -t uarch
```

Run rk-sim and rk-uarch sessions in separate tmux windows, each started in its own clone.

## rk-sim, next door

- **Read-only from rk-uarch.** U-P1 and U-P2 read rk-sim at one SHA and record it in ADR
  U0001; agree that SHA before U1 starts. No rk-uarch session edits rk-sim (CLAUDE.md); only
  U-P19 and U-P20 run inside rk-sim, under rk-sim's rules.
- **`make vendor-rk SHA=<sha> RK=~/AI-infra-simulation/rk-sim`** is run by a human (U-P2).
  It refuses an rk-sim tree with local changes, and it runs rk-sim's own code in rk-sim's own
  environment, so rk-sim's `uv sync` must have succeeded in that account.
- **Never a symlink between the clones.** A link inside either repo shows in `git status`
  and can be committed by an agent running `git add -A`.

## The pre-commit hook

The script installs `.git/hooks/pre-commit`, which runs `scripts/hooks/human_owned.sh` and
`scripts/hooks/frozen_predictions.sh`. Agents cannot commit `contract/`, `CLAUDE.md`,
`docs/decisions/` or `tests/golden/expected/`, and nobody can edit a committed L3
prediction. When you, a human, commit a human-owned path:

```bash
UARCH_HUMAN=1 git commit -m "..."
```

## Before U3 · choose the container runtime

U3 builds the engine image (the pinned fork, BookSim 2 and Ramulator 2), and the native engine
builds there too. The script only reports what it finds. **Membership of the `docker` group is
root-equivalent**: anyone in it can mount the host filesystem into a container as root. Adding
Javid to it would undo rk-sim's "no sudo" rule while looking like it kept it. Two options that
keep it:

| Option | Admin, once | Each user |
|---|---|---|
| **Podman (recommended)** — rootless by default, accepts the same Dockerfile | `sudo apt-get install -y podman uidmap` | nothing |
| Rootless Docker | `sudo apt-get install -y uidmap docker-ce-rootless-extras` (from Docker's apt repository) | `dockerd-rootless-setuptool.sh install` |

Decide before U-P5 starts, and record it in ADR U0005 next to the image digest.

## If something breaks

| Symptom | Fix |
|---|---|
| Script exits saying no GitHub auth | Ask the admin to install `gh`, or add an SSH key at github.com/settings/keys |
| `gh repo clone` says not found | Javid hasn't accepted the rk-uarch collaborator invite |
| `cargo: command not found` after install | `source ~/.bashrc`, or open a new shell |
| Rust install says `linker 'cc' not found` | Admin installs `build-essential` |
| `no rk-sim clone at ~/AI-infra-simulation/rk-sim` | Run rk-sim's `docs/server/setup-dev.sh` first |
| `git commit` says "human-owned path(s) staged" | Expected for agents. A human commits with `UARCH_HUMAN=1` |
| docker installed but unusable | Not in the `docker` group, by design; use Podman or rootless Docker (above) |
