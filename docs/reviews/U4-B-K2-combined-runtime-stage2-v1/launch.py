"""Default render-only launcher. Execution requires actual placed/published authority."""

import argparse
import importlib.util
import json
import os
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import bindings as b
import publication
from prepare import checked_bundle, published
from receipt_checks import replay_admission

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
    if spec is None or spec.loader is None:
        raise ValueError("loadable bound module spec required")
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


def receipt_bytes(root):
    total = 0
    for path in Path(root).rglob("*"):
        try:
            info = path.lstat()
        except FileNotFoundError:
            # Only the exact vanished-entry race is tolerated. Every surviving entry
            # is still accounted; no name-based exclusion and no other error swallowed.
            continue
        b.need(not stat.S_ISLNK(info.st_mode), "receipt symlink")
        if stat.S_ISREG(info.st_mode):
            total += info.st_size
        else:
            b.need(stat.S_ISDIR(info.st_mode), "unexpected receipt inode")
    return total


def run(argv, action, output, binding):
    output = Path(output)
    if action == "replay":
        original(b.read(HERE / "candidate.json"))
        sys_path = str(b.OLD / "campaign")
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)
        replay_admission(output, binding, b.read(b.OLD / "campaign/campaign-plan.json"))
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
                    b.need(time.monotonic() - start < timeout, "outer deadline")
                    b.need(
                        receipt_bytes(output) <= 2 * 1024**3,
                        "receipt budget",
                    )
                    time.sleep(0.1)
            except BaseException as error:
                reason = repr(error)
            finally:
                if proc.poll() is None:
                    try:
                        killed = subprocess.run(
                            argv[:3] + ["kill", "--signal", "KILL", name],
                            env=env,
                            capture_output=True,
                            timeout=10,
                            check=False,
                        )
                        if killed.returncode != 0:
                            reason = str(reason) + "; owned container cleanup unconfirmed: " + name
                    except (OSError, subprocess.TimeoutExpired) as error:
                        reason = str(reason) + "; cleanup error: " + repr(error)
                    # Even daemon failure must not skip client process-group cleanup.

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
                    "stage": action,
                    "operational_hash": b.digest(
                        (output / "campaign-operational.json").read_bytes()
                    )
                    if action == "campaign" and (output / "campaign-operational.json").is_file()
                    else None,
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
    with publication.observe() as view:
        try:
            execute(a, view)
        finally:
            # Keep the actual remote observation even when a later guard refuses.
            print(
                json.dumps({"publication_check": view.receipt()}, sort_keys=True), file=sys.stderr
            )


def execute(a, view):
    c, _ = checked_bundle(a.repo, a.publication)
    argv = command(a.action, a.output, c)
    if a.execute_placed:
        binding = verify(a.repo, a.publication, a.action)
        run(argv, a.action, a.output, binding)
        with (a.output / (a.action + "-publication-check.json")).open("xb") as stream:
            stream.write(b.encoded(view.receipt()))
    else:
        print(json.dumps({"argv": argv, "publication_check": view.receipt()}, indent=2))


if __name__ == "__main__":
    main()
