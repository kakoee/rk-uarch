"""Run private proposal checks with asserted project origins, not editable-install paths.

Usage: python -I -B isolated.py PRIVATE_ROOT pytest [pytest args...]
       python -I -B isolated.py PRIVATE_ROOT module MODULE [module args...]
"""

import os
import runpy
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
mode, args = sys.argv[2], sys.argv[3:]
sys.path[:] = [str(root), str(root / "src"), str(root / "contract")] + [
    p for p in sys.path if p and ("site-packages" in p or ("rk-uarch" not in p and "/tmp" not in p))
]
os.chdir(root)
for key in ("PYTHONPATH", "MYPYPATH"):
    os.environ.pop(key, None)
if mode == "pytest":
    import pytest

    status = pytest.main(args)
else:
    assert mode == "module"
    sys.argv = args
    runpy.run_module(args[0], run_name="__main__")
    status = 0
for name, module in tuple(sys.modules.items()):
    if name.split(".")[0] in ("rkuarch", "uarch_contract", "validation", "scripts"):
        filename = getattr(module, "__file__", None)
        if filename:
            assert Path(filename).resolve().is_relative_to(root), (name, filename)
raise SystemExit(status)
