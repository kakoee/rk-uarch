"""Exact approved baseline only; private outputs, no changed flags or source."""

import gzip
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

R = Path("/tmp/u4-b-c2-review")
A = Path("/tmp/u4-k2-c2.75eyx6ab")
P = R / "subject/docs/reviews/U4-A-K2-C2-probes-v1"
N = R / "repeat"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def snapshot(root):
    return {
        str(f.relative_to(root)): {
            "sha256": sha(f.read_bytes()),
            "bytes": f.stat().st_size,
            "mtime_ns": f.stat().st_mtime_ns,
        }
        for f in sorted(root.rglob("*"))
        if f.is_file()
    }


before = snapshot(A)
(R / "original-before.json").write_text(json.dumps(before, sort_keys=True))
print("original snapshot", len(before), flush=True)
for name, row in json.loads((P / "private-receipts.json").read_bytes())["files"].items():
    actual = before[name]
    assert all(actual[k] == row[k] for k in ("sha256", "bytes"))
for name, row in json.loads(
    (R / "subject/docs/reviews/U4-A-K2-C1-precise-v1/cache-inventory.json").read_bytes()
)["files"].items():
    assert before["cache/" + name]["sha256"] == row["sha256"]
for name, row in json.loads((P / "preservation.json").read_bytes())["private_source_files"].items():
    assert before["workspace/" + name]["sha256"] == row["sha256"]
assert len(list((A / "workspace").rglob("*.rs"))) == 1
summary = json.loads((P / "summary.json").read_bytes())
for mode in ("debug", "release"):
    assert before[f"target/{mode}/c2-probe"]["sha256"] == summary[f"{mode}_executable_sha256"]
N.mkdir()
for name in ("workspace", "cache", "controls", "vectors"):
    shutil.copytree(A / name, N / name)
for name in ("target", "receipts", "docker-config"):
    (N / name).mkdir()
assert (N / "workspace/native/crates/uarch-engine/src/bin/c2-probe.rs").read_bytes() == (
    P / "probe.rs"
).read_bytes()
assert (N / "vectors/vectors.jsonl").read_bytes() == gzip.decompress(
    (P / "vectors.jsonl.gz").read_bytes()
)
for name in ("rustc-wrapper.sh", "linker.sh"):
    assert (N / "controls" / name).read_bytes() == (R / "controls" / name).read_bytes()
selected = [
    "image-inspect",
    "rustc",
    "cargo",
    "probe-metadata",
    "compiler-cfg",
    "tool-versions",
    "build-debug-package",
    "build-release-package",
    "execute-debug",
    "execute-release",
    "build-test-debug-package",
    "build-test-release-package",
    "debug-nm",
    "debug-objdump",
    "debug-readelf",
    "release-nm",
    "release-objdump",
    "release-readelf",
    "debug-relocations",
    "release-relocations",
    "identity-supplement-debug",
    "identity-supplement-release",
]
commands = {x["name"]: x for x in json.loads((P / "commands.json").read_bytes())}
receipts = []
for name in selected:
    old = commands[name]
    argv = [s.replace(str(A), str(N)) for s in old["argv"]]
    if "run" in argv:
        assert argv[argv.index("--network") + 1] == "none"
        assert argv[argv.index("--pull") + 1] == "never"
        assert not any("no-vectorize" in s or "target-cpu" in s for s in argv)
    data = None
    if old.get("stdin_sha256"):
        file = "identity-supplement.jsonl.gz" if name.startswith("identity") else "vectors.jsonl.gz"
        data = gzip.decompress((P / file).read_bytes())
        assert sha(data) == old["stdin_sha256"]
    env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": str(N / "docker-config")}
    start = time.time()
    result = subprocess.run(argv, env=env, cwd=R, input=data, capture_output=True)
    row = {
        "name": name,
        "argv": argv,
        "environment": env,
        "cwd": str(R),
        "exit_code": result.returncode,
        "seconds": round(time.time() - start, 3),
        "stdin_sha256": sha(data) if data else None,
    }
    for stream in ("stdout", "stderr"):
        content = getattr(result, stream)
        (N / "receipts" / f"{name}.{stream}").write_bytes(content)
        row[stream] = {
            "sha256": sha(content),
            "bytes": len(content),
            "equals_A": sha(content) == old[f"{stream}_sha256"],
        }
    receipts.append(row)
    (R / "output/commands.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print(name, result.returncode, round(time.time() - start, 2), flush=True)
    assert result.returncode == 0, result.stderr[-2000:]
for mode in ("debug", "release"):
    path = N / f"target/{mode}/c2-probe"
    print("binary", mode, sha(path.read_bytes()), flush=True)
    assert sha(path.read_bytes()) == summary[f"{mode}_executable_sha256"]
assert snapshot(A) == before
print("Original evidence preserved; exact binaries independently reproduced.", flush=True)
