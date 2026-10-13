#!/usr/bin/env bash
# Human-only protected installation. --check never edits, stages or commits.
set -euo pipefail
mode="${1:---check}"
reviewed_commit="${2:-}"
reviewed_digest="${3:-}"
expected_patch_sha256=c3b8beef81e223a852c48f1d59bfd40bf992e5e7a2151d440931cb89e9930e63
if [[ "$mode" != --check && "$mode" != --commit ]]; then
  echo 'Usage: bash human-install.sh --check [reviewed-commit digest] | --commit <reviewed-package-commit> <reviewed-patch-sha256>' >&2
  exit 2
fi
repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
package_dir=docs/reviews/U3-plan-amendment-v2
if [[ "$(git branch --show-current)" != main ]]; then
  echo 'STOP: expected main' >&2; exit 1
fi
if [[ "$mode" == --commit ]]; then
  if [[ -z "$reviewed_commit" || "$reviewed_digest" != "$expected_patch_sha256" ]]; then
    echo 'STOP: reviewed package commit and exact reviewed patch digest required' >&2; exit 1
  fi
  if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
    echo 'STOP: preserve and reconcile worktree/index changes first' >&2; exit 1
  fi
fi
python3 - "$package_dir" "$reviewed_commit" "$reviewed_digest" "$expected_patch_sha256" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

package = Path(sys.argv[1])
review = json.loads((package / 'review.json').read_text())
reviewed_commit, reviewed_digest, expected_digest = sys.argv[2:5]
patch = package / 'plan.patch'
if hashlib.sha256(patch.read_bytes()).hexdigest() != expected_digest or review['patch_sha256'] != expected_digest:
    raise SystemExit('STOP: patch differs from the pinned reviewed digest')
if bool(reviewed_commit) != bool(reviewed_digest):
    raise SystemExit('STOP: provide both reviewed commit and digest')
if reviewed_commit:
    if reviewed_digest != expected_digest:
        raise SystemExit('STOP: supplied reviewed digest mismatch')
    subprocess.run(['git', 'merge-base', '--is-ancestor', reviewed_commit, 'HEAD'], check=True)
    if subprocess.check_output(['git', 'diff', '--name-only', reviewed_commit, 'HEAD', '--', str(package)]):
        raise SystemExit('STOP: package changed since reviewed commit; new recheck required')
    committed_patch = subprocess.check_output(['git', 'show', reviewed_commit + ':' + str(patch)])
    if hashlib.sha256(committed_patch).hexdigest() != expected_digest:
        raise SystemExit('STOP: reviewed commit does not contain the pinned patch')
    # The live installer and metadata must also be the exact committed package files.
    for path in sorted(package.rglob('*')):
        if path.is_file():
            committed = subprocess.check_output(['git', 'show', reviewed_commit + ':' + str(path)])
            if committed != path.read_bytes():
                raise SystemExit('STOP: live package differs from reviewed bytes: ' + str(path))
subprocess.run(['git', 'merge-base', '--is-ancestor', review['baseline_commit'], 'HEAD'], check=True)
if subprocess.check_output(['git', 'diff', '--cached', '--name-only']):
    raise SystemExit('STOP: index is not empty')
allowed = (
    'docs/reviews/U3-post-fork-plan-review-v1/',
    'docs/reviews/U3-plan-amendment-v2/',
    'docs/reviews/U3-artifact-dependency-repair-proposal-v2/',
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
