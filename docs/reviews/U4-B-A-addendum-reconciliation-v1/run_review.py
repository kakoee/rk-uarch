"""Bounded host review only. Caller prepares three private exports per README."""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    return {
        str(p.relative_to(root)): (sha(p), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


def main(work):
    work = work.resolve()
    package = Path(__file__).resolve().parent
    assert work.is_relative_to(Path("/tmp"))
    roots = {x: work / x for x in ("baseline", "proposed", "guarded")}
    assert all(x.is_dir() and not (x / ".git").exists() for x in roots.values())
    out = work / "receipts"
    out.mkdir(exist_ok=True)
    env = dict(os.environ)
    for name in ("PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN"):
        env.pop(name, None)
    py = [sys.executable, "-I", "-B"]
    rows = []
    before = {name: snapshot(root) for name, root in roots.items()}

    def run(name, root, command, expected=0, needle=None):
        start = time.monotonic()
        r = subprocess.run(
            command, cwd=root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        log = out / (name + ".log")
        log.write_text(r.stdout)
        rows.append(
            dict(
                name=name,
                command=command,
                cwd=str(root),
                exit=r.returncode,
                expected_exit=expected,
                seconds=round(time.monotonic() - start, 3),
                log_sha256=sha(log),
            )
        )
        (out / "checks.partial.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(name, r.returncode, r.stdout[-250:], flush=True)
        assert r.returncode == expected, (name, r.stdout)
        if needle:
            assert needle in r.stdout, (name, r.stdout)

    def setup(root):
        paths = [
            package,
            root / "docs/reviews/U4-B-K2-semantic-reconciliation-v1",
            root / "docs/reviews/U4-A-K2-semantic-construction-v1",
            root,
            root / "src",
            root / "contract",
        ]
        return (
            "import sys; from pathlib import Path; sys.path[:0]="
            + repr(list(map(str, paths)))
            + "; "
            "import uarch_contract.mapped as m, rkuarch.workload.mapped as loader; "
            f"r=Path({str(root)!r}); "
            "assert Path(m.__file__).resolve().is_relative_to(r); "
            "assert Path(loader.__file__).resolve().is_relative_to(r); "
        )

    def tests(name, which, selection, expected=0, needle=None):
        root = roots[which]
        args = [
            "-q",
            "-c",
            str(root / "pyproject.toml"),
            "--rootdir=" + str(root),
            "-p",
            "no:cacheprovider",
            "--basetemp=" + str(work / ("pytest-" + name)),
            *selection,
        ]
        run(
            name,
            root,
            py
            + [
                "-c",
                setup(root) + "import pytest; raise SystemExit(pytest.main(" + repr(args) + "))",
            ],
            expected,
            needle,
        )

    b = "docs/reviews/U4-B-K2-semantic-reconciliation-v1/"
    tests(
        "preserved-B",
        "baseline",
        [b + "test_literals.py", b + "test_membership.py", b + "test_boundary.py"],
    )
    tests(
        "exact-A-joins",
        "proposed",
        [str(package / "test_joins.py"), "-k", "not notification_must_follow"],
    )
    tests(
        "notification-baseline",
        "proposed",
        [str(package / "test_joins.py") + "::test_notification_must_follow_its_zero_completion"],
        1,
        "DID NOT RAISE",
    )
    tests("records-plan", "proposed", [str(package / "test_records_and_plan.py")])
    tests("guard-corrected", "guarded", [str(package / "test_joins.py")])
    patch = package / "notification-order.proposed.patch"
    path = roots["guarded"] / "contract/uarch_contract/mapped.py"
    expected_guard = sha(path)
    run("guard-reverse", roots["guarded"], ["git", "apply", "--reverse", str(patch)])
    assert sha(path) == sha(roots["proposed"] / "contract/uarch_contract/mapped.py")
    tests(
        "notification-reverted",
        "guarded",
        [str(package / "test_joins.py") + "::test_notification_must_follow_its_zero_completion"],
        1,
        "DID NOT RAISE",
    )
    run("guard-forward", roots["guarded"], ["git", "apply", str(patch)])
    assert sha(path) == expected_guard
    tests(
        "notification-restored",
        "guarded",
        [str(package / "test_joins.py") + "::test_notification_must_follow_its_zero_completion"],
    )
    tests(
        "affected-regressions",
        "guarded",
        [
            "contract/tests/mapped",
            "tests/unit/test_u4_a_mapped_loader.py",
            "tests/unit/test_prompt_sync.py",
        ],
    )
    for which, root in roots.items():
        run(
            which + "-audit",
            root,
            py + [str(package / "audit_source.py"), str(root), str(out / (which + "-audit.json"))],
        )
        run(
            which + "-schema",
            root,
            py
            + [
                "-c",
                setup(root) + "from uarch_contract.generate_mapped import generate; "
                "assert generate(check=True)==[]; "
                'print("Mapped schemas fresh; private origins checked.")',
            ],
        )
    tools = Path(sys.executable).parent
    run(
        "ruff",
        roots["guarded"],
        [
            str(tools / "ruff"),
            "check",
            "--no-cache",
            str(package),
            "contract/uarch_contract/mapped.py",
        ],
    )
    for name, args in [
        ("source-types", ["src", "contract/uarch_contract", "scripts"]),
        ("contract-types", ["--no-explicit-package-bases", "contract/tests"]),
    ]:
        run(
            name,
            roots["guarded"],
            [str(tools / "mypy"), "--cache-dir", str(work / ("mypy-" + name)), *args],
        )
    preservation = {}
    for which, root in roots.items():
        after = snapshot(root)
        old = before[which]
        changed = sorted(k for k in old.keys() & after.keys() if old[k] != after[k])
        added = sorted(after.keys() - old.keys())
        removed = sorted(old.keys() - after.keys())
        # Only the guarded mapped.py mtime can change through exact reverse/forward.
        assert not removed
        assert (
            all(k == "contract/uarch_contract/mapped.py" for k in changed)
            if which == "guarded"
            else not changed
        )
        assert all(k.endswith(".pyc") and "/__pycache__/" in k for k in added)
        assert all(old[k][0] == after[k][0] for k in changed)
        preservation[which] = dict(
            existing_files=len(old),
            added_scratch_bytecode=added,
            removed=removed,
            existing_bytes_changed=[],
            mtime_only_changes=changed,
        )
    receipt = dict(
        subject="1a52fa82f3aabc3eca5de4fa5597295a0fa04e27",
        python=sys.version,
        environment_unset=["PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN"],
        commands=rows,
        preservation=preservation,
        native_execution=False,
        cargo_resolution_build_or_run=False,
        live_mutation=False,
    )
    (out / "checks.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
