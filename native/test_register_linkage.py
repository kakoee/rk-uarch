"""K1 documentation/register controls using actual accepted-image Cargo metadata.

Run on the host with K1_METADATA pointing to cargo metadata --locked --offline output.
This checks build roles, not new dependency or licence admission.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = "Runtime library graph"
MACRO = "Proc-macro/build tool; not runtime-linked"
TEST = "Test-only library graph"
BUILD = "Test-only build tool; not runtime-linked"
CONDITIONAL = "Test-only conditional UEFI; not linked on Linux target"


def roles():
    metadata = json.loads(Path(os.environ["K1_METADATA"]).read_text())
    packages = {p["id"]: p for p in metadata["packages"]}
    nodes = {n["id"]: n for n in metadata["resolve"]["nodes"]}
    result = {}
    pending = [(metadata["workspace_members"][0], RUNTIME)]
    seen = set()
    while pending:
        package_id, context = pending.pop()
        if (package_id, context) in seen:
            continue
        seen.add((package_id, context))
        package = packages[package_id]
        if any("proc-macro" in t["kind"] for t in package["targets"]):
            context = MACRO
        if package["source"]:
            result.setdefault(package["name"], set()).add(context)
        for dep in nodes[package_id]["deps"]:
            for edge in dep["dep_kinds"]:
                role = TEST if edge["kind"] == "dev" else context
                if edge["kind"] == "build":
                    role = BUILD if role in (TEST, BUILD) else MACRO
                if edge["target"] and 'target_os = "uefi"' in edge["target"]:
                    role = CONDITIONAL
                pending.append((dep["pkg"], role))
    assert all(len(v) == 1 for v in result.values()), result
    return {k: next(iter(v)) for k, v in result.items()}


def test_linkage_matches_locked_dependency_graph():
    rows = [x.split("|") for x in (ROOT / "third_party/LICENSES.md").read_text().splitlines()
            if x.startswith("| ")][1:]
    actual = {r[1].strip(): r[5].strip() for r in rows}
    assert actual == roles()


def test_native_readme_describes_delivered_boundary():
    text = (ROOT / "native/README.md").read_text()
    assert "Binary: uarch-engine" not in text
    for phrase in ("library target", "dispatch capability", "phase-2", "not a public"):
        assert phrase in text
