"""Default render-only launcher. Execution requires actual placed/published authority."""

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

import bindings as b
from prepare import checked_bundle, published

HERE = Path(__file__).resolve().parent


def seal(root):
    for p in (root, *root.rglob("*")):
        s = p.lstat()
        b.need(s.st_uid == 0, "root-owned deployment")
        if p.is_symlink():
            b.need(p.resolve().is_relative_to(root), "deployment symlink escape")
        else:
            b.need(not s.st_mode & 0o222, "immutable deployment")
    for p in root.parents:
        s = p.lstat()
        b.need(
            p.is_dir() and not p.is_symlink() and s.st_uid == 0 and not s.st_mode & 0o022,
            "protected deployment ancestors",
        )


def original(candidate):
    b.old_bindings(b.OLD, candidate)
    manifest = b.read(b.OLD / "manifests/campaign-files.json")
    b.inventory(b.OLD / "campaign", {n: v["sha256"] for n, v in manifest.items()}, sealed=True)
    for name, record in manifest.items():
        b.need(
            b.digest((b.OLD / "campaign" / name).read_bytes()) == record["sha256"],
            "original campaign helper bytes",
        )
    path = b.OLD / "campaign/deployment.py"
    b.need(
        b.digest(path.read_bytes()) == manifest["deployment.py"]["sha256"],
        "original deployment helper",
    )
    spec = importlib.util.spec_from_file_location("original_deployment", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command(action, output, candidate):
    b.need(action in ("preflight", "campaign", "replay"), "explicit action")
    output = Path(output).absolute()
    b.need(
        output.is_relative_to("/tmp") and output.resolve() == output and "," not in str(output),
        "literal private output",
    )
    b.need(not output.is_relative_to("/tmp/u4-k2-approved-campaign"), "preserve stopped run")
    argv = original(candidate).docker_argv(action, output, action != "preflight")
    mounts = [("project", "/project"), ("helpers", "/combined"), ("record", "/combined-record")]
    if action != "preflight":
        mounts.append(("authority", "/combined-authority"))
    additions = []
    for src, dst in mounts:
        additions += [
            "--mount",
            f"type=bind,src={b.NEW}/{src},dst={dst},readonly,bind-propagation=rprivate",
        ]
    argv[argv.index("--entrypoint") : argv.index("--entrypoint")] = additions
    argv[-2:] = [
        "-c",
        'import sys,runpy;sys.path.insert(0,"/combined");sys.argv=["/combined/runtime_entry.py","'
        + action
        + '"];runpy.run_path(sys.argv[0],run_name="__main__")',
    ]
    return argv


def verify(repo, commit, action):
    c, data = checked_bundle(repo, commit)
    b.need(os.getuid() == os.geteuid() == 1000, "UID1000 launcher")
    seal(b.OLD)
    seal(b.NEW)
    placed, placed_data, publication = b.check_payload(
        b.NEW / "project", b.NEW / "helpers", b.NEW / "record"
    )
    b.need(
        placed_data == data and publication["helper_commit"] == commit, "actual published payload"
    )
    b.need(
        {p.name for p in b.NEW.iterdir()} == {"project", "helpers", "record", "authority"},
        "exact deployment layout",
    )
    old = original(c)
    old.verify_bytes(
        b.OLD / "candidate", b.read(b.OLD / "campaign/candidate-layout.json")["files"], sealed=True
    )
    b.need(
        b.digest((b.OLD / "authority/k2-host-selector.json").read_bytes())
        == c["native_selector_hash"],
        "unchanged native selector",
    )
    if action == "preflight":
        b.need(not any((b.NEW / "authority").iterdir()), "preflight before authority placement")
        return b.identity(data)
    binding = b.check_authority(b.NEW / "authority", data, publication)
    selector = b.read(b.NEW / "authority/selector.json")
    for key, path, name in [
        ("decision_commit", b.DECISION, "decision.json"),
        ("placement_commit", b.PLACEMENT, "placement.json"),
    ]:
        raw = published(repo, selector[key], path)
        b.need(
            raw == (b.NEW / "authority" / name).read_bytes(),
            "actual published human/coordinator record",
        )
    return binding


def run(argv, action, output, binding):
    output = Path(output)
    if action == "replay":
        b.need(
            (output / "campaign.json").is_file() and not (output / "replays.json").exists(),
            "new complete campaign before fresh replay",
        )
        b.need(
            b.read(output / "campaign.json")["runtime_binding"] == binding,
            "same combined runtime replay",
        )
    else:
        output.mkdir(exist_ok=False)
    name = "u4-k2-combined-" + uuid.uuid4().hex
    argv = list(argv)
    argv[4:4] = ["--name", name]
    start, reason, code = time.monotonic(), None, None
    timeout = 120 if action == "preflight" else 7200
    with tempfile.TemporaryDirectory(prefix="u4-combined-docker-config-") as config:
        env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": config}
        with (
            (output / (action + ".stdout")).open("xb") as stdout,
            (output / (action + ".stderr")).open("xb") as stderr,
        ):
            proc = subprocess.Popen(
                argv, env=env, stdout=stdout, stderr=stderr, start_new_session=True
            )
            try:
                while proc.poll() is None:
                    entries = list(output.rglob("*"))
                    b.need(not any(p.is_symlink() for p in entries), "receipt symlink")
                    b.need(time.monotonic() - start < timeout, "outer deadline")
                    b.need(
                        sum(p.stat().st_size for p in entries if p.is_file()) <= 2 * 1024**3,
                        "receipt budget",
                    )
                    time.sleep(0.1)
            except BaseException as error:
                reason = repr(error)
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
    with (output / (action + "-launch.json")).open("xb") as stream:
        stream.write(
            b.encoded(
                {
                    "argv": argv,
                    "runtime_binding": binding,
                    "exit_code": code,
                    "stop_reason": reason,
                    "elapsed_seconds": time.monotonic() - start,
                    "timeout_seconds": timeout,
                    "complete": code == 0 and reason is None,
                }
            )
        )
    b.need(code == 0 and reason is None, "incomplete launch; preserve all evidence")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("preflight", "campaign", "replay"))
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--publication", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--execute-placed", action="store_true")
    a = p.parse_args()
    c, _ = checked_bundle(a.repo, a.publication)
    argv = command(a.action, a.output, c)
    if a.execute_placed:
        binding = verify(a.repo, a.publication, a.action)
        run(argv, a.action, a.output, binding)
    else:
        print(json.dumps(argv, indent=2))


if __name__ == "__main__":
    main()
