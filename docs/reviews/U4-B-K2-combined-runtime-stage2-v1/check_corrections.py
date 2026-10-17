"""Private essential-guard removal/restoration tests. Never edits target or historical code."""

import argparse
import ast
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def replace_function(text, name, replacement):
    tree = ast.parse(text)
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = text.splitlines(True)
    assert node.end_lineno is not None
    lines[node.lineno - 1 : node.end_lineno] = [replacement + "\n"]
    return "".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    assert a.output.is_absolute() and a.output.is_relative_to("/tmp") and not a.output.exists()
    a.output.mkdir()
    config = a.output / "pytest.ini"
    config.write_text("[pytest]\n")
    choices = [
        ("F1", "publication.py", "test_F1_unpushed_local_tracking_ref_is_not_publication"),
        ("F2-host", "launch.py", "test_F2_incomplete_launch_refuses_before_process"),
        ("F2-runtime", "runtime_entry.py", "test_F2_container_gate_precedes_resolution"),
        ("F3", "bindings.py", "test_F3_observation_shape_and_private_distinctions"),
        ("F4", "launch.py", "test_F4_store_transient_disappears_during_actual_poll"),
        ("F5", "bindings.py", "test_F5_earlier_helper_shadow_refused"),
        ("F6", "bindings.py", "test_F6_unknown_decision_condition_refused"),
    ]
    results = []
    for finding, file, test in choices:
        root = a.output / finding
        shutil.copytree(a.package, root / "package")
        package = root / "package"
        target = package / file
        original = target.read_bytes()
        text = original.decode()
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN")
        }
        env.update(STAGE2_PACKAGE=str(package), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
        argv = [
            sys.executable,
            "-I",
            "-B",
            "-m",
            "pytest",
            "-q",
            "-c",
            str(config),
            "--rootdir=" + str(root),
            "-p",
            "no:cacheprovider",
            str(package / "test_stage2.py") + "::" + test,
        ]

        def run(label, argv=argv, env=env, root=root):
            result = subprocess.run(argv, env=env, capture_output=True, timeout=60)
            raw = result.stdout + result.stderr
            (root / (label + ".log")).write_bytes(raw)
            return result.returncode, raw

        before, _ = run("corrected")
        assert before == 0, finding + " corrected baseline must pass"
        if finding == "F1":
            # Reintroduce local-object authority instead of the isolated remote context.
            changed = replace_function(
                text,
                "read",
                """    def read(self, commit: str, path: str) -> bytes:
        return subprocess.check_output(["/usr/bin/git", "show", commit + ":" + path],
            cwd=Path(self.endpoint).parent / "local", env=self.env)""",
            )
        elif finding == "F2-host":
            changed = text.replace(
                'replay_admission(output, binding, b.read(b.OLD / "campaign/campaign-plan.json"))',
                "None  # removed replay admission guard",
            )
        elif finding == "F2-runtime":
            changed = text.replace(
                "replay_admission(OUT, BINDING, context[1])",
                "None  # removed container replay admission guard",
            )
        elif finding == "F3":
            start = text.index('        need(\n            seal["seal_check_enforced"]')
            end = text.index("        need(", start + 10)
            changed = (
                text[:start]
                + '        need(True, "removed observed production seal check")\n'
                + text[end:]
            )
        elif finding == "F4":
            changed = text.replace(
                "            continue\n        b.need(not stat.S_ISLNK",
                "            raise\n        b.need(not stat.S_ISLNK",
            )
        elif finding == "F5":
            changed = replace_function(
                text,
                "helper_origins",
                (
                    "def helper_origins(modules, expected):\n"
                    "    return expected  # removed helper file identity guard"
                ),
            )
        else:
            changed = text.replace(
                'need(set(decision) == DECISION_FIELDS, "exact decision schema fields")',
                'need(True, "removed exact decision schema fields")',
            )
        assert changed != text, finding + " essential mutation applied"
        ast.parse(changed)
        (root / "guard-removal.patch").write_text(
            "".join(
                difflib.unified_diff(
                    text.splitlines(True),
                    changed.splitlines(True),
                    fromfile="a/" + file,
                    tofile="b/" + file,
                )
            )
        )
        try:
            target.write_text(changed)
            removed, failure = run("removed")
            assert removed == 1 and b"FAILED" in failure, finding + " must fail a real assertion"
            assert b"ERROR collecting" not in failure and b"ModuleNotFoundError" not in failure, (
                "setup failure is not discrimination"
            )
        finally:
            target.write_bytes(original)
        restored, _ = run("restored")
        assert restored == 0 and target.read_bytes() == original
        results.append(
            {
                "finding": finding,
                "test": test,
                "source_hash": digest(original),
                "corrected_exit": before,
                "removed_exit": removed,
                "restored_exit": restored,
                "exact_restoration": True,
                "patch_hash": digest((root / "guard-removal.patch").read_bytes()),
                "failure_log_hash": digest(failure),
            }
        )
    (a.output / "checks.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
