import hashlib,json,subprocess,tarfile,tempfile,io
from pathlib import Path
base=Path('/home/jjaff/AI-infra-simulation')
b=base/'rk-uarch-u2-b'
h=b/'docs/reviews/U2-B-real-report-exits-v1'
out=Path(json.loads((h/'output-location.json').read_text())['root'])
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(h/'README.md')=='1f7bf648a4f5776b95c8773f9c0e41e38ce44ae316ab414b7077c85f8e98de42'
assert sha(out/'SHA256SUMS')=='228143269eba793db3290dbb4ff89dfa43c26ce5c65e461c053e3656b376af58'
entries={}
for line in (out/'SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1)
 assert name not in entries and not Path(name).is_absolute() and '..' not in Path(name).parts
 assert sha(out/name)==digest,name
 entries[name]=digest
assert set(entries)=={str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()}-{'SHA256SUMS'}
assert len(entries)==13276
support=json.loads((b/'contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963/u2-inputs/support-files.json').read_text())
assert len(support)==84
for name,digest in support.items():assert sha(b/name)==digest,name
for name in ('rk-uarch-u2-a','rk-uarch-u2-b','rk-uarch-u2-integration'):
 root=base/name
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()=='7aab97d35ca554b0477ac5719dfa4e5306f8bbab'
 for args in (['diff','--exit-code'],['diff','--cached','--exit-code']):subprocess.run(['git',*args],cwd=root,check=True)
inv=json.loads((h/'new-files.json').read_text())
assert {p.name for p in h.iterdir()}==set(inv['new_files'])
receipt={'handoff_sha256':sha(h/'README.md'),'artifact_members_verified':len(entries),'support_members_verified':len(support),'artifact_bytes':sum((out/n).stat().st_size for n in entries),'proposed_B_files':len(inv['proposed_commit_files']),'proposed_B_bytes':sum((h/n).stat().st_size for n in inv['proposed_commit_files']),'tracked_workers_clean':True}
Path('/tmp/u2-rr-c1-coordinator/audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt),flush=True)
root=Path(tempfile.mkdtemp(prefix='u2-rr-c1-git-'))
raw=subprocess.check_output(['git','archive','7aab97d35ca554b0477ac5719dfa4e5306f8bbab'],cwd=b)
with tarfile.open(fileobj=io.BytesIO(raw)) as tf:tf.extractall(root,filter='data')
Path('/tmp/u2-rr-c1-coordinator/export-path.txt').write_text(str(root))
print('Git export:',root,flush=True)
