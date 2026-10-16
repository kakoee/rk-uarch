"""Verify published C2 receipts without builds, native runs or reference derivation."""

import ast
import collections
import gzip
import hashlib
import importlib.util
import io
import json
import tarfile
from pathlib import Path

D = Path(__file__).resolve().parent
BASE = D.parent / "U4-A-K2-C2-probes-v1"
C1 = D.parent / "U4-A-K2-C1-precise-v1"
spec = importlib.util.spec_from_file_location("c2_compare", D / "compare.py")
compare_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare_module)
records = compare_module.records
compare = compare_module.compare


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    return json.loads((D / name).read_bytes())


def compressed(name):
    return json.loads(gzip.decompress((D / name).read_bytes()))


def archive(name):
    with tarfile.open(fileobj=io.BytesIO((D / name).read_bytes()), mode="r:gz") as tar:
        members = tar.getmembers()
        assert len({m.name for m in members}) == len(members)
        assert all(
            m.isfile() and not m.name.startswith("/") and ".." not in Path(m.name).parts
            for m in members
        )
        return {m.name: tar.extractfile(m).read() for m in members}


inventory = read("inventory.json")
for name, expected in inventory.items():
    data = (D / name).read_bytes()
    assert {"sha256": sha(data), "bytes": len(data)} == expected, name
outputs = archive("command-outputs.tar.gz")
controls = archive("executed-controls.tar.gz")
for name, item in read("executed-controls-index.json").items():
    assert sha(controls[name]) == item["sha256"] and len(controls[name]) == item["bytes"]
assert ast.dump(ast.parse((D / "compare.py").read_text())) == ast.dump(
    ast.parse(controls["controls/u4-c2r-comparator.py"].decode())
)
output_map = read("command-output-map.json")
for name, binding in output_map.items():
    raw = outputs[binding["member"]]
    assert sha(raw) == binding["sha256"] and len(raw) == binding["bytes"], name


def output(name, ext="stdout"):
    return outputs[output_map[name + "." + ext]["member"]]


commands = read("commands.json")
assert len({c["name"] for c in commands}) == len(commands)
for command in commands:
    name = command["name"]
    for ext in ["stdout", "stderr"]:
        assert sha(output(name, ext)) == command[ext + "_sha256"]
    expected_exit = (
        101
        if name.startswith("revert-") and name.endswith("-unit")
        else 1
        if name == "host-comparator-reverted"
        else 0
    )
    assert command["exit_code"] == expected_exit, name
    if command["argv"][0] == "/usr/bin/docker" and "run" in command["argv"]:
        argv = command["argv"]
        assert argv[argv.index("--network") + 1] == "none"
        assert argv[argv.index("--pull") + 1] == "never"
        assert "--read-only" in argv
        assert not any("no-vectorize" in a for a in argv)
for name in ["image-inspect", "rustc", "cargo", "cargo-deny", "rustfmt", "clippy"]:
    assert output(name) == (C1 / (name + ".stdout")).read_bytes()
assert (D / "accepted.Cargo.lock").read_bytes() == (C1 / "candidate.Cargo.lock").read_bytes()
assert (D / "probe.Cargo.toml").read_bytes() == (C1 / "scratch.Cargo.toml").read_bytes()
assert (
    json.loads(output("probe-metadata"))["resolve"]
    == json.loads((C1 / "metadata-full.stdout").read_bytes())["resolve"]
)
summary = read("summary.json")
assert (
    sha((D / "probe.rs").read_bytes())
    == summary["source_sha256"]
    == read("build-inputs.json")["probe_source_sha256"]
)
assert sha((D / "refusals.json").read_bytes()) == read("refusal-freeze.json")["sha256"]
for name in ["extension-freeze.json", "refusal-freeze.json", "unit-tests-freeze.json"]:
    assert read(name)["time_ns"] < read("build-inputs.json")["timestamp_ns"]
