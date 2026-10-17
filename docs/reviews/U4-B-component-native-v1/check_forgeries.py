"""Discriminating synthetic forgeries of saved native results in a private checker copy."""

import argparse
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ATTACKS = [
    "duration-law",
    "missing-occupancy",
    "false-latency-occupancy",
    "channel-clock",
    "dma-clock",
    "ordinary-clock",
    "channel-population",
    "o2-early-allocation",
    "o2-late-free",
    "o2-persistent",
    "o2-first-consumer",
    "missing-cause",
]


def child(run, name):
    from uarch_contract.mapped import MappedEngineJob, validate_result

    from validation.component.native_check import CONTRACT, check_native
    from validation.component.native_forgeries import forge
    from validation.component.observations_v2 import check_v2

    case = "B-native-O2" if name.startswith("o2-") or name == "missing-cause" else "D01"
    proposal = json.loads((run / "vectors/proposal.json").read_text())
    job = json.loads((run / "vectors/jobs" / (case + ".json")).read_text())
    result = json.loads((run / (case + "-debug-0") / "result.json").read_text())
    assert result["outcome"] == "success"
    valid = result["result"]
    check_native(job, valid, proposal["items"][case])
    bad = forge(valid, name)
    row = dict(
        case=case,
        attack=name,
        label="synthetic forgery of saved private native output",
        valid_control="pass",
        original_result_hash=valid["result_hash"],
        forged_result_hash=bad["result_hash"],
    )
    parsed = MappedEngineJob.model_validate(job)
    for layer, callback in [
        ("structural", lambda: validate_result(bad, parsed)),
        ("independent_v2", lambda: check_v2(job, bad, CONTRACT)),
        ("full_literal_consumer", lambda: check_native(job, bad, proposal["items"][case])),
    ]:
        try:
            callback()
            row[layer] = "accepted"
        except (ValueError, AssertionError) as error:
            row[layer] = str(error)
    import validation.component.observations_v2 as checker
    import validation.component.transition_checks as transitions

    row["origins"] = dict(checker=checker.__file__, transitions=transitions.__file__)
    print(json.dumps(row, sort_keys=True))


def without_guard(raw, message):
    source = raw.decode()
    matches = [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "need"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == message
    ]
    assert len(matches) == 1, (message, len(matches))
    node = matches[0]
    lines = source.splitlines(keepends=True)
    start = sum(map(len, lines[: node.lineno - 1])) + node.col_offset
    end = sum(map(len, lines[: node.end_lineno - 1])) + node.end_col_offset
    return (source[:start] + "None" + source[end:]).encode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--child")
    args = parser.parse_args()
    if args.child:
        child(args.run.resolve(), args.child)
        return
    out = args.output.resolve()
    assert out.is_relative_to(Path("/tmp"))
    out.mkdir(exist_ok=False)
    private = out / "checker-source"
    shutil.copytree(ROOT / "validation", private / "validation")
    sidecar = Path("docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json")
    (private / sidecar).parent.mkdir(parents=True)
    shutil.copyfile(ROOT / sidecar, private / sidecar)
    for cache in (private / "validation").rglob("__pycache__"):
        shutil.rmtree(cache)
    env = {
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join(map(str, [private, ROOT / "contract", ROOT / "src", ROOT])),
    }
    records = []

    def execute(label, names):
        for name in names:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    str(args.run.resolve()),
                    str(out),
                    "--child",
                    name,
                ],
                cwd=private,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            (out / (label + "-" + name + ".stdout")).write_text(proc.stdout)
            (out / (label + "-" + name + ".stderr")).write_text(proc.stderr)
            assert proc.returncode == 0, proc.stderr
            row = json.loads(proc.stdout)
            assert Path(row["origins"]["checker"]).is_relative_to(private)
            assert Path(row["origins"]["transitions"]).is_relative_to(private)
            row["stage"] = label
            records.append(row)
            print(label, name, row["independent_v2"], flush=True)

    execute("baseline", ATTACKS)
    expected = {
        "duration-law": "mechanism duration",
        "missing-occupancy": "required occupancy",
        "false-latency-occupancy": "required occupancy",
        "channel-clock": "nonclocked exact binding",
        "dma-clock": "nonclocked exact binding",
        "ordinary-clock": "ordinary queue exact binding",
        "channel-population": "channel population lifecycle",
        "o2-early-allocation": "accumulator lifetime mechanism",
        "o2-late-free": "accumulator lifetime mechanism",
        "o2-persistent": "accumulator lifetime mechanism",
        "o2-first-consumer": "allocation access lifetime",
        "missing-cause": "complete eligible causes",
    }
    for row in records:
        assert row["independent_v2"] == expected[row["attack"]], row
        if row["attack"].startswith("o2-") or row["attack"] in ("duration-law", "missing-cause"):
            assert row["structural"] == "accepted", row
        else:
            assert row["structural"].startswith("IncompleteObservations"), row
    plans = [
        ("duration", "observations_v2.py", "mechanism duration", ["duration-law"]),
        (
            "lifetime",
            "observations_v2.py",
            "accumulator lifetime mechanism",
            ["o2-early-allocation", "o2-late-free", "o2-persistent", "o2-first-consumer"],
        ),
        ("access", "observations_v2.py", "allocation access lifetime", ["o2-first-consumer"]),
        ("causes", "transition_checks.py", "complete eligible causes", ["missing-cause"]),
    ]
    restorations = []
    for label, filename, message, names in plans:
        path = private / "validation/component" / filename
        before = path.read_bytes()
        changed = without_guard(before, message)
        try:
            path.write_bytes(changed)
            execute(label + "-removed", names)
        finally:
            path.write_bytes(before)
            assert path.read_bytes() == before
            restorations.append(
                dict(
                    guard=message,
                    preimage_sha256=hashlib.sha256(before).hexdigest(),
                    mutant_sha256=hashlib.sha256(changed).hexdigest(),
                    exact_restoration=True,
                )
            )
        execute(label + "-restored", names)
    report = dict(
        records=records,
        restorations=restorations,
        successful_public_jobs=0,
        full_sweeps_repeated=False,
    )
    (out / "forgeries.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    essential = {
        "duration-law": "duration-removed",
        "o2-early-allocation": "lifetime-removed",
        "o2-late-free": "lifetime-removed",
        "o2-persistent": "lifetime-removed",
        "missing-cause": "causes-removed",
    }
    for name, stage in essential.items():
        assert (
            next(r for r in records if r["attack"] == name and r["stage"] == stage)[
                "independent_v2"
            ]
            == "accepted"
        )
    assert all(
        r["independent_v2"] != "accepted"
        for r in records
        if r["stage"] == "baseline" or r["stage"].endswith("-restored")
    )


if __name__ == "__main__":
    main()
