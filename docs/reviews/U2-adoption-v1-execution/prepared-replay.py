"""Real adopted reference replay; physical producers disabled; nominal still executes."""
from pathlib import Path
import hashlib,importlib,json,time
from tests import u2_refresh as refresh,u2_comparison as old
from scripts import vendor_rk as vr
root=Path('/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration');d=root/'docs/reviews/U2-adoption-v1-execution';receipt=json.loads((d/'acceptance-and-placement.json').read_text());saved=d/'runtime'
def disabled(*args,**kwargs):raise AssertionError('Physical producer invoked during prepared replay')
old.prepare_h1=disabled;old.physical_point=disabled
importlib.import_module('rkuarch.workload.prepare').prepare=disabled
importlib.import_module('rkuarch.engines.analytic.core').run_analytic=disabled
started=time.monotonic();replay=refresh.consume_adopted(adoption_review=Path(receipt['adoption_review_path']),review_sha256=receipt['adoption_review_sha256'],physical_replay=json.loads((saved/'physical-capture.json').read_bytes()))
assert {p.stem for p in (saved/'comparison-artifacts').iterdir()}=={identity[7:] for identity in replay['artifacts']}
for identity,value in replay['artifacts'].items():
 actual=value if isinstance(value,bytes) else vr.canonical(value)
 assert (saved/'comparison-artifacts'/(identity[7:]+'.json')).read_bytes()==actual,identity
for name in ['nominal','physical','inventory']:assert (saved/(name+'.json')).read_bytes()==vr.canonical(replay[name].model_dump(mode='json'))
record={'status':'passed','elapsed_s':time.monotonic()-started,'synthetic':replay['synthetic'],'physical_producers_disabled':True,'nominal_candidate_executed':True,'artifact_files_byte_identical':len(replay['artifacts']),'all_three_top_level_files_byte_identical':True,'nominal_gate':replay['nominal'].gate_outcome,'physical_gate':replay['physical'].gate_outcome,'nominal_evidence':replay['nominal'].evidence_outcome,'physical_evidence':replay['physical'].evidence_outcome,'limitations':'Prepared comparison replay only; no repeated rendered-output equality claimed by this probe.'}
(d/'prepared-replay.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