input_receipt = read("inputs.json")
for path, digest in input_receipt["approval"]["approved_files_sha256"].items():
    assert sha((D.parents[2] / path).read_bytes()) == digest
for path, digest in input_receipt["reconciliation"]["bindings"].items():
    assert sha((D.parents[2] / path).read_bytes()) == digest

vectors = {
    "vectors": records(gzip.decompress((BASE / "vectors.jsonl.gz").read_bytes())),
    "supplement": records(gzip.decompress((BASE / "identity-supplement.jsonl.gz").read_bytes())),
    "B-extension": records(gzip.decompress((D / "B-extension.jsonl.gz").read_bytes())),
    "A-extension": records(gzip.decompress((D / "A-extension.jsonl.gz").read_bytes())),
}
rules = read("refusals.json")
assert len(rules) == 160
for name, rows in vectors.items():
    assert (
        len(rows)
        == {"vectors": 20965, "supplement": 3, "B-extension": 52, "A-extension": 139}[name]
    )
    filename = "identity-supplement.jsonl.gz" if name == "supplement" else name + ".jsonl.gz"
    raw = gzip.decompress(
        ((BASE if name in ["vectors", "supplement"] else D) / filename).read_bytes()
    )
    frozen_name = "supplement.jsonl" if name == "supplement" else name + ".jsonl"
    assert sha(raw) == summary["datasets"][frozen_name]["sha256"]
    for mode in ["debug", "release"]:
        actual = records(output("corrected-" + mode + "-" + name))
        result = compare(rows, actual, rules)
        assert result["mismatch_count"] == 0
        assert result == compressed("comparison-" + mode + ".json.gz")[name]
    assert output("corrected-debug-" + name) == output("corrected-release-" + name)
assert vectors["B-extension"] == json.loads(
    (D.parent / "U4-B-K2-C2-reconciliation-v1/B-expectations.json").read_bytes()
)
for mode in ["debug", "release"]:
    assert output("baseline-" + mode + "-vectors") == gzip.decompress(
        (BASE / "outcomes-debug.jsonl.gz").read_bytes()
    )
    assert output("baseline-" + mode + "-supplement") == gzip.decompress(
        (BASE / "identity-supplement-outcomes.jsonl.gz").read_bytes()
    )
    unit = output("build-test-" + mode + "-package").decode()
    names = [
        x.split(" ... ")[0] for x in unit.splitlines() if x.startswith("test ") and " ... " in x
    ]
    assert len(names) == 12 and names == summary["unit_names"][mode]
    assert "12 passed; 0 failed; 0 ignored" in unit
    for name, rows in vectors.items():
        actual = records(output("baseline-" + mode + "-" + name))
        bad = [
            v["id"]
            for v, a in zip(rows, actual, strict=True)
            if any(
                a.get(k) != value
                for k, value in v["expected"].items()
                if k in ["status", "canonical", "sha256"]
            )
        ]
        assert bad == read("baseline-rerun.json")[mode + "-" + name]["value_or_status_mismatches"]
for family, modes in compressed("reversions.json.gz").items():
    raw = controls["variants/" + family + "/selection.jsonl"]
    rows = records(raw)
    assert sha(raw) == read("reversion-plan.json")["variants"][family]["selection_sha256"]
    for mode, report in modes.items():
        tag = "revert-" + family + "-" + mode
        actual = records(output(tag + "-execute"))
        result = compare(rows, actual, rules)
        assert result == report["reverted"] and result["mismatch_count"] > 0
        assert any(m["expected"]["status"] == "ok" for m in result["mismatches"])
        restored = compare(rows, records(output("restored-" + family + "-" + mode)), rules)
        assert restored == report["restored"] and restored["mismatch_count"] == 0
        assert b"12 tests" in output(tag + "-unit") and b"FAILED" in output(tag + "-unit")
