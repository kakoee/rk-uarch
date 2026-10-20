"""Check the remaining original F2 drift against the optional process regression."""
import json
import os
import subprocess
from pathlib import Path
ROOT=Path('/tmp/u4-recheck-808076a-source')
OUT=Path(__file__).resolve().parents[1]/'receipts'
p=ROOT/'src/rkuarch/verification/component/observations_v3.py'
original=p.read_bytes()
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=f'{ROOT}/src:{ROOT}/contract:{ROOT}',
 ORDINARY_NATIVE='/tmp/u4-recheck-808076a-target/x86_64-unknown-linux-gnu/debug/uarch-engine')
command=['/tmp/rk-uarch-u4-correction/.venv/bin/python','-B','-m','pytest','-q','-p','no:cacheprovider',
 'tests/native/test_ordinary_process.py']
rows=[]
def run(name,code):
 r=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
 (OUT/(name+'.txt')).write_text(r.stdout+r.stderr)
 rows.append(dict(name=name,exit_code=r.returncode,command=command,executable=env['ORDINARY_NATIVE']))
 assert r.returncode==code,(name,r.stdout,r.stderr)
try:
 p.write_bytes(original.replace(b'("compute_overhead", 32)',b'("compute_overhead", 31)'))
 run('f2-original-drift-with-process',1)
finally:
 p.write_bytes(original)
run('ordinary-process-restored',0)
(OUT/'f2-process-control.json').write_text(json.dumps(rows,indent=2)+'\n')
