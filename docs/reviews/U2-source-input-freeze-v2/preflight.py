"""Read-only Git/source/input/environment check; never computes oracle workloads."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from scripts import u2_inputs, vendor_rk as vendor

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-acceptance', action='store_true')
    args = parser.parse_args()
    spec = json.loads((HERE / 'inventory.json').read_text())
    assert Path.cwd().resolve() == ROOT
    assert not os.environ.get('PARAMS'), 'Unexpected PARAMS override'
    if args.require_acceptance:
        acceptance = json.loads((HERE.parent / 'U2-source-input-freeze-v2-acceptance.json').read_text())
        assert acceptance['decision'] == 'accepted'
        assert acceptance['inventory_sha256'] == digest(HERE / 'inventory.json')
        assert acceptance['input_manifest_sha256'] == spec['input_manifest_sha256']
    for name, expected in spec['review_files_sha256'].items():
        assert digest(HERE / name) == expected, ('reviewed wrapper/preflight metadata drift', name)
    # Git supplies the reviewed baseline plus exact source/test delta, not a new source manifest.
    with tempfile.TemporaryDirectory(prefix='u2-freeze-v2-index-') as temp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temp) / 'index'))
        # Reconstruct from reachable baseline/blobs; no reliance on an orphan temporary tree.
        source = json.loads((HERE / 'source-tree.json').read_text())
        subprocess.run(['git', 'read-tree', source['base_commit']], cwd=ROOT, env=env, check=True)
        for path, blob in source['changed_git_blobs'].items():
            subprocess.run(['git', 'update-index', '--add', '--cacheinfo', '100644', blob, path], cwd=ROOT, env=env, check=True)
        tree = subprocess.check_output(['git', 'write-tree'], cwd=ROOT, env=env, text=True).strip()
        assert tree == spec['source_tree'], 'Reviewed Git source tree identity changed'
        refreshed = subprocess.run(['git', 'update-index', '--refresh'], cwd=ROOT, env=env, capture_output=True, text=True)
        assert refreshed.returncode == 0, ('reviewed source differs', refreshed.stdout[:2000], refreshed.stderr[:1000])
        diff = subprocess.check_output(['git', 'diff-files', '--name-only'], cwd=ROOT, env=env, text=True)
        assert not diff, ('reviewed Git source tree differs', diff)
    u2_inputs.load_inputs(HERE / 'inputs', spec['input_manifest_sha256'], check_support=True)
    old = ROOT / 'contract/vendor' / ('rk-sim@' + vendor.PIN)
    assert digest(old / 'MANIFEST.json') == spec['previous_adopted_manifest_sha256']
    vendor.check_manifest(old)
    rk = Path(spec['rk_clone'])
    vendor.check_clone(rk, vendor.PIN)
    env = vendor.oracle_environment(rk)
    assert env['UV_PROJECT_ENVIRONMENT'] == spec['oracle_environment']
    vendor.verify_oracle_environment(rk, env)
    metadata = vendor.record_oracle_environment(rk, env)
    expected = json.loads((HERE / 'oracle-environment-preflight.json').read_text())['metadata']
    assert metadata == expected, 'Oracle environment changed since review'
    print(json.dumps(dict(status='passed', source_tree=spec['source_tree'], input_manifest_sha256=spec['input_manifest_sha256'], pin=vendor.PIN, environment_metadata=metadata), sort_keys=True))

if __name__ == '__main__':
    main()