for version, rejected in [("reverted", False), ("restored", True)]:
    result = json.loads(output("host-comparator-" + version))
    assert len(result["controls"]) == 4 and all(
        c["rejected"] == rejected for c in result["controls"]
    )
    assert result["positive_pass"]

# Repeat all 27 discriminators using the published comparator, including the gaps.
v = vectors["vectors"]
a = records(output("baseline-debug-vectors"))
checked = []


def rejects(name, rows, actual):
    try:
        result = compare(rows, actual, rules)
    except (ValueError, TypeError, KeyError, UnicodeError):
        pass
    else:
        assert result["mismatch_count"] > 0, name
    checked.append(name)


for name, rows, actual in [
    ("empty", [], []),
    ("missing", v[:1], []),
    ("duplicate-output", v[:1], a[:1] * 2),
    ("extra", v[:1], a[:2]),
    ("reordered", v[:2], a[:2][::-1]),
    ("duplicate-selection", v[:1] * 2, a[:1] * 2),
    ("wrong-id", v[:1], [dict(a[0], id="foreign")]),
]:
    rejects(name, rows, actual)
for name, changes in [
    ("wrong-bytes", {"canonical": "x"}),
    ("wrong-hash", {"sha256": "0" * 64}),
    ("foreign-key", {"extra": 1}),
    ("missing-canonical", {"canonical": None}),
    ("bad-status", {"status": "other"}),
    ("malformed-refusal", {"status": "refuse", "layer": "carrier"}),
    ("wrong-refusal", {"status": "refuse", "layer": "transport", "error": "unrelated"}),
]:
    rejects(name, v[:1], [dict(a[0], **changes)])
i = next(i for i, row in enumerate(v) if row["family"] == "duplicates")
for name, changes in [
    ("wrong-layer", {"layer": "transport", "error": "unrelated"}),
    ("wrong-reason", {"error": "unrelated"}),
]:
    rejects(name, v[i : i + 1], [dict(a[i], **changes)])
for name, raw in [
    ("empty-bytes", b""),
    ("no-LF", b"{}"),
    ("blank", b"{}\n\n"),
    ("bad-json", b"{\n"),
    ("duplicate-key", b'{"id":"a","id":"a"}\n'),
    ("scalar-output", b"1\n"),
    ("missing-id", b"{}\n"),
    ("null-id", b'{"id":null}\n'),
    ("nonfinite", b'{"id":"a","x":NaN}\n'),
    ("invalid-utf8", b'{"id":"\xff"}\n'),
    ("CRLF", b'{"id":"a"}\r\n'),
]:
    try:
        records(raw)
    except (ValueError, UnicodeError):
        checked.append(name)
    else:
        raise AssertionError(name)
assert checked == read("host-controls-before.json")["controls"]
assert compare(v[:2], a[:2], rules)["mismatch_count"] == 0
assert compare(v[i : i + 1], a[i : i + 1], rules)["mismatch_count"] == 0
# Verify original ten with the reviewed original comparator, not revised refusal diagnostics.
namespace = {"collections": collections}
exec(compile(controls["controls/inherited-compare.py"], "inherited-compare.py", "exec"), namespace)
baseline = namespace["compare"](v, a)
assert baseline["mismatch_count"] == 10
assert [x["id"] for x in baseline["mismatches"]] == [
    x["id"] for x in json.loads((BASE / "counterexample-inputs.json").read_bytes())
]
assert read("preservation.json")["bytes_sizes_mtimes_unchanged"]
print(
    json.dumps(
        {
            "published_inventory_entries": len(inventory),
            "commands_verified": len(commands),
            "per_mode_cases": {k: len(v) for k, v in vectors.items()},
            "unit_tests_per_mode": 12,
            "explicit_refusals_per_mode": 160,
            "host_negative_controls": len(checked),
            "native_reversion_families": 3,
            "comparator_reversion_restored": True,
            "new_native_execution": False,
        },
        indent=2,
    )
)
