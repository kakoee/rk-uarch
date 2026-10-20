"""Verify restored source, unchanged pinned package, and exact owned-container cleanup."""
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
ROOT=Path('/tmp/u4-recheck-808076a-source')
REPO=Path('/tmp/u4-recheck-808076a-pin')
OUT=Path(__file__).resolve().parents[1]/'receipts'
with tempfile.TemporaryDirectory(prefix='u4-recheck-index-') as temporary:
 env=dict(os.environ,GIT_WORK_TREE=str(ROOT),GIT_INDEX_FILE=str(Path(temporary)/'index'))
 subprocess.run(['git','read-tree','12be87558c5a3312068ab1c5aa147fd95df232da'],cwd=REPO,env=env,check=True)
 subprocess.run(['git','add','-A'],cwd=REPO,env=env,check=True)
 tree=subprocess.check_output(['git','write-tree'],cwd=REPO,env=env,text=True).strip()
assert tree=='9a86cab622504e68746534c94e93b659cacf794d',tree
assert subprocess.check_output(['git','status','--porcelain'],cwd=REPO)==b''
rows=json.loads((OUT/'native-controls.json').read_text())
for row in rows:
 cid=row['container_id']
 p=subprocess.run(['docker','inspect',cid],capture_output=True,text=True)
 assert p.returncode!=0 and 'no such object' in p.stderr.lower()
report=Path(__file__).resolve().parents[2]/'README.md'
prior=json.loads((OUT/'prior-report.json').read_text())
assert hashlib.sha256(report.read_bytes()[:prior['bytes']]).hexdigest()==prior['sha256']
(OUT/'final-integrity.json').write_text(json.dumps({'restored_source_tree':tree,'pin_checkout_clean':True,
 'containers_created_and_removed':len(rows),'prior_report_bytes':prior['bytes'],
 'prior_report_sha256':prior['sha256'],'prior_report_prefix_unchanged':True},indent=2)+'\n')
print('All temporary implementation mutations restored; prior report prefix unchanged;',len(rows),'owned containers removed.')
