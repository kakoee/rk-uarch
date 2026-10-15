"""Read-only C1 receipt checks; no Cargo, downloads, builds or authority creation."""

import ast
import copy
import hashlib
import json
import re
import subprocess
import tomllib
from pathlib import Path

D = Path(__file__).resolve().parent
R = D.parents[2]
SOURCE = "0718955cc0656e5bac4688d4696abbd547cb4186"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    return json.loads((D / name).read_bytes())


def exported(path):
    return subprocess.check_output(["git", "show", f"{SOURCE}:{path}"], cwd=R)


def tuples(name):
    return [
        {k: p[k] for k in ("name", "version", "source", "checksum") if k in p}
        for p in tomllib.loads((D / name).read_text())["package"]
    ]


def main():
    plan_bytes = exported("docs/reviews/U4-A-K2-semantic-construction-v1/construction-plan.json")
    assert digest(plan_bytes) == read("status.json")["construction_plan_sha256"]
    plan = json.loads(plan_bytes)
    assert exported("native/Cargo.lock") == (D / "starting.Cargo.lock").read_bytes()
    assert digest((D / "starting.Cargo.lock").read_bytes()) == plan["existing_lock_sha256"]
    original = R / "docs/reviews/U4-A-K2-C1-resolution-v1"
    assert (D / "input-rejected.Cargo.lock").read_bytes() == (
        original / "after-root-update.Cargo.lock"
    ).read_bytes()
    assert (D / "scratch-manifest.diff").read_bytes() == (
        original / "scratch-manifest.diff"
    ).read_bytes()
    manifest = tomllib.loads((D / "scratch.Cargo.toml").read_text())
    for name, expected in plan["direct_dependencies"].items():
        group = "dev-dependencies" if expected.get("kind") == "dev" else "dependencies"
        actual = manifest[group][name]
        assert actual["version"] == expected["version"]
        assert actual["default-features"] == expected["default_features"]
        assert sorted(actual["features"]) == sorted(expected["features"])
    assert "features" not in manifest
    predicate_path = "docs/reviews/U4-B-A-addendum-reconciliation-v1/test_records_and_plan.py"
    tree = ast.parse(exported(predicate_path))
    fn = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "entries_allowed"
    )
    namespace = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), predicate_path, "exec"), namespace)
    gate = namespace["entries_allowed"]
    candidate = tuples("candidate.Cargo.lock")
    gate(candidate, plan)
    assert (
        digest((D / "candidate.Cargo.lock").read_bytes())
        == read("status.json")["candidate_lock_sha256"]
    )
    first = tuples("after-crypto-common.Cargo.lock")
    rejected = tuples("input-rejected.Cargo.lock")
    target = next(p for p in rejected if p["name"] == "typenum")
    expected = [target if p["name"] == "typenum" else p for p in candidate]
    assert first == expected
    assert tuples("after-typenum.Cargo.lock") == candidate
    # Negative controls remain in memory and never become Cargo inputs.
    controls = [rejected, first, candidate[1:], candidate + [candidate[0]]]
    for field, value in [
        ("checksum", "0" * 64),
        ("source", "git+https://invalid.invalid"),
        ("version", "99.0.0"),
    ]:
        bad = copy.deepcopy(candidate)
        bad[0][field] = value
        controls.append(bad)
    for bad in controls:
        try:
            gate(bad, plan)
        except AssertionError:
            pass
        else:
            raise AssertionError("whole-lock predicate accepted a negative control")
    gate(candidate, plan)
    features = read("features.full.json")
    assert features["passed"] and all(n["matches"] for n in features["nodes"])
    expected_features = {(p["name"], p["version"]): p["expected"] for p in features["nodes"]}
    for view, count in [("full", 36), ("linux", 35)]:
        meta = read(f"metadata-{view}.stdout")
        packages = {p["id"]: p for p in meta["packages"]}
        assert len(meta["resolve"]["nodes"]) == count
        for node in meta["resolve"]["nodes"]:
            p = packages[node["id"]]
            assert sorted(node["features"]) == expected_features[(p["name"], p["version"])]
            assert any(
                c["name"] == p["name"]
                and c["version"] == p["version"]
                and c.get("source") == p["source"]
                for c in candidate
            )
    archives = read("archives.json")
    registry = {(p["name"], p["version"]): p for p in candidate if "checksum" in p}
    assert len(archives) == len(registry) == 35
    cache = read("cache-inventory.json")["files"]
    for archive in archives:
        key = (archive["name"], archive["version"])
        assert archive["sha256"] == registry[key]["checksum"] == cache[archive["path"]]["sha256"]
    commands = read("commands.json")
    private = read("private-receipts.json")
    for command in commands:
        assert command["exit_code"] == 0
        for ext in ("stdout", "stderr"):
            name = f"{command['name']}.{ext}"
            actual = (
                digest((D / name).read_bytes())
                if (D / name).exists()
                else private["files"]["receipts/" + name]["sha256"]
            )
            assert actual == command[f"{ext}_sha256"]
        if command["name"] not in {
            "source-export",
            "source-extract",
            "manifest-apply",
            "image-inspect",
        }:
            argv = command["argv"]
            assert argv[argv.index("--pull") + 1] == "never"
            assert argv[argv.index("--network") + 1] == (
                "bridge" if command["name"] == "metadata-full" else "none"
            )
        assert command.get("lock_unchanged", True)
    for view in ("full", "linux"):
        repeat = next(c for c in commands if c["name"] == f"metadata-{view}-repeat")
        assert repeat["stdout_sha256"] == digest((D / f"metadata-{view}.stdout").read_bytes())
    network = read("network.json")
    assert network["new_index_requests"] == 0 and len(network["requests"]) == 35
    urls = {
        f"https://static.crates.io/crates/{name}/{version}/download" for name, version in registry
    }
    assert {r["url"] for r in network["requests"]} == urls
    assert all(r["http_status"] == 200 for r in network["requests"])
    assert (D / "deny-check.stdout").read_text().strip() == "bans ok, licenses ok, sources ok"
    preservation = read("preservation.json")
    assert preservation["original_bytes_sizes_mtimes_unchanged"]
    assert (
        preservation["old_private_before"]["sha256"] == preservation["old_private_after"]["sha256"]
    )
    assert set(preservation["target_files"]) == {".rustc_info.json"}
    for p in preservation["human_postimages"]:
        assert digest((R / p["path"]).read_bytes()) == p["sha256"]
    old_tree = (
        subprocess.check_output(
            ["git", "rev-parse", "HEAD:docs/reviews/U4-A-K2-C1-resolution-v1"], cwd=R
        )
        .decode()
        .strip()
    )
    assert old_tree == preservation["old_evidence_tree"]
    for target in re.findall(r"\]\(([^)]+)\)", (D / "README.md").read_text()):
        assert (D / target).is_file(), target
    inventory = read("inventory.json")
    for name, expected_hash in inventory.items():
        assert digest((D / name).read_bytes()) == expected_hash, name
    print(
        f"PASS: actual transitions and full lock; {len(controls)} in-memory refusals; "
        "graphs/features;35 archives;24 command receipts; offline repeats; "
        "preservation; links/inventory"
    )


if __name__ == "__main__":
    main()
