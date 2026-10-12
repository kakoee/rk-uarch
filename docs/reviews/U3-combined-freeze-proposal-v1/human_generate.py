"""PROPOSED human-only two-process generation; agents must not execute this file.

After coordinator review and Javid's authorization, invoke A python -I -B with
--approved-proposal FULL_COMMIT, and UARCH_HUMAN=1 supplied by the human. Stops
before adoption/test activation/commit/push. No dependency installation or runner work.
"""

import argparse
import hashlib
import json
import os
import runpy
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-proposal", required=True)
    args = parser.parse_args()
    if os.environ.get("UARCH_HUMAN") != "1":
        raise SystemExit("Human must supply UARCH_HUMAN=1 after exact proposal approval")
    p = runpy.run_path(str(HERE / "preflight.py"))
    check, spec, source, output = p["preflight"], p["SPEC"], p["A"], p["OUTPUT"]
    receipt = check(proposal_commit=args.approved_proposal)
    output.parent.mkdir(exist_ok=True)  # ignored tables parent, checked for symlink/non-directory
    output.mkdir()  # exclusive absent leaf; no cleanup, overwrite or automatic resume
    logs = output / "receipts"
    logs.mkdir()

    def save(name, value):
        with (logs / name).open("x") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")

    save("preflight-before.json", receipt)
    u, v = p["load_source"]()
    inputs, candidate = output / "inputs", output / "candidate"
    identity = u.prepare_inputs(inputs)
    p["require"](identity == spec["input_manifest_sha256"], "input staging drift")
    env = dict(
        os.environ,
        UV_PROJECT_ENVIRONMENT=spec["oracle_environment"],
        PYTHONDONTWRITEBYTECODE="1",
        GIT_OPTIONAL_LOCKS="0",
    )
    # Isolated fresh interpreter, explicit A paths: never import B/primary by cwd/editable.
    bootstrap = (
        "import sys,runpy;sys.path[:0]="
        + repr([str(source), str(source / "src"), str(source / "contract")])
        + ";runpy.run_module('scripts.vendor_rk',run_name='__main__')"
    )
    command = [
        str(source / ".venv/bin/python"),
        "-I",
        "-B",
        "-c",
        bootstrap,
        "--sha",
        spec["upstream_pin"],
        "--rk",
        spec["upstream_root"],
        "--inputs",
        str(inputs),
        "--input-manifest-sha256",
        identity,
        "--output-root",
        str(candidate),
    ]
    manifests = []
    for index, status in enumerate(("created", "verified-identical"), 1):
        before = check(proposal_commit=args.approved_proposal, stage="during")
        save(f"preflight-run-{index}.json", before)
        process = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True)
        (logs / f"run-{index}.stdout").write_text(process.stdout)
        (logs / f"run-{index}.stderr").write_text(process.stderr)
        save(
            f"run-{index}.json",
            dict(
                command=command,
                exit_code=process.returncode,
                expected_status=status,
                proposal_commit=args.approved_proposal,
            ),
        )
        p["require"](process.returncode == 0, "generation failed; retain receipts and stop")
        expected = f"{status}: {spec['expected_candidate_files']} files at {candidate}"
        p["require"](process.stdout.splitlines() == [expected], "unexpected publication status")
        after = check(proposal_commit=args.approved_proposal, stage="during")
        save(f"postflight-run-{index}.json", after)
        v.check_manifest(candidate)
        v.check_snapshot_inputs(candidate, check_support=True)
        generator = v.check_generator(candidate, current=True)
        p["require"](
            generator["environment"] == before["oracle_environment"],
            "recorded oracle environment differs",
        )
        manifests.append(hashlib.sha256((candidate / "MANIFEST.json").read_bytes()).hexdigest())
    p["require"](manifests[0] == manifests[1], "two-process manifest drift")
    save(
        "generation-receipt.json",
        dict(
            source_commit=spec["source_commit"],
            source_tree=spec["source_tree"],
            input_manifest_sha256=identity,
            candidate_manifest_sha256=manifests[0],
            proposal_commit=args.approved_proposal,
            candidate=str(candidate),
            runs=2,
            status="created then verified-identical; NOT adopted",
        ),
    )
    print("STOP before adoption/test activation. Return receipts and manifest:", manifests[0])


if __name__ == "__main__":
    main()
