"""Independent final verification over completed v2 runtime outputs; no producers."""
import hashlib
import json
from pathlib import Path
import subprocess
from scripts import u2_inputs as ui
from tests.u2_refresh import audit_candidate, adoption_authority

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def files(root):
    return {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}


def compare(left, right, names):
    size = 0
    for name in sorted(names):
        with (left / name).open('rb') as a, (right / name).open('rb') as b:
            while True:
                x, y = a.read(1048576), b.read(1048576)
                assert x == y, name
                size += len(x)
                if not x:
                    break
    return dict(files=len(names), bytes=size)


def main():
    state = json.loads((HERE / 'runtime-progress.json').read_text())
    assert state['status'] == 'passed'
    assert all(p['status'] == 'passed' for p in state['phases'])
    out = Path(state['output_root'])
    manifest = out / 'SHA256SUMS'
    assert digest(manifest) == state['artifact_manifest']['sha256']
    entries = {}
    for line in manifest.read_text().splitlines():
        sha, name = line.split('  ', 1)
        assert name not in entries and not Path(name).is_absolute() and '..' not in Path(name).parts
        assert digest(out / name) == sha, name
        entries[name] = sha
    assert set(entries) == files(out) - {'SHA256SUMS'}
    assert len(entries) == state['artifact_manifest']['entries']
    names = files(out / 'report')
    assert names == files(out / 'replay-report')
    replay = compare(out / 'report', out / 'replay-report', names)
    repeat = compare(out / 'repeat', out / 'report', files(out / 'repeat'))
    assert replay['files'] == 3316 and repeat['files'] == 6
    original = json.loads((out / 'report/table.json').read_text())
    saved = json.loads((out / 'replay-report/table.json').read_text())
    assert original == saved and len(original['rows']) == 24
    conditions = original['provenance']['conditional_on']
    assert len(conditions) == 59
    assert [c['path'] for c in conditions] == sorted({c['path'] for c in conditions})
    assert state['RR_C1']['fresh_table_hash'] == state['RR_C1']['replayed_table_hash'] == original['table_hash']
    assert set(state['capability_refusals']) == {'table_hash', 'report_context_hash', 'renderer_version'}
    assert set(state['capability_refusals'].values()) == {'RenderIdentityBindingMismatch'}
    assert state['actual_execution']['calls'] == dict(nominal=1008, physical_point=96, prepare_h1=6)
    for mode in ('hidden', 'opt-in'):
        counters = state['renders'][mode]['counters']
        assert counters.get('visible', 0) == (18768 if mode == 'opt-in' else 0)
        assert counters['synthetic_assessment'] == 0 and counters['missing_or_incomplete'] == 0
        assert counters['null_value'] == 12432
    def unknown_errors(value):
        for key, item in value.items():
            if isinstance(item, dict):
                unknown_errors(item)
            elif key == 'n_samples':
                assert item == 0
            else:
                assert item is None, (key, item)
    unknown_errors(state['errors'])
    surfaces = json.loads((HERE / 'serialized-surface-results.json').read_text())
    for mode, formats in surfaces.items():
        for value in formats.values():
            assert value == dict(checked=40320, visible=18768 if mode == 'opt-in' else 0)
    assert digest(HERE / 'runtime_driver.py') == state['preflight']['driver_sha256']
    assert digest(ROOT / 'docs/reviews/U2-B-real-report-exits-v1/real_report_driver.py') == state['preflight']['helpers_sha256']
    assert digest(ROOT / 'docs/reviews/U2-B-real-report-exits-v1/serialized_surface_check.py') == state['preflight']['surface_checker_sha256']
    checked = audit_candidate(ui.ADOPTED)
    assert checked == state['preflight']['audit']
    adoption_authority(ui.ADOPTED, HERE / 'adoption-review.json', state['preflight']['review_sha256'])
    assert digest(HERE / 'displaced-adopted-v1/MANIFEST.json') == '2d15afd7dd80124f70d387bc7cde4addda29162cd49370d40da7b99830709b44'
    expected = set(json.loads((HERE / 'acceptance-and-placement.json').read_text())['changed_tracked_paths'])
    assert set(subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT, text=True).splitlines()) == expected
    assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT)
    main_root = ROOT.parent / 'rk-uarch'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=main_root, text=True).strip() == '1e9e794a84c5173812c23a1cf2fc04b85e6f6831'
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=main_root)
    record = dict(status='passed', generated_manifest_sha256=digest(manifest), generated_members=len(entries), generated_bytes=sum((out / n).stat().st_size for n in entries), replay_stream_comparison=replay, repeat_stream_comparison=repeat, runtime_driver_unchanged=True, support_and_adopted_inputs_unchanged=True, actual_producer_counts=state['actual_execution']['calls'], capability_refusals=state['capability_refusals'], exact_tracked_delta=sorted(expected), real_index_clean=True, main_unchanged=True, commit_push_tag_cleanup_performed=False)
    (HERE / 'final-verification.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
