"""Remove only the structural pending+acquired guard; restore exact private bytes."""

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

SOURCE = Path("/tmp/u4-b-issue-edge-01/source")
OUT = Path("/tmp/u4-b-issue-edge-capacity-fault-01")


def worker():
    from uarch_contract.mapped import MappedEngineJob, validate_result
    from validation.component.observations_v3 import check_v3

    j = json.loads(Path("/tmp/u4-b-issue-edge-runs-01/jobs/gap-cap1.json").read_text())
    good = json.loads(Path("/tmp/u4-b-issue-edge-runs-01/gap-cap1-debug/result.json").read_text())[
        "result"
    ]
    bad = json.loads(
        Path("/tmp/u4-b-issue-edge-consume-final2/pending-overbook-only.json").read_text()
    )
    expected = json.loads(
        (SOURCE / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_text()
    )["observation_contract"]
    validate_result(good, MappedEngineJob.model_validate(j))
    check_v3(j, good, expected)
    row = dict(valid="pass")
    for name, fn in [
        ("structural", lambda: validate_result(bad, MappedEngineJob.model_validate(j))),
        ("independent", lambda: check_v3(j, bad, expected)),
    ]:
        try:
            fn()
            row[name] = "unsafe-acceptance"
        except Exception as e:
            row[name] = str(e)
    print(json.dumps(row))


def main():
    OUT.mkdir(exist_ok=False)
    path = SOURCE / "contract/uarch_contract/mapped_issue.py"
    original = path.read_bytes()
    rows = []

    def run(label):
        env = {
            **os.environ,
            "PYTHONPATH": str(SOURCE / "contract") + ":" + str(SOURCE / "src") + ":" + str(SOURCE),
        }
        p = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()), "worker"],
            cwd=SOURCE,
            env=env,
            capture_output=True,
            timeout=30,
        )
        assert p.returncode == 0, p.stderr
        (OUT / (label + ".stdout")).write_bytes(p.stdout)
        row = dict(
            label=label,
            source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            **json.loads(p.stdout),
        )
        rows.append(row)
        return row

    try:
        assert (
            run("baseline")["structural"]
            == "IncompleteObservations: pending plus acquired capacity"
        )
        tree = ast.parse(original)
        hits = 0
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "require"
                and len(node.args) == 3
                and isinstance(node.args[2], ast.Constant)
                and node.args[2].value == "pending plus acquired capacity"
            ):
                node.args[0] = ast.Constant(value=True)
                hits += 1
        assert hits == 1
        path.write_text(ast.unparse(tree) + "\n")
        row = run("remove-combined-capacity")
        assert row["structural"] == "unsafe-acceptance", row
        assert row["independent"] == "earliest reservation / ready tie", row
    finally:
        path.write_bytes(original)
        assert path.read_bytes() == original
    assert run("restored")["structural"] == "IncompleteObservations: pending plus acquired capacity"
    (OUT / "checks.json").write_text(
        json.dumps(dict(rows=rows, exact_restoration=True, synthetic_output_only=True), indent=2)
        + "\n"
    )
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    worker() if len(sys.argv) > 1 else main()
