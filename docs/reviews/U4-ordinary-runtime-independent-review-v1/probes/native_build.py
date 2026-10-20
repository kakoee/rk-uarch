"""Reviewer-owned offline native build/test in the accepted image; removes only its own IDs.

Usage: python -I native_build.py SOURCE_TREE WORK_DIR MODE [MODE...]
MODE in: versions, debug, release, test, clippy, fmt-check.
Each container is created with --pull never --network none, read-only source and Cargo
home, and is removed by the exact 64-hex ID returned by `docker create`.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
CARGO_HOME = "/tmp/u4-k2-c1-precise.styffox_/cargo-home"
BIN = "/usr/local/rustup/toolchains/1.99.0-x86_64-unknown-linux-gnu/bin/"
TARGET = ["--locked", "--offline", "--target", "x86_64-unknown-linux-gnu"]
COMMANDS = {
    "versions": ["sh", "-c", "rustc --version && cargo --version"],
    "debug": ["cargo", "build", *TARGET],
    "release": ["cargo", "build", "--release", *TARGET],
    "test": ["cargo", "test", "--all-features", *TARGET],
    "clippy": ["cargo", "clippy", "--all-targets", *TARGET, "--", "-D", "warnings"],
    "fmt-check": ["cargo", "fmt", "--all", "--check"],
}

source, work = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
(work / "target").mkdir(parents=True, exist_ok=True)
ledger = work / "containers.jsonl"
for mode in sys.argv[3:]:
    args = [
        "docker", "create", "--pull", "never", "--network", "none", "--read-only",
        "--user", f"{os.getuid()}:{os.getgid()}", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--tmpfs", "/tmp", "--workdir", "/work/native",
        "--mount", f"type=bind,src={source},dst=/work,readonly",
        "--mount", f"type=bind,src={CARGO_HOME},dst=/cargo-home,readonly",
        "--mount", f"type=bind,src={work}/target,dst=/target",
        "--entrypoint", "/usr/bin/env", IMAGE, "-i",
        f"PATH={BIN}:/usr/local/cargo/bin:/usr/bin:/bin", "CARGO_HOME=/cargo-home",
        "CARGO_TARGET_DIR=/target", "CARGO_NET_OFFLINE=true", "RUSTUP_AUTO_INSTALL=0",
        f"RUSTC={BIN}rustc", "LC_ALL=C", *COMMANDS[mode],
    ]
    cid = subprocess.check_output(args, text=True).strip()
    assert re.fullmatch("[0-9a-f]{64}", cid), cid
    with ledger.open("a") as f:
        f.write(json.dumps({"id": cid, "mode": mode, "event": "created"}) + "\n")
    try:
        log = work / f"{mode}.log"
        with log.open("w") as out:
            attach = subprocess.run(
                ["docker", "start", "--attach", cid], stdout=out, stderr=subprocess.STDOUT,
                timeout=1200,
            )
        state = json.loads(subprocess.check_output(["docker", "inspect", cid]))[0]["State"]
        record = {"mode": mode, "id": cid, "attach": attach.returncode,
                  "exit": state["ExitCode"], "oom": state["OOMKilled"], "error": state["Error"]}
        print(json.dumps(record))
        print(log.read_text()[-3000:])
    finally:
        subprocess.run(["docker", "rm", "--force", cid], check=True, stdout=subprocess.DEVNULL)
        with ledger.open("a") as f:
            f.write(json.dumps({"id": cid, "mode": mode, "event": "removed"}) + "\n")
