#!/usr/bin/env bash
# Uninstalled CI template. Private publication/access is approved; credentials remain required.
set -euo pipefail
root=${GITHUB_WORKSPACE:?}
package="$root/docs/reviews/U4-B-final-reconciliation-v1"
: "${NATIVE_IMAGE:?}" "${K1_TEST_PLAN:?}" "${RUNNER_TEMP:?}"
[[ "$NATIVE_IMAGE" =~ ^[^[:space:]]+@sha256:[0-9a-f]{64}$ ]]
test -f "$root/$K1_TEST_PLAN"
receipts=$(mktemp -d "$RUNNER_TEMP/u4-native.XXXXXXXX")
printf 'U4_RECEIPTS_DIR=%s\n' "$receipts" >> "${GITHUB_ENV:?}"
# Host interpreter is a guard tool, never the native compiler or a claimed immutable OS.
python3 -c 'import sys; assert sys.version_info >= (3, 11); print(sys.executable); print(sys.version)' \
  > "$receipts/host-python.txt"
sha256sum "$(readlink -f "$(command -v python3)")" "$package/ci_host_guard.py" \
  > "$receipts/host-guard.sha256"
printf '%s\n' "${ImageOS:-unknown}" "${ImageVersion:-unknown}" > "$receipts/host-image.txt"
git -C "$root" rev-parse HEAD > "$receipts/checkout.sha"
test -z "$(git -C "$root" status --porcelain --untracked-files=all)"
python3 "$package/ci_host_guard.py" preflight "$root" "$root/$K1_TEST_PLAN"
docker version > "$receipts/docker-version.txt"
bash "$root/docs/reviews/U4-B-K1-private-ci-v1/private-pull.sh" "$NATIVE_IMAGE" "$receipts"
unset K1_GHCR_READ_TOKEN
replay_test=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["replay_test"])' \
  "$root/$K1_TEST_PLAN")
docker image inspect "$NATIVE_IMAGE" > "$receipts/image-inspect.json"
python3 "$package/ci_host_guard.py" image "$receipts/image-inspect.json" "$NATIVE_IMAGE"
run_container() {
  local stage=$1
  local rc=0
  docker run --rm --pull never --platform linux/amd64 --network none \
    --mount "type=bind,src=$root,dst=$root,readonly" \
    --mount "type=bind,src=$receipts,dst=/receipts" \
    --tmpfs /tmp --tmpfs /target:exec --workdir "$root/native" \
    --entrypoint /bin/bash "$NATIVE_IMAGE" "$package/native-container.sh" "$root" "$stage" "$replay_test" \
    > "$receipts/$stage-container.log" 2>&1 || rc=$?
  printf '%s\n' "$rc" > "$receipts/$stage-container.exit"
  return "$rc"
}
# Do not validate metadata against a different host path: the checkout is mounted at the same path.
run_container inspect
python3 "$package/ci_host_guard.py" metadata "$root" "$receipts/metadata.log" "$root/$K1_TEST_PLAN"
python3 "$package/ci_host_guard.py" metadata-target "$root" "$receipts/metadata-target.log" "$root/$K1_TEST_PLAN"
run_container checks
python3 "$package/ci_host_guard.py" results "$root" "$receipts" "$root/$K1_TEST_PLAN"
test -z "$(git -C "$root" status --porcelain --untracked-files=all)"
echo "Verified native commands; receipts: $receipts"
