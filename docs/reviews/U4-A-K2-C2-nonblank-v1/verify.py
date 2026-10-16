"""Verify saved nonblank experiment receipts; no native run or reference re-derivation."""

import gzip
import hashlib
import importlib.util
import io
import json
import tarfile
from pathlib import Path

D = Path(__file__).resolve().parent
A = D.parent / "U4-A-K2-C2-compatibility-v1"
B = D.parent / "U4-B-K2-C2-compatibility-review-v1"
ORIGINAL = D.parent / "U4-A-K2-C2-probes-v1"
C1 = D.parent / "U4-A-K2-C1-precise-v1"
spec = importlib.util.spec_from_file_location("reviewed_compare", D / "compare.py")
comparator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparator)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    return json.loads((D / name).read_bytes())


def compressed(name):
    return json.loads(gzip.decompress((D / name).read_bytes()))


def archive(name):
    with tarfile.open(fileobj=io.BytesIO((D / name).read_bytes()), mode="r:gz") as tar:
        members = tar.getmembers()
        assert len(members) == len({m.name for m in members})
        assert all(
            m.isfile() and not m.name.startswith("/") and ".." not in Path(m.name).parts
            for m in members
        )
        return {m.name: tar.extractfile(m).read() for m in members}


inventory = read("inventory.json")
for name, expected in inventory.items():
    raw = (D / name).read_bytes()
    assert {"sha256": sha(raw), "bytes": len(raw)} == expected, name
outputs = archive("command-outputs.tar.gz")
controls = archive("executed-controls.tar.gz")
for name, binding in read("executed-controls-index.json").items():
    assert sha(controls[name]) == binding["sha256"] and len(controls[name]) == binding["bytes"]
output_map = read("command-output-map.json")
for name, binding in output_map.items():
    raw = outputs[binding["member"]]
    assert sha(raw) == binding["sha256"] and len(raw) == binding["bytes"], name


def output(name, ext="stdout"):
    return outputs[output_map[name + "." + ext]["member"]]


assert (D / "compare.py").read_bytes() == (A / "compare.py").read_bytes()
assert sha((D / "compare.py").read_bytes()) == read("starting-source.json")["comparator_sha256"]
commands = read("commands.json")
assert len(commands) == len({c["name"] for c in commands})
for command in commands:
    name = command["name"]
    for ext in ["stdout", "stderr"]:
        assert sha(output(name, ext)) == command[ext + "_sha256"]
    assert command["exit_code"] == (
        101 if name.startswith("reverted-") and name.endswith("-unit") else 0
    )
    if "run" in command["argv"]:
        argv = command["argv"]
        assert argv[argv.index("--pull") + 1] == "never"
        assert argv[argv.index("--network") + 1] == "none"
        assert argv[argv.index("--user") + 1] == "1000:1000"
        assert "--read-only" in argv
for name in ["image-inspect", "rustc", "cargo", "cargo-deny", "rustfmt", "clippy"]:
    assert output(name) == (C1 / (name + ".stdout")).read_bytes()
metadata = json.loads(output("probe-metadata"))
assert metadata["resolve"] == json.loads((C1 / "metadata-full.stdout").read_bytes())["resolve"]
root = next(p for p in metadata["packages"] if p["name"] == "uarch-engine")
assert len(root["targets"]) == 1 and root["targets"][0]["kind"] == ["bin"]
assert root["targets"][0]["name"] == "c2-probe"
assert len(read("preservation.json")["source_inventory"]) == 4
assert len(read("starting-source.json")["workspace_files"]) == 4
summary = read("summary.json")
assert (
    sha((D / "probe.rs").read_bytes())
    == summary["source_sha256"]
    == read("build-inputs.json")["probe_source_sha256"]
)
assert read("preservation.json")["restored_source_sha256"] == summary["source_sha256"]
for path, digest in read("inputs.json")["reconciliation"]["bindings"].items():
    assert sha((D.parents[2] / path).read_bytes()) == digest
for path, digest in read("inputs.json")["approval"]["approved_files_sha256"].items():
    assert sha((D.parents[2] / path).read_bytes()) == digest
for name in ["python-freeze.json", "refusal-freeze.json", "unit-freeze.json"]:
    assert (
        read(name)["time_ns"]
        < read("implementation.json")["time_ns"]
        < read("build-inputs.json")["timestamp_ns"]
    )
assert sha(controls["receipts/units-before-correction.rs"]) == read("unit-freeze.json")["sha256"]
blank = read("python-freeze.json")["blank_set"]
assert len(blank["codepoints"]) == 29
assert sha("".join(f"{c:08x}\n" for c in blank["codepoints"]).encode()) == blank["sha256"]
assert blank["sha256"] in (D / "probe.rs").read_text()
raw_vectors = {
    "vectors": gzip.decompress((ORIGINAL / "vectors.jsonl.gz").read_bytes()),
    "supplement": gzip.decompress((ORIGINAL / "identity-supplement.jsonl.gz").read_bytes()),
    "B-extension": gzip.decompress((A / "B-extension.jsonl.gz").read_bytes()),
    "A-extension": gzip.decompress((A / "A-extension.jsonl.gz").read_bytes()),
    "B-independent": (B / "independent.jsonl").read_bytes(),
    "focused": gzip.decompress((D / "focused.jsonl.gz").read_bytes()),
}
vectors = {k: comparator.records(v) for k, v in raw_vectors.items()}
for name, raw in raw_vectors.items():
    frozen = summary["datasets"][name + ".jsonl"]
    assert sha(raw) == frozen["sha256"] and len(vectors[name]) == frozen["count"]
