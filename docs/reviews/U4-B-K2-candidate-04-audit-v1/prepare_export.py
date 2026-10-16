# ruff: noqa: E401, E402, E731, I001, F401, E501
# Exact executed orchestration; preserve import order and origin-observation imports.
import hashlib, io, json, pathlib, shutil, subprocess, tarfile

B = pathlib.Path("/home/jjaff/AI-infra-simulation/rk-uarch-u4-b")
R = pathlib.Path("/tmp/u4-b-candidate04-audit")
R.mkdir(exist_ok=False)
ref = R / "reference"
ref.mkdir()
raw = subprocess.check_output(["git", "archive", "7639542"], cwd=B)
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
    t.extractall(ref, filter="data")
P = ref / "docs/reviews/U4-A-K2-construction-v1"
C = P / "candidate-04"
old = pathlib.Path("/tmp/u4-k2-candidate-04")
h = lambda p: "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
build = json.loads((C / "BuildInputs.json").read_bytes())
for f in build["source_files"]:
    assert h(ref / f["path"]) == f["byte_hash"], f
    blob = subprocess.check_output(["git", "show", "24fa368:" + f["path"]], cwd=B)
    assert "sha256:" + hashlib.sha256(blob).hexdigest() == f["byte_hash"], f
for mode in ["debug", "release"]:
    expected = json.loads((C / f"BuildReceipt-{mode}.json").read_bytes())["executable"]["byte_hash"]
    assert h(old / "targets" / mode / mode / "uarch-engine") == expected
for d in ["output", "receipts", "docker-config", "canary"]:
    (R / d).mkdir()
for src, dst in [
    ("workspace", "source"),
    ("cache", "cache"),
    ("controls", "controls"),
    ("vectors", "vectors"),
]:
    shutil.copytree(old / src, R / dst)
shutil.copytree("/tmp/u4-b-read-trace-v1/diagnostics", R / "diagnostics")
for f in build["source_files"]:
    assert h(R / "source" / f["path"]) == f["byte_hash"]
expected = json.loads(
    (ref / "docs/reviews/U4-A-K2-C1-precise-v1/cache-inventory.json").read_bytes()
)["files"]
actual = {
    str(p.relative_to(R / "cache")): {"sha256": h(p)[7:], "bytes": p.stat().st_size}
    for p in (R / "cache").rglob("*")
    if p.is_file()
}
assert actual == expected
assert (
    h(R / "diagnostics/usr/bin/strace")
    == "sha256:aebaf212ce84a12208c5fa25f08c892029e6f6949b778da55e071ac145404a1e"
)
receipt = {
    "source": "24fa36803081e5077d5977baa91441a2c8534ec8",
    "handoff": "7639542cd28552bd7b9c6b65dcf47f256ce81653",
    "source_files_checked": len(build["source_files"]),
    "cache_files_checked": len(actual),
    "actual_original_binaries_checked": True,
    "private_root": str(R),
}
(R / "output/preflight.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(receipt)
