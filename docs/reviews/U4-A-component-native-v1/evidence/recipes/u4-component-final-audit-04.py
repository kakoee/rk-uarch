import json,hashlib,importlib.util,copy
from pathlib import Path
from uarch_contract.mapped import MappedEngineJob,validate_result
from validation.component.observations_v2 import check_v2
root=Path('/home/jjaff/AI-infra-simulation/rk-uarch-u4-a'); s=Path('/tmp/u4-component-a-candidate-04')
spec=importlib.util.spec_from_file_location('candidate',root/'native/tools/component_candidate.py'); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
inputs=json.loads((s/'source/native/crates/uarch-engine/testdata/synthetic-component-jobs.json').read_bytes()); inputs['SYNTHETIC-O2-transient']=json.loads((s/'source/native/crates/uarch-engine/testdata/synthetic-component-transient-job.json').read_bytes())
contract=json.loads((root/'docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json').read_bytes())['observation_contract']
base=s/'outputs/debug/debug-replay-1'; report={'kind':'author-observed private synthetic replay; not independent B verdict','cases':{},'failures':[]}
for f in sorted(base.glob('*.json')):
    name=f.stem
    if name=='index':continue
    try:
        job=MappedEngineJob.model_validate(inputs[name]); raw=json.loads(f.read_bytes());validate_result(raw,job);check_v2(inputs[name],raw,contract)
        h=hashlib.sha256(f.read_bytes()).hexdigest()
        paths=[s/'outputs'/mode/(mode+'-replay-'+str(n))/f.name for mode in ['debug','release'] for n in [1,2,3]]
        assert all(p.read_bytes()==f.read_bytes() for p in paths),'byte replay difference'
        report['cases'][name]={'sha256':h,'bytes':f.stat().st_size,'six_way_equal':True,'installed_result':True,'B_checker_v2':True}
    except Exception as e:report['failures'].append({'case':name,'error':str(e)})
assert len(report['cases'])+len(report['failures'])==79
(s/'replay-audit.json').write_text(json.dumps(report,indent=2)+'\n'); print('replay',len(report['cases']),report['failures'])
refusals=[]
for mode in ['debug','release']:
    good=inputs['C02']; wrong=copy.deepcopy(good);wrong['engine']['implementation_hash']='sha256:'+'f'*64
    cases=[('absent-authority',m.canonical(good),'TestProfileMismatch',['--protocol','uarch-engine/3']),('wrong-engine',m.canonical(wrong),'TestProfileMismatch',['--protocol','uarch-engine/3']),('malformed',b'{','InvalidJson',['--protocol','uarch-engine/3']),('wrong-protocol',b'{"protocol":"uarch-engine/2"}','UnsupportedProtocol',['--protocol','uarch-engine/3']),('wrong-cli',b'', 'UnsupportedProtocol',[])]
    for name,data,code,args in cases:
        tag=mode+'-public-refusal-stdin-'+name
        prefix=m.docker(s,mode,tag);prefix.insert(prefix.index('run')+1,'-i')
        status=m.command(s,tag,prefix+['/target/'+mode+'/uarch-engine']+args,stdin=data)
        out=(s/'commands'/tag).with_suffix('.stdout').read_bytes();err=(s/'commands'/tag).with_suffix('.stderr').read_bytes();obj=json.loads(err)
        assert status==2 and out==b'' and obj['code']==code,(tag,status,out,obj)
        refusals.append({'mode':mode,'case':name,'code':code,'exit_code':status,'empty_stdout':True,'stderr_sha256':hashlib.sha256(err).hexdigest()})
(s/'public-refusals.json').write_text(json.dumps(refusals,indent=2)+'\n')
tag='loader-library-hashes';m.command(s,tag,m.docker(s,'debug',tag)+['/usr/bin/sha256sum','/lib/x86_64-linux-gnu/libgcc_s.so.1','/lib/x86_64-linux-gnu/libc.so.6','/lib64/ld-linux-x86-64.so.2'])
assert not report['failures']
