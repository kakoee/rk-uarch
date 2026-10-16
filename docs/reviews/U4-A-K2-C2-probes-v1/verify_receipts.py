"""Read-only C2 evidence verification; never builds or executes native code."""

import gzip
import hashlib
import io
import json
import re
import subprocess
import tarfile
from collections import Counter
from pathlib import Path

D = Path(__file__).resolve().parent
R = D.parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(name):
    return json.loads((D / name).read_bytes())


def lines(data):
    # U+2028 is valid JSON string content; it is not the JSONL record separator.
    return [json.loads(line) for line in data.split(b"\n") if line]


def compare(vectors, actual):
    ids = [x["id"] for x in actual]
    assert len(set(ids)) == len(ids)
    assert Counter(ids) == Counter(x["id"] for x in vectors)
    observed = {x["id"]: x for x in actual}
    mismatches = []
    for vector in vectors:
        want = vector["expected"]
        got = observed[vector["id"]]
        matches = want["status"] == got["status"]
        if matches and want["status"] == "ok":
            matches = want["sha256"] == got.get("sha256")
            if "canonical" in want:
                matches = matches and want["canonical"] == got.get("canonical")
        if not matches:
            mismatches.append(vector["id"])
    return mismatches


def main():
    inputs = load("inputs.json")
    approval = (R / inputs["approval_file"]).read_bytes()
    assert sha(approval) == inputs["approval_sha256"]
    for path, digest in json.loads(approval)["approved_files_sha256"].items():
        assert sha((R / path).read_bytes()) == digest
    original = R / "docs/reviews/U4-A-K2-C1-precise-v1"
    assert sha((original / "candidate.Cargo.lock").read_bytes()) == inputs["candidate_lock_sha256"]
    assert sha((D / "probe.Cargo.toml").read_bytes()) == inputs["candidate_manifest_sha256"]
    assert (D / "probe.Cargo.toml").read_bytes() == (original / "scratch.Cargo.toml").read_bytes()
    assert sha((original / "cache-inventory.json").read_bytes()) == inputs["cache_inventory_sha256"]
    build = load("build-inputs.json")
    assert sha((D / "probe.rs").read_bytes()) == build["probe_source_sha256"]
    assert sha((D / "workspace.Cargo.toml").read_bytes()) == build["workspace_manifest_sha256"]
    assert build["metadata_resolve_exact_match"] and build["freeze_precedes_build"]
    assert load("freeze.json")["frozen_at_unix_ns"] < build["timestamp_ns"]
    source = inputs["source_commit"]
    assert source != inputs["historical_C1_source"]
    for path, digest in load("freeze.json")["fixture_bindings"].items():
        data = subprocess.check_output(["git", "show", f"{source}:{path}"], cwd=R)
        assert sha(data) == digest, path
    artifacts = {}
    for item in load("compressed-artifacts.json"):
        data = (D / item["file"]).read_bytes()
        assert sha(data) == item["sha256"]
        raw = gzip.decompress(data)
        assert sha(raw) == item["uncompressed_sha256"]
        assert len(raw) == item["uncompressed_bytes"]
        artifacts[item["file"]] = raw
    vectors = lines(artifacts["vectors.jsonl.gz"])
    assert sha(artifacts["vectors.jsonl.gz"]) == load("freeze.json")["vectors_sha256"]
    assert Counter(v["family"] for v in vectors) == load("freeze.json")["families"]
    assert len(vectors) == 20965
    assert sum(v["family"] == "finite-sweep" for v in vectors) == 4096
    assert sum(v["family"] == "B113" for v in vectors) == 113
    actual = lines(artifacts["outcomes-debug.jsonl.gz"])
    mismatches = compare(vectors, actual)
    expected_ids = [v["id"] for v in load("counterexample-inputs.json")]
    assert mismatches == expected_ids and len(mismatches) == 10
    for mode in ("debug", "release"):
        result = load(f"comparison-{mode}.json")
        assert [x["id"] for x in result["mismatches"]] == mismatches
    supplement = lines(artifacts["identity-supplement.jsonl.gz"])
    assert len(supplement) == 3
    assert (
        sha(artifacts["identity-supplement.jsonl.gz"])
        == load("identity-supplement-freeze.json")["sha256"]
    )
    assert not compare(supplement, lines(artifacts["identity-supplement-outcomes.jsonl.gz"]))
    # Synthetic comparison controls cannot count as native or authority evidence.
    for bad in ([], actual + actual[:1], [dict(actual[0], id="extra"), *actual[1:]]):
        try:
            compare(vectors, bad)
        except AssertionError:
            pass
        else:
            raise AssertionError("selection fault accepted")
    changed = [dict(actual[0], canonical="wrong canonical bytes"), *actual[1:]]
    assert len(compare(vectors, changed)) == 11
    assert compare(vectors, actual) == mismatches
    with tarfile.open(fileobj=io.BytesIO(artifacts["command-outputs.tar.gz"])) as tar:
        raw_outputs = {m.name: tar.extractfile(m).read() for m in tar if m.isfile()}
    formatted = raw_outputs["probe-rustfmt.stdout"]
    if formatted.startswith(b"/work/native/"):
        formatted = formatted.split(b"\n\n", 1)[1]
    assert formatted == (D / "probe.rs").read_bytes()
    locations = load("raw-output-locations.json")
    private = load("private-receipts.json")
    for command in load("commands.json"):
        name = command["name"]
        assert command["exit_code"] == (101 if name == "build-debug" else 0), name
        argv = command["argv"]
        if "run" in argv:
            assert argv[argv.index("--network") + 1] == "none"
            assert argv[argv.index("--pull") + 1] == "never"
            assert any("dst=/cargo-home,readonly" in a for a in argv)
        if "lock_sha256_after" in command:
            assert command["lock_sha256_after"] == inputs["candidate_lock_sha256"]
        for ext in ("stdout", "stderr"):
            name = f"{command['name']}.{ext}"
            location = locations[name]
            assert location["sha256"] == command[f"{ext}_sha256"]
            if "public_gzip" in location:
                raw = artifacts[location["public_gzip"]]
            elif "public_tar_member" in location:
                raw = raw_outputs[location["public_tar_member"]]
            else:
                assert location["sha256"] == private["files"]["receipts/" + name]["sha256"]
                continue
            assert sha(raw) == command[f"{ext}_sha256"]
    for mode in ("debug", "release"):
        test_log = raw_outputs[f"build-test-{mode}-package.stdout"]
        assert b"test result: ok. 6 passed; 0 failed" in test_log
    commands = {x["name"]: x for x in load("commands.json")}
    assert (
        commands["execute-debug"]["stdout_sha256"] == commands["execute-release"]["stdout_sha256"]
    )
    assert commands["execute-debug"]["stdin_sha256"] == build["vectors_sha256"]
    compilers = json.loads(artifacts["compiler-linker-commands.json.gz"])
    assert len(compilers) == 138
    for compiler in compilers:
        assert not any("target-cpu=native" in arg for arg in compiler["argv"])
        assert not any("no-vectorize" in arg for arg in compiler["argv"])
    software = load("release-software-path.json")
    assert software["compress256_reachable_by_direct_or_relocated_pointer_edges"]
    boundary = next(s for s in software["selected_symbols"] if s["symbol"] == "c2_sha256_boundary")
    assert boundary["simd_mnemonics"]["packuswb"] == 2
    compression = next(
        s for s in software["selected_symbols"] if s["symbol"] == "sha2::sha256::compress256"
    )
    assert compression["simd_register_instruction_count"] == 0
    preservation = load("preservation.json")
    assert preservation["before_inventory"]["sha256"] == preservation["after_inventory"]["sha256"]
    assert preservation["copied_cache_files_unchanged"] == 1719
    for item in preservation["human_semantic_postimages_verified"]:
        assert sha((R / item["path"]).read_bytes()) == item["sha256"]
    assert sha((R / "native/Cargo.lock").read_bytes()) == preservation["live_Cargo_lock_sha256"]
    for document in ("README.md", "next-decision.md"):
        for target in re.findall(r"\]\(([^)]+)\)", (D / document).read_text()):
            assert (D / target).is_file(), target
    for name, digest in load("inventory.json").items():
        assert sha((D / name).read_bytes()) == digest, name
    print(
        "PASS: approvals, accepted inputs, frozen source/vectors, actual 10 mismatches, "
        "supplement, raw outputs, controls, unit receipts, SIMD evidence, preservation and links. "
        "This verifies evidence integrity, not C2 parity/no-SIMD success."
    )


if __name__ == "__main__":
    main()
