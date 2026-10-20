"""Pinned offline native workflow and two small reversible regression controls."""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path('/tmp/u4-recheck-808076a-source')
TARGET = Path('/tmp/u4-recheck-808076a-target')
TARGET.mkdir(exist_ok=True)
OUT = Path(__file__).resolve().parents[1] / 'receipts'
IMAGE = 'sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523'
BIN = '/usr/local/rustup/toolchains/1.99.0-x86_64-unknown-linux-gnu/bin/'
rows = json.loads((OUT / 'native-controls.json').read_text()) if (OUT / 'native-controls.json').exists() else []


def run(name, command, expected, work='/work/native'):
    args = ['docker', 'create', '--pull', 'never', '--network', 'none', '--read-only',
            '--user', f'{os.getuid()}:{os.getgid()}', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp', '--workdir', work,
            '--mount', f'type=bind,src={ROOT},dst=/work,readonly',
            '--mount', 'type=bind,src=/tmp/u4-k2-c1-precise.styffox_/cargo-home,dst=/cargo-home,readonly',
            '--mount', f'type=bind,src={TARGET},dst=/target',
            '--entrypoint', '/usr/bin/env', IMAGE, '-i',
            'PATH='+BIN+':/usr/local/cargo/bin:/usr/bin:/bin', 'CARGO_HOME=/cargo-home',
            'CARGO_TARGET_DIR=/target', 'CARGO_NET_OFFLINE=true', 'RUSTUP_AUTO_INSTALL=0',
            'RUSTC='+BIN+'rustc', 'LC_ALL=C', *command]
    cid = subprocess.check_output(args, text=True).strip()
    assert re.fullmatch('[0-9a-f]{64}', cid)
    record = dict(name=name, container_id=cid, command=command, expected=expected)
    rows.append(record)
    try:
        with (OUT / (name+'.txt')).open('w') as f:
            p = subprocess.run(['docker', 'start', '--attach', cid], stdout=f,
                               stderr=subprocess.STDOUT, timeout=120)
        state = json.loads(subprocess.check_output(['docker', 'inspect', cid]))[0]['State']
        record.update(attach_status=p.returncode, state=state)
        assert state['ExitCode'] == expected and p.returncode == expected, record
        assert not state['OOMKilled'] and not state['Error']
    finally:
        subprocess.run(['docker', 'rm', '--force', cid], check=True, capture_output=True)
        absent = subprocess.run(['docker', 'inspect', cid], capture_output=True, text=True)
        record['removed'] = absent.returncode != 0 and 'no such object' in absent.stderr.lower()
        (OUT / 'native-controls.json').write_text(json.dumps(rows, indent=2)+'\n')
        assert record['removed']


def mutate(path, before, after, action):
    p = ROOT / path
    original = p.read_bytes()
    assert original.count(before.encode()) == 1
    try:
        p.write_bytes(original.replace(before.encode(), after.encode()))
        action()
    finally:
        p.write_bytes(original)
    assert hashlib.sha256(p.read_bytes()).digest() == hashlib.sha256(original).digest()

common = ['cargo','test','--locked','--offline','--all-features','--target','x86_64-unknown-linux-gnu']
f1 = common + ['--lib', 'protocol::ordinary_capability_tests::checker_hardware_domain']
f3 = common + ['--test', 'ordinary']
expanded = subprocess.check_output(['make', '-n', 'native-test'], cwd=ROOT, text=True)
(OUT / 'make-native-test-expansion.txt').write_text(expanded)
assert expanded.strip() == 'cd native && ' + ' '.join(common)
run('normal-native-test-recipe', common, 0)
mutate('native/crates/uarch-engine/src/component_admission.rs', '''    require(
        integer(&c["job_overhead_cycles"])? == 32
            && integer(&h["sync"]["barrier_latency_cycles"])? == 32,
        "UnsupportedHardware",
        "model-2 checker requires 32-cycle job overhead and barrier latency",
    )?;
''', '', lambda: run('f1-native-pin-removed', f1, 101))
run('f1-native-restored', f1, 0)
mutate('native/crates/uarch-engine/src/main.rs',
       'match respond_with_test_mode(&input, test_only)',
       'match respond_with_test_mode(&input, !test_only)',
       lambda: run('f3-shipping-invocation-broken', f3, 101))
run('f3-shipping-restored', f3, 0)
print(json.dumps(rows, indent=2))
