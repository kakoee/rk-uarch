"""Private component candidate construction in the accepted offline image.

This recipe emits an explicit no-public-authority identity. Unit tests supply synthetic
anchors internally; the ordinary executable refuses component public first use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
BIN = "/usr/local/rustup/toolchains/1.99.0-x86_64-unknown-linux-gnu/bin/"
CACHE_RECORD = ROOT / "docs/reviews/U4-A-K2-C1-precise-v1/cache-inventory.json"
TOOLS = ROOT / "docs/reviews/U4-A-K2-construction-v1/candidate-04/ToolInputs.json"


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def inventory(path: Path) -> dict:
    return {
        str(f.relative_to(path)): {
            "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
            "bytes": f.stat().st_size,
        }
        for f in sorted(path.rglob("*"))
        if f.is_file()
    }


def command(scratch: Path, name: str, argv: list[str], stdin: bytes | None = None) -> int:
    output = scratch / "commands" / name
    output.parent.mkdir(exist_ok=True)
    if output.with_suffix(".json").exists():
        raise ValueError("receipt already exists: " + name)
    env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": str(scratch / "docker-config")}
    start = time.time_ns()
    run = subprocess.run(argv, input=stdin, capture_output=True, env=env, timeout=600)
    output.with_suffix(".stdout").write_bytes(run.stdout)
    output.with_suffix(".stderr").write_bytes(run.stderr)
    write(
        output.with_suffix(".json"),
        {
            "argv": argv,
            "environment": env,
            "exit_code": run.returncode,
            "started_ns": start,
            "elapsed_ns": time.time_ns() - start,
            "stdout_hash": digest(run.stdout),
            "stderr_hash": digest(run.stderr),
            "stdin_hash": None if stdin is None else digest(stdin),
        },
    )
    print(name, run.returncode, flush=True)
    if run.returncode:
        print(run.stdout.decode(errors="replace")[-4000:])
        print(run.stderr.decode(errors="replace")[-6000:])
    return run.returncode


def docker(scratch: Path, mode: str, tag: str) -> list[str]:
    receipts = scratch / "receipts" / mode / tag
    receipts.mkdir(parents=True, exist_ok=True)
    args = [
        "/usr/bin/docker",
        "--host",
        "unix:///var/run/docker.sock",
        "run",
        "--rm",
        "--pull",
        "never",
        "--platform",
        "linux/amd64",
        "--network",
        "none",
        "--read-only",
        "--user",
        "1000:1000",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--tmpfs",
        "/tmp",
        "--workdir",
        "/work/native",
    ]
    for src, dst, ro in [
        (scratch / "source", "/work", True),
        (scratch / "cache", "/cargo-home", True),
        (scratch / "controls", "/controls", True),
        (scratch / "targets" / mode, "/target", False),
        (scratch / "outputs" / mode, "/outputs", False),
        (receipts, "/receipts", False),
    ]:
        src.mkdir(parents=True, exist_ok=True)
        args += ["--mount", f"type=bind,src={src},dst={dst}" + (",readonly" if ro else "")]
    return args + [
        "--entrypoint",
        "/usr/bin/env",
        IMAGE,
        "-i",
        "PATH=" + BIN + ":/usr/local/cargo/bin:/usr/bin:/bin",
        "CARGO_HOME=/cargo-home",
        "CARGO_NET_OFFLINE=true",
        "CARGO_TARGET_DIR=/target",
        "CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse",
        "RUSTUP_AUTO_INSTALL=0",
        "LC_ALL=C",
        "RUSTC=" + BIN + "rustc",
        "RUSTC_WRAPPER=/controls/rustc-wrapper.sh",
        "RUSTFLAGS=-C debuginfo=1 -C linker=/controls/linker.sh",
        "C2_RUN_TAG=" + tag,
    ]


def prepare(scratch: Path) -> None:
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT):
        raise ValueError("candidate must be built from a clean committed source freeze")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    scratch.mkdir(exist_ok=False)
    for name in ("commands", "docker-config", "source", "controls"):
        (scratch / name).mkdir()
    status = command(
        scratch,
        "image",
        [
            "/usr/bin/docker",
            "--host",
            "unix:///var/run/docker.sock",
            "image",
            "inspect",
            IMAGE,
            "--format",
            "{{.Id}} {{.Os}} {{.Architecture}}",
        ],
    )
    if status or (scratch / "commands/image.stdout").read_text().strip() != IMAGE + " linux amd64":
        raise ValueError("accepted image missing")
    accepted = json.loads(CACHE_RECORD.read_bytes())
    cache = Path(accepted["private_root"])
    if inventory(cache) != accepted["files"]:
        raise ValueError("accepted cache changed")
    shutil.copytree(cache, scratch / "cache")
    if inventory(scratch / "cache") != accepted["files"]:
        raise ValueError("private cache copy mismatch")
    names = (
        subprocess.check_output(["git", "ls-files", "-z", "native"], cwd=ROOT).decode().split("\0")
    )
    sources = []
    for name in sorted(x for x in names if x):
        data = (ROOT / name).read_bytes()
        dest = scratch / "source" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        sources.append({"path": name, "byte_hash": digest(data)})
    for name in ("rustc-wrapper.sh", "linker.sh"):
        shutil.copy2(
            ROOT / "docs/reviews/U4-A-K2-construction-v1/inputs" / name, scratch / "controls" / name
        )
    tools = json.loads(TOOLS.read_bytes())
    model_paths = [x for x in sources if x["path"].startswith("native/crates/uarch-engine/src/")]
    build = {
        "format": "uarch-component-build-inputs/1",
        "source_commit": commit,
        "source_files": sources,
        "model_sources": model_paths,
        "tool_inputs_file": {
            "path": str(TOOLS.relative_to(ROOT)),
            "byte_hash": digest(TOOLS.read_bytes()),
        },
        "tool_inputs_hash": digest(canonical(tools)),
        "image": IMAGE,
        "cargo_lock_hash": digest((ROOT / "native/Cargo.lock").read_bytes()),
        "controls": inventory(scratch / "controls"),
        "features": "unchanged Cargo.lock/Cargo.toml; no default feature changes",
        "modes": ["debug", "release"],
        "rustflags": "-C debuginfo=1 -C linker=/controls/linker.sh",
        "authority": "absent; private synthetic tests only",
    }
    engine = {
        "name": "native",
        "version": "native-stage/1",
        "implementation_hash": digest(canonical(build)),
        "compiler_lock_hash": digest(canonical(tools)),
        "model": {
            "name": "native-intervals",
            "version": "1",
            "implementation_hash": digest(canonical(model_paths)),
        },
    }
    trust = {
        "format": "uarch-component-build-trust/1",
        "purpose": "private-synthetic-tests-only",
        "public_authority": None,
        "registry_hash": "sha256:" + "0" * 64,
        "profiles": [],
    }
    generated = scratch / "source/native/crates/uarch-engine/generated/identity.rs"
    generated.parent.mkdir()
    generated.write_text(
        'pub const ENGINE_JSON: &str = r###"'
        + canonical(engine).decode()
        + '"###;\n'
        + 'pub const TRUST_JSON: &str = r###"'
        + canonical(trust).decode()
        + '"###;\n'
    )
    write(scratch / "BuildInputs.json", build)
    write(scratch / "engine.json", engine)
    write(scratch / "BuildTrust.json", trust)
    write(
        scratch / "generated.json",
        {"path": str(generated.relative_to(scratch)), "byte_hash": digest(generated.read_bytes())},
    )
    for tool, argv in [
        ("rustc", [BIN + "rustc", "-vV"]),
        ("cargo", [BIN + "cargo", "-vV"]),
        ("rustfmt", [BIN + "rustfmt", "--version"]),
        ("clippy", [BIN + "clippy-driver", "--version"]),
        ("cargo-deny", ["/usr/local/cargo/bin/cargo-deny", "--version"]),
    ]:
        if command(scratch, "tool-" + tool, docker(scratch, "debug", "tool-" + tool) + argv):
            raise ValueError("tool probe failed")
        expected = ROOT / "docs/reviews/U4-A-K2-C1-precise-v1" / (tool + ".stdout")
        if (
            scratch / "commands" / ("tool-" + tool + ".stdout")
        ).read_bytes() != expected.read_bytes():
            raise ValueError("tool identity mismatch: " + tool)


def run(scratch: Path, action: str, mode: str, tag: str) -> None:
    build = json.loads((scratch / "BuildInputs.json").read_bytes())
    for item in build["source_files"]:
        if digest((scratch / "source" / item["path"]).read_bytes()) != item["byte_hash"]:
            raise ValueError("frozen source changed")
    prefix = docker(scratch, mode, tag)
    release = ["--release"] if mode == "release" else []
    if action == "build":
        args = [
            BIN + "cargo",
            "rustc",
            "--offline",
            "--locked",
            "-p",
            "uarch-engine",
            "--bin",
            "uarch-engine",
            "-vv",
            "--message-format=json",
            *release,
            "--",
            "-C",
            "link-arg=-Wl,-Map=/receipts/" + mode + ".map",
        ]
    elif action in ("test", "export"):
        args = [
            BIN + "cargo",
            "test",
            "--offline",
            "--locked",
            "-p",
            "uarch-engine",
            "--lib",
            *release,
        ]
        if action == "export":
            prefix += ["COMPONENT_PRIVATE_OUTPUT=/outputs/" + tag]
            args += [
                "component_tests::export_private_synthetic_results",
                "--",
                "--ignored",
                "--exact",
                "--nocapture",
            ]
    elif action == "clippy":
        args = [
            BIN + "cargo",
            "clippy",
            "--offline",
            "--locked",
            "--all-targets",
            *release,
            "--",
            "-D",
            "warnings",
        ]
    elif action == "fmt":
        args = [BIN + "cargo", "fmt", "--check"]
    elif action == "licenses":
        args = [
            "/usr/local/cargo/bin/cargo-deny",
            "--locked",
            "--offline",
            "--all-features",
            "--config",
            "deny.toml",
            "check",
            "licenses",
            "bans",
            "sources",
        ]
    else:
        raise ValueError(action)
    status = command(scratch, tag, prefix + args)
    if inventory(scratch / "cache") != json.loads(CACHE_RECORD.read_bytes())["files"]:
        raise ValueError("private cache changed")
    if status:
        raise SystemExit(status)
    if action == "build":
        binary = scratch / "targets" / mode / mode / "uarch-engine"
        write(
            scratch / (mode + "-executable.json"),
            {
                "path": str(binary),
                "byte_hash": digest(binary.read_bytes()),
                "engine": json.loads((scratch / "engine.json").read_bytes()),
            },
        )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "action", choices=["prepare", "build", "test", "export", "clippy", "fmt", "licenses"]
    )
    p.add_argument("--scratch", type=Path, required=True)
    p.add_argument("--mode", choices=["debug", "release"], default="debug")
    p.add_argument("--tag", default=None)
    args = p.parse_args()
    if args.action == "prepare":
        prepare(args.scratch)
    else:
        run(args.scratch, args.action, args.mode, args.tag or args.mode + "-" + args.action)


if __name__ == "__main__":
    main()
