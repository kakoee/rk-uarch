import json,shutil,subprocess,os,hashlib
from pathlib import Path
base=Path('/tmp/u4-component-a-candidate-04/source');root=Path('/tmp/u4-component-a-accounting-fault-final/source');shutil.copytree(base,root)
folder=root/'native/crates/uarch-engine/src';runtime=folder/'component.rs';accounting=folder/'component_accounting.rs';original={p:p.read_bytes() for p in (runtime,accounting)}
controls=[
 ('omit-overhead',runtime,'h.overhead,','0,','synthetic_compute_literals'),
 ('omit-stage',runtime,'input.div_ceil(h.operand_rate),','0,','synthetic_compute_literals'),
 ('omit-wave-fill-drain',runtime,'add(h.wave_fill_drain, *m)?,','*m,','synthetic_compute_literals'),
 ('omit-output-drain',runtime,'output.div_ceil(h.operand_rate),','0,','synthetic_compute_literals'),
 ('channel-rounded-carry',runtime,'self.channels.insert(p.owner, hi);','self.channels.insert(p.owner, Ratio::integer(hi.ceil()?));','synthetic_exact_channel_carry_and_refresh'),
 ('credit-unlimited',runtime,'live.len() as u64 >= v.hardware.credit_limit','live.len() as u64 >= u64::MAX','synthetic_credit_and_shared_port_literals'),
 ('drop-completion-work',runtime,'self.counts.merge(&c)?;','// private fault drops completed counters','synthetic_compute_literals'),
 ('drop-occupied-rows',accounting,'if occupied {','if occupied && a.phase.name == "impossible-private-fault" {','synthetic_phase_inventory_and_completed_traffic'),
 ('extend-transient-start',runtime,'self.allocations[i].start = Some(self.now);','self.allocations[i].start = Some(0);','synthetic_transient_all_terminal_readers'),
]
controls=[c for c in controls if c[0]=='drop-occupied-rows']
results=[]
def run(tag,test):
 env=dict(os.environ,COMPONENT_PRIVATE_SOURCE=str(root))
 p=subprocess.run(['python3','/tmp/u4-component-a-development/run.py',tag,'cargo','test','--offline','--locked','-p','uarch-engine','--lib','component_tests::'+test,'--','--exact','--nocapture'],env=env,capture_output=True,text=True)
 print(tag,p.returncode,flush=True);return p
baseline=run('accounting-final-baseline','synthetic_compute_literals');assert baseline.returncode==0
for name,path,old,new,test in controls:
 text=original[path].decode();assert text.count(old)==1,(name,text.count(old));path.write_text(text.replace(old,new))
 try:
  fault=run('accounting-final-'+name,test)
  assert fault.returncode==101 and 'test result: FAILED' in fault.stdout,(name,fault.stdout,fault.stderr)
 finally:path.write_bytes(original[path])
 restored=run('accounting-final-'+name+'-restored',test);assert restored.returncode==0,(name,restored.stdout)
 results.append({'fault':name,'test':test,'fault_exit':fault.returncode,'restored_exit':restored.returncode,'before_sha256':hashlib.sha256(original[path]).hexdigest(),'restored_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
Path('/tmp/u4-component-a-development/accounting-final-fault.json').write_text(json.dumps({'source_commit':'64837be','private_synthetic':True,'baseline':0,'controls':results},indent=2))
