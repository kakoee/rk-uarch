"""Run B probe or named unit tests in the pinned image against the verified build.

Usage: python -I run.py BUILD OUT probe NAME JOB.json TRUST.json VERSION
VERSION: 2|3; private synthetic anchors only.
       python -I run.py BUILD OUT tests NAME FILTER
Each run: --network none, read-only root, binary hash re-verified, debug and release.
"""

import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
build, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
mode_kind, name = sys.argv[3], sys.argv[4]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


meta = json.loads((build / "build.json").read_text())
out.mkdir(exist_ok=True)
case = out / name
case.mkdir(exist_ok=False)
env_args: list[str] = []
if mode_kind == "probe":
    job, trust, version = Path(sys.argv[5]).resolve(), Path(sys.argv[6]).resolve(), sys.argv[7]
    (case / "job.json").write_bytes(job.read_bytes())
    (case / "trust.json").write_bytes(trust.read_bytes())
    env_args = [
        f"B_OBSERVATION_VERSION={version}",
        "B_COMPONENT_JOB=/vectors/job.json",
        "B_COMPONENT_TRUST=/vectors/trust.json",
        "B_COMPONENT_OUTPUT=/output/result.json",
    ]
    test_args = ["b_private_probe::private_component_probe", "--ignored", "--exact", "--nocapture"]
else:
    test_args = [sys.argv[5], "--nocapture"]
report = dict(case=name, kind=mode_kind, runs=[])
outputs = []
for mode in ("debug", "release"):
    target = build / (mode + "-target")
    binary = target / meta["commands"][mode]["test_executable"]
    assert sha(binary) == meta["commands"][mode]["test_executable_sha256"]
    receipt = case / mode
    receipt.mkdir()
    container = "u4-review-issue-" + uuid.uuid4().hex
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
        f"type=bind,src={case},dst=/vectors,readonly",
        "--mount",
        f"type=bind,src={receipt},dst=/output",
        "--entrypoint",
        "/usr/bin/env",
        IMAGE,
        "-i",
        "LC_ALL=C",
        *env_args,
        "/target/" + meta["commands"][mode]["test_executable"],
        *test_args,
    ]
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            timeout=60,
            env={"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": str(build / "docker-config")},
        )
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock", "kill", container],
            capture_output=True,
            timeout=10,
            check=False,
        )
        raise
    (receipt / "stdout").write_bytes(proc.stdout)
    (receipt / "stderr").write_bytes(proc.stderr)
    row = dict(
        mode=mode,
        exit_code=proc.returncode,
        binary_sha256=sha(binary),
        argv=argv,
        stdout_sha256=sha(receipt / "stdout"),
    )
    if mode_kind == "probe" and (receipt / "result.json").exists():
        raw = (receipt / "result.json").read_bytes()
        row["output_sha256"] = hashlib.sha256(raw).hexdigest()
        row["outcome"] = json.loads(raw)["outcome"]
        outputs.append(raw)
    else:
        tail = proc.stdout.decode(errors="replace").strip().splitlines()[-3:]
        row["summary"] = tail
    report["runs"].append(row)
    print(
        name,
        mode,
        proc.returncode,
        row.get("outcome"),
        row.get("output_sha256", "")[:16],
        row.get("summary", ""),
        flush=True,
    )
if mode_kind == "probe":
    report["debug_release_identical"] = len(outputs) == 2 and outputs[0] == outputs[1]
    print(name, "debug==release", report["debug_release_identical"])
(case / "run.json").write_text(json.dumps(report, indent=2) + "\n")
