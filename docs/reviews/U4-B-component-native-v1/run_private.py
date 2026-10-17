"""Fresh private native unit processes and independent /2 checks; no public invocation."""

import argparse
import hashlib
import json
import os
import subprocess
import tarfile
import time
import uuid
from pathlib import Path

from validation.component.native_check import check_native

HERE = Path(__file__).resolve().parent
IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("build", type=Path)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--development-cases", nargs="+")
    args = parser.parse_args()
    build = args.build.resolve()
    meta = json.loads((build / "build.json").read_text())
    freeze = json.loads((HERE / "input-freeze-v2.json").read_text())
    assert sha(args.archive.read_bytes()) == freeze["archive_sha256"]
    root = HERE.parents[2]
    for path, digest in freeze["sources"].items():
        assert sha((root / path).read_bytes()) == digest
    out = args.output.resolve()
    assert out.is_relative_to(Path("/tmp"))
    out.mkdir(exist_ok=False)
    vectors = out / "vectors"
    vectors.mkdir()
    with tarfile.open(args.archive, "r:gz") as archive:
        archive.extractall(vectors, filter="data")
    for name, digest in freeze["members"].items():
        assert sha((vectors / name).read_bytes()) == digest
    proposal = json.loads((vectors / "proposal.json").read_text())
    plan = json.loads((HERE / "private-run-plan.json").read_text())
    cases = args.development_cases or plan["cases"]
    assert set(cases) <= set(plan["cases"])
    repeats = 1 if args.development_cases else 3
    report = dict(
        source_commit=meta["source_commit"],
        image=IMAGE,
        build_sha256=sha((build / "build.json").read_bytes()),
        input_freeze_sha256=sha((HERE / "input-freeze-v2.json").read_bytes()),
        plan_sha256=sha((HERE / "private-run-plan.json").read_bytes()),
        runner_sha256=sha(Path(__file__).read_bytes()),
        development_selection=bool(args.development_cases),
        synthetic_unit_anchors=True,
        successful_public_jobs=0,
        producer_code_mounted=False,
        observations=[],
        failures=[],
    )
    for name in cases:
        item = proposal["items"][name]
        outputs = []
        for mode in ("debug", "release"):
            target = build / (mode + "-target")
            executable = target / meta["commands"][mode]["test_executable"]
            assert sha(executable.read_bytes()) == meta["commands"][mode]["test_executable_sha256"]
            for repeat in range(repeats):
                run_id = f"{name}-{mode}-{repeat}"
                receipt = out / run_id
                receipt.mkdir()
                container = "u4-b-component-unit-" + uuid.uuid4().hex
                argv = [
                    "/usr/bin/docker",
                    "--host",
                    "unix:///var/run/docker.sock",
                    "run",
                    "--rm",
                    "--name",
                    container,
                    "--pull",
                    "never",
                    "--platform",
                    "linux/amd64",
                    "--network",
                    "none",
                    "--read-only",
                    "--user",
                    f"{os.getuid()}:{os.getgid()}",
                    "--cap-drop",
                    "ALL",
                    "--security-opt",
                    "no-new-privileges",
                    "--tmpfs",
                    "/tmp",
                    "--mount",
                    f"type=bind,src={target},dst=/target,readonly",
                    "--mount",
                    f"type=bind,src={vectors},dst=/vectors,readonly",
                    "--mount",
                    f"type=bind,src={receipt},dst=/output",
                    "--entrypoint",
                    "/usr/bin/env",
                    IMAGE,
                    "-i",
                    "LC_ALL=C",
                    f"B_COMPONENT_JOB=/vectors/jobs/{name}.json",
                    f"B_COMPONENT_TRUST=/vectors/trust/{name}.json",
                    "B_COMPONENT_OUTPUT=/output/result.json",
                    "/target/" + meta["commands"][mode]["test_executable"],
                    "b_private_probe::private_component_probe",
                    "--ignored",
                    "--exact",
                    "--nocapture",
                ]
                start = time.monotonic()
                try:
                    process = subprocess.run(
                        argv,
                        capture_output=True,
                        timeout=30,
                        env={
                            "PATH": "/usr/bin:/bin",
                            "DOCKER_CONFIG": str(build / "docker-config"),
                        },
                    )
                except subprocess.TimeoutExpired:
                    subprocess.run(
                        [
                            "/usr/bin/docker",
                            "--host",
                            "unix:///var/run/docker.sock",
                            "kill",
                            "--signal",
                            "KILL",
                            container,
                        ],
                        capture_output=True,
                        timeout=10,
                        check=False,
                    )
                    report["failures"].append(dict(run_id=run_id, failure="30 second timeout"))
                    (out / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
                    raise
                (receipt / "stdout").write_bytes(process.stdout)
                (receipt / "stderr").write_bytes(process.stderr)
                row = dict(
                    case=name,
                    mode=mode,
                    repeat=repeat,
                    argv=argv,
                    exit_code=process.returncode,
                    seconds=time.monotonic() - start,
                    binary_sha256=sha(executable.read_bytes()),
                    stdout_sha256=sha(process.stdout),
                    stderr_sha256=sha(process.stderr),
                )
                try:
                    assert process.returncode == 0, process.stderr.decode(errors="replace")
                    raw = (receipt / "result.json").read_bytes()
                    assert len(raw) <= 64 * 1024**2
                    row["output_sha256"] = sha(raw)
                    result = json.loads(raw)
                    row["rust_outcome"] = result["outcome"]
                    row["expected_layer"] = item["expected_layer"]
                    if item["expected_layer"] == "result":
                        assert result["outcome"] == "success", result
                        job = json.loads((vectors / "jobs" / (name + ".json")).read_text())
                        check_native(job, result["result"], item)
                        row["independent_check"] = "pass"
                    else:
                        assert result["outcome"] == "refusal", "intended refusal accepted unsafely"
                        assert result["code"] == item["expected_public_code"], result
                        row["rust_code"] = result["code"]
                    outputs.append(raw)
                except Exception as error:
                    row["failure"] = f"{type(error).__name__}: {error}"
                    report["failures"].append(dict(run_id=run_id, failure=row["failure"]))
                report["observations"].append(row)
                (out / "checks.json").write_text(
                    json.dumps(report, indent=2, sort_keys=True) + "\n"
                )
                print(run_id, row.get("failure", "pass"), flush=True)
        if len(outputs) == repeats * 2 and len(set(outputs)) != 1:
            report["failures"].append(dict(case=name, failure="complete output bytes differ"))
    report["all_selected_calls_completed"] = len(report["observations"]) == len(cases) * 2 * repeats
    report["passed"] = report["all_selected_calls_completed"] and not report["failures"]
    (out / "checks.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    assert report["passed"], report["failures"]


if __name__ == "__main__":
    main()
