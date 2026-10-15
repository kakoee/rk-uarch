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
path = 'docs/decisions/U0011-the-native-engine-core.md'
expected_patch = '3dbe69f47765089d67fbd5badf5c130ee2609c04bf6022a03fc899b61d47bbc0'
approved = '448a3fb7e7f5eca2c5218ea1bd768af6e8d1cc94'


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
for name in ('human-install.sh', 'acceptance.md', 'next-decision.md', 'adr-identity.json', 'protected-adr.patch'):
    data = (folder / name).read_bytes()
    require(data == git('show', args.package_commit + ':' + relative + '/' + name), 'package changed: ' + name)
    require(data == git('show', 'HEAD:' + relative + '/' + name), 'package not committed: ' + name)
for name in ('next-decision.md', 'adr-identity.json', 'protected-adr.patch'):
    require((folder / name).read_bytes() == git('show', approved + ':' + relative + '/' + name),
            'approved proposal changed: ' + name)
for peer in ('docs/reviews/U4-A-M-package-v1', 'docs/reviews/U4-A-toolchain-v1',
             'docs/reviews/U4-B-final-reconciliation-v1'):
    require(not text('diff', '1a56ff22068ded35cac944fd8c1de8ffde9cc86d', 'HEAD', '--', peer),
            'accepted peer package changed: ' + peer)
hook = Path(text('rev-parse', '--path-format=absolute', '--git-path', 'hooks/pre-commit'))
normal = Path(text('rev-parse', '--absolute-git-dir')) / 'hooks/pre-commit'
require(hook.resolve() == normal.resolve() and hook.is_file() and os.access(hook, os.X_OK),
        'normal executable pre-commit hook required')
require(all(s in hook.read_text() for s in ('scripts/hooks/human_owned.sh', 'scripts/hooks/frozen_predictions.sh')),
        'normal ownership/prediction hook calls required')
meta = json.loads((folder / 'adr-identity.json').read_text())
patch = folder / 'protected-adr.patch'
require(hashlib.sha256(patch.read_bytes()).hexdigest() == expected_patch == meta['patch_sha256'],
        'approved patch digest mismatch')
require([line[6:] for line in patch.read_text().splitlines() if line.startswith('+++ b/')] == [path],
        'unexpected patch target')
require(meta['path'] == path and hashlib.sha256((root / path).read_bytes()).hexdigest() == meta['before_sha256'],
        'ADR before-image changed or already installed')
parent = text('rev-parse', 'HEAD')
git('apply', '--check', '--index', str(patch))
with tempfile.TemporaryDirectory(prefix='u4-adr-preflight-') as tmp:
    dest = Path(tmp) / path
    dest.parent.mkdir(parents=True)
    dest.write_bytes((root / path).read_bytes())
    subprocess.run(['git', 'apply', str(patch)], cwd=tmp, check=True)
    expected = dest.read_bytes()
require(hashlib.sha256(expected).hexdigest() == meta['after_sha256'], 'ADR postimage mismatch')
print(json.dumps({'decision': 'U4-M-and-K1-release-v1', 'preflight': 'passed', 'parent': parent,
                  'paths': [path], 'patch_sha256': expected_patch}, indent=2), flush=True)
if args.check_only:
    print('Read-only preflight complete; no live installation, staging, commit or push.')
    raise SystemExit(0)
require(clean() and text('rev-parse', 'HEAD') == parent, 'repository moved during preflight')
git('apply', '--index', str(patch))
require(text('diff', '--cached', '--name-only').splitlines() == [path], 'unexpected staged paths')
require(git('show', ':' + path) == expected and (root / path).read_bytes() == expected, 'installed bytes mismatch')
git('diff', '--cached', '--check')
subprocess.run(['git', '-C', str(root), 'commit', '-m',
                'docs(u4): accept exact M carriers and release private K1'], check=True)
require(text('rev-parse', 'HEAD^') == parent, 'unexpected commit parent')
require(text('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines() == [path],
        'unexpected committed paths')
require(git('show', 'HEAD:' + path) == expected and clean(), 'commit bytes or clean-state check failed')
print(json.dumps({'decision': 'U4-M-and-K1-release-v1', 'status': 'human ADR installation verified',
                  'commit': text('rev-parse', 'HEAD'), 'parent': parent,
                  'tree': text('rev-parse', 'HEAD^{tree}'), 'paths': [path],
                  'M_installation_generation_adoption_native_execution_push': False}, indent=2))
print('STOP: return this receipt. Coordinator verifies and publishes before lanes continue.')
PY
