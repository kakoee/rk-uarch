"""Audit the human-generated v2 candidate without adoption or oracle execution."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

from scripts import u2_inputs as inputs, vendor_rk as vendor
from tests.u2_refresh import audit_candidate

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RUN = ROOT / 'docs/reviews/U2-real-generation-v2'
FREEZE = ROOT / 'docs/reviews/U2-source-input-freeze-v2'
NEW = RUN / 'candidate'
OLD = inputs.ADOPTED
NEW_MANIFEST = 'f8220c9457226562040e5646835c3073acd2f58cd7631a5eb9e74632e60cc96e'
OLD_MANIFEST = '2d15afd7dd80124f70d387bc7cde4addda29162cd49370d40da7b99830709b44'
INPUT = '9a30b29029a32339dfc6062e138cebc23f7f1474044b414068dd9c8113c1dca0'
COMMIT = '14fa0ede963c03ebe4bdafa3b396e7d513d0f24f'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def inventory(root):
    assert not root.is_symlink()
    assert not any(p.is_symlink() for p in root.rglob('*'))
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}

def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == COMMIT
    assert not subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT)
    assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT)
    assert sha(NEW / 'MANIFEST.json') == NEW_MANIFEST
    assert sha(OLD / 'MANIFEST.json') == OLD_MANIFEST
    assert not (NEW / 'SYNTHETIC-REFERENCE').exists()
    acceptance = json.loads((FREEZE.parent / 'U2-source-input-freeze-v2-acceptance.json').read_text())
    assert acceptance['decision'] == 'accepted'
    assert acceptance['inventory_sha256'] == sha(FREEZE / 'inventory.json') == 'e3ab3eef76b5483b618c9ba73a18d47a24c59f1faf9e494d4795c87563d34c3d'
    assert acceptance['input_manifest_sha256'] == INPUT
    for status in ('created', 'verified-identical'):
        assert (RUN / (status + '.log')).read_text().strip() == f'{status}: 48 files at {NEW}'
    preflights = [json.loads((RUN / n).read_text()) for n in ('preflight.json', 'preflight-between.json', 'preflight-after.json')]
    assert preflights[0] == preflights[1] == preflights[2]
    assert preflights[0]['status'] == 'passed' and preflights[0]['input_manifest_sha256'] == INPUT
    assert preflights[0]['source_tree'] == acceptance['source_tree'] == '36f24dc4b0a1a27775f6a566fb913ed3d8cd177e'
    assert (RUN / 'local-HEAD.txt').read_text().strip() == COMMIT
    assert (RUN / 'local-branch.txt').read_text().strip() == 'u2/integration'
    assert (RUN / 'candidate-manifest-sha256.txt').read_text().strip() == f'{NEW_MANIFEST}  {NEW / "MANIFEST.json"}'
    checked = audit_candidate(NEW)
    assert checked == json.loads((RUN / 'raw-inspection.json').read_text())
    delta = inputs.compare_snapshots(OLD, NEW)
    assert delta == json.loads((RUN / 'semantic-diff.json').read_text())
    assert delta['rows'] == dict(added=[], changed=[], removed=[], unchanged=1008)
    assert delta['descriptors'] == []
    assert delta['refusals']['before'] == delta['refusals']['after']
    assert len(delta['refusals']['after']) == 4
    a, b = inventory(OLD), inventory(NEW)
    assert len(a) == len(b) == 48 and a.keys() == b.keys()
    changed = sorted(p for p in a if a[p] != b[p])
    assert changed == ['MANIFEST.json', 'u2-inputs/SHA256SUMS', 'u2-inputs/support-files.json']
    assert (NEW / 'parity/fixtures.json').read_bytes() == (OLD / 'parity/fixtures.json').read_bytes()
    assert (NEW / 'parity/refusals.json').read_bytes() == (OLD / 'parity/refusals.json').read_bytes()
    frozen_inputs = inventory(FREEZE / 'inputs')
    assert inventory(NEW / 'u2-inputs') == frozen_inputs
    assert len(frozen_inputs) == 24 and sha(NEW / 'u2-inputs/SHA256SUMS') == INPUT
    inputs.load_inputs(NEW / 'u2-inputs', INPUT, check_support=True)
    sa = json.loads((OLD / 'u2-inputs/support-files.json').read_text())
    sb = json.loads((NEW / 'u2-inputs/support-files.json').read_text())
    assert len(sa) == len(sb) == 84 and sa.keys() == sb.keys()
    assert [p for p in sa if sa[p] != sb[p]] == ['src/rkuarch/table/build.py']
    metadata = json.loads((NEW / 'GENERATOR.json').read_text())
    assert metadata == json.loads((OLD / 'GENERATOR.json').read_text())
    assert metadata['environment'] == preflights[0]['environment_metadata']
    assert metadata['script_sha256'] == sha(ROOT / 'scripts/vendor_rk.py')
    assert metadata['oracle_program_sha256'] == hashlib.sha256(vendor.ORACLE_PROGRAM.encode()).hexdigest()
    pinned = []
    for path in vendor.SOURCES:
        raw = subprocess.check_output(['git', '-C', '/home/jjaff/AI-infra-simulation/rk-sim-u1-pin', 'show', f'{vendor.PIN}:{path}'])
        assert raw == (NEW / path).read_bytes(), path
        pinned.append(path)
    # Verify the complete predecessor is already preserved by reachable Git history.
    rel = OLD.relative_to(ROOT).as_posix()
    for path in a:
        assert subprocess.check_output(['git', 'show', f'{COMMIT}:{rel}/{path}'], cwd=ROOT) == (OLD / path).read_bytes()
    evidence = {p.name: sha(p) for p in sorted(RUN.iterdir()) if p.is_file()}
    record = dict(status='complete candidate audit passed; adoption awaits explicit approval', audited_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), audit_source_sha256=sha(Path(__file__)), source_commit=COMMIT, source_tree=acceptance['source_tree'], old_manifest_sha256=OLD_MANIFEST, candidate_manifest_sha256=NEW_MANIFEST, input_manifest_sha256=INPUT, human_generation_pair=dict(created_and_verified_identical=True, all_three_preflights_identical=True, generation_evidence_sha256=evidence), file_counts=dict(old=48, new=48, unchanged=45, changed=3, added=0, removed=0), changed_files=delta['files'], workload_rows=dict(unchanged=1008, added=0, removed=0, changed=0, raw_fixture_bytes_identical=True), refusals=dict(unchanged=4, raw_bytes_identical=True, source_bindings_checked=True), generator_metadata_unchanged=True, environment_and_scope_unchanged=True, pinned_upstream_sources_verified=pinned, frozen_input_files_exact=24, support_files=84, support_changed=['src/rkuarch/table/build.py'], raw_inspection=checked, predecessor_preserved_in_git=COMMIT + ':' + rel, canonical_adopted_unchanged=True, oracle_computation_by_coordinator=False, adopted_consumption_executed=False, adoption_performed=False)
    (HERE / 'audit.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: record[k] for k in ('status', 'candidate_manifest_sha256', 'file_counts', 'workload_rows', 'refusals', 'generator_metadata_unchanged', 'adoption_performed')}, indent=2))

if __name__ == '__main__':
    main()
