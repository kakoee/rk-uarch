"""Read-only scoped diff, retained-consumer and historical-byte inspection."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

REPO=Path('/tmp/u4-recheck-808076a-pin')
ROOT=Path('/tmp/u4-recheck-808076a-source')
OLD=Path('/tmp/u4-recheck-808076a-v1-source')
OUT=Path(__file__).resolve().parents[1]/'receipts'
V1='b0f1755e52bfe1a3a7ee6f3b37da77a4f8ce3ac0'
V2='9a86cab622504e68746534c94e93b659cacf794d'
package=REPO/'docs/reviews/U4-ordinary-runtime-correction-v2'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()=='808076a8f1786f00ef9e3cd0de6ab8f2adea83ad'
assert hashlib.sha256((package/'transition.patch').read_bytes()).hexdigest()==(package/'transition.sha256').read_text().split()[0]
diff=subprocess.check_output(['git','diff','--no-renames','--name-status',V1,V2],cwd=REPO,text=True)
(OUT/'correction-changes.txt').write_text(diff)
changes=[line.split('\t') for line in diff.splitlines()]
code_changes=[(s,p) for s,p in changes if not p.startswith('docs/reviews/')]
allow=('CLAUDE.md','README.md','ruff.toml','hatch.toml','contract/uarch_contract/ordinary.py','docs/build-spec.md',
       'docs/decisions/U0011-the-native-engine-core.md','native/','src/rkuarch/engines/native/',
       'src/rkuarch/workload/mapped.py','tests/component_current_identity.py','tests/native/',
       'tests/unit/test_component_','tests/unit/test_u4_k2_','tests/unit/test_ordinary_native.py','validation/component/')
assert all(any(p==a or p.startswith(a) for a in allow) for s,p in code_changes)
# Historical data, analytic/table/report code, dependency/lockfiles and hosted workflows.
protected=('tests/golden/','native/crates/uarch-engine/testdata/','contract/fixtures/','contract/schema/mapped/',
           'third_party/','hw/','src/rkuarch/table/','src/rkuarch/report/','src/rkuarch/provenance/',
           'src/rkuarch/engines/analytic','validation/reporting/','.github/','pyproject.toml','uv.lock',
           'native/Cargo.toml','native/Cargo.lock')
assert not [(s,p) for s,p in changes if any(p.startswith(x) for x in protected)]
# All historical review files in the original reconstruction survive byte-exactly.
history=[p for p in (OLD/'docs/reviews').rglob('*') if p.is_file()]
assert all((ROOT/p.relative_to(OLD)).read_bytes()==p.read_bytes() for p in history)
modules=('arithmetic','checks','issue_checks','matrix_order','phase_laws','transition_checks_v3','observations_v3')
for name in modules:
 assert not (ROOT/f'validation/component/{name}.py').exists()
 assert (ROOT/f'src/rkuarch/verification/component/{name}.py').read_bytes()==(OLD/f'src/rkuarch/verification/component/{name}.py').read_bytes()
# Removal of host machinery leaves no imports in active Python source or default tests.
deleted=[p for status,p in code_changes if status=='D' and p.endswith('.py')]
lookup={p:p.removeprefix('src/').removesuffix('.py').replace('/','.') for p in deleted}
remaining={}
for folder in ['src','contract','validation','tests','native/tools']:
 for p in (ROOT/folder).rglob('*.py'):
  if 'contract/vendor/' in str(p):continue
  tree=ast.parse(p.read_text());imports=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):imports.extend(a.name for a in n.names)
   if isinstance(n,ast.ImportFrom) and n.module:
    imports += [n.module]+[n.module+'.'+a.name for a in n.names]
  for path,module in lookup.items():
   if module in imports:remaining.setdefault(path,[]).append(str(p.relative_to(ROOT)))
assert not remaining,remaining
# Keep named archived consumers exact; historical helpers are pure observation checks.
consumers={}
for name in ['native_check','selection','runtime_checks']:
 consumers[name]=[str(p.relative_to(ROOT)) for p in ROOT.rglob('*.py')
                  if '__pycache__' not in str(p) and f'validation.component.{name} import' in p.read_text()]
# Deleted files include mixed-purpose tests; list their functions, do not label all as retired laws.
functions={}
for path in deleted:
 if Path(path).name.startswith('test_'):
  tree=ast.parse((OLD/path).read_text())
  functions[path]=[n.name for n in tree.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
(OUT/'deleted-test-functions.json').write_text(json.dumps(functions,indent=2)+'\n')
transport=subprocess.check_output(['git','diff',V1,V2,'--','src/rkuarch/engines/native/transport.py'],cwd=REPO,text=True)
(OUT/'transport-diff.txt').write_text(transport)
assert (ROOT/'src/rkuarch/engines/native/ordinary.py').read_bytes()==(OLD/'src/rkuarch/engines/native/ordinary.py').read_bytes()
(OUT/'inventory.json').write_text(json.dumps({'pin':'808076a8f1786f00ef9e3cd0de6ab8f2adea83ad','source_tree':V2,
 'patch_sha256':hashlib.sha256((package/'transition.patch').read_bytes()).hexdigest(),
 'correction_changed_files':len(code_changes),'historical_review_files_unchanged':len(history),
 'unchanged_shipped_checker_modules':list(modules),'remaining_active_deleted_module_imports':remaining,
 'retained_historical_consumers':consumers,'ordinary_runtime_byte_identical_to_v1':True,
 'unrelated_analytic_table_report_and_data_unchanged':True},indent=2)+'\n')
print('Scoped source/data/import inventory passed.')
