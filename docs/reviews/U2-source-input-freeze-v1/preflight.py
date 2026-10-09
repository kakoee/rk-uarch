"""Read-only exact freeze and environment verification; never executes oracle computation."""
from pathlib import Path
import hashlib,json,os,subprocess
from scripts import vendor_rk as v,u2_inputs as inputs
root=Path('/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration')
f=root/'docs/reviews/U2-source-input-freeze-v1'
expected=json.loads((f/'inventory.json').read_text())
def sha(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
assert Path.cwd().resolve()==root
assert sha(f/'source-SHA256SUMS')==expected['source_manifest_sha256']
for line in (f/'source-SHA256SUMS').read_text().splitlines():
 digest,path=line.split('  ',1);assert sha(root/path)==digest,('frozen source changed',path)
inputs.load_inputs(f/'inputs',expected['input_manifest_sha256'])
assert not os.environ.get('PARAMS'), 'Unexpected PARAMS override'
rk=Path('/home/jjaff/AI-infra-simulation/rk-sim-u1-pin')
v.check_clone(rk,v.PIN);env=v.oracle_environment(rk);assert env['UV_PROJECT_ENVIRONMENT']=='/tmp/rk-sim-u1-jjaffari-1e5706e'
v.verify_oracle_environment(rk,env)
metadata=v.record_oracle_environment(rk,env)
assert metadata==json.loads((f/'oracle-environment-preflight.json').read_text())['metadata'],'Oracle environment changed since review'
print(json.dumps({'status':'passed','source_manifest_sha256':expected['source_manifest_sha256'],'input_manifest_sha256':expected['input_manifest_sha256'],'pin':v.PIN,'environment_metadata':metadata},sort_keys=True))
