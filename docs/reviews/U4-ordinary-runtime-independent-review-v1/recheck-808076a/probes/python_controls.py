"""Small reversible sensitivity controls in a disposable successor reconstruction."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path('/tmp/u4-recheck-808076a-source')
OUT = Path(__file__).resolve().parents[1] / 'receipts'
PYTHON = '/tmp/rk-uarch-u4-correction/.venv/bin/python'
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=f'{ROOT}/src:{ROOT}/contract:{ROOT}')
rows = []

def run(name, selection, expected):
    command = [PYTHON, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *selection]
    p = subprocess.run(command, cwd=ROOT, env=ENV, capture_output=True, text=True, timeout=180)
    (OUT / (name + '.txt')).write_text(p.stdout + p.stderr)
    rows.append(dict(name=name, command=command, exit_code=p.returncode, expected=expected))
    (OUT / 'python-controls.json').write_text(json.dumps(rows, indent=2) + '\n')
    assert p.returncode == expected, (name, p.stdout, p.stderr)


def mutate(path, before, after, action):
    p = ROOT / path
    original = p.read_bytes()
    assert original.count(before.encode()) == 1, (path, before)
    try:
        p.write_bytes(original.replace(before.encode(), after.encode()))
        action()
    finally:
        p.write_bytes(original)
    assert hashlib.sha256(p.read_bytes()).digest() == hashlib.sha256(original).digest()

ordinary = ['tests/unit/test_ordinary_native.py']
checker = ['validation/component/test_phase_laws.py', 'validation/component/test_runtime_checks.py',
           'validation/component/test_issue_checks.py', 'validation/component/test_matrix_order.py']
run('python-positive', ordinary + checker + ['tests/unit/test_u4_k2_process.py'], 0)
mutate('contract/uarch_contract/ordinary.py', '''        # The independent model-2 checker supports exactly these E3 overhead laws.
        m.require(
            self.hardware_spec.cores.core_type.job_overhead_cycles.value == 32
            and self.hardware_spec.sync.barrier_latency_cycles.value == 32,
            "UnsupportedHardware",
            "model-2 checker requires 32-cycle job overhead and barrier latency",
        )
''', '', lambda: run('f1-python-pin-removed', ordinary + ['-k', 'test_test_only_checker_capability'], 1))
run('f1-python-restored', ordinary + ['-k', 'test_test_only_checker_capability'], 0)
mutate('src/rkuarch/verification/component/phase_laws.py', 'overhead=32,', 'overhead=31,',
       lambda: run('f2-shipped-scalar-drift', ['validation/component/test_phase_laws.py'], 1))
mutate('src/rkuarch/verification/component/observations_v3.py', '(32, "noc")', '(31, "noc")',
       lambda: run('f2-shipped-barrier-drift', ['validation/component/test_runtime_checks.py'], 1))
# Repeat the original Stage 1 drift narrowly: this branch has no compute task in sr2.
mutate('src/rkuarch/verification/component/observations_v3.py', '("compute_overhead", 32)', '("compute_overhead", 31)',
       lambda: run('f2-original-compute-drift', ordinary + checker, 0))
run('f2-checkers-restored', checker, 0)
run('cleanup-discovery', ['--collect-only'], 0)
print(json.dumps(rows, indent=2))
