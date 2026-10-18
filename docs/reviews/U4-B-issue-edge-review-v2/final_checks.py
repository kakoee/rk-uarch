"""One final affected Python/static batch after exact checker restoration."""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VENV = Path("/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin")
p = argparse.ArgumentParser()
p.add_argument("source", type=Path)
p.add_argument("out", type=Path)
a = p.parse_args()
a.out.mkdir(exist_ok=False)
package = ROOT / "docs/reviews/U4-A-issue-edge-amendment-v2"
manifest = json.loads((package / "manifest.json").read_text())
for row in manifest["files"]:
    assert (
        hashlib.sha256((a.source / row["path"]).read_bytes()).hexdigest() == row["postimage_sha256"]
    )
selection = json.loads((package / "evidence/python-checks/receipts.json").read_text())
rows = []
for command in selection:
    argv = command["argv"][:]
    executable = Path(argv[0]).name
    argv[0] = str(VENV / executable)
    argv = [
        ("--junitxml=" + str(a.out / "affected.xml")) if x.startswith("--junitxml=") else x
        for x in argv
    ]
    env = {
        **os.environ,
        "PYTHONPATH": ":".join(map(str, [a.source / "contract", a.source / "src", a.source])),
    }
    run = subprocess.run(argv, cwd=a.source, env=env, capture_output=True, timeout=180)
    name = command["name"]
    (a.out / (name + ".stdout")).write_bytes(run.stdout)
    (a.out / (name + ".stderr")).write_bytes(run.stderr)
    row = dict(
        name=name,
        argv=argv,
        cwd=str(a.source),
        exit_code=run.returncode,
        stdout_sha256=hashlib.sha256(run.stdout).hexdigest(),
        stderr_sha256=hashlib.sha256(run.stderr).hexdigest(),
    )
    rows.append(row)
    (a.out / "checks.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(name, run.returncode, run.stdout.decode()[-170:], flush=True)
assert all(x["exit_code"] == 0 for x in rows)
