"""Actual private .pth and timestamp-valid pyc vectors; no runtime authority."""

import hashlib
import importlib._bootstrap_external as bytecode
import importlib.util
import json
import subprocess
import sysconfig
import venv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
START = ROOT / "native/tools/component_trusted_start.py"


@pytest.fixture(scope="module")
def startup(tmp_path_factory):
    root = tmp_path_factory.mktemp("trusted-start")
    environment = root / "venv"
    venv.create(environment, with_pip=False)
    python = environment / "bin/python"
    site = next((environment / "lib").glob("python*/site-packages"))
    project = root / "project"
    package = project / "validation/component"
    package.mkdir(parents=True)
    (project / "validation/__init__.py").write_text("")
    (package / "__init__.py").write_text("")
    checker = package / "observations_v3.py"
    checker.write_text(
        "def check_v3(job, result, expected):\n"
        "    if result != 'valid': raise ValueError('independent corruption refusal')\n"
        "    return {}\n"
    )
    (project / "entry.py").write_text(
        "import json,sys\nfrom validation.component.observations_v3 import check_v3\n"
        "check_v3(None, 'valid', None)\n"
        "try: check_v3(None, 'corrupt', None)\n"
        "except ValueError: outcome='refused'\n"
        "else: outcome='UNSAFE ACCEPTANCE'\n"
        "state=sys.modules.get('_rkuarch_trusted_startup')\n"
        "if state: state.refresh()\n"
        "print(json.dumps({'outcome':outcome,'site':'site' in sys.modules,"
        "'hook':'zz_probe' in sys.modules}))\n"
    )
    stdlib = Path(sysconfig.get_path("stdlib"))
    roots = [project, site, stdlib, stdlib / "lib-dynload"]
    files = {}
    for parent in (project, stdlib):
        for f in parent.rglob("*"):
            if f.is_file() and f.suffix in (".py", ".so") and "site-packages" not in f.parts:
                files[str(f.resolve())] = hashlib.sha256(f.read_bytes()).hexdigest()
    manifest = root / "startup.json"
    manifest.write_text(json.dumps({"roots": list(map(str, roots)), "files": files}))
    yield root, python, site, project, checker, manifest


def invoke(startup, trusted, launcher=START):
    _, python, _, project, _, manifest = startup
    if trusted:
        argv = [
            str(python),
            "-I",
            "-S",
            "-B",
            str(launcher),
            str(manifest),
            hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "entry",
        ]
    else:
        argv = [
            str(python),
            "-I",
            "-B",
            "-c",
            f"import sys;sys.path.insert(0,{str(project)!r});import entry",
        ]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_valid_startup(startup):
    assert invoke(startup, True) == {"outcome": "refused", "site": False, "hook": False}


@pytest.mark.parametrize("vector", ["pth", "pyc"])
def test_real_substitution_is_blocked_and_restored(startup, vector, tmp_path):
    _, _, site, _, checker, _ = startup
    original = checker.read_bytes()
    pth, hook = site / "zz_probe.pth", site / "zz_probe.py"
    pyc = Path(importlib.util.cache_from_source(str(checker)))
    if vector == "pth":
        pth.write_text("import zz_probe\n")
        hook.write_text(
            "import importlib.machinery,sys\n"
            "class Finder:\n"
            " def find_spec(self,name,path=None,target=None):\n"
            "  if name!='validation.component.observations_v3': return None\n"
            "  spec=importlib.machinery.PathFinder.find_spec(name,path); real=spec.loader\n"
            "  class Loader:\n"
            "   def create_module(self,s): return real.create_module(s)\n"
            "   def exec_module(self,m):\n"
            "    real.exec_module(m);m.check_v3=lambda *args:{}\n"
            "  spec.loader=Loader();return spec\n"
            "sys.meta_path.insert(0,Finder())\n"
        )
    else:
        code = compile(
            original.decode() + "\ndef check_v3(*args): return {}\n", str(checker), "exec"
        )
        st = checker.stat()
        pyc.parent.mkdir(exist_ok=True)
        pyc.write_bytes(bytecode._code_to_timestamp_pyc(code, int(st.st_mtime), st.st_size))
    try:
        assert invoke(startup, False)["outcome"] == "UNSAFE ACCEPTANCE"
        assert checker.read_bytes() == original
        assert invoke(startup, True) == {"outcome": "refused", "site": False, "hook": False}
        if vector == "pyc":
            # Revert only the no-bytecode-read defense, leaving source pins intact.
            scratch = tmp_path / "start.py"
            original_launcher = START.read_bytes()
            text = original_launcher.decode()
            target = 'return compile(checked(self.path), self.path, "exec", dont_inherit=True)'
            assert text.count(target) == 1
            scratch.write_text(
                text.replace(target, "checked(self.path); return super().get_code(fullname)")
            )
            assert invoke(startup, True, scratch)["outcome"] == "UNSAFE ACCEPTANCE"
            scratch.write_bytes(original_launcher)
            assert invoke(startup, True, scratch)["outcome"] == "refused"
            assert scratch.read_bytes() == START.read_bytes()
        else:
            # Relevant launch-defense revert: -I -B still executes this actual .pth.
            # Startup flag refusal cannot undo site code that has already executed.
            assert invoke(startup, False)["hook"] is True
            assert invoke(startup, True)["hook"] is False
    finally:
        for f in (pth, hook, pyc):
            f.unlink(missing_ok=True)
    assert invoke(startup, False)["outcome"] == "refused"
    assert invoke(startup, True)["outcome"] == "refused"
