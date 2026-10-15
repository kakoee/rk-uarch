#!/usr/bin/env bash
# Human executes installation. --check-only is read-only for the live repository.
set -euo pipefail
python3 - "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" "$@" <<'PY'
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

folder = Path(sys.argv[1]).resolve()
root = folder.parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--package-commit', required=True)
parser.add_argument('--check-only', action='store_true')
args = parser.parse_args(sys.argv[2:])
relative = folder.relative_to(root).as_posix()
expected_patch = 'c49135cc363f230b4f06c264fcd8064cc416ad88dd116e01fd97852076b414e1'
approved = 'e9a740f77d42527bf8790ea26eaaf46faa525930'


def require(condition, message):
    if not condition:
        raise SystemExit('STOP: ' + message)


def git(*argv):
    result = subprocess.run(['git', '-C', str(root), *argv], capture_output=True)
    require(result.returncode == 0, result.stderr.decode().strip() or 'Git check failed')
    return result.stdout


def text(*argv):
    return git(*argv).decode().strip()


def ancestor(commit):
    return subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', commit, 'HEAD'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def clean():
    return not text('status', '--porcelain', '--untracked-files=no')


require(args.check_only or os.environ.get('UARCH_HUMAN') == '1',
        'human installation requires your explicit UARCH_HUMAN=1')
require(Path(text('rev-parse', '--show-toplevel')).resolve() == root, 'unexpected repository root')
require(text('branch', '--show-current') == 'main', 'must be on main')
require(text('remote', 'get-url', 'origin') == 'https://github.com/kakoee/rk-uarch.git', 'unexpected origin')
require(clean(), 'tracked worktree and index must be clean; preserve unrelated work')
for state in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
    require(not Path(text('rev-parse', '--path-format=absolute', '--git-path', state)).exists(),
            'unfinished Git operation')
require(ancestor(approved) and ancestor(args.package_commit), 'approved/package commit must be an ancestor')
for name in ('human-install.sh', 'acceptance.md', 'identity.json', 'documentation.patch', 'proposed-U0024.md'):
    data = (folder / name).read_bytes()
    require(data == git('show', args.package_commit + ':' + relative + '/' + name), 'package changed: ' + name)
    require(data == git('show', 'HEAD:' + relative + '/' + name), 'package not committed: ' + name)
hook = Path(text('rev-parse', '--path-format=absolute', '--git-path', 'hooks/pre-commit'))
normal = Path(text('rev-parse', '--absolute-git-dir')) / 'hooks/pre-commit'
require(hook.resolve() == normal.resolve() and hook.is_file() and os.access(hook, os.X_OK),
        'normal executable pre-commit hook required')
require(all(s in hook.read_text() for s in ('scripts/hooks/human_owned.sh', 'scripts/hooks/frozen_predictions.sh')),
        'normal ownership/prediction hook calls required')
meta = json.loads((folder / 'identity.json').read_text())
patch = folder / 'documentation.patch'
require(meta['base_commit'] == approved, 'wrong approved base')
require(hashlib.sha256(patch.read_bytes()).hexdigest() == expected_patch == meta['patch_sha256'],
        'approved patch digest mismatch')
paths = [item['path'] for item in meta['paths']]
require(len(paths) == len(set(paths)) == 8, 'expected exactly eight targets')
require([line[6:] for line in patch.read_text().splitlines() if line.startswith('+++ b/')] == paths,
        'unexpected patch targets')
for item in meta['paths']:
    dest = root / item['path']
    require(not dest.is_symlink(), 'target must not be a symlink')
    if item['before_sha256'] is None:
        require(not dest.exists(), 'new ADR already exists')
    else:
        require(dest.is_file() and hashlib.sha256(dest.read_bytes()).hexdigest() == item['before_sha256'],
                'before-image changed: ' + item['path'])
parent = text('rev-parse', 'HEAD')
git('apply', '--check', '--index', str(patch))
expected = {}
with tempfile.TemporaryDirectory(prefix='u0024-preflight-') as tmp:
    for item in meta['paths']:
        if item['before_sha256'] is not None:
            dest = Path(tmp) / item['path']
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((root / item['path']).read_bytes())
    subprocess.run(['git', 'apply', str(patch)], cwd=tmp, check=True)
    for item in meta['paths']:
        data = (Path(tmp) / item['path']).read_bytes()
        require(hashlib.sha256(data).hexdigest() == item['after_sha256'], 'postimage mismatch: ' + item['path'])
        expected[item['path']] = data
require(expected[paths[0]] == (folder / 'proposed-U0024.md').read_bytes(), 'ADR draft mismatch')
print(json.dumps({'decision': 'U0024-local-verification-deferral', 'preflight': 'passed', 'parent': parent,
                  'paths': paths, 'patch_sha256': expected_patch}, indent=2), flush=True)
if args.check_only:
    print('Read-only preflight complete; no live installation, staging, commit or push.')
    raise SystemExit(0)
require(clean() and text('rev-parse', 'HEAD') == parent, 'repository moved during preflight')
git('apply', '--index', str(patch))
require(text('diff', '--cached', '--name-only').splitlines() == sorted(paths), 'unexpected staged paths')
for path in paths:
    require(git('show', ':' + path) == expected[path] and (root / path).read_bytes() == expected[path],
            'installed bytes mismatch: ' + path)
git('diff', '--cached', '--check')
subprocess.run(['git', '-C', str(root), 'commit', '-m',
                'docs: defer native CI infrastructure with reviewed local development'], check=True)
require(text('rev-parse', 'HEAD^') == parent, 'unexpected commit parent')
require(text('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines() == sorted(paths),
        'unexpected committed paths')
for path in paths:
    require(git('show', 'HEAD:' + path) == expected[path], 'committed bytes mismatch: ' + path)
require(clean(), 'tracked worktree/index not clean after commit')
print(json.dumps({'decision': 'U0024-local-verification-deferral', 'status': 'human documentation installation verified',
                  'commit': text('rev-parse', 'HEAD'), 'parent': parent,
                  'tree': text('rev-parse', 'HEAD^{tree}'), 'paths': paths,
                  'runtime_workflow_server_registry_generation_adoption_push': False}, indent=2))
print('STOP: return this receipt. Push and lane continuation remain separate; infrastructure stays deferred.')
PY
