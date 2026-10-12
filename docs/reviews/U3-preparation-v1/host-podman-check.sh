#!/usr/bin/env bash
# Run as javid, after administrator installs Podman and its rootless helpers.
# May initialize Javid's Podman storage. No image pull, simulator build or benchmark.
set -euo pipefail
[ "$(id -un)" = javid ] || { echo 'Run as javid, without sudo.' >&2; exit 1; }
[ "$(hostname)" = v2202507191245365394 ] || { echo 'Unexpected host; stop.' >&2; exit 1; }
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
python3 - <<'PYHOST'
import json,os,platform,shutil,subprocess,sys
for name in ('podman','newuidmap','newgidmap'):
 if not shutil.which(name):raise SystemExit('Missing required tool: '+name)
def run(args):
 p=subprocess.run(args,text=True,capture_output=True,timeout=60)
 if p.returncode:
  print(p.stdout,file=sys.stderr);print(p.stderr,file=sys.stderr)
  raise SystemExit('Command failed: '+' '.join(args))
 if p.stderr:print(p.stderr,file=sys.stderr)
 return p.stdout
info=json.loads(run(['podman','info','--format','json']))
assert info['host']['security']['rootless'] is True, 'Podman did not report rootless mode'
maps={}
for kind,host_id in [('uid',os.getuid()),('gid',os.getgid())]:
 raw=run(['podman','unshare','cat','/proc/self/'+kind+'_map'])
 rows=[[int(x) for x in line.split()] for line in raw.splitlines()]
 assert any(a==0 and b==host_id and n==1 for a,b,n in rows),kind+' caller mapping missing'
 assert any(n>=65536 for a,b,n in rows),kind+' subordinate mapping missing'
 maps[kind]=rows
print(json.dumps({'hostname':platform.node(),'podman_version':run(['podman','--version']).strip(),'rootless':True,'user_namespace_maps':maps,'storage_driver':info['store'].get('graphDriverName'),'graph_root':info['store'].get('graphRoot'),'runtime':info['host'].get('ociRuntime'),'status':'rootless information and user-namespace checks passed','limits':'No image build/run, simulator execution, performance measurement or runner registration performed'},indent=2))
PYHOST
