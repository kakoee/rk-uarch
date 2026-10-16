"""Future approved launcher, default print-only. No capabilities or security fallback."""

import argparse
import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from deployment import HERE, HOST_ROOT, digest, docker_argv, require, verify_bytes


def launch(action, output, execute):
    argv = docker_argv(action, output, action != "preflight")
    if not execute:
        print(json.dumps(argv, indent=2))
        return
    require(
        (HOST_ROOT / "manifests/campaign-files.json").read_bytes()
        == (HERE / "campaign-files.expected.json").read_bytes(),
        "published helper manifest drift",
    )
    require(os.getuid() == os.geteuid() == 1000, "launch as existing UID1000 user")
    layout = json.loads((HERE / "candidate-layout.json").read_bytes())
    verify_bytes(HOST_ROOT / "candidate", layout["files"], sealed=True)
    # A human must verify/protect the entire staging root before this check. Refuse
    # writable or non-root runtime/manifests/authority inodes, never repair them here.
    for p in (HOST_ROOT, *HOST_ROOT.rglob("*")):
        st = p.lstat()
        require(st.st_uid == 0, "root-owned sealed deployment required")
        if p.is_symlink():
            require(p.resolve().is_relative_to(HOST_ROOT), "deployment symlink escape")
        else:
            require(not st.st_mode & 0o222, "unsealed deployment inode")
    output = output.resolve()
    if action == "replay":
        require((output / "campaign.json").is_file(), "actual complete campaign required")
        require(not (output / "replays.json").exists(), "never overwrite replay evidence")
    else:
        output.mkdir(exist_ok=False)
    timeout = 120 if action == "preflight" else 7200
    byte_limit = 2 * 1024**3
    name = "u4-k2-first-use-" + uuid.uuid4().hex
    argv[4:4] = ["--name", name]
    with tempfile.TemporaryDirectory(prefix="u4-k2-docker-config-") as config:
        env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": config}
        started = time.monotonic()
        reason = None
        with (
            (output / (action + ".stdout")).open("xb") as out,
            (output / (action + ".stderr")).open("xb") as err,
        ):
            process = subprocess.Popen(
                argv, stdout=out, stderr=err, env=env, start_new_session=True
            )
            try:
                while process.poll() is None:
                    paths = list(output.rglob("*"))
                    require(not any(p.is_symlink() for p in paths), "receipt symlink")
                    if time.monotonic() - started >= timeout:
                        reason = "time limit"
                        break
                    if sum(p.stat().st_size for p in paths if p.is_file()) >= byte_limit:
                        reason = "receipt limit"
                        break
                    time.sleep(0.1)
            finally:
                if reason or process.poll() is None:
                    subprocess.run(
                        argv[:3] + ["kill", "--signal", "KILL", name],
                        env=env,
                        capture_output=True,
                        timeout=10,
                        check=False,
                    )
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, 9)
                    process.wait()
        record = {
            "argv": argv,
            "exit_code": process.returncode,
            "stop_reason": reason,
            "elapsed_seconds": time.monotonic() - started,
            "limit_seconds": timeout,
            "byte_limit": byte_limit,
            "source": layout["candidate_source"],
            "plan_hash": digest((HERE / "campaign-plan.json").read_bytes()),
        }
        (output / (action + "-launch.json")).write_text(json.dumps(record, indent=2) + "\n")
        require(
            process.returncode == 0 and reason is None, "incomplete execution; preserve receipts"
        )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["preflight", "campaign", "replay"])
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--execute-approved",
        action="store_true",
        help="Only after the coordinator records genuine authorization for this package",
    )
    args = p.parse_args()
    launch(args.action, args.output, args.execute_approved)
