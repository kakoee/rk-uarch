#!/usr/bin/env bash
# rk-uarch — per-user development setup on the Linux box. RUN AS YOURSELF. Never with sudo.
#
#   bash setup-dev.sh
#
# Ray and Javid both run this, unchanged, in their own accounts. It installs nothing
# system-wide and needs no root: uv, rustup and Claude Code go into your home directory, and
# everything else lives in your own clone at ~/AI-infra-simulation/rk-uarch, next to the
# rk-sim clone that rk-sim's own docs/server/setup-dev.sh created.
#
# Idempotent — safe to re-run any time. Re-running is also how you pull the latest main and
# re-check that your environment still passes the gates.
#
# Flags:
#   --no-claude     skip installing Claude Code
#   --no-rust       skip installing the Rust toolchain (rustup, into ~/.cargo)
#   --no-hooks      skip installing the repo's git pre-commit hook
#   --with-measure  also install the `measure` extra (JAX on CPU, for U-P10's dry run; large)
#   --no-gates      skip the test/lint/typecheck checks at the end

set -uo pipefail

WORKROOT="$HOME/AI-infra-simulation"
CLONE="$WORKROOT/rk-uarch"
RKSIM="$WORKROOT/rk-sim"
REPO="kakoee/rk-uarch"
HOOK_MARK="installed by rk-uarch docs/server/setup-dev.sh"
INSTALL_CLAUDE=1
INSTALL_RUST=1
INSTALL_HOOKS=1
WITH_MEASURE=0
RUN_GATES=1
MISSING=()

for arg in "$@"; do
  case "$arg" in
    --no-claude)    INSTALL_CLAUDE=0 ;;
    --no-rust)      INSTALL_RUST=0 ;;
    --no-hooks)     INSTALL_HOOKS=0 ;;
    --with-measure) WITH_MEASURE=1 ;;
    --no-gates)     RUN_GATES=0 ;;
    *) echo "unknown flag: $arg"; exit 1 ;;
  esac
done

[[ $EUID -ne 0 ]] || { echo "Do NOT run this as root or with sudo. Log in as yourself."; exit 1; }

say() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
ok()  { printf '    \033[32m✓\033[0m %s\n' "$1"; }
warn(){ printf '    \033[33m!\033[0m %s\n' "$1"; }

echo "rk-uarch dev setup — user: $(whoami)  host: $(hostname)"

# ---------------------------------------------------------------- 1. preflight
say "checking what's already here (installing no system packages)"
for tool in git curl; do
  if command -v "$tool" >/dev/null; then
    ok "$tool $("$tool" --version 2>&1 | head -1)"
  else
    warn "$tool MISSING — required"
    MISSING+=("$tool")
  fi
done
if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo
  echo "Cannot continue without: ${MISSING[*]}"
  echo "Admin runs:  sudo apt-get install -y ${MISSING[*]}"
  exit 1
