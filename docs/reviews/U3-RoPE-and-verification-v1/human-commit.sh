#!/usr/bin/env bash
# HUMAN invocation only. --check is read-only and may be run by the coordinator.
set -euo pipefail
python3 - "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" "$@" <<'PYCOMMIT'
import hashlib,json,os,subprocess,sys
from pathlib import Path
folder=Path(sys.argv[1]).resolve()
args=sys.argv[2:]
if args not in ([],['--check']):
    raise SystemExit('Usage: bash human-commit.sh [--check]')
root=folder.parents[2]
def git(*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def require(ok,message):
    if not ok: raise SystemExit('STOP: '+message)
require(Path(git('rev-parse','--show-toplevel')).resolve()==root,'unexpected repository')
require(git('branch','--show-current')=='main','expected main')
require(git('remote','get-url','origin')=='https://github.com/kakoee/rk-uarch.git','unexpected origin')
require(not git('diff','--cached','--name-only'),'index must be empty')
require(not git('diff','--name-only'),'tracked worktree must be clean')
for state in ('MERGE_HEAD','CHERRY_PICK_HEAD','REVERT_HEAD','rebase-merge','rebase-apply'):
    require(not Path(git('rev-parse','--path-format=absolute','--git-path',state)).exists(),'unfinished Git operation')
for ancestor in ('7d15c5aa73504c38eac3b3dc162d2885cc1f33dc','428b7bb29664b7de2b8c8ef8ce3a8bad2e5245ee'):
    require(subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',ancestor,'HEAD']).returncode==0,'accepted proposal is not in HEAD')
hooks=git('rev-parse','--path-format=absolute','--git-path','hooks')
precommit=Path(hooks)/'pre-commit'
require(precommit.exists() and os.access(precommit,os.X_OK),'normal pre-commit hook missing')
hooktext=precommit.read_text()
require('scripts/hooks/human_owned.sh' in hooktext and 'scripts/hooks/frozen_predictions.sh' in hooktext,'unexpected normal hooks')
expected={'U0006-what-verification-can-and-cannot-establish.md': '3db0424f16c9d373289cb0af21f8d5f3bfd17479d750830f10632249e1b34b2e', 'U0022-explicit-rope-semantics.md': 'a71f306fe3055cbc153aa43074383e5e071908738fac94c7f442c0a7fdced6bf'}
contents={}
for name,digest in expected.items():
    data=(folder/name).read_bytes()
    require(hashlib.sha256(data).hexdigest()==digest,'draft changed: '+name)
    require(not (root/'docs/decisions'/name).exists(),'destination already exists: '+name)
    contents[name]=data
print('Verified both approved ADR drafts, proposal ancestry, branch, normal hooks and clean index.')
if args==['--check']: raise SystemExit(0)
parent=git('rev-parse','HEAD')
paths=['docs/decisions/'+name for name in expected]
for name,data in contents.items():
    with (root/'docs/decisions'/name).open('xb') as output: output.write(data)
subprocess.run(['git','-C',str(root),'add','--',*paths],check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(paths),'unexpected staged paths')
for name,digest in expected.items():
    staged=subprocess.check_output(['git','-C',str(root),'show',':docs/decisions/'+name])
    require(hashlib.sha256(staged).hexdigest()==digest,'staged bytes changed')
subprocess.run(['git','-C',str(root),'diff','--cached','--check'],check=True)
require(git('rev-parse','HEAD')==parent,'HEAD moved during preparation')
# Only the human's non-check invocation sets this required hook authorization.
env=os.environ.copy()
env['UARCH_HUMAN']='1'
subprocess.run(['git','-C',str(root),'commit','-m','docs(u3): accept U0006 verification and U0022 RoPE semantics'],check=True,env=env)
commit=git('rev-parse','HEAD')
require(git('rev-parse','HEAD^')==parent,'unexpected parent')
require(set(git('diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines())==set(paths),'unexpected committed paths')
require(not git('diff','--cached','--name-only') and not git('diff','--name-only'),'index/tracked worktree not clean')
print(json.dumps({'decision':'U3-RoPE-and-verification-v1','commit':commit,'parent':parent,'branch':'main','paths':paths,'tracked_and_index_clean':True,'push_performed':False},indent=2))
print('STOP: return this receipt. Push and lane implementation remain separate.')
PYCOMMIT
