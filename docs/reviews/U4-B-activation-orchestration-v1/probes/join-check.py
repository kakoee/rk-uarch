import ast,hashlib,json,sys
from pathlib import Path
from validation.component.ordinary_eof_acceptance import verify_closure
from validation.component import ordinary_eof_campaign, capture_monitor
root=Path.cwd(); pkg=Path(sys.argv[1]); pins=json.loads((pkg/'source-consumer-bindings.json').read_bytes())['files']
# Consumer expects bare hex source hashes, as its verify_sources uses existing convention.
config={'source':str(root),'pins':pins}
verify_closure(config)
transition=json.loads((pkg/'source-transition.json').read_bytes())
for name,pin in transition['source_files'].items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==pin,name
prior=Path('/tmp/u4-b-activation-final-01/reconstruction-final')
old=json.loads((root/'docs/reviews/U4-B-component-activation-final-v1/source-transition.json').read_bytes())
for name,pin in old['activation_prospective_source_files'].items():
 assert hashlib.sha256((prior/name).read_bytes()).hexdigest()==pin,name
newtool=Path('/tmp/u4-b-orchestration-01/overlay-preview/native/tools/component_runtime_candidate.py')
expected=dict(old['activation_prospective_source_files']);expected.update(transition['actual_added_files']);expected.update(transition['new_runtime_consumer_pins']);expected['native/tools/component_runtime_candidate.py']=hashlib.sha256(newtool.read_bytes()).hexdigest()
assert expected==transition['activation_prospective_source_files']
ast.parse(newtool.read_bytes())
# Route currentness and missing runtime-module pin must be independently refused.
for removed in ('validation/component/ordinary_eof_campaign.py','validation/component/capture_monitor.py'):
 bad=dict(pins);bad.pop(removed)
 try:verify_closure({'source':str(root),'pins':bad})
 except ValueError as e:assert 'complete matching consumer/structural closure' in str(e)
 else:raise AssertionError('missing loaded-module binding accepted')
bad=dict(pins);bad['validation/component/capture_monitor.py']='0'*64
try:verify_closure({'source':str(root),'pins':bad})
except ValueError:pass
else:raise AssertionError('wrong source accepted')
print(json.dumps({'source_files':len(transition['source_files']),'activation_source_files':len(expected),'source_consumer':len(pins),'activation_consumer':len(json.loads((pkg/'activation-consumer-bindings.json').read_bytes())['files']),'valid_closure':'pass','missing_and_wrong_source':'refused, identity controls only','proposal':'private exact pre/postimage verified; parsed, not executed','D3':'prior verified postimage reused; A integrated confirmation pending'}))
