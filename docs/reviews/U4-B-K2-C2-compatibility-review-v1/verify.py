"""Portable saved-evidence checks; no native execution or live project imports."""

import hashlib
import importlib.util
import json
import pathlib
import tarfile

ROOT = pathlib.Path(__file__).resolve().parent
AUTHOR = ROOT.parent / "U4-A-K2-C2-compatibility-v1"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(name):
    return json.loads((ROOT / name).read_text())


def archive(path):
    with tarfile.open(path) as handle:
        return {item.name: handle.extractfile(item).read() for item in handle if item.isfile()}


def main():
    inventory = read("inventory.json")
    for name, info in inventory.items():
        raw = (ROOT / name).read_bytes()
        assert digest(raw) == info["sha256"] and len(raw) == info["bytes"], name
    assert digest((AUTHOR / "compare.py").read_bytes()) == (
        "05c2b2a0e81f3a5157246b6d487fedc903d6390735e4b76712f70f3c4e033338"
    )
    spec = importlib.util.spec_from_file_location("reviewed_comparator", AUTHOR / "compare.py")
    comparator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(comparator)
    assert pathlib.Path(comparator.__file__).resolve() == (AUTHOR / "compare.py").resolve()
    controls = archive(ROOT / "executed-host-controls.tar.gz")
    for name, info in read("executed-host-controls.json").items():
        assert digest(controls[name]) == info["sha256"] and len(controls[name]) == info["bytes"]
    output_map = read("command-output-map.json")
    archives = {name: archive(ROOT / name) for name in {v["archive"] for v in output_map.values()}}

    def output(command, extension="stdout"):
        binding = output_map[command + "." + extension]
        raw = archives[binding["archive"]][binding["member"]]
        assert digest(raw) == binding["sha256"] and len(raw) == binding["bytes"]
        return raw

    commands = read("commands.json")
    assert len(commands) == 42 and len({c["name"] for c in commands}) == 42
    for command in commands:
        for extension in ("stdout", "stderr"):
            assert digest(output(command["name"], extension)) == command[extension + "_sha256"]
        expected_exit = (
            101
            if command["name"].startswith("revert-") and command["name"].endswith("-unit")
            else 0
        )
        assert command["exit_code"] == expected_exit
        args = command["argv"]
        if "run" in args:
            assert args[args.index("--network") + 1] == "none"
            assert args[args.index("--pull") + 1] == "never"
            assert "--read-only" in args and "--cap-drop" in args
            assert "no-new-privileges" in args
            assert not any("/diagnostics" in arg or "no-vectorize" in arg for arg in args)
    native = read("native-review.json")
    rules = json.loads((AUTHOR / "refusals.json").read_text())
    import gzip

    original = AUTHOR.parent / "U4-A-K2-C2-probes-v1"
    datasets = {
        "vectors": original / "vectors.jsonl.gz",
        "supplement": original / "identity-supplement.jsonl.gz",
        "B-extension": AUTHOR / "B-extension.jsonl.gz",
        "A-extension": AUTHOR / "A-extension.jsonl.gz",
    }
    for mode in ("debug", "release"):
        total = refused = 0
        for name, path in datasets.items():
            vectors = comparator.records(gzip.decompress(path.read_bytes()))
            actual = output(f"corrected-{mode}-{name}")
            result = comparator.compare(vectors, comparator.records(actual), rules)
            assert result["mismatch_count"] == 0
            total += result["count"]
            refused += len(result["refusals"])
            assert actual == output(f"corrected-debug-{name}")
        assert total == 21159 and refused == 160
        unit = native["modes"][mode]["unit_results"]
        assert len(unit) == len(set(unit)) == 12 and all(n.endswith(" ... ok") for n in unit)
        for name in unit:
            assert name.encode() in output(f"build-test-{mode}-package")
        observations = comparator.records(output(f"independent-{mode}"))
        vectors = comparator.records((ROOT / "independent.jsonl").read_bytes())
        assert len(vectors) == len(observations) == 66
        assert [v["id"] for v in vectors] == [v["id"] for v in observations]
        mismatches = []
        for vector, actual in zip(vectors, observations, strict=True):
            expected = vector["expected"]
            if (
                expected["status"] != actual["status"]
                or actual["status"] == "ok"
                and any(expected.get(key) != actual[key] for key in ("canonical", "sha256"))
            ):
                mismatches.append({"input": vector, "actual": actual})
        assert mismatches == native["independent"][mode]["mismatches"]
        assert len(mismatches) == 2
    frozen = read("python-derivation.json")
    assert digest((ROOT / "independent.jsonl").read_bytes()) == frozen["independent_sha256"]
    assert all(c["started_ns"] > frozen["timestamp_ns"] for c in commands)
    author_controls = archive(AUTHOR / "executed-controls.tar.gz")
    for family, receipt in read("native-faults.json").items():
        raw = author_controls[f"variants/{family}/selection.jsonl"]
        assert digest(raw) == receipt["selection_sha256"]
        rows = comparator.records(raw)
        for mode in ("debug", "release"):
            result = comparator.compare(
                rows, comparator.records(output(f"revert-{family}-{mode}-execute")), rules
            )
            expected = receipt["modes"][mode]
            assert result["mismatch_count"] == expected["mismatches"] > 0
            positives = [v["id"] for v in result["mismatches"] if v["expected"]["status"] == "ok"]
            assert positives == expected["expected_positive_failures"] and positives
            restored = comparator.compare(
                rows, comparator.records(output(f"restored-{family}-{mode}")), rules
            )
            assert restored["mismatch_count"] == 0
    preservation = read("preservation.json")
    assert preservation["original_A_files_unchanged"] == 10160
    assert preservation["copied_cache_entries_unchanged"] == 1719
    assert preservation["all_three_scratch_variant_sources_restored_to_corrected"]
    print(
        json.dumps(
            {
                "inventory_entries": len(inventory),
                "new_command_receipts": 42,
                "cases_per_mode": 21159,
                "refusals_per_mode": 160,
                "unit_tests_per_mode": 12,
                "preserved_new_counterexamples_per_mode": 2,
                "native_fault_families": 3,
                "verification_is_saved_receipt_check_only": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