fi
# Recommended now, required later: a C compiler (Rust links with it; the Ramulator 2 bridge
# in U-P13b compiles C++), cmake (the fork, BookSim 2 and Ramulator 2 build with it), tmux.
RECOMMEND=()
command -v cc    >/dev/null && ok "cc $(cc --version 2>&1 | head -1)"   || { warn "no C compiler — Rust cannot link without one"; RECOMMEND+=(build-essential); }
command -v cmake >/dev/null && ok "cmake $(cmake --version | head -1 | awk '{print $3}')" || { warn "cmake missing — needed from U3 (fork, BookSim 2, Ramulator 2)"; RECOMMEND+=(cmake); }
command -v tmux  >/dev/null && ok "tmux $(tmux -V | awk '{print $2}')" || { warn "tmux missing — agents should run inside it"; RECOMMEND+=(tmux); }
if command -v gh >/dev/null; then ok "gh $(gh --version | head -1 | awk '{print $3}')"
else warn "gh not installed — the script will fall back to git-over-SSH for cloning"; fi
[[ ${#RECOMMEND[@]} -eq 0 ]] || echo "    admin can add them with:  sudo apt-get install -y ${RECOMMEND[*]}"

# ---------------------------------------------------------------- 2. PATH
say "PATH"
mkdir -p "$HOME/.local/bin"
for rc in "$HOME/.bashrc" "$HOME/.profile"; do
  [[ -f "$rc" ]] || touch "$rc"
  grep -q 'HOME/.local/bin' "$rc" || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
done
export PATH="$HOME/.local/bin:$PATH"
ok "~/.local/bin on PATH (in this shell and in future ones)"

# ---------------------------------------------------------------- 3. uv + Python
say "uv (installs into ~/.local — no root)"
if command -v uv >/dev/null; then
  ok "already installed: $(uv --version)"
else
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
  ok "installed: $(uv --version)"
fi
uv python install 3.12 >/dev/null 2>&1 && ok "Python 3.12 available (the repo pins it in .python-version)" \
  || warn "could not pre-install Python 3.12 — uv will fetch it on first sync"

# ---------------------------------------------------------------- 4. Rust
if [[ $INSTALL_RUST -eq 1 ]]; then
  say "Rust toolchain (rustup into ~/.cargo — no root; the native engine is Rust)"
  [[ -f "$HOME/.cargo/env" ]] && . "$HOME/.cargo/env"
  if command -v rustup >/dev/null; then
    ok "rustup already installed: $(rustup --version 2>/dev/null | head -1)"
  else
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
      | sh -s -- -y --profile default --no-modify-path >/dev/null
    . "$HOME/.cargo/env"
    ok "installed: $(rustc --version)"
  fi
  for rc in "$HOME/.bashrc" "$HOME/.profile"; do
    grep -q '.cargo/env' "$rc" || echo '[ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"' >> "$rc"
  done
  rustup component add clippy rustfmt >/dev/null 2>&1 && ok "clippy and rustfmt present" \
    || warn "could not add clippy/rustfmt"
fi

# ---------------------------------------------------------------- 5. Claude Code
if [[ $INSTALL_CLAUDE -eq 1 ]]; then
  say "Claude Code (also ~/.local — your OWN account, never a shared login)"
  if command -v claude >/dev/null; then
    ok "already installed"
  else
    curl -fsSL https://claude.ai/install.sh | bash
    export PATH="$HOME/.local/bin:$PATH"
    command -v claude >/dev/null && ok "installed — run 'claude' once to log in" \
      || warn "install finished but 'claude' not on PATH yet; open a new shell"
  fi
fi

# ---------------------------------------------------------------- 6. GitHub auth
say "GitHub access (the repo is private, so this is required)"
AUTH_OK=0
if command -v gh >/dev/null; then
  if gh auth status >/dev/null 2>&1; then
    ok "gh authenticated as $(gh api user -q .login 2>/dev/null)"
    AUTH_OK=1
  else
    echo "    starting device-flow login — it prints a code you paste in a browser"
    if gh auth login --hostname github.com --git-protocol https --web; then
      gh auth setup-git
      ok "authenticated as $(gh api user -q .login 2>/dev/null)"
      AUTH_OK=1
    fi
  fi
fi
if [[ $AUTH_OK -eq 0 ]]; then
  if ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    ok "SSH key works against GitHub — will clone over SSH"
    AUTH_OK=2
  else
    warn "no GitHub auth available"
    cat <<'EOF'

    Pick one, then re-run this script:
      a) ask the admin to install gh, then re-run — easiest
      b) ssh-keygen -t ed25519 -C "$(whoami)@rk-uarch"
         then add ~/.ssh/id_ed25519.pub at https://github.com/settings/keys
EOF
    exit 1
  fi
fi

# ---------------------------------------------------------------- 7. clone
say "repository → $CLONE"
mkdir -p "$WORKROOT"
if [[ -d "$CLONE/.git" ]]; then
  ok "already cloned"
  git -C "$CLONE" pull --ff-only && ok "pulled latest" || warn "pull skipped (local changes?)"
else
  if [[ $AUTH_OK -eq 1 ]]; then gh repo clone "$REPO" "$CLONE"
  else git clone "git@github.com:$REPO.git" "$CLONE"; fi
  ok "cloned"
fi
cd "$CLONE" || exit 1

# ---------------------------------------------------------------- 8. git identity
say "git identity for this machine"
if git config user.email >/dev/null; then
  ok "$(git config user.name) <$(git config user.email)>"
else
  read -rp "    your name  : " GN
  read -rp "    your email : " GE
  git config user.name "$GN"; git config user.email "$GE"
  ok "set"
fi

# ---------------------------------------------------------------- 9. rk-sim alongside
say "rk-sim, next door (read-only from here)"
RKSIM_SHA="none"
if [[ -d "$RKSIM/.git" ]]; then
  RKSIM_SHA="$(git -C "$RKSIM" rev-parse --short HEAD)"
  ok "found $RKSIM at $RKSIM_SHA"
  if [[ -n "$(git -C "$RKSIM" status --porcelain)" ]]; then
    warn "rk-sim has local changes — U-P2's 'make vendor-rk' refuses a dirty tree"
  fi
  echo "    U-P1 and U-P2 read rk-sim at a named SHA and record it in ADR U0001. An rk-uarch"
  echo "    session never edits rk-sim (CLAUDE.md); only U-P19 and U-P20 run inside it."
else
  warn "no rk-sim clone at $RKSIM — run rk-sim's docs/server/setup-dev.sh first; U1 needs it"
fi

# ---------------------------------------------------------------- 10. dependencies
say "project dependencies"
EXTRAS=(--extra dev)
[[ $WITH_MEASURE -eq 1 ]] && EXTRAS+=(--extra measure)
uv sync "${EXTRAS[@]}" && ok "python deps installed (${EXTRAS[*]})" || warn "uv sync FAILED — see output above"
if command -v rustup >/dev/null && [[ -f native/rust-toolchain.toml ]]; then
  # rustup ≥ 1.28 installs a toolchain file's pin only on request; older ones do it on `show`.
  (cd native && { rustup toolchain install >/dev/null 2>&1 || rustup show >/dev/null 2>&1; }) \
    && ok "pinned Rust toolchain from native/rust-toolchain.toml is installed" \
    || warn "could not install the pinned Rust toolchain"
fi

# ---------------------------------------------------------------- 11. git hook
if [[ $INSTALL_HOOKS -eq 1 ]]; then
  say "pre-commit hook (the two checks in .pre-commit-config.yaml)"
  HOOK="$(git rev-parse --git-path hooks)/pre-commit"
  if [[ -f "$HOOK" ]] && ! grep -q "$HOOK_MARK" "$HOOK"; then
    warn "a different pre-commit hook already exists at $HOOK — left untouched"
  else
    cat > "$HOOK" <<EOF
#!/usr/bin/env bash
# $HOOK_MARK. Agents may not commit human-owned paths
# (contract/, CLAUDE.md, docs/decisions/, tests/golden/expected/); committed predictions
# are never edited. A human commits a human-owned path with: UARCH_HUMAN=1 git commit ...
set -e
root="\$(git rev-parse --show-toplevel)"
"\$root/scripts/hooks/human_owned.sh"
"\$root/scripts/hooks/frozen_predictions.sh"
EOF
    chmod +x "$HOOK" scripts/hooks/*.sh
    ok "installed — humans commit human-owned paths with UARCH_HUMAN=1"
  fi
fi

# ---------------------------------------------------------------- 12. container runtime
say "container runtime (needed from U3, for the engine image; nothing is built now)"
if command -v podman >/dev/null; then
  ok "podman $(podman --version | awk '{print $3}') — rootless, no extra privileges"
elif command -v docker >/dev/null; then
  if docker info >/dev/null 2>&1; then
    ok "docker usable from this account"
  else
    warn "docker is installed but this account cannot use it — see RUNBOOK-server.md before U3"
  fi
else
  warn "no docker or podman yet — decide before U3; RUNBOOK-server.md explains the choice"
fi

# ---------------------------------------------------------------- 13. tmux
if command -v tmux >/dev/null && [[ ! -f "$HOME/.tmux.conf" ]]; then
  cat > "$HOME/.tmux.conf" <<'EOF'
set -g mouse on
set -g history-limit 50000
set -g default-terminal "screen-256color"
EOF
fi

# ---------------------------------------------------------------- 14. gates
if [[ $RUN_GATES -eq 1 ]]; then
  say "acceptance gates"
  FAIL=0
  printf "    pytest       : "; out="$(uv run pytest -q 2>&1)" || FAIL=1; echo "$out" | tail -1
  printf "    ruff         : "; out="$(uv run ruff check 2>&1)" || FAIL=1; echo "$out" | tail -1
  printf "    mypy         : "; out="$(uv run mypy src contract 2>&1)" || FAIL=1; echo "$out" | tail -1
  printf "    import-linter: "; out="$(uv run lint-imports 2>&1)" || FAIL=1; echo "$out" | tail -1
  if [[ -n "$(find native/crates -name '*.rs' -print -quit 2>/dev/null)" ]]; then
    if command -v cargo >/dev/null; then
      printf "    native       : "
      (cd native && cargo fmt --check && cargo clippy --all-targets -q -- -D warnings \
        && cargo test -q) >/tmp/rk-uarch-native-$$.log 2>&1 \
        && echo "fmt, clippy, tests green" || { echo "FAILED (see /tmp/rk-uarch-native-$$.log)"; FAIL=1; }
    else
      warn "native sources exist but cargo is missing — re-run without --no-rust"; FAIL=1
    fi
  else
    echo "    native       : nothing yet (the engine arrives in U-P11a)"
  fi
  [[ $FAIL -eq 0 ]] && ok "all green" || warn "something failed above — fix before starting a sprint"
fi

# ---------------------------------------------------------------- done
# Server usernames and GitHub handles differ on this box (e.g. kakoe vs kakoee). CODEOWNERS
# and gh use the GitHub handle; $HOME and file ownership use the server account.
if [[ "$(whoami)" == "javid" ]]; then
  LANE="B — evidence & product  (hw/, provenance, report, study, validation/, measure/, scripts/)"
  FIRST="Lane B runs U-P2 (the vendored rk-sim snapshot and FLOP parity)."
else
  LANE="A — engine  (hw, workload, mapping, engines, table, native/, third_party/, containers/)"
  FIRST="Lane A runs U-P1 (the contract) — do it with BOTH of you present."
fi
GH_USER="$(gh api user -q .login 2>/dev/null || echo 'not signed in via gh')"

cat <<EOF

────────────────────────────────────────────────────────────────────
 Ready.

   account $(whoami) on $(hostname)   ·   github $GH_USER
   clone   $CLONE
   rk-sim  $RKSIM  (HEAD $RKSIM_SHA, read-only from rk-uarch)
   lane    $LANE

 Read first, in this order:
   docs/execution-plan.md            what happens when, and which prompt to run
   docs/build-spec.md §0–§2          how to use the spec, scope, architecture
   docs/reviews/rev2-plan-review.md  what Rev 2.1 fixed, and what is still open
   CLAUDE.md                         standing orders your agent already loads

 Work inside tmux so a dropped connection doesn't kill an agent mid-task:

   tmux new -s uarch
   cd $CLONE && claude
   # detach: Ctrl-b then d       reattach: tmux attach -t uarch

 Next is U1. $FIRST
 Both prompts read rk-sim at one SHA; agree it first (e.g. $RKSIM_SHA).
────────────────────────────────────────────────────────────────────
EOF
