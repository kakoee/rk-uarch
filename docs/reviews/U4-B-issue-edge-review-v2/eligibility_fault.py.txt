"""One dependency-completion guard fault in the private checker, with exact restoration."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def worker(source, runs, controls):
    from uarch_contract.mapped import MappedEngineJob, validate_result
    from validation.component.observations_v3 import check_v3

    expected = json.loads(
        (source / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_text()
    )["observation_contract"]
    answers = {}
    for name in ("r00", "r01", "forgery"):
        case = "r00" if name == "forgery" else name
        j = json.loads((runs / "jobs" / (case + ".json")).read_text())
        r = (
            json.loads((controls / "consistent-ineligible-first.json").read_text())
            if name == "forgery"
            else json.loads((runs / (case + "-debug") / "result.json").read_text())["result"]
        )
        validate_result(r, MappedEngineJob.model_validate(j))
        try:
            check_v3(j, r, expected)
            answers[name] = "pass"
        except Exception as error:
            answers[name] = type(error).__name__ + ": " + str(error)
    print(json.dumps(answers))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("runs", type=Path)
    parser.add_argument("controls", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker(args.source, args.runs, args.controls)
        return
    assert args.source.resolve().is_relative_to(Path("/tmp"))
    args.out.mkdir(exist_ok=False)
    path = args.source / "validation/component/issue_checks.py"
    original = path.read_bytes()
    rows = []

    def run(label):
        argv = [
            sys.executable,
            "-B",
            str(Path(__file__).resolve()),
            str(args.source),
            str(args.runs),
            str(args.controls),
            str(args.out),
            "--worker",
        ]
        env = {
            **os.environ,
            "PYTHONPATH": ":".join(
                map(str, [args.source / "contract", args.source / "src", args.source])
            ),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        proc = subprocess.run(argv, cwd=args.source, env=env, capture_output=True, timeout=30)
        (args.out / (label + ".stdout")).write_bytes(proc.stdout)
        (args.out / (label + ".stderr")).write_bytes(proc.stderr)
        assert proc.returncode == 0, proc.stderr
        observed = json.loads(proc.stdout)
        rows.append(
            dict(
                label=label,
                argv=argv,
                source_sha256=sha(path.read_bytes()),
                observed=observed,
                stdout_sha256=sha(proc.stdout),
                stderr_sha256=sha(proc.stderr),
            )
        )
        assert observed["r01"] == "pass"
        return observed

    try:
        baseline = run("baseline")
        assert baseline["r00"] == "pass"
        assert baseline["forgery"] == "CheckFailure: opportunity eligible grants / ready tie"
        needle = b'and all(job_ends[p] < cursor for p in dependencies.get(row["job_id"], []))'
        assert original.count(needle) == 1
        path.write_bytes(
            original.replace(needle, b"# PRIVATE FAULT: dependency-completion predicate removed")
        )
        assert run("without-dependency-completion")["forgery"] == "pass"
    finally:
        path.write_bytes(original)
        assert path.read_bytes() == original
    assert run("restored") == baseline
    (args.out / "checks.json").write_text(
        json.dumps(
            dict(
                recipe_sha256=sha(Path(__file__).read_bytes()),
                rows=rows,
                exact_restoration=True,
                unsafe_acceptance=(
                    "consistent early-eligibility forgery passes full checker "
                    "with only dependency predicate removed"
                ),
                private_synthetic_only=True,
            ),
            indent=2,
        )
        + "\n"
    )
    print(
        "Paired control passes throughout; one guard removed admits forgery; "
        "exact restoration rejects"
    )


if __name__ == "__main__":
    main()
