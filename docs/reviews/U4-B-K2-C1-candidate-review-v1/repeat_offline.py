"""Repeat only named, already authorized C1 offline read checks in private copies."""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path("/tmp/u4-b-c1-review")
ORIGINAL = Path("/tmp/u4-k2-c1-precise.styffox_")
COPY = ROOT / "repeat"
PACKAGE = ROOT / "subject/docs/reviews/U4-A-K2-C1-precise-v1"
OUTPUT = ROOT / "output"
COPY.mkdir()
for name in ("source", "cargo-home", "controls"):
    shutil.copytree(ORIGINAL / name, COPY / name)
for name in ("target", "docker-config"):
    (COPY / name).mkdir()
allowed = {
    "image-inspect",
    "rustc",
    "cargo",
    "cargo-deny",
    "rustfmt",
    "clippy",
    "metadata-full-repeat",
    "metadata-linux-repeat",
    "fetch-full-repeat",
    "fetch-linux-repeat",
    "deny-check",
}
receipts = []
for old in json.loads((PACKAGE / "commands.json").read_text()):
    if old["name"] not in allowed:
        continue
    argv = [s.replace(str(ORIGINAL), str(COPY)) for s in old["argv"]]
    # The entire private source copy is mounted read-only; only cache/target are writable.
    argv = [s + ",readonly" if s.endswith("dst=/work/native") else s for s in argv]
    if "run" in argv:
        assert argv[argv.index("--network") + 1] == "none"
        assert argv[argv.index("--pull") + 1] == "never"
    env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": str(COPY / "docker-config")}
    result = subprocess.run(argv, env=env, cwd=ROOT, capture_output=True, check=False)
    row = {
        "name": old["name"],
        "argv": argv,
        "environment": env,
        "cwd": str(ROOT),
        "exit_code": result.returncode,
    }
    for stream in ("stdout", "stderr"):
        data = getattr(result, stream)
        path = OUTPUT / (old["name"] + "." + stream)
        path.write_bytes(data)
        row[stream] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "equals_A": hashlib.sha256(data).hexdigest() == old[stream + "_sha256"],
        }
    receipts.append(row)
    (OUTPUT / "offline-commands.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print(old["name"], result.returncode, flush=True)
    assert result.returncode == 0, result.stderr.decode()
print("All authorized checks complete; no build or dependency execution invoked.")
