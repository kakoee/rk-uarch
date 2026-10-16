"""Read-only receipt validation; this never runs native code or imports project modules."""

import gzip
import hashlib
import importlib.util
import json
import pathlib
import tarfile

ROOT = pathlib.Path(__file__).resolve().parent
AUTHOR = ROOT.parent / "U4-A-K2-C2-nonblank-v1"
PREVIOUS = ROOT.parent / "U4-A-K2-C2-compatibility-v1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(name):
    return json.loads((ROOT / name).read_bytes())


def archive(path):
    with tarfile.open(path) as handle:
        return {item.name: handle.extractfile(item).read() for item in handle if item.isfile()}


def main():
    inventory = read("inventory.json")
    for name, binding in inventory.items():
        raw = (ROOT / name).read_bytes()
        assert sha(raw) == binding["sha256"] and len(raw) == binding["bytes"], name
    setup = read("setup.json")
    assert setup["review_subject"] == "c678dedd47e639f7e7f0ac55f48a8775fe524708"
    for name, digest in setup["coordinator_bindings"].items():
        assert sha((AUTHOR / name).read_bytes()) == digest
    assert (AUTHOR / "compare.py").read_bytes() == (PREVIOUS / "compare.py").read_bytes()
    spec = importlib.util.spec_from_file_location("pinned_compare", AUTHOR / "compare.py")
    comparator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(comparator)
    assert pathlib.Path(comparator.__file__).resolve() == (AUTHOR / "compare.py").resolve()
    controls = archive(ROOT / "executed-controls.tar.gz")
    for name, binding in read("executed-controls-index.json").items():
        assert sha(controls[name]) == binding["sha256"] and len(controls[name]) == binding["bytes"]
    mapping = read("command-output-map.json")
    archives = {name: archive(ROOT / name) for name in {x["archive"] for x in mapping.values()}}

    def output(name, ext="stdout"):
        binding = mapping[name + "." + ext]
        raw = archives[binding["archive"]][binding["member"]]
        assert sha(raw) == binding["sha256"] and len(raw) == binding["bytes"]
        return raw

    commands = read("commands.json")
    assert len(commands) == len({x["name"] for x in commands}) == 32
    frozen = read("python-review.json")
    for command in commands:
        assert command["started_ns"] > frozen["time_ns"]
        for ext in ["stdout", "stderr"]:
            assert sha(output(command["name"], ext)) == command[ext + "_sha256"]
        expected_exit = (
            101
            if command["name"].startswith("reverted-") and command["name"].endswith("-unit")
            else 0
        )
        assert command["exit_code"] == expected_exit
        argv = command["argv"]
        if "run" in argv:
            for flag, value in [
                ("--network", "none"),
                ("--pull", "never"),
                ("--user", "1000:1000"),
                ("--cap-drop", "ALL"),
            ]:
                assert argv[argv.index(flag) + 1] == value
            assert "--read-only" in argv and "no-new-privileges" in argv
    metadata = json.loads(output("probe-metadata"))
    accepted = json.loads((ROOT.parent / "U4-A-K2-C1-precise-v1/metadata-full.stdout").read_bytes())
    assert metadata["resolve"] == accepted["resolve"] and len(metadata["packages"]) == 36
    root = next(x for x in metadata["packages"] if x["name"] == "uarch-engine")
    assert len(root["targets"]) == 1 and root["targets"][0]["name"] == "c2-probe"
    assert root["targets"][0]["kind"] == ["bin"]
    original = ROOT.parent / "U4-A-K2-C2-probes-v1"
    raw_vectors = {
        "vectors": gzip.decompress((original / "vectors.jsonl.gz").read_bytes()),
        "supplement": gzip.decompress((original / "identity-supplement.jsonl.gz").read_bytes()),
        "B-extension": gzip.decompress((PREVIOUS / "B-extension.jsonl.gz").read_bytes()),
        "A-extension": gzip.decompress((PREVIOUS / "A-extension.jsonl.gz").read_bytes()),
        "B-independent": (
            ROOT.parent / "U4-B-K2-C2-compatibility-review-v1/independent.jsonl"
        ).read_bytes(),
        "focused": gzip.decompress((AUTHOR / "focused.jsonl.gz").read_bytes()),
    }
    rules = json.loads((PREVIOUS / "refusals.json").read_bytes())
    new_rules = json.loads((AUTHOR / "new-refusals.json").read_bytes())
    assert len(rules) == 160 and len(new_rules) == 257 and not set(rules) & set(new_rules)
    rules.update(new_rules)
    native = read("native-review.json")
    summary = json.loads((AUTHOR / "summary.json").read_bytes())
    for mode in ["debug", "release"]:
        count = refused = 0
        for name, raw in raw_vectors.items():
            assert sha(raw) == frozen["datasets"][name + ".jsonl"]["sha256"]
            actual = output(f"corrected-{mode}-{name}")
            assert actual == output(f"corrected-debug-{name}")
            result = comparator.compare(comparator.records(raw), comparator.records(actual), rules)
            assert result["mismatch_count"] == 0
            count += result["count"]
            refused += len(result["refusals"])
        assert count == 21694 and refused == 417
        units = native["modes"][mode]["unit_results"]
        assert len(units) == len(set(units)) == 17 and all(x.endswith(" ... ok") for x in units)
        assert all(x.encode() in output(f"build-test-{mode}-package") for x in units)
        assert native["modes"][mode]["binary_sha256"] == summary["binary_sha256"][mode]
    selection = comparator.records(raw_vectors["B-independent"] + raw_vectors["focused"])
    predicted = set(frozen["predicted_wrong_acceptances"])
    assert len(predicted) == 35
    for phase, binding in native["phases"].items():
        result = comparator.compare(
            selection, comparator.records(output(phase + "-selection")), rules
        )
        assert result["mismatches"] == binding["mismatches"] and binding["positive_controls"] == 278
        units = binding["unit_results"]
        assert len(units) == len(set(x.split(" ... ")[0] for x in units)) == 17
        assert all(x.encode() in output(phase + "-unit") for x in units)
        if phase.startswith("reverted"):
            assert {x["id"] for x in result["mismatches"]} == predicted
            assert all(
                x["expected"]["status"] == "refuse" and x["actual"]["status"] == "ok"
                for x in result["mismatches"]
            )
            assert any(x.endswith(" ... FAILED") for x in units)
        else:
            assert result["mismatch_count"] == 0 and all(x.endswith(" ... ok") for x in units)
            assert binding["binary_sha256"] == summary["binary_sha256"][phase.split("-")[1]]
            assert binding["source_sha256"] == summary["source_sha256"]
    blank = frozen["strip_empty_codepoints"]
    assert (
        len(blank) == 29
        and sha("".join(f"{cp:08x}\n" for cp in blank).encode()) == frozen["blank_encoding_sha256"]
    )
    assert len(frozen["focused_refusal_classifications"]) == 221
    preservation = read("preservation.json")
    assert preservation["original_files_unchanged"] == 7667
    assert preservation["readonly_copied_cache_entries_unchanged"] == 1719
    print(
        json.dumps(
            {
                "inventory_entries": len(inventory),
                "command_receipts": 32,
                "cases_per_mode": 21694,
                "refusals_per_mode": 417,
                "unit_tests_per_mode": 17,
                "predicted_wrong_acceptances_per_mode": 35,
                "restored_mismatches": 0,
                "new_native_execution_by_this_verifier": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
