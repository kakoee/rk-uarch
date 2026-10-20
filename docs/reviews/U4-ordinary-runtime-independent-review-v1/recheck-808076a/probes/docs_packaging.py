"""Read-only advisory and exact wheel/source checks; no installation."""
import ast
import hashlib
import json
import zipfile
from pathlib import Path
ROOT=Path('/tmp/u4-recheck-808076a-source')
OLD=Path('/tmp/u4-recheck-808076a-v1-source')
PKG=Path('/tmp/u4-recheck-808076a-pin/docs/reviews/U4-ordinary-runtime-correction-v2')
OUT=Path(__file__).resolve().parents[1]/'receipts'
claims={}
for name in ['CLAUDE.md','docs/build-spec.md','src/rkuarch/workload/mapped.py']:
 s=(ROOT/name).read_text()
 assert 'native, grids and studies are planned' not in s
 assert 'Native is planned, not yet implemented' not in s
 assert 'must revalidate current bytes and verify its executable against accepted build receipts' not in s
 claims[name]=[(i+1,line) for i,line in enumerate(s.splitlines())
               if any(x in line for x in ['ordinary /4','implemented through','Shared component validation','without host authority'])]
for name in ['README.md','native/README.md','docs/build-spec.md','docs/decisions/U0011-the-native-engine-core.md']:
 s=(ROOT/name).read_text()
 assert '0.0.1' in s and 'cross-version replay' in s
 claims[name]=claims.get(name,[])+[(i+1,line) for i,line in enumerate(s.splitlines())
               if any(x in line for x in ['0.0.1','distinguish builds','Compatibility policy','compatibility decision','cross-version replay'])]
assert 'package_version: Literal["0.0.1"]' in (ROOT/'contract/uarch_contract/ordinary.py').read_text()
assert 'job.engine.package_version == version("rk-uarch")' in (ROOT/'src/rkuarch/engines/native/ordinary.py').read_text()
# Runtime wheel from the pinned receipt remains available; inspect, do not install.
digests=json.loads((PKG/'evidence/artifact-digests.json').read_text())
wheel=next(Path(n) for n in digests if n.endswith('.whl'))
assert hashlib.sha256(wheel.read_bytes()).hexdigest()==digests[str(wheel)]
checked=[]
with zipfile.ZipFile(wheel) as z:
 names=z.namelist()
 assert sorted(n for n in names if n.startswith('rkuarch/engines/native/'))==sorted('rkuarch/engines/native/'+n for n in ['__init__.py','ordinary.py','transport.py'])
 for name in names:
  if name.endswith('.py') and name.startswith('rkuarch/'):
   assert z.read(name)==(ROOT/'src'/name).read_bytes();checked.append(name)
  elif name.endswith('.py') and name.startswith('uarch_contract/'):
   assert z.read(name)==(ROOT/'contract'/name).read_bytes();checked.append(name)
  elif name.startswith('rkuarch/schemas/ordinary/'):
   assert z.read(name)==(ROOT/'contract/schema/ordinary'/Path(name).name).read_bytes();checked.append(name)
 assert not any(n.startswith(('validation/','tests/','docs/')) for n in names)
# Shared mapped logic is unchanged after removing module documentation.
def body(path):
 t=ast.parse(path.read_text());t.body=t.body[1:];return ast.dump(t)
assert body(ROOT/'src/rkuarch/workload/mapped.py')==body(OLD/'src/rkuarch/workload/mapped.py')
# Inspect receipt claims instead of repeating the installed/timing/process campaigns.
run=json.loads((PKG/'evidence/smoke-run.stdout').read_text())
replay=json.loads((PKG/'evidence/smoke-replay.stdout').read_text())
assert len(run['negative_controls'])==26
assert replay['native_binary']=='absent'
assert all(c['debug_release_equal'] for c in run['cases'].values())
(OUT/'docs-packaging.json').write_text(json.dumps({'advisory_statements':claims,
 'wheel_sha256':digests[str(wheel)],'wheel_source_members_equal':len(checked),
 'shared_mapped_ast_unchanged':True,'inherited_smoke_cases':run['cases'],
 'inherited_negative_controls':26,'inherited_binary_free_replay':True},indent=2)+'\n')
print('A1/A2 statements, wheel source bytes and inherited smoke receipts verified.')
