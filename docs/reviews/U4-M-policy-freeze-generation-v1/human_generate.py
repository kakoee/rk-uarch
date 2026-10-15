"""Human-only two-process oracle generation. Never adopt, commit, push or restage inputs."""

import argparse
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-commit", required=True)
    parser.add_argument("--authorization-commit", required=True)
    args = parser.parse_args()
    if os.environ.get("UARCH_HUMAN") != "1":
        raise SystemExit("STOP: separately approved human generation requires UARCH_HUMAN=1")
    require_isolated = sys.flags.isolated and sys.dont_write_bytecode
    if not require_isolated:
        raise SystemExit("STOP: use the reviewed interpreter with -I -B")
    p = runpy.run_path(str(HERE / "preflight.py"))
    spec, root = p["SPEC"], p["COORDINATOR"]
    require, git, text = p["require"], p["git"], p["text"]
    require(
        args.authorization_commit == text(root, "rev-parse", "HEAD"), "authorization must be HEAD"
    )
    record_path = HERE.relative_to(root).as_posix() + "/authorization.json"
    require(
        text(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD") == record_path,
        "authorization commit must contain only its exact decision record",
    )
    require(
        json.loads(git(root, "show", "HEAD:" + record_path))
        == {
            "action": "accept-freeze-and-generate-two-processes",
            "approved": True,
            "authorizer": "Javid",
            "package_commit": args.package_commit,
            "source_commit": spec["source_commit"],
            "input_manifest_sha256": spec["input_manifest_sha256"],
            "freeze_sha256": p["digest"](HERE / "freeze.json"),
            "output_root": spec["generation_output"],
        },
        "wrong exact generation authorization",
    )
    check = p["preflight"]
    before = check(args.package_commit)
    output = p["OUTPUT"]
    output.parent.mkdir(exist_ok=True)
    output.mkdir()  # Exclusive absent output, outside frozen source and upstream.
    logs = output / "receipts"
    logs.mkdir()

    def save(name, value):
        with (logs / name).open("x") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")

    save("preflight-before.json", before)
    _, _, vendor = p["load_source"]()
    env = dict(
        os.environ,
        UV_PROJECT_ENVIRONMENT=spec["oracle_environment"],
        PYTHONDONTWRITEBYTECODE="1",
        GIT_OPTIONAL_LOCKS="0",
    )
    bootstrap = (
        "import sys,runpy;sys.path[:0]="
        + repr(
            [
                spec["source_root"],
                spec["source_root"] + "/src",
                spec["source_root"] + "/contract",
            ]
        )
        + ";runpy.run_module('scripts.vendor_rk',run_name='__main__')"
    )
    candidate = output / "candidate"
    command = [
        spec["source_python"],
        "-I",
        "-B",
        "-c",
        bootstrap,
        "--sha",
        spec["upstream_pin"],
        "--rk",
        spec["upstream_root"],
        "--inputs",
        spec["inputs"],
        "--input-manifest-sha256",
        spec["input_manifest_sha256"],
        "--output-root",
        str(candidate),
    ]
    manifests = []
    for index, status in enumerate(("created", "verified-identical"), 1):
        save(f"preflight-{index}.json", check(args.package_commit, during=True))
        result = subprocess.run(
            command, cwd=spec["source_root"], env=env, capture_output=True, text=True
        )
        (logs / f"run-{index}.stdout").write_text(result.stdout)
        (logs / f"run-{index}.stderr").write_text(result.stderr)
        save(
            f"run-{index}.json",
            {"argv": command, "exit": result.returncode, "expected_status": status},
        )
        require(result.returncode == 0, "generation failed; preserve receipts and stop")
        require(
            result.stdout.splitlines()
            == [f"{status}: {spec['expected_candidate_files']} files at {candidate}"],
            "unexpected generation status/count; preserve candidate and audit",
        )
        after = check(args.package_commit, during=True)
        save(f"postflight-{index}.json", after)
        vendor.check_manifest(candidate)
        vendor.check_snapshot_inputs(candidate, check_support=True)
        require(
            vendor.check_generator(candidate, current=True)["environment"]
            == spec["oracle_metadata"],
            "candidate environment differs",
        )
        manifests.append(p["digest"](candidate / "MANIFEST.json"))
        print(result.stdout.strip(), flush=True)
    require(manifests[0] == manifests[1], "repeat manifest differs")
    receipt = {
        "decision": "U4-M-policy-freeze-generation-v1",
        "source_commit": spec["source_commit"],
        "source_tree": spec["source_tree"],
        "input_manifest_sha256": spec["input_manifest_sha256"],
        "candidate_manifest_sha256": manifests[0],
        "candidate": str(candidate),
        "runs": 2,
        "package_commit": args.package_commit,
        "authorization_commit": args.authorization_commit,
        "status": "created then verified-identical; NOT adopted",
        "adoption_commit_push": False,
    }
    save("generation-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print(
        "STOP: return both status lines and manifest digest for candidate audit. "
        "Adoption remains separate."
    )


if __name__ == "__main__":
    main()
