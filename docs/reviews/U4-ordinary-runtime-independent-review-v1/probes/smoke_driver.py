"""Run installed_smoke.py in two containers (run with binaries; replay without). Exact-ID cleanup.

Usage: python3 -I smoke_driver.py WORK_DIR RUNTIME_DIR
WORK_DIR holds inputs/, mutants/, bin/{debug,release}, probe/installed_smoke.py, outputs/.
Image: the already-local python:3.11-slim (only used as a minimal Linux userland; the
runtime interpreter is the copied CPython 3.12.14 in RUNTIME_DIR). No pull, no network.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

work, runtime = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
(work / "outputs").mkdir(exist_ok=True)
image = subprocess.check_output(["docker", "image", "inspect", "python:3.11-slim", "--format", "{{.Id}}"],
                                text=True).strip()
ledger = work / "containers.jsonl"
status = 0
for mode in ("run", "replay"):
    args = ["docker", "create", "--pull", "never", "--network", "none", "--read-only",
            "--user", f"{os.getuid()}:{os.getgid()}", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--pids-limit", "128", "--memory", "2g",
            "--tmpfs", "/tmp:exec", "--tmpfs", "/scratch", "--workdir", "/scratch",
            "--mount", f"type=bind,src={runtime},dst={runtime},readonly",
            "--mount", f"type=bind,src={work}/inputs,dst=/inputs,readonly",
            "--mount", f"type=bind,src={work}/mutants,dst=/mutants,readonly",
            "--mount", f"type=bind,src={work}/probe,dst=/probe,readonly",
            "--mount", f"type=bind,src={work}/outputs,dst=/outputs",
            "--env", "PYTHONDONTWRITEBYTECODE=1"]
    if mode == "run":
        args += ["--mount", f"type=bind,src={work}/bin,dst=/native,readonly"]
    args += ["--entrypoint", f"{runtime}/env/bin/python", image, "/probe/installed_smoke.py", mode]
    cid = subprocess.check_output(args, text=True).strip()
    assert re.fullmatch("[0-9a-f]{64}", cid), cid
    with ledger.open("a") as f:
        f.write(json.dumps({"id": cid, "mode": mode, "event": "created"}) + "\n")
    try:
        with (work / f"{mode}.stdout").open("w") as out, (work / f"{mode}.stderr").open("w") as err:
            attach = subprocess.run(["docker", "start", "--attach", cid], stdout=out, stderr=err,
                                    timeout=900)
        inspected = json.loads(subprocess.check_output(["docker", "inspect", cid]))[0]
        meta = {"mode": mode, "container_id": cid, "image": inspected["Image"],
                "mounts": [{k: m[k] for k in ("Source", "Destination", "RW")} for m in inspected["Mounts"]],
                "exit": inspected["State"]["ExitCode"], "oom": inspected["State"]["OOMKilled"],
                "attach": attach.returncode}
        (work / f"{mode}-container.json").write_text(json.dumps(meta, indent=1) + "\n")
        print(json.dumps({k: meta[k] for k in ("mode", "container_id", "exit", "oom")}))
        status |= meta["exit"] != 0
    finally:
        subprocess.run(["docker", "rm", "--force", cid], check=True, stdout=subprocess.DEVNULL)
        with ledger.open("a") as f:
            f.write(json.dumps({"id": cid, "mode": mode, "event": "removed"}) + "\n")
sys.exit(status)
