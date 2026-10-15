#!/usr/bin/env bash
# PROPOSAL ONLY. Runs inside the accepted final offline image after separate release.
set -euo pipefail
root=$1
stage=$2
receipts=/receipts
package="$root/docs/reviews/U4-A-toolchain-v1"
cd "$root/native"
export CARGO_HOME=/usr/local/cargo
export RUSTUP_HOME=/usr/local/rustup
export RUSTUP_TOOLCHAIN=1.99.0-x86_64-unknown-linux-gnu
export CARGO_NET_OFFLINE=true
export CARGO_TARGET_DIR=/target
run_log() {
  local name=$1
  shift
  local rc=0
  "$@" > "$receipts/$name.log" 2> "$receipts/$name.stderr" || rc=$?
  printf '%s\n' "$rc" > "$receipts/$name.exit"
  return "$rc"
}
run_log "$stage-inputs" sha256sum --check "$package/native-inputs.sha256"
if [ "$stage" = inspect ]; then
  uname -a > "$receipts/container-uname.txt"
  for tool in rustc cargo rustfmt clippy-driver cargo-deny; do
    command -v "$tool"
    readlink -f "$(command -v "$tool")"
  done > "$receipts/tool-paths.txt"
  rustup which rustc >> "$receipts/tool-paths.txt"
  rustup which rustfmt >> "$receipts/tool-paths.txt"
  rustup which clippy-driver >> "$receipts/tool-paths.txt"
  run_log rustc rustc -vV
  run_log cargo cargo -V
  run_log rustfmt cargo fmt --version
  run_log clippy cargo clippy --version
  run_log cargo-deny cargo deny --version
  for tool in rustc cargo rustfmt clippy cargo-deny; do
    cmp "$package/version-receipts/$tool.txt" "$receipts/$tool.log"
  done
  run_log targets rustup target list --installed
  grep -Fx 'x86_64-unknown-linux-gnu' "$receipts/targets.log"
  run_log metadata cargo metadata --locked --offline --all-features --format-version 1 \
    --filter-platform x86_64-unknown-linux-gnu
elif [ "$stage" = checks ]; then
  run_log fmt cargo fmt --all -- --check
  run_log clippy-tests cargo clippy --locked --offline --workspace --all-targets --all-features \
    --target x86_64-unknown-linux-gnu -- -D warnings
  run_log licences cargo deny --locked --offline --all-features --config deny.toml \
    check licenses bans sources
  for mode in debug release; do
    flags=()
    if [ "$mode" = release ]; then flags+=(--release); fi
    run_log "$mode-list" cargo test --locked --offline --workspace --all-targets --all-features \
      --target x86_64-unknown-linux-gnu "${flags[@]}" -- --list
    run_log "$mode-tests" cargo test --locked --offline --workspace --all-targets --all-features \
      --target x86_64-unknown-linux-gnu "${flags[@]}" -- --nocapture
  done
else
  echo "unknown container stage" >&2
  exit 2
fi