assert sum(map(len, vectors.values())) == 21694
rules = json.loads((A / "refusals.json").read_bytes())
new = read("new-refusals.json")
assert len(rules) == 160 and len(new) == 257 and not set(rules) & set(new)
assert sha((D / "new-refusals.json").read_bytes()) == read("refusal-freeze.json")["new_sha256"]
rules.update(new)
assert (
    sha((json.dumps(rules, indent=2) + "\n").encode())
    == read("refusal-freeze.json")["combined_sha256"]
)
for mode in ["debug", "release"]:
    for phase in ["baseline", "corrected"]:
        saved = compressed(phase + "-" + mode + "-comparison.json.gz")
        for name, rows in vectors.items():
            actual = comparator.records(output(phase + "-" + mode + "-" + name))
            result = comparator.compare(rows, actual, rules)
            assert result == saved[name]
            wanted = {"B-independent": 2, "focused": 33}.get(name, 0) if phase == "baseline" else 0
            assert result["mismatch_count"] == wanted
            if phase == "baseline" and wanted:
                assert all(
                    m["expected"]["status"] == "refuse" and m["actual"]["status"] == "ok"
                    for m in result["mismatches"]
                )
    b_bad = compressed("baseline-" + mode + "-comparison.json.gz")["B-independent"]["mismatches"]
    assert [m["id"] for m in b_bad] == [
        "B2:legacy:blank-control-unit",
        "B2:legacy:blank-control-rationale",
    ]
    unit = output("build-test-" + mode + "-package").decode()
    names = [
        line.split(" ... ")[0]
        for line in unit.splitlines()
        if line.startswith("test ") and " ... " in line
    ]
    assert names == summary["unit_names"][mode] and len(set(names)) == 17
    assert "17 passed; 0 failed; 0 ignored" in unit
    for name in vectors:
        baseline = comparator.records(output("baseline-" + mode + "-" + name))
        corrected = comparator.records(output("corrected-" + mode + "-" + name))
        assert all(
            a == b
            for a, b in zip(baseline, corrected, strict=True)
            if a["status"] == b["status"] == "ok"
        )
        if name not in ["B-independent", "focused"]:
            assert output("baseline-" + mode + "-" + name) == output(
                "corrected-" + mode + "-" + name
            )
            assert (
                sha(output("corrected-" + mode + "-" + name))
                == json.loads((B / "native-review.json").read_bytes())["modes"][mode]["datasets"][
                    name
                ]["stdout_sha256"]
            )
for name in vectors:
    assert output("corrected-debug-" + name) == output("corrected-release-" + name)
selection = controls["reversion/selection.jsonl"]
assert selection == raw_vectors["B-independent"] + raw_vectors["focused"]
assert sha(selection) == read("reversion-plan.json")["selection_sha256"]
assert (
    sha(controls["receipts/reverted-probe.rs"])
    == read("reversion-plan.json")["reverted_source_sha256"]
)
for key, report in compressed("reversion-results.json.gz").items():
    result = comparator.compare(
        comparator.records(selection), comparator.records(output(key + "-selection")), rules
    )
    assert result == report["comparison"]
    assert result["mismatch_count"] == (35 if key.startswith("reverted") else 0)
    assert b"17 tests" in output(key + "-unit")
    if key.startswith("restored"):
        assert b"17 passed; 0 failed" in output(key + "-unit")
        assert report["source_sha256"] == summary["source_sha256"]
        assert report["binary_sha256"] == summary["binary_sha256"][key.split("-")[1]]
    else:
        assert b"FAILED" in output(key + "-unit")
        assert all(
            m["expected"]["status"] == "refuse" and m["actual"]["status"] == "ok"
            for m in result["mismatches"]
        )
        assert (
            report["binary_sha256"] == read("reverted-binaries.json")[key.split("-")[1]]["sha256"]
        )
assert read("preservation.json")["bytes_sizes_mtimes_unchanged"]
# Meaningful refusal control: a transport failure cannot satisfy a nonblank refusal.
row = next(v for v in vectors["B-independent"] if v["id"] == "B2:legacy:blank-control-unit")
wrong = {"id": row["id"], "status": "refuse", "layer": "transport", "error": "unrelated"}
assert comparator.compare([row], [wrong], rules)["mismatch_count"] == 1
wrong.update(layer="carrier", error="LegacyFloatSyntax")
assert comparator.compare([row], [wrong], rules)["mismatch_count"] == 1
print(
    json.dumps(
        {
            "inventory_entries": len(inventory),
            "commands": len(commands),
            "cases_per_mode": 21694,
            "refusals_per_mode": 417,
            "unit_tests_per_mode": 17,
            "baseline_new_failures_per_mode": 35,
            "reverted_failures_per_mode": 35,
            "corrected_and_restored_mismatches": 0,
            "new_native_execution": False,
        },
        indent=2,
    )
)
