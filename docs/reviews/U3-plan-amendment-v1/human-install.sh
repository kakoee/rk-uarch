#!/usr/bin/env bash
# Human-only protected installation. --check never edits, stages or commits.
set -euo pipefail
mode="${1:---check}"
package_commit="${2:-}"
if [[ "$mode" != --check && "$mode" != --commit ]]; then
  echo 'Usage: bash human-install.sh --check | --commit <exact-package-commit>' >&2
  exit 2
fi
repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
package_dir=docs/reviews/U3-plan-amendment-v1
if [[ "$(git branch --show-current)" != main ]]; then
  echo 'STOP: expected main' >&2; exit 1
fi
if [[ "$mode" == --commit ]]; then
  if [[ -z "$package_commit" || "$(git rev-parse HEAD)" != "$package_commit" ]]; then
    echo 'STOP: exact committed package HEAD required; reconcile before installation' >&2; exit 1
  fi
  if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
    echo 'STOP: preserve and reconcile worktree/index changes first' >&2; exit 1
  fi
fi
python3 - "$package_dir" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

package = Path(sys.argv[1])
review = json.loads((package / 'review.json').read_text())
patch = package / 'plan.patch'
if hashlib.sha256(patch.read_bytes()).hexdigest() != review['patch_sha256']:
    raise SystemExit('STOP: patch digest mismatch')
subprocess.run(['git', 'merge-base', '--is-ancestor', review['baseline_commit'], 'HEAD'], check=True)
if subprocess.check_output(['git', 'diff', '--cached', '--name-only']):
    raise SystemExit('STOP: index is not empty')
allowed = (
    'docs/reviews/U3-post-fork-plan-review-v1/',
    'docs/reviews/U3-plan-amendment-v1/',
    'docs/reviews/U3-artifact-dependency-repair-proposal-v1/',
)
changed = subprocess.check_output(
    ['git', 'diff', '--name-only', review['baseline_commit']], text=True
).splitlines()
untracked = subprocess.check_output(
    ['git', 'ls-files', '--others', '--exclude-standard'], text=True
).splitlines()
if any(not name.startswith(allowed) for name in changed + untracked):
    raise SystemExit('STOP: changes outside reviewed documentation package; reconcile')
numstat = subprocess.check_output(['git', 'apply', '--numstat', str(patch)], text=True)
actual = [line.split('\t', 2)[2] for line in numstat.splitlines()]
if actual != [item['path'] for item in review['paths']]:
    raise SystemExit('STOP: patch path selection mismatch')
for item in review['paths']:
    path = Path(item['path'])
    if path.is_symlink():
        raise SystemExit('STOP: target symlink')
    current = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    if current != item['before_sha256']:
        raise SystemExit('STOP: target preimage changed: ' + str(path))
for name, digest in review['review_inputs'].items():
    if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest:
        raise SystemExit('STOP: review input changed: ' + name)
print(f"Preflight passed: exact {len(actual)}-path documentation amendment; no runtime/support edits.")
PY
git apply --check "$package_dir/plan.patch"
if [[ "$mode" == --check ]]; then
  echo 'CHECK ONLY: no installation, staging, commit or push.'
  exit 0
fi
if [[ "${UARCH_HUMAN:-0}" != 1 ]]; then
  echo 'STOP: the human must invoke with UARCH_HUMAN=1' >&2; exit 1
fi
git apply --index "$package_dir/plan.patch"
python3 - "$package_dir" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

review = json.loads((Path(sys.argv[1]) / 'review.json').read_text())
actual = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], text=True).splitlines()
if actual != [item['path'] for item in review['paths']]:
    raise SystemExit('STOP: staged scope changed; preserve state for reconciliation')
for item in review['paths']:
    index_bytes = subprocess.check_output(['git', 'show', ':' + item['path']])
    if hashlib.sha256(index_bytes).hexdigest() != item['after_sha256']:
        raise SystemExit('STOP: staged target bytes changed')
print('Exact staged target bytes verified.')
PY
git diff --cached --check
git commit -m 'docs: align progressive engine delivery with consumers and silicon readiness'
git show --stat --oneline HEAD
echo 'STOP: protected documentation committed locally. Return this receipt; push and lane implementation remain separate.'
