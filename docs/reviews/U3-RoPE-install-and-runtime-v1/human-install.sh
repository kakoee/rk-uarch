#!/usr/bin/env bash
# Human invocation only. --check performs repository-read-only preflight.
set -euo pipefail
python3 - "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" "$@" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

folder = Path(sys.argv[1]).resolve()
args = sys.argv[2:]
if args not in ([], ['--check']):
    raise SystemExit('Usage: bash human-install.sh [--check]')
primary = folder.parents[2]
root = primary.parent / 'rk-uarch-u3-a'
patch_relative = 'docs/reviews/U3-RoPE-protected-patch-v1/protected.patch'
base = '531d9c923c30dd465cf56c8a5865cd9ce62cdd84'
proposal = '7454ececbdc03cddd83194ac756a41cd06d99392'
digest = '8a02ed6cf56846c6f688d195b068aadd19bb2bab11fe751a8af36d8408e04169'
message = 'feat(contract): install approved U0022 additive rotary v2 carriers'

def require(condition, explanation):
    if not condition:
        raise SystemExit('STOP: ' + explanation)

def git(*arguments):
    return subprocess.check_output(['git', '-C', str(root), *arguments])

def text(*arguments):
    return git(*arguments).decode().strip()

require(root.is_dir(), 'Lane A clone is missing')
require(Path(text('rev-parse', '--show-toplevel')).resolve() == root, 'unexpected clone')
require(text('branch', '--show-current') == 'main', 'Lane A must be on main')
require(text('remote', 'get-url', 'origin') == 'https://github.com/kakoee/rk-uarch.git', 'unexpected origin')
require(not text('status', '--porcelain', '--untracked-files=all'), 'Lane A clone/index must be clean')
for state in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
    require(not Path(text('rev-parse', '--path-format=absolute', '--git-path', state)).exists(), 'unfinished Git operation')
for ancestor in (base, proposal, '53435927497eb3e4552e32e2c5e887e0bcb05ddc'):
    require(subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', ancestor, 'HEAD']).returncode == 0, 'Lane A must integrate the reviewed published main first')
acceptance = 'docs/reviews/U3-RoPE-install-and-runtime-v1/README.md'
require(git('show', 'HEAD:' + acceptance) == (folder / 'README.md').read_bytes(), 'accepted installation record absent or changed')
require(not subprocess.run(['git', '-C', str(root), 'config', '--get', 'core.hooksPath'], capture_output=True).stdout.strip(), 'unexpected custom hooks path')
hook = Path(text('rev-parse', '--path-format=absolute', '--git-path', 'hooks/pre-commit'))
require(hook.is_file() and os.access(hook, os.X_OK), 'normal pre-commit hook is missing')
require(all(name in hook.read_text() for name in ('scripts/hooks/human_owned.sh', 'scripts/hooks/frozen_predictions.sh')), 'normal ownership/prediction hooks are missing')
patch = (root / patch_relative).read_bytes()
require(hashlib.sha256(patch).hexdigest() == digest, 'approved patch digest changed')
paths = [line[6:] for line in patch.decode().splitlines() if line.startswith('+++ b/')]
require(len(paths) == len(set(paths)) == 17, 'unexpected patch path inventory')
require(all(p.startswith(('contract/', 'docs/decisions/')) and '..' not in Path(p).parts for p in paths), 'unexpected patch target')
require(not text('diff', base, 'HEAD', '--', *paths), 'protected destinations changed since reviewed base')
parent = text('rev-parse', 'HEAD')
subprocess.run(['git', '-C', str(root), 'apply', '--check', '--index', '--unidiff-zero', str(root / patch_relative)], check=True)
# Compute expected contents in disposable scratch; never install protected paths in --check.
with tempfile.TemporaryDirectory(prefix='u3-human-install-check-') as scratch:
    scratch_path = Path(scratch)
    for path in paths:
        found = subprocess.run(['git', '-C', str(root), 'show', parent + ':' + path], capture_output=True)
        if found.returncode == 0:
            destination = scratch_path / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(found.stdout)
        else:
            require(not (root / path).exists(), 'new target already exists: ' + path)
    subprocess.run(['git', 'apply', '--unidiff-zero', str(root / patch_relative)], cwd=scratch, check=True)
    expected = {path: (scratch_path / path).read_bytes() for path in paths}
print(json.dumps({'decision': 'U3-RoPE-install-and-runtime-v1', 'preflight': 'passed', 'repository': str(root), 'parent': parent, 'paths': len(paths), 'patch_sha256': digest}, indent=2))
if args == ['--check']:
    print('Read-only preflight complete. No live installation, staging, commit or push.')
    raise SystemExit(0)
require(text('rev-parse', 'HEAD') == parent and not text('status', '--porcelain', '--untracked-files=all'), 'clone moved during preflight')
subprocess.run(['git', '-C', str(root), 'apply', '--index', '--unidiff-zero', str(root / patch_relative)], check=True)
require(set(text('diff', '--cached', '--name-only').splitlines()) == set(paths), 'unexpected staged paths')
for path, contents in expected.items():
    require(git('show', ':' + path) == contents and (root / path).read_bytes() == contents, 'installed bytes differ: ' + path)
subprocess.run(['git', '-C', str(root), 'diff', '--cached', '--check'], check=True)
require(text('rev-parse', 'HEAD') == parent, 'HEAD moved before commit')
# Only this human non-check invocation authorizes the normal protected-path hook.
environment = os.environ.copy()
environment['UARCH_HUMAN'] = '1'
subprocess.run(['git', '-C', str(root), 'commit', '-m', message], check=True, env=environment)
commit = text('rev-parse', 'HEAD')
require(text('rev-parse', 'HEAD^') == parent, 'unexpected commit parent')
require(set(text('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines()) == set(paths), 'unexpected committed paths')
for path, contents in expected.items():
    require(git('show', 'HEAD:' + path) == contents, 'committed bytes differ: ' + path)
require(not text('status', '--porcelain', '--untracked-files=all'), 'clone not clean after commit')
print(json.dumps({'decision': 'U3-RoPE-install-and-runtime-v1', 'status': 'human installation and local commit verified', 'repository': str(root), 'branch': 'main', 'parent': parent, 'commit': commit, 'tree': text('rev-parse', 'HEAD^{tree}'), 'paths': len(paths), 'patch_sha256': digest, 'push_generation_adoption_performed': False}, indent=2))
print('STOP: return this receipt for coordinator verification. Do not push; source currentness is intentionally pending the combined U0002 lifecycle.')
PY
