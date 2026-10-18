"""Bounded final identity join, with no installation or native execution."""

import hashlib
import json
import sys
from pathlib import Path

from uarch_contract.hashing import content_hash

from validation.component.installation_identity import installation_bindings, verify_postimages

source, repo, out = map(Path, sys.argv[1:])
a = repo / "docs/reviews/U4-A-issue-edge-F2-F3-v1"
old = Path("/tmp/u4-b-f2f3-source-01")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_bytes())


manifest = read(a / "manifest.json")
assert (
    sha(a / "manifest.json") == "e7c8241c191f663f3b4b874b6e6e71316d52b95ecbfe02987924378dd0be6c80"
)
prior = read(repo / "docs/reviews/U4-A-issue-edge-stage2-v1/manifest.json")
assert (
    sha(repo / "docs/reviews/U4-A-issue-edge-stage2-v1/manifest.json")
    == "6d163e1a85cec9ed55f959dc7f13250ea9a6d09e1b25539f69e797bb8ba334f2"
)
for row in prior["files"]:
    assert sha(old / row["path"]) == row["postimage_sha256"]
for row in manifest["files"]:
    assert sha(source / row["path"]) == row["postimage_sha256"]
for row in manifest["verification"]["historical_controls"]:
    assert sha(source / row["path"]) == row["sha256"] == sha(old / row["path"])
for row in read(a / "artifact-inventory.json")["files"]:
    assert sha(a / row["path"]) == row["sha256"]
    assert (a / row["path"]).stat().st_size == row["bytes"]
selection = read(source / "docs/reviews/U4-B-component-stage2-v1/execution-selection.json")
bindings = installation_bindings(source, selection)
verify_postimages(source, bindings)
overlay = read(source / "validation/component/issue-amendment-binding.json")
assert len(overlay["replacements"]) == 6 and len(overlay["additions"]) == 10
for p, v in overlay["replacements"].items():
    assert bindings[p] == v["after"] == sha(source / p)
for p, v in overlay["additions"].items():
    assert bindings[p] == v == sha(source / p)
assert "validation/component/issue-amendment-binding.json" not in bindings
adr = "docs/decisions/U0011-the-native-engine-core.md"
assert (source / adr).read_bytes()[:48294] == (old / adr).read_bytes()[:48294]
support = read(repo / "docs/reviews/U4-B-component-native-audit-v1/source-audit-final.json")[
    "selected_support"
]
assert len(support) == 56
for p, h in support.items():
    assert sha(source / p) == h == sha(old / p)
closure = {
    str(p.relative_to(source)): sha(p)
    for base in ("contract/uarch_contract", "validation/component")
    for p in (source / base).glob("*.py")
    if not p.name.startswith("test_")
}
assert closure == read(a / "consumer-bindings.json")["closure"]
assert len(closure) == 48
changed_closure = [p for p, h in closure.items() if sha(old / p) != h]
assert changed_closure == ["validation/component/installation_identity.py"]
recipe = "docs/reviews/U4-B-issue-edge-stage2-v1/first_use.py"
assert (
    sha(repo / recipe)
    == sha(source / recipe)
    == sha(old / recipe)
    == read(a / "consumer-bindings.json")["recipe_sha256"]
)
for base in ("native", "contract/schema"):
    before = {str(p.relative_to(old)): sha(p) for p in (old / base).rglob("*") if p.is_file()}
    after = {str(p.relative_to(source)): sha(p) for p in (source / base).rglob("*") if p.is_file()}
    assert before == after
changes = [
    dict(
        path=row["path"],
        before=sha(old / row["path"]) if (old / row["path"]).exists() else None,
        after=row["postimage_sha256"],
    )
    for row in manifest["files"]
    if not (old / row["path"]).exists() or sha(old / row["path"]) != row["postimage_sha256"]
]
assert len(changes) == 6
prospective = read(a / "prospective-first-use.json")
assert sha(repo / prospective["B_requirements"]["path"]) == prospective["B_requirements"]["sha256"]
# Check inherited fault evidence against exact bytes, not only prose claims.
fault = read(a / "evidence/focused/fault-restoration.json")
for row in fault["records"]:
    for stream in ("stdout", "stderr"):
        assert (
            sha(a / ("evidence/focused/" + row["name"] + "." + stream)) == row[stream + "_sha256"]
        )
    assert row["test_sha256"] == sha(
        source / "contract/tests/mapped/test_component_capacity_integration_v3.py"
    )
p = source / "contract/uarch_contract/mapped_issue.py"
call = fault["only_mutation"].encode()
assert p.read_bytes().count(call) == 1
assert sha(p) == fault["exact_restoration_sha256"]
mutant_sha = hashlib.sha256(p.read_bytes().replace(call, b"")).hexdigest()
assert (
    mutant_sha == fault["records"][1]["validator_sha256"] == fault["records"][2]["validator_sha256"]
)
assert (
    "DID NOT RAISE ValueError"
    in (a / "evidence/focused/disconnected-regression.stdout").read_text()
)
assert "1 failed, 1 passed" in (a / "evidence/focused/disconnected-regression.stdout").read_text()
assert read(a / "evidence/focused/baseline-consumers.json") == read(
    a / "evidence/focused/restored-consumers.json"
)
report = dict(
    manifest_sha256=sha(a / "manifest.json"),
    postimages=29,
    changes=changes,
    overlay_replacements=6,
    overlay_additions=10,
    binding_count=len(bindings),
    no_self_hash_cycle=True,
    historical_controls=manifest["verification"]["historical_controls"],
    preserved_ADR_prefix_bytes=48294,
    selected_support=support,
    selected_support_hash=content_hash(support),
    selected_support_changes=[],
    consumer_closure=closure,
    changed_closure_files=changed_closure,
    consumer_recipe_sha256=sha(repo / recipe),
    native_and_schema_changes=[],
    inherited_fault_receipt_sha256=sha(a / "evidence/focused/fault-restoration.json"),
    inherited_mutant_sha256=mutant_sha,
    inventory_verified=True,
    authority=None,
)
out.write_text(json.dumps(report, indent=2) + "\n")
print(
    "29 postimages; 6 changed paths; 6/10 overlay; 48 consumers; "
    "56 unchanged support; 9 historical controls; inherited fault bytes verified"
)
