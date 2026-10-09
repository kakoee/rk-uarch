import json,hashlib
from pathlib import Path
out=Path('/tmp/u2-b-real-report-exits-v1-xn5pjr8z/outputs')
results=[]
for left,right in [('report','replay-report'),('repeat','report')]:
 a,b=out/left,out/right
 names={p.relative_to(a) for p in a.rglob('*') if p.is_file()}
 if left=='report':assert names=={p.relative_to(b) for p in b.rglob('*') if p.is_file()}
 count=0
 for n in sorted(names):
  with (a/n).open('rb') as x,(b/n).open('rb') as y:
   while True:
    aa,bb=x.read(1024*1024),y.read(1024*1024)
    assert aa==bb,str(n)
    count+=len(aa)
    if not aa:break
 results.append(dict(left=left,right=right,files=len(names),bytes=count))
Path('/tmp/u2-rr-c1-coordinator/stream-comparison.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results))
