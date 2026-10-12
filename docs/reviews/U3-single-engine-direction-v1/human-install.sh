#!/usr/bin/env bash
# Human-only protected documentation install; --check is read-only.
set -euo pipefail
mode="${1:-}"
package_commit="${2:-}"
if [[ "$mode" != --check && "$mode" != --commit ]] || [[ -z "$package_commit" ]]; then
  echo "Usage: bash human-install.sh --check|--commit <exact-package-commit>" >&2
  exit 2
fi
repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
package_dir=docs/reviews/U3-single-engine-direction-v1
if [[ "$(git branch --show-current)" != main ]]; then echo 'STOP: expected main' >&2; exit 1; fi
if [[ "$(git rev-parse HEAD)" != "$package_commit" ]]; then echo 'STOP: HEAD differs from package commit; reconcile first' >&2; exit 1; fi
if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then echo 'STOP: worktree/index not clean; preserve and reconcile changes' >&2; exit 1; fi
python3 - "$package_dir" <<'PY'
import hashlib
import json
import pathlib
import subprocess
import sys

package = pathlib.Path(sys.argv[1])
review = json.loads((package / 'review.json').read_text())
patch = package / 'architecture.patch'
if hashlib.sha256(patch.read_bytes()).hexdigest() != review['patch_sha256']:
    raise SystemExit('STOP: patch digest mismatch')
extra = subprocess.check_output(
    ['git', 'diff', '--name-only', review['checkpoint_commit'], 'HEAD', '--', '.',
     f':(exclude){package}'], text=True,
).splitlines()
if extra:
    raise SystemExit('STOP: changes since checkpoint outside package; reconcile first')
paths = subprocess.check_output(['git', 'apply', '--numstat', str(patch)], text=True)
actual = [line.split('\t', 2)[2] for line in paths.splitlines()]
if actual != review['paths']:
    raise SystemExit('STOP: patch scope mismatch')
print(f'Preflight passed: exact {len(actual)}-path documentation amendment; no runtime/support changes.')
PY
git apply --check "$package_dir/architecture.patch"
if [[ "$mode" == --check ]]; then
  echo 'CHECK ONLY: no installation, staging, commit or push performed.'
  exit 0
fi
if [[ "${UARCH_HUMAN:-0}" != 1 ]]; then echo 'STOP: human must invoke with UARCH_HUMAN=1' >&2; exit 1; fi
# Apply and stage the exact patch. Do not amend, force, skip hooks or reset on failure.
git apply --index "$package_dir/architecture.patch"
git diff --cached --check
git commit -m "docs: adopt one progressive simulator and scoped validation plan"
git show --stat --oneline HEAD
echo 'STOP: protected documentation committed locally. Return this receipt; push and runtime implementation remain separate.'
