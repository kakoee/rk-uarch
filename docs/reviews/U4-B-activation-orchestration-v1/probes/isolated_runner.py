"""Run pytest or a script against a private export with every live clone path removed.

Usage: python -I runner.py EXPORT pytest <args...>
       python -I runner.py EXPORT script <path.py> <args...>
Fails if any project module was imported from outside EXPORT.
"""

import json
import os
import runpy
import sys

LIVE = [
    "/home/jjaff/AI-infra-simulation/rk-uarch",
    "/home/jjaff/AI-infra-simulation/rk-uarch-u4-a",
    "/home/jjaff/AI-infra-simulation/rk-uarch-u4-b",
]
root = os.path.realpath(sys.argv[1])
mode, rest = sys.argv[2], sys.argv[3:]


def live(p: str) -> bool:
    return any((p == x or p.startswith(x + "/")) and "/.venv/" not in p for x in LIVE)


sys.path[:] = [p for p in sys.path if not live(p)]
sys.path[:0] = [root, root + "/src", root + "/contract"]
os.chdir(root)
for k in ("PYTHONPATH", "MYPYPATH"):
    os.environ.pop(k, None)
sys.dont_write_bytecode = True
PROJECT = ("uarch_contract", "rkuarch", "validation")


def origins() -> dict:
    bad, seen = [], {}
    for name, mod in sorted(sys.modules.items()):
        f = getattr(mod, "__file__", None) or ""
        # Namespace packages have no __file__; every __path__ entry must be inside the export.
        paths = [f] if f else [str(p) for p in getattr(mod, "__path__", [])]
        if any(live(p) for p in paths):
            bad.append((name, paths))
        if name.split(".")[0] in PROJECT:
            seen[name] = paths[0] if paths else ""
            if not paths or not all(p.startswith(root + "/") for p in paths):
                bad.append((name, paths))
    return dict(live_or_foreign=bad, project_modules=len(seen),
                sample={k: seen[k] for k in sorted(seen) if k in (
                    "uarch_contract.mapped", "uarch_contract.mapped_issue",
                    "validation.component.issue_checks", "validation.component.observations_v3",
                    "validation.component.transition_checks_v3")})


if mode == "pytest":
    import pytest

    class Origins:
        def pytest_sessionfinish(self, session, exitstatus):
            o = origins()
            print("\nREVIEW-ORIGINS " + json.dumps(o, sort_keys=True))
            assert not o["live_or_foreign"], o["live_or_foreign"]

    sys.exit(int(pytest.main(["-c", root + "/pyproject.toml", "--rootdir", root,
                              "-p", "no:cacheprovider", *rest], plugins=[Origins()])))
elif mode == "script":
    sys.argv = rest
    try:
        runpy.run_path(rest[0], run_name="__main__")
    finally:
        o = origins()
        print("REVIEW-ORIGINS " + json.dumps(o, sort_keys=True))
        assert not o["live_or_foreign"], o["live_or_foreign"]
else:
    raise SystemExit("mode")
