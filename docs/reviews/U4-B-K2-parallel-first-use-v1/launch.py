"""Default print-only replacement launcher; original deployment remains untouched."""

import argparse
import importlib.util
import json
import os
import signal
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from parallel_core import digest, require

HERE = Path(__file__).resolve().parent
OLD_ROOT = Path("/var/lib/rkuarch/k2/candidate-04-first-use-v1")
NEW_ROOT = Path("/var/lib/rkuarch/k2/candidate-04-parallel-v1")


def base_deployment():
    # Load only the actual immutable original helper; its digest is a published
    # member of the unchanged original approved manifest.
    manifest_bytes = (OLD_ROOT / "manifests/campaign-files.json").read_bytes()
    policy = json.loads((HERE / "parallel-policy.json").read_bytes())
    require(
        digest(manifest_bytes) == policy["original_helper_manifest_hash"],
        "exact original approved helper manifest required",
    )
    manifest = json.loads(manifest_bytes)
    path = OLD_ROOT / "campaign/deployment.py"
    require(digest(path.read_bytes()) == manifest["deployment.py"]["sha256"], "old helper drift")
    spec = importlib.util.spec_from_file_location("original_deployment", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command(action, output):
    require(action in ("preflight", "campaign", "replay"), "explicit stage")
    output = Path(output).resolve()
    require(
        not output.is_relative_to(Path("/tmp/u4-k2-approved-campaign")),
        "original stopped evidence cannot be output",
    )
    argv = base_deployment().docker_argv(action, output, action != "preflight")
    index = argv.index("--entrypoint")
    argv[index:index] = [
        "--mount",
        f"type=bind,src={NEW_ROOT}/helpers,dst=/parallel,readonly,bind-propagation=rprivate",
        "--mount",
        f"type=bind,src={NEW_ROOT}/authority,dst=/parallel-authority,readonly,bind-propagation=rprivate",
    ]
    argv[-2:] = [
        "-c",
        'import runpy,sys;sys.path.insert(0,"/parallel");'
        'sys.argv=["/parallel/parallel_entrypoint.py","' + action + '"];'
        'runpy.run_path(sys.argv[0],run_name="__main__")',
    ]
    return argv


def verify_placement():
    require(os.getuid() == os.geteuid() == 1000, "existing UID1000 launcher required")
    for root in (OLD_ROOT, NEW_ROOT):
        for p in (root, *root.rglob("*")):
            s = p.lstat()
            require(s.st_uid == 0, "root-owned immutable deployment")
            if p.is_symlink():
                require(p.resolve().is_relative_to(root), "deployment symlink escape")
            else:
                require(not s.st_mode & 0o222, "writable deployment inode")
    manifest = (HERE / "helper-manifest.json").read_bytes()
    require(
        (NEW_ROOT / "authority/helper-manifest.json").read_bytes() == manifest,
        "published helper manifest required",
    )
    for name, binding in json.loads(manifest).items():
        data = (NEW_ROOT / "helpers" / name).read_bytes()
        require(digest(data) == binding["sha256"], "parallel helper byte drift")
    original = base_deployment()
    layout = json.loads((OLD_ROOT / "campaign/candidate-layout.json").read_bytes())
    original.verify_bytes(OLD_ROOT / "candidate", layout["files"], sealed=True)


def launch(action, output, execute):
    argv = command(action, output)
    if not execute:
        print(json.dumps(argv, indent=2))
        return
    verify_placement()
    output = Path(output).resolve()
    if action == "replay":
        require(
            (output / "campaign.json").is_file() and not (output / "replays.json").exists(),
            "completed new campaign and fresh replay required",
        )
    else:
        output.mkdir(exist_ok=False)
    name = "u4-k2-parallel-" + uuid.uuid4().hex
    argv[4:4] = ["--name", name]
    timeout = 120 if action == "preflight" else 7200
    reason, code = None, None
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="u4-k2-parallel-docker-") as config:
        env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": config}
        with (
            (output / (action + ".stdout")).open("xb") as out,
            (output / (action + ".stderr")).open("xb") as err,
        ):
            proc = subprocess.Popen(argv, stdout=out, stderr=err, env=env, start_new_session=True)
            try:
                while proc.poll() is None:
                    files = list(output.rglob("*"))
                    require(not any(p.is_symlink() for p in files), "receipt symlink")
                    require(time.monotonic() - start < timeout, "container deadline")
                    require(
                        sum(p.stat().st_size for p in files if p.is_file()) <= 2 * 1024**3,
                        "container receipt budget",
                    )
                    time.sleep(0.1)
            except BaseException as exc:
                reason = repr(exc)
            finally:
                if proc.poll() is None:
                    subprocess.run(
                        argv[:3] + ["kill", "--signal", "KILL", name],
                        env=env,
                        capture_output=True,
                        timeout=10,
                        check=False,
                    )
                try:
                    code = proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    code = proc.wait()
    (output / (action + "-launch.json")).write_text(
        json.dumps(
            {
                "argv": argv,
                "exit_code": code,
                "stop_reason": reason,
                "elapsed_seconds": time.monotonic() - start,
                "limit_seconds": timeout,
                "helper_manifest_hash": digest((HERE / "helper-manifest.json").read_bytes()),
            },
            indent=2,
        )
        + "\n"
    )
    require(code == 0 and reason is None, "incomplete run; preserve all receipts")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["preflight", "campaign", "replay"])
    p.add_argument("--output", required=True, type=Path)
    p.add_argument(
        "--execute-placed",
        action="store_true",
        help="Only after coordinator reconciliation and human placement of this exact version",
    )
    args = p.parse_args()
    launch(args.action, args.output, args.execute_placed)
