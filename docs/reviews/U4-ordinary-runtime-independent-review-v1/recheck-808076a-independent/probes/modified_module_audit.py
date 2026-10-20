"""Classify v1->v2 edits to retained Python modules: import-only vs substantive.

Usage: python3 -I modified_module_audit.py V1_TREE V2_TREE NAME_STATUS_FILE
Normalises `validation.component.<shipped>` imports to `rkuarch.verification.component.<shipped>`
and strips docstrings, then compares ASTs per top-level definition. For test modules it also
reports test functions and `assert`/`pytest.raises` counts removed or added.
"""

import ast
import json
import sys
from pathlib import Path

v1, v2 = Path(sys.argv[1]), Path(sys.argv[2])
modified = [l.split()[1] for l in open(sys.argv[3]) if l.startswith("M") and l.split()[1].endswith(".py")]
SHIPPED = {"arithmetic", "checks", "issue_checks", "matrix_order", "observations_v3", "phase_laws",
           "transition_checks_v3"}


class Norm(ast.NodeTransformer):
    def visit_ImportFrom(self, node):
        if node.module:
            head, _, tail = node.module.rpartition(".")
            if head == "validation.component" and tail in SHIPPED:
                node.module = "rkuarch.verification.component." + tail
        return node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None
        return node


def defs(path):
    tree = Norm().visit(ast.parse(path.read_text()))
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        name = getattr(node, "name", None) or ast.dump(node)[:60]
        out[name] = ast.dump(node)
    imports = sorted(ast.dump(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom)))
    return out, imports


def counts(path):
    t = ast.parse(path.read_text())
    tests = {n.name for n in ast.walk(t) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
    asserts = sum(isinstance(n, ast.Assert) for n in ast.walk(t))
    raises = sum(isinstance(n, ast.Attribute) and n.attr == "raises" for n in ast.walk(t))
    return tests, asserts, raises


report = {}
for rel in modified:
    a, b = v1 / rel, v2 / rel
    da, ia = defs(a)
    db, ib = defs(b)
    changed = sorted(k for k in da.keys() & db.keys() if da[k] != db[k])
    row = {"removed_defs": sorted(da.keys() - db.keys()), "added_defs": sorted(db.keys() - da.keys()),
           "changed_defs": changed, "imports_changed": ia != ib}
    row["class"] = ("import/docstring-only" if not (row["removed_defs"] or row["added_defs"] or changed)
                    else "substantive")
    if Path(rel).name.startswith("test_"):
        ta, aa, ra = counts(a)
        tb, ab, rb = counts(b)
        row.update(tests_removed=sorted(ta - tb), tests_added=sorted(tb - ta),
                   asserts=f"{aa}->{ab}", raises=f"{ra}->{rb}")
    report[rel] = row
summary = {}
for rel, row in report.items():
    summary.setdefault(row["class"], []).append(rel)
print(json.dumps({"summary": {k: len(v) for k, v in summary.items()},
                  "substantive": {k: v for k, v in report.items() if v["class"] == "substantive"},
                  "import_or_docstring_only": summary.get("import/docstring-only", [])}, indent=1))
