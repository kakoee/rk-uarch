"""Run private author checks with explicit configuration and asserted source origins."""

import json
import os
import runpy
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
mode, arguments = sys.argv[2], sys.argv[3:]
# Keep installed dependencies, remove every editable project path before importing code.
sys.path[:] = [p for p in sys.path if "site-packages" in p or "python3.12" in p]
sys.path[:0] = [str(root), str(root / "src"), str(root / "contract")]
os.chdir(root)
os.environ.pop("PYTHONPATH", None)
os.environ.pop("MYPYPATH", None)
sys.dont_write_bytecode = True


def verify():
    origins = {}
    for name, module in sys.modules.items():
        if name.split(".")[0] in ("rkuarch", "uarch_contract", "validation"):
            filename = getattr(module, "__file__", None)
            if filename:
                path = Path(filename).resolve()
                assert path.is_relative_to(root), (name, str(path))
                origins[name] = str(path.relative_to(root))
    print("B-PRIVATE-ORIGINS " + json.dumps(origins, sort_keys=True))


if mode == "pytest":
    import pytest

    class OriginCheck:
        def pytest_sessionfinish(self, session, exitstatus):
            verify()

    sys.exit(
        pytest.main(
            [
                "-c",
                str(root / "pyproject.toml"),
                "--rootdir",
                str(root),
                "-p",
                "no:cacheprovider",
                *arguments,
            ],
            plugins=[OriginCheck()],
        )
    )
elif mode == "script":
    sys.argv = arguments
    try:
        runpy.run_path(arguments[0], run_name="__main__")
    finally:
        verify()
else:
    raise SystemExit("expected pytest or script")
