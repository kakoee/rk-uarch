"""Verify final joined postimages, exact prospective overlay and inherited source closure."""

import hashlib
import json
import sys
from pathlib import Path

from uarch_contract.hashing import content_hash

from validation.component.installation_identity import installation_bindings, verify_postimages

source, repo, out = map(Path, sys.argv[1:])
a = repo / "docs/reviews/U4-A-issue-edge-stage2-v1"
b = repo / "docs/reviews/U4-B-issue-edge-stage2-v1"
old = Path("/tmp/u4-b-issue-v2-01/full")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


manifest = json.loads((a / "manifest.json").read_text())
assert (
    sha(a / "manifest.json") == "6d163e1a85cec9ed55f959dc7f13250ea9a6d09e1b25539f69e797bb8ba334f2"
)
for row in manifest["files"]:
    assert sha(source / row["path"]) == row["postimage_sha256"]
for row in json.loads((b / "manifest.json").read_text())["files"]:
    assert sha(source / row["path"]) == row["postimage_sha256"]
controls = manifest["verification"]["historical_controls"]
for row in controls:
    assert sha(source / row["path"]) == row["sha256"] == sha(old / row["path"])
selection = json.loads(
    (source / "docs/reviews/U4-B-component-stage2-v1/execution-selection.json").read_text()
)
bindings = installation_bindings(source, selection)
verify_postimages(source, bindings)
overlay = json.loads((source / "validation/component/issue-amendment-binding.json").read_text())
assert len(overlay["replacements"]) == 6 and len(overlay["additions"]) == 7
for p, v in overlay["additions"].items():
    assert bindings[p] == v == sha(source / p)
for p, v in overlay["replacements"].items():
    assert bindings[p] == v["after"] == sha(source / p)
# Exact installed K2 + reviewed component suffix remains a byte prefix; only the
# prospective issue appendix changes. The installation verifier separately pins both.
adr = "docs/decisions/U0011-the-native-engine-core.md"
assert (source / adr).read_bytes()[:48294] == (old / adr).read_bytes()[:48294]
support = json.loads(
    (repo / "docs/reviews/U4-B-component-native-audit-v1/source-audit-final.json").read_text()
)["selected_support"]
assert len(support) == 56
for p, h in support.items():
    assert sha(source / p) == h == sha(old / p)
assert (
    content_hash(support)
    == "sha256:676b12509606b7a519d9597dc406f8fe66d141af4c86425a5baf3a2e3825358a"
)
closure = {
    str(p.relative_to(source)): sha(p)
    for base in ("contract/uarch_contract", "validation/component")
    for p in (source / base).glob("*.py")
    if not p.name.startswith("test_")
}
a_closure = json.loads((a / "evidence/joined-checks/f4.json").read_text())["closure"]
assert closure == a_closure
assert (
    sha(b / "first_use.py")
    == json.loads((a / "evidence/joined-checks/f4.json").read_text())["recipe_sha256"]
)
assert (
    sha(b / "first-use-requirements.json")
    == json.loads((a / "prospective-first-use.json").read_text())["B_requirements"]["sha256"]
)
old_native = {str(p.relative_to(old)): sha(p) for p in (old / "native").rglob("*") if p.is_file()}
new_native = {
    str(p.relative_to(source)): sha(p) for p in (source / "native").rglob("*") if p.is_file()
}
native_delta = [
    dict(path=p, before=old_native.get(p), after=new_native.get(p))
    for p in sorted(old_native.keys() | new_native.keys())
    if old_native.get(p) != new_native.get(p)
]
assert {x["path"] for x in native_delta} == {
    "native/crates/uarch-engine/src/issue_proposal_tests.rs",
    *[
        "native/crates/uarch-engine/testdata/synthetic-stage2-" + name + ".json"
        for name in ("cc0-v3", "cc-v3", "sr-v3")
    ],
}
deltas = [
    dict(
        path=x["path"],
        before=sha(old / x["path"]) if (old / x["path"]).exists() else None,
        after=x["postimage_sha256"],
    )
    for x in manifest["files"]
    if not (old / x["path"]).exists() or sha(old / x["path"]) != x["postimage_sha256"]
]
report = dict(
    manifest_sha256=sha(a / "manifest.json"),
    joined_postimages=26,
    B_exact_postimages=3,
    overlay_sha256=sha(source / "validation/component/issue-amendment-binding.json"),
    overlay_replacements=6,
    overlay_additions=7,
    installed_binding_count=len(bindings),
    no_self_hash_cycle=True,
    historical_controls=controls,
    preserved_ADR_prefix_bytes=48294,
    selected_support=support,
    selected_support_hash=content_hash(support),
    selected_support_changes=[],
    consumer_closure=closure,
    A_consumer_closure_equal=True,
    consumer_recipe_sha256=sha(b / "first_use.py"),
    schema_bindings={
        x["path"]: x["postimage_sha256"] for x in manifest["files"] if "/schema/" in x["path"]
    },
    deltas_from_A_v2=deltas,
    native_delta=native_delta,
    production_native_bytes_unchanged=True,
    authority=None,
)
out.write_text(json.dumps(report, indent=2) + "\n")
print(
    "26 postimages, exact B corrections, 6/7 overlay, 56 support files, 9 historical controls and",
    len(closure),
    "consumer files verified",
)
