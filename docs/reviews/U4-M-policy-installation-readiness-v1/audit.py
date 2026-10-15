"""Disposable M/policy validation only; no input staging, oracle or adoption operations."""

import argparse
import ast
import hashlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

BASE = "9b1408437b6dc08d9b77848f5fffe56c0cf1db72"
M = "docs/reviews/U4-A-M-package-v1/protected.patch"
POLICY = "docs/reviews/U3-B-artifact-dependency-audit-v1/repair.patch"
PINS = {
    M: "d392b24304a5f63fe69679ce991c5dbf2f742e95fee867a82dec2b0eef3a25e3",
    POLICY: "c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b",
}
PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    return {
        p.relative_to(root).as_posix(): (sha(p.read_bytes()), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def write(name, data):
    (PACKAGE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def export(revision, destination):
    destination.mkdir()
    with tarfile.open(fileobj=io.BytesIO(git(ROOT, "archive", revision))) as archive:
        archive.extractall(destination, filter="data")
    subprocess.run(["git", "init", "-q", str(destination)], check=True)


def setup(source, work):
    expected_m = {
        p["path"]: p["sha256"]
        for p in json.loads((ROOT / "docs/reviews/U4-A-M-package-v1/package.json").read_text())[
            "files"
        ]
    }
    rows = []
    for patch_path, pin in PINS.items():
        patch = ROOT / patch_path
        assert sha(patch.read_bytes()) == pin
        paths = [line[6:] for line in patch.read_text().splitlines() if line.startswith("+++ b/")]
        assert len(paths) == (26 if patch_path == M else 6)
        before = {
            path: sha((source / path).read_bytes()) if (source / path).exists() else None
            for path in paths
        }
        if patch_path == POLICY:
            # Independently reproduce the reviewed repair postimages at its previously audited base.
            old = work / "accepted-repair"
            old.mkdir()
            subprocess.run(["git", "init", "-q", str(old)], check=True)
            for path, digest in before.items():
                if digest is not None:
                    data = git(ROOT, "show", "f58e07828fa7a953b06800b227b948d7e9e71a88:" + path)
                    assert sha(data) == digest, "repair preimage drift: " + path
                    dest = old / path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
            subprocess.run(["git", "apply", "--check", str(patch)], cwd=old, check=True)
            subprocess.run(["git", "apply", str(patch)], cwd=old, check=True)
            expected = {path: sha((old / path).read_bytes()) for path in paths}
        else:
            expected = expected_m
        subprocess.run(["git", "apply", "--check", str(patch)], cwd=source, check=True)
        subprocess.run(["git", "apply", str(patch)], cwd=source, check=True)
        for path in paths:
            after = sha((source / path).read_bytes())
            assert after == expected[path], "postimage mismatch: " + path
            rows.append(
                {
                    "path": path,
                    "patch": patch_path,
                    "before_sha256": before[path],
                    "after_sha256": after,
                }
            )
    assert len({row["path"] for row in rows}) == 32
    write(
        "selection.json",
        {"base_commit": BASE, "patches": PINS, "files": sorted(rows, key=lambda row: row["path"])},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True)
    args = parser.parse_args()
    assert git(ROOT, "rev-parse", "HEAD").decode().strip() == BASE, "audit needs exact base"
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "origin/main"], cwd=ROOT, check=True
    )
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in {"PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN", "SHA", "RK", "PARAMS"}
    }
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
    checks = []

    def run(name, command, cwd, expected=0, contains=None):
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
        output = result.stdout + result.stderr
        if name != "inventory":
            (PACKAGE / (name + ".log")).write_text(output)
        checks.append(
            {
                "name": name,
                "argv": command,
                "cwd": str(cwd),
                "exit": result.returncode,
                "expected_exit": expected,
            }
        )
        write("checks.json", checks)
        print(name, result.returncode, output[-650:], flush=True)
        assert result.returncode == expected, name
        assert contains is None or contains in output, name
        return result.stdout

    prefix = "import sys;sys.path[:0]=['.','src','contract'];"
    strict = [
        args.python,
        "-B",
        "-c",
        prefix
        + "from scripts import vendor_rk;print('origin:',vendor_rk.__file__);vendor_rk.main()",
        "--check",
    ]
    live_before = {
        p: (sha((ROOT / p).read_bytes()), (ROOT / p).stat().st_mtime_ns)
        for p in git(ROOT, "ls-files", "-z").decode().split("\0")
        if p
    }
    run("live-currentness", strict, ROOT)
    with tempfile.TemporaryDirectory(prefix="u4-m-policy-") as temp:
        work = Path(temp)
        source = work / "source"
        export(BASE, source)
        setup(source, work)
        before = snapshot(source)

        def python(name, code, expected=0):
            return run(name, [args.python, "-B", "-c", prefix + code], source, expected)

        origins = python(
            "inventory",
            "import json,platform,os;"
            "from scripts import u2_support as p,u2_inputs as u,vendor_rk as v;"
            "import uarch_contract.mapped as m,uarch_contract.assumptions as a;"
            "mods=[p,u,v,m,a];"
            "assert all(os.path.realpath(x.__file__).startswith(os.getcwd()+'/') for x in mods);"
            "print(json.dumps({'origins':[x.__file__ for x in mods],"
            "'closure':p.inventory(),'broad_count':len(u.support_files()),"
            "'policy':p.POLICY,'python':sys.version,'executable':sys.executable,"
            "'platform':platform.platform(),'uname':list(platform.uname()),"
            "'oracle_sha256':v.digest(v.ORACLE_PROGRAM.encode()),"
            "'vendor_sha256':v.digest(open(v.__file__,'rb').read())},sort_keys=True))",
        )
        write("inventory.json", json.loads(origins))
        suites = [
            "tests/unit/test_u2_support_policy.py",
            "tests/unit/test_vendor_script_entry.py",
            "contract/tests/mapped",
            "contract/tests/test_rotary_v2.py",
            "tests/rotary_v2",
            "tests/unit/test_u2_a_prepared.py",
            "docs/reviews/U4-B-final-reconciliation-v1/test_fixture_inputs.py",
        ]
        run(
            "admission-policy-regressions",
            [
                args.python,
                "-B",
                "-m",
                "pytest",
                "-c",
                "pyproject.toml",
                "--rootdir",
                ".",
                "-p",
                "no:cacheprovider",
                "--basetemp",
                str(work / "pytest"),
                "-q",
                "-rs",
                *suites,
            ],
            source,
        )
        for module in ["generate_mapped", "generate", "generate_rotary_v2"]:
            python(
                module,
                "import runpy;sys.argv=['schema','--check'];"
                + "runpy.run_module('uarch_contract."
                + module
                + "',run_name='__main__')",
            )
        for name, targets in [
            ("mypy-source", ["src", "contract/uarch_contract", "scripts"]),
            ("mypy-contract-tests", ["--no-explicit-package-bases", "contract/tests"]),
        ]:
            run(
                name,
                [args.python, "-B", "-m", "mypy", "--cache-dir", str(work / name), *targets],
                source,
            )
        run("ruff", [args.python, "-B", "-m", "ruff", "check", "--no-cache", "."], source)
        python(
            "imports",
            "from importlinter.cli import lint_imports;"
            "sys.exit(lint_imports(no_cache=True,no_logo=True))",
        )
        run("combined-stale-refusal", strict, source, 1, "input support inventory changed")
        # Reached/leaf imports and non-import expressions are inspected without executing producers.
        audit = {}
        for name in [
            "contract/uarch_contract/mapped.py",
            "contract/uarch_contract/generate_mapped.py",
            "contract/tests/mapped/test_admission.py",
            "contract/tests/rotary_v2_cases.py",
        ]:
            tree = ast.parse((source / name).read_text())
            audit[name] = {
                "sha256": sha((source / name).read_bytes()),
                "imports": [
                    ast.unparse(n)
                    for n in ast.walk(tree)
                    if isinstance(n, (ast.Import, ast.ImportFrom))
                ],
                "read_or_dynamic_calls": [
                    ast.unparse(n)
                    for n in ast.walk(tree)
                    if isinstance(n, ast.Call)
                    and any(
                        part in ast.unparse(n.func)
                        for part in [
                            "read_",
                            "open",
                            "run_path",
                            "import_module",
                            "__import__",
                            "getenv",
                            "environ",
                            "glob",
                        ]
                    )
                ],
            }
        write("import-reads.json", audit)
        after_source = snapshot(source)
        delta = {
            path: {"before": before.get(path), "after": after_source.get(path)}
            for path in before.keys() | after_source.keys()
            if before.get(path) != after_source.get(path)
        }
        write("isolation-delta.json", delta)
        assert not delta, "source bytes/mtime changed during normal checks"
        write(
            "isolation.json",
            {
                "export_files_compared": len(before),
                "export_unchanged": True,
                "base_commit": BASE,
                "temporary_export_removed_on_exit": True,
            },
        )
    after = {p: (sha((ROOT / p).read_bytes()), (ROOT / p).stat().st_mtime_ns) for p in live_before}
    assert live_before == after, "live source changed"
    isolation = json.loads((PACKAGE / "isolation.json").read_text())
    isolation.update(live_tracked_files_compared=len(live_before), live_tracked_unchanged=True)
    write("isolation.json", isolation)


if __name__ == "__main__":
    main()
