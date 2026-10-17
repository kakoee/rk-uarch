"""Run the bounded F5 single-guard experiment in an already reconstructed private export."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
TEST = "validation/component/test_f5_mechanism_duration.py"
GUARD = (
    b'        need(a["end_ps"] == edge_after(hz, a["start_ps"], cycles), "mechanism duration")\n'
)
SOURCE = "validation/component/observations_v2.py"
SOURCE_SHA = "dd9c049b2fb2f28e2b6cbba04e5b3b627a6e7e4dbfcf3cbaf305969587915d62"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("review_probe", type=Path)
    parser.add_argument("logs", type=Path)
    args = parser.parse_args()
    root = args.export.resolve()
    assert root.is_relative_to(Path("/tmp")) and not (root / ".git").exists()
    args.logs.mkdir(parents=True, exist_ok=False)
    source = root / SOURCE
    original = source.read_bytes()
    assert sha(original) == SOURCE_SHA and original.count(GUARD) == 1
    records = {}

    def run(name: str, mode: str, arguments: list[str], expected: int) -> str:
        command = [sys.executable, "-I", "-B", str(PACKAGE / "isolated.py"), str(root)]
        command += [mode, *arguments]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        raw = (result.stdout + result.stderr).encode()
        (args.logs / (name + ".log")).write_bytes(raw)
        records[name] = dict(command=command, returncode=result.returncode, sha256=sha(raw))
        assert result.returncode == expected, (name, result.returncode, raw.decode())
        assert "B-PRIVATE-ORIGINS " in result.stdout, name
        return result.stdout

    run("control", "pytest", ["-q", TEST], 0)
    mutant = original.replace(GUARD, b"")
    try:
        source.write_bytes(mutant)
        output = run("single-guard-removed", "pytest", ["-q", TEST], 1)
        assert "DID NOT RAISE" in output and "1 failed, 1 passed" in output
        output = run(
            "reviewer-probe-guard-removed", "script", [str(args.review_probe.resolve())], 0
        )
        report = json.loads(output.split("B-PRIVATE-ORIGINS ")[0])
        for name in ("control D01", "F5 response hop 4 cycles ends 58500 (law 59000)"):
            assert report[name] == dict(validate_result="accepted", check_v2="accepted")
        output = run(
            "old-masked-test-guard-removed",
            "pytest",
            [
                "-q",
                "validation/component/test_consistent_observations.py::"
                "test_mechanism_and_field_forgery[duration-mechanism duration]",
            ],
            1,
        )
        assert "clock mechanism binding" in output and "DID NOT RAISE" not in output
    finally:
        source.write_bytes(original)
        assert source.read_bytes() == original
    run("restored-controls", "pytest", ["-q", TEST], 0)
    run(
        "affected-checker-and-identity",
        "pytest",
        [
            "-q",
            TEST,
            "validation/component/test_consistent_observations.py",
            "validation/component/test_join_selection.py",
            "validation/component/test_stage2_selection.py",
            "-m",
            "not native",
        ],
        0,
    )
    run(
        "discovery",
        "pytest",
        ["--collect-only", "-q", TEST, "-m", "not native and not nightly and not silicon"],
        0,
    )
    assert source.read_bytes() == original
    receipt = dict(
        scope="one F5 guard, synthetic unit carriers only",
        source=SOURCE,
        original_sha256=SOURCE_SHA,
        mutant_sha256=sha(mutant),
        restored_sha256=sha(source.read_bytes()),
        exact_restoration=True,
        mutation="Delete only the single mechanism duration need call; all other bytes unchanged.",
        behavioral_kill="new forged-carrier test: DID NOT RAISE; valid control passes",
        old_test="alternative clock mechanism binding refusal; not an unsafe-acceptance kill",
        test_path=TEST,
        test_sha256=sha((root / TEST).read_bytes()),
        executed=records,
        native_calls=0,
    )
    (args.logs / "restoration.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("F5: 2 control pass; 1 fail/1 pass under single removal; both layers admit forgery;")
    print("old masked test alternate-refuses; exact restore; 2 restored pass; 49 affected pass.")


if __name__ == "__main__":
    main()
