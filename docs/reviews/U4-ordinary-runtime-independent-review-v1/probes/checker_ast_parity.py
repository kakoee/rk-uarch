"""Compare packaged independent checkers with their validation/ originals.

Usage: python -I checker_ast_parity.py RECONSTRUCTED_TREE
Normalizes only the import module prefix validation.component -> rkuarch.verification.component
and reports any other AST difference. Also reports whether any test pins the two copies together.
"""

import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
packaged = root / "src/rkuarch/verification/component"
original = root / "validation/component"


class Rename(ast.NodeTransformer):
    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        if node.module and node.module.startswith("validation.component"):
            node.module = "rkuarch.verification.component" + node.module[len("validation.component"):]
        return node


status = 0
for path in sorted(packaged.glob("*.py")):
    if path.name == "__init__.py":
        continue
    old = Rename().visit(ast.parse((original / path.name).read_text()))
    new = ast.parse(path.read_text())
    same = ast.dump(old) == ast.dump(new)
    print(f"{path.name}: {'AST-equal after import rename' if same else 'DIFFERENT'}")
    status |= not same

pins = [
    p.relative_to(root).as_posix()
    for p in (root / "tests").rglob("*.py")
    if "verification/component" in p.read_text() or "verification.component" in p.read_text()
]
pins += [
    p.relative_to(root).as_posix()
    for p in (root / "validation").rglob("*.py")
    if "verification.component" in p.read_text() or "verification/component" in p.read_text()
]
print("tests/validation files referencing the packaged copy:", pins or "none")
sys.exit(status)
