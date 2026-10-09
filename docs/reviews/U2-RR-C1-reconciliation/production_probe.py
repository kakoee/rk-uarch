import importlib,json,time,sys
from pathlib import Path
import yaml
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json,spec_hash
from rkuarch.table.artifacts import load_verified_report_inputs
from rkuarch.table.build import CapturedWork,build_table
root=Path.cwd()
report=Path('/tmp/u2-b-real-report-exits-v1-xn5pjr8z/outputs/report/table.json')
def trap(*a,**kw):raise AssertionError('producer called')
importlib.import_module('rkuarch.workload.prepare').prepare=trap
importlib.import_module('rkuarch.engines.analytic.core').run_analytic=trap
start=time.monotonic()
v=load_verified_report_inputs(report)
print('public full-package load passed',time.monotonic()-start,flush=True)
hw=HardwareSpec.model_validate(yaml.safe_load((root/'hw/designs/npu-l4.yaml').read_text()))
assert hw==v.hardware and spec_hash(hw)==spec_hash(v.hardware)
a=CapturedWork(v.bundle.model_copy(update={'hardware_spec':hw}),v.assumptions,v.request,v.derivation,v.jobs,v.results)
b=CapturedWork(v.bundle,v.assumptions,v.request,v.derivation,v.jobs,v.results)
pa=build_table(a,context=v.context,model_card=v.model_card,artifacts=v.artifacts)
print('YAML-order complete build passed',time.monotonic()-start,flush=True)
pb=build_table(b,context=v.context,model_card=v.model_card,artifacts=v.artifacts)
print('canonical-order complete build passed',time.monotonic()-start,flush=True)
assert len(pa.table.rows)==len(pb.table.rows)==24
assert pa.table.rows==pb.table.rows
assert len(pa.table.provenance.conditional_on)==59
same=canonical_json(pa.table)==canonical_json(pb.table)
expected=sys.argv[1]=='patched'
assert same==expected,(same,expected)
if expected:
 assert pa==pb
 paths=[c.path for c in pa.table.provenance.conditional_on]
 assert paths==sorted(paths)
 assert pa.table.table_hash=='sha256:200ca0f703feb341e3871ad3a1f897ac45cb1e42f270d10384ea31cdcafbd554'
else:
 assert pa.table.table_hash=='sha256:e42bd0dbe02b323f28384cf52a25fc96d5892ab9011ed705eb6c8210575668f4'
 assert pb.table.table_hash=='sha256:6af7d7c3117d4c46c6718cf48d4362fd5e2043fb191742a6769fad7ae1fcb245'
receipt=dict(mode=sys.argv[1],rows=24,conditions=59,same_table_bytes=same,yaml_table_hash=pa.table.table_hash,saved_table_hash=pb.table.table_hash,producers_trapped=True,source='actual saved engine results, real report context; hardware from current H1 YAML and canonical capture',elapsed_s=time.monotonic()-start)
Path('/tmp/u2-rr-c1-coordinator/'+sys.argv[1]+'.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt),flush=True)
