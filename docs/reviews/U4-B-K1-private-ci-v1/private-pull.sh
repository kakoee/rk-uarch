#!/usr/bin/env bash
# Authorized private pull only; executable CI installation still requires observed access.
set +x
set -euo pipefail
: "${K1_GHCR_USER:?}" "${K1_GHCR_READ_TOKEN:?}" "${RUNNER_TEMP:?}"
image=$1
receipts=$2
[[ "${GITHUB_EVENT_NAME:-}" = push && "${GITHUB_REF:-}" = refs/heads/main ]]
[[ "$image" =~ ^ghcr\.io/kakoee/rk-uarch-k1-builder@sha256:[0-9a-f]{64}$ ]]
umask 077
config=$(mktemp -d "$RUNNER_TEMP/k1-ghcr.XXXXXXXX")
trap 'rm -rf -- "$config"' EXIT
trap 'exit 130' HUP INT TERM
# A new config avoids persistent desktop/runner credential helpers. No credential is logged.
printf '%s' "$K1_GHCR_READ_TOKEN" | docker --config "$config" login ghcr.io \
  --username "$K1_GHCR_USER" --password-stdin > "$receipts/registry-login.log" 2>&1
unset K1_GHCR_READ_TOKEN
docker --config "$config" pull --platform linux/amd64 "$image" \
  > "$receipts/pull.log" 2>&1
# EXIT removes credentials on success and failure, before native code can execute.
