import subprocess,sys,json,time,hashlib,os
from pathlib import Path
root=Path(os.environ.get('COMPONENT_PRIVATE_SOURCE','/home/jjaff/AI-infra-simulation/rk-uarch-u4-a')); scratch=Path('/tmp/u4-component-a-development')
name=sys.argv[1]; args=sys.argv[2:]
argv=['docker','--host','unix:///var/run/docker.sock','run','--rm','--pull','never','--platform','linux/amd64','--network','none','--read-only','--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp','--workdir','/work/native','--mount',f'type=bind,src={root},dst=/work,readonly','--mount','type=bind,src=/tmp/u4-k2-c1-precise.styffox_/cargo-home,dst=/cargo-home,readonly','--mount',f'type=bind,src={scratch}/target,dst=/target','--entrypoint','/usr/bin/env','sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523','-i','PATH=/usr/local/rustup/toolchains/1.99.0-x86_64-unknown-linux-gnu/bin:/usr/local/cargo/bin:/usr/bin:/bin','CARGO_HOME=/cargo-home','CARGO_NET_OFFLINE=true','CARGO_TARGET_DIR=/target','RUSTUP_AUTO_INSTALL=0','LC_ALL=C',*args]
p=scratch/'logs'/name
assert not p.with_suffix('.json').exists()
t=time.time(); r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
p.with_suffix('.stdout').write_bytes(r.stdout); p.with_suffix('.stderr').write_bytes(r.stderr)
p.with_suffix('.json').write_text(json.dumps({'argv':argv,'exit_code':r.returncode,'elapsed_s':time.time()-t,'source':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((root/'native').rglob('*')) if f.is_file() and 'target' not in f.parts}},indent=2))
print(name,r.returncode); print(r.stdout.decode()[-10000:]); print(r.stderr.decode()[-5000:]); sys.exit(r.returncode)
