"""One cleanup-risk control: retained ordinary checker invocation coverage."""
import json
import os
import subprocess
from pathlib import Path
ROOT=Path('/tmp/u4-recheck-808076a-source')
OUT=Path(__file__).resolve().parents[1]/'receipts'
p=ROOT/'src/rkuarch/engines/native/ordinary.py'
original=p.read_bytes()
block=b'''    check_v3(
        job.model_dump(mode="json"),
        result.model_dump(mode="json"),
        {"unrepresented": UNREPRESENTED},
    )'''
assert original.count(block)==1
# Keep the import referenced: this probes behavior, not an unused-import lint error.
replacement=b'    if False:\n'+b'\n'.join(b'    '+line for line in block.splitlines())
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=f'{ROOT}/src:{ROOT}/contract:{ROOT}',
 ORDINARY_NATIVE='/tmp/u4-recheck-808076a-target/x86_64-unknown-linux-gnu/debug/uarch-engine')
command=['/tmp/rk-uarch-u4-correction/.venv/bin/python','-B','-m','pytest','-q','-p','no:cacheprovider',
 'tests/unit/test_ordinary_native.py','tests/native/test_ordinary_process.py','validation/component/test_runtime_checks.py']
rows=[]
def run(name):
 r=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
 (OUT/(name+'.txt')).write_text(r.stdout+r.stderr)
 rows.append(dict(name=name,exit_code=r.returncode,command=command))
 assert r.returncode==0,(name,r.stdout,r.stderr)
try:
 p.write_bytes(original.replace(block,replacement))
 run('cleanup-checker-call-disabled')
finally:
 p.write_bytes(original)
run('cleanup-checker-call-restored')
(OUT/'cleanup-wiring-control.json').write_text(json.dumps(rows,indent=2)+'\n')
