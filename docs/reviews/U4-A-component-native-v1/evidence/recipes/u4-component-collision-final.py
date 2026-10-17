import json,shutil,subprocess,os,copy
from pathlib import Path
from uarch_contract.hashing import content_hash,canonical_json
from uarch_contract.mapped import MappedEngineJob,validate_result
from validation.component.observations_v2 import check_v2
r=Path('/home/jjaff/AI-infra-simulation/rk-uarch-u4-a');s=Path('/tmp/u4-component-collision-final');out=Path('/tmp/u4-component-a-development/target')
shutil.copytree('/tmp/u4-component-a-candidate-03/source',s)
p=s/'native/crates/uarch-engine/src';shutil.copy2(r/'docs/reviews/U4-B-component-native-v1/private_probe.rs',p/'b_private_probe.rs')
with (p/'lib.rs').open('a') as f:f.write('\n#[cfg(test)]\nmod b_private_probe;\n')
v=json.loads((s/'native/crates/uarch-engine/testdata/synthetic-request-collision.json').read_bytes());positive=copy.deepcopy(v)
b=positive['workload_closure'];point=b['points'][0];g=point['task_graph'];next(j for j in g['jobs'] if j['kind']=='dma')['fragments'][0]['request_id']='synthetic-distinct-fragment'
g['graph_hash']=content_hash(g,exclude=('graph_hash',));point['payload_hash']=content_hash(point,exclude=('payload_hash',));positive['mapped_point']=point;positive['point_hash']=point['payload_hash'];positive['profile']['entries'][0].update(graph_hash=g['graph_hash'],point_hash=point['payload_hash']);positive['profile']['profile_hash']=content_hash(positive['profile'],exclude=('profile_hash',));positive['admission']['profile_hash']=positive['profile']['profile_hash'];b['admission']=positive['admission'];b['bundle_hash']=content_hash(b,exclude=('bundle_hash',));positive['bundle_hash']=b['bundle_hash'];positive['job_hash']=content_hash(positive,exclude=('job_hash',))
report={}
for name,j in [('collision',v),('distinct',positive)]:
 (s/(name+'.json')).write_text(canonical_json(j));(s/(name+'-trust.json')).write_text(canonical_json({'registry':j['registry']['registry_hash'],'profile':j['profile']['profile_hash'],'case':j['admission']['case_id'],'engine':j['engine']}))
 env={**os.environ,'COMPONENT_PRIVATE_SOURCE':str(s)};tag='request-identity-final-'+name
 subprocess.run(['python3','/tmp/u4-component-a-development/run.py',tag,'B_COMPONENT_JOB=/work/'+name+'.json','B_COMPONENT_TRUST=/work/'+name+'-trust.json','B_COMPONENT_OUTPUT=/target/'+tag+'.json','cargo','test','--offline','--locked','--lib','b_private_probe::private_component_probe','--','--ignored','--exact'],env=env,check=True)
 result=json.loads((out/(tag+'.json')).read_bytes())
 if name=='collision':assert result['outcome']=='refusal' and result['code']=='InvalidTransfer';report[name]=result
 else:
  assert result['outcome']=='success';validate_result(result['result'],MappedEngineJob.model_validate(j));contract=json.loads((r/'docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json').read_bytes())['observation_contract'];check_v2(j,result['result'],contract);report[name]={'outcome':'success','installed_result':True,'B_checker_v2':True}
(s/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
