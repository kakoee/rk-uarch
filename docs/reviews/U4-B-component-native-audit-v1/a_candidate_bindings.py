"""Independently verify published A construction identities; create no trust."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
A = ROOT / "docs/reviews/U4-A-component-native-v1/evidence/candidate-04"


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


build = json.loads((A / "BuildInputs.json").read_bytes())
engine = json.loads((A / "engine.json").read_bytes())
trust = json.loads((A / "BuildTrust.json").read_bytes())
assert build["source_commit"] == "64837bea3724919facbc27be1c7f5644a6354cfa"
names = (
    subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", build["source_commit"], "native"], cwd=ROOT
    )
    .decode()
    .splitlines()
)
assert sorted(names) == [r["path"] for r in build["source_files"]]
for row in build["source_files"]:
    assert digest((ROOT / row["path"]).read_bytes()) == row["byte_hash"]
assert build["model_sources"] == [
    r for r in build["source_files"] if r["path"].startswith("native/crates/uarch-engine/src/")
]
assert engine["implementation_hash"] == digest(canonical(build))
assert engine["model"]["implementation_hash"] == digest(canonical(build["model_sources"]))
tools = ROOT / build["tool_inputs_file"]["path"]
assert digest(tools.read_bytes()) == build["tool_inputs_file"]["byte_hash"]
assert digest(canonical(json.loads(tools.read_bytes()))) == engine["compiler_lock_hash"]
assert trust["format"] == "uarch-component-build-trust/1"
assert trust["public_authority"] is None and trust["purpose"] == "private-synthetic-tests-only"
generated = json.loads((A / "generated.json").read_text())
assert digest((A / "generated-identity.rs.txt").read_bytes()) == generated["byte_hash"]
executables = {}
for mode in ("debug", "release"):
    record = json.loads((A / (mode + "-executable.json")).read_text())
    assert record["engine"] == engine
    assert digest(Path(record["path"]).read_bytes()) == record["byte_hash"]
    executables[mode] = record
report = dict(
    source_commit=build["source_commit"],
    engine=engine,
    actual_executables=executables,
    source_files_verified=len(names),
    model_files_verified=len(build["model_sources"]),
    source_inventory_sha256=digest(canonical(build["source_files"])),
    BuildInputs_sha256=digest((A / "BuildInputs.json").read_bytes()),
    BuildTrust_sha256=digest((A / "BuildTrust.json").read_bytes()),
    generated_identity_sha256=generated["byte_hash"],
    authority_created=False,
    purpose="read-only verification of A frozen private candidate; no public authority",
    runtime_loader_evidence="A published ELF/ldd/library hashes; B image hashes checked separately",
    inherited_author_tests=(
        "74 per mode, 79-output six-way replay, ten public-process refusals; not B executions"
    ),
)
print(json.dumps(report, indent=2, sort_keys=True))
