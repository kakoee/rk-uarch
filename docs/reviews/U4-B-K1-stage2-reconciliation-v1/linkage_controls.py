"""Real graph-bound F5 controls, confined to a previously verified private export."""

import argparse
import json
import os
import subprocess
from pathlib import Path

import native_check as n


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    work = args.work.resolve()
    assert work.parent == Path("/tmp") and work.name.startswith("u4-b-k1-native-stage2-")
    source, receipts = work / "source", work / "receipts"
    assert source.resolve() == source and not (source / ".git").exists()
    subject = json.loads((n.HERE / "subject.json").read_text())
    for path, expected in subject["postimages"].items():
        assert n.sha(source / path) == expected
    verified = json.loads((receipts / "verified.json").read_text())
    assert verified["image_id"] == subject["image_id"]
    metadata = receipts / "metadata-full.stdout"
    command = json.loads((receipts / "metadata-full.json").read_text())
    assert command["exit"] == 0
    assert json.loads(metadata.read_text())["workspace_root"] == str(source / "native")
    c = n.load(source / n.OLD / "construct.py", "linkage_construct")
    initial = c.snapshot(source)
    records = []
    env = os.environ.copy()
    for key in ("PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN", "K1_METADATA"):
        env.pop(key, None)
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", K1_METADATA=str(metadata))
    boot = (
        "import sys,json;from pathlib import Path;r=Path.cwd();"
        "sys.path[:0]=[str(r),str(r/'src'),str(r/'contract')];import pytest;"
        "\nclass Origin:\n def pytest_collection_modifyitems(self,items):\n"
        "  paths=sorted({str(Path(i.module.__file__).resolve()) for i in items})\n"
        "  assert paths and all(Path(p).is_relative_to(r) for p in paths),paths\n"
        "  print('ISOLATED_TEST_ORIGINS='+json.dumps(paths))\n"
        "sys.exit(pytest.main(sys.argv[1:],plugins=[Origin()]))"
    )
    faults = [
        (
            "F5-linkage",
            "third_party/LICENSES.md",
            "| Runtime library graph |",
            "| Linked (proptest closure dev-only) |",
            "test_linkage_matches_locked_dependency_graph",
            "assert actual == roles()",
        ),
        (
            "F5-readme",
            "native/README.md",
            "not a public\nbinary",
            "Binary: uarch-engine; not a public\nbinary",
            "test_native_readme_describes_delivered_boundary",
            'assert "Binary: uarch-engine" not in text',
        ),
    ]
    try:
        for label, path, before, after, test, diagnostic in faults:
            target = source / path
            raw, stat = target.read_bytes(), target.stat()
            assert before.encode() in raw
            try:
                for state in ("baseline", "fault", "restored"):
                    if state == "fault":
                        target.write_bytes(raw.replace(before.encode(), after.encode()))
                    if state == "restored":
                        target.write_bytes(raw)
                        os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns))
                    argv = [
                        n.PYTHON,
                        "-I",
                        "-B",
                        "-c",
                        boot,
                        "-c",
                        str(source / "pyproject.toml"),
                        "--rootdir=" + str(source),
                        "-p",
                        "no:cacheprovider",
                        "--basetemp=" + str(work / (label + "-" + state)),
                        "-q",
                        str(source / "native/test_register_linkage.py") + "::" + test,
                    ]
                    done = subprocess.run(argv, cwd=source, env=env, capture_output=True, text=True)
                    log = done.stdout + done.stderr
                    name = label + "-" + state + ".log"
                    assert not (receipts / name).exists(), "refuse receipt overwrite"
                    (receipts / name).write_text(log)
                    records.append(
                        {
                            "fault": label,
                            "state": state,
                            "argv": argv,
                            "exit": done.returncode,
                            "log_sha256": n.sha(receipts / name),
                            "path": path,
                            "before_sha256": n.sha(target)
                            if state != "fault"
                            else subject["postimages"][path],
                            "before": before,
                            "after": after,
                            "diagnostic": diagnostic,
                        }
                    )
                    assert done.returncode == (1 if state == "fault" else 0), log
                    assert "ISOLATED_TEST_ORIGINS=" in log, log
                    assert (
                        (diagnostic in log and "1 failed" in log)
                        if state == "fault"
                        else "1 passed" in log
                    )
                    (n.HERE / name).write_text(log)
            finally:
                target.write_bytes(raw)
                os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    finally:
        unchanged = initial == c.snapshot(source)
        (n.HERE / "linkage-controls.json").write_text(
            json.dumps(
                {
                    "source": subject,
                    "work": str(work),
                    "metadata_sha256": n.sha(metadata),
                    "metadata_command": command,
                    "K1_METADATA": str(metadata),
                    "source_bytes_mtimes_restored": unchanged,
                    "records": records,
                },
                indent=2,
            )
            + "\n"
        )
        assert unchanged
    print("F5: two intended assertion failures, four positive controls; source restored")


if __name__ == "__main__":
    main()
