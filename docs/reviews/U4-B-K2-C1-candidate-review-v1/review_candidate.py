"""Read-only C1 evidence review. Stdlib only; never invokes Cargo or project code."""

import argparse
import ast
import copy
import hashlib
import json
import tarfile
import tomllib
from pathlib import Path

PUBLICATION = "cd273b99c6b9d68ed2dd07d10f8ffad4bedbadb0"
SOURCE = "0718955cc0656e5bac4688d4696abbd547cb4186"
LOCK = "cbe9a580e0c6209abdb34be23965c2fe2f75b5970819d2021c943e2e02d939be"
PLAN = "4a5cbb16f5f249234d8ffc0a0e01476c89f4769a57ab96f422ff3c10093eebd5"
REGISTRY = "registry+https://github.com/rust-lang/crates.io-index"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def key(p):
    return p["name"], p["version"]


def tuples(packages):
    return [
        {k: p[k] for k in ("name", "version", "source", "checksum") if k in p} for p in packages
    ]


def retained_gate(root):
    path = root / "docs/reviews/U4-B-A-addendum-reconciliation-v1/test_records_and_plan.py"
    assert (
        sha(path.read_bytes()) == "a1ec3147bbead129ed7e7ab78fdb66299aad10a98cb2bc84ea82d156279d4d0e"
    )
    fn = next(
        n
        for n in ast.parse(path.read_bytes()).body
        if isinstance(n, ast.FunctionDef) and n.name == "entries_allowed"
    )
    namespace = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["entries_allowed"]


def graph(meta):
    ids = {p["id"]: key(p) for p in meta["packages"]}
    assert len(ids) == len(meta["packages"])
    result = {}
    for n in meta["resolve"]["nodes"]:
        ident = ids[n["id"]]
        assert ident not in result
        result[ident] = {
            "features": sorted(n["features"]),
            "edges": sorted(
                (d["name"], ids[d["pkg"]], json.dumps(d["dep_kinds"], sort_keys=True))
                for d in n["deps"]
            ),
        }
    assert set(result) == set(ids.values())
    return result


def check_graph(meta, baseline, plan, entries, linux=False):
    got, old = graph(meta), graph(baseline)
    expected_keys = {key(e) for e in entries} - ({("r-efi", "6.0.0")} if linux else set())
    assert set(got) == expected_keys
    for p in meta["packages"]:
        assert p["source"] == (None if p["name"] == "uarch-engine" else REGISTRY)
    for ident, before in old.items():
        expected = copy.deepcopy(before)
        if ident[0] == "serde_json":
            expected["features"] = sorted(before["features"] + ["arbitrary_precision"])
        if ident[0] == "uarch-engine":
            expected["edges"] = sorted(
                before["edges"]
                + [
                    (
                        "sha2",
                        ("sha2", "0.10.9"),
                        json.dumps([{"kind": None, "target": None}], sort_keys=True),
                    )
                ]
            )
        assert got[ident] == expected, ident
    expected_new_edges = {
        "sha2": {"cfg-if", "cpufeatures", "digest"},
        "digest": {"block-buffer", "crypto-common"},
        "block-buffer": {"generic-array"},
        "crypto-common": {"generic-array", "typenum"},
        "generic-array": {"typenum", "version_check"},
        "typenum": set(),
        "version_check": set(),
        "cpufeatures": set() if linux else {"libc"},
    }
    for entry in plan["only_permitted_additional_packages"]:
        name = entry["name"]
        ident = key(entry)
        feature_key = "cpufeatures@0.2.17" if name == "cpufeatures" else name
        assert got[ident]["features"] == sorted(plan["feature_expectations"][feature_key])
        assert {e[1][0] for e in got[ident]["edges"]} == expected_new_edges[name]
    # Full lock dependency identities and actual full graph must agree, including two cpufeatures.
    return got


def licence_texts(files):
    """MIT branch plus retained Unicode conjunct; notices remain separately recorded."""
    chosen = (
        "AUTHORS" if "AUTHORS" in files else "LICENSE-MIT" if "LICENSE-MIT" in files else "LICENSE"
    )
    text = " ".join(files[chosen].decode().split())
    assert "Permission is hereby granted, free of charge" in text
    assert "copyright notice and this permission notice shall be included" in text
    assert "WITHOUT WARRANTY" in text
    return chosen


def review(root, private):
    package = root / "docs/reviews/U4-A-K2-C1-precise-v1"
    plan_path = root / "docs/reviews/U4-A-K2-semantic-construction-v1/construction-plan.json"
    assert sha(plan_path.read_bytes()) == PLAN
    plan = read(plan_path)
    lock_names = [
        "starting.Cargo.lock",
        "input-rejected.Cargo.lock",
        "after-crypto-common.Cargo.lock",
        "after-typenum.Cargo.lock",
        "candidate.Cargo.lock",
    ]
    locks = {n: tomllib.loads((package / n).read_text())["package"] for n in lock_names}
    final = locks["candidate.Cargo.lock"]
    entries = tuples(final)
    retained_gate(root)(entries, plan)
    assert sha((package / "candidate.Cargo.lock").read_bytes()) == LOCK
    assert sha((package / "starting.Cargo.lock").read_bytes()) == plan["existing_lock_sha256"]
    assert tuples(locks["starting.Cargo.lock"]) == plan["existing_packages_must_retain"]
    assert (private / "source/native/Cargo.lock").read_bytes() == (
        package / "candidate.Cargo.lock"
    ).read_bytes()
    transitions = []
    for before, after, name, oldver, newver in [
        (
            "input-rejected.Cargo.lock",
            "after-crypto-common.Cargo.lock",
            "crypto-common",
            "0.1.7",
            "0.1.6",
        ),
        (
            "after-crypto-common.Cargo.lock",
            "after-typenum.Cargo.lock",
            "typenum",
            "1.20.1",
            "1.19.0",
        ),
    ]:
        a, b = locks[before], locks[after]
        assert [p for p in a if p["name"] != name] == [p for p in b if p["name"] != name]
        x = next(p for p in a if p["name"] == name)
        y = next(p for p in b if p["name"] == name)
        assert (x["version"], y["version"]) == (oldver, newver)
        assert y == next(p for p in final if p["name"] == name)
        transitions.append({"before": before, "after": after, "removed": x, "added": y})
    assert locks["after-typenum.Cargo.lock"] == final
    manifest = tomllib.loads((package / "scratch.Cargo.toml").read_text())
    assert (private / "source/native/crates/uarch-engine/Cargo.toml").read_bytes() == (
        package / "scratch.Cargo.toml"
    ).read_bytes()
    assert "features" not in manifest
    for group in ("dependencies", "dev-dependencies"):
        expected = {
            name: {
                "version": e["version"],
                "default-features": e["default_features"],
                "features": e["features"],
            }
            for name, e in plan["direct_dependencies"].items()
            if ("dev-dependencies" if e.get("kind") == "dev" else "dependencies") == group
        }
        assert manifest[group] == expected
    graphs = {}
    for view in ("full", "linux"):
        meta = read(package / f"metadata-{view}.stdout")
        baseline = read(
            root / f"docs/reviews/U4-K1-installed-verification-v1/cargo-metadata.{view}.json"
        )
        g = check_graph(meta, baseline, plan, entries, linux=view == "linux")
        root_meta = next(p for p in meta["packages"] if p["name"] == "uarch-engine")
        for dep in root_meta["dependencies"]:
            e = plan["direct_dependencies"][dep["name"]]
            assert (dep["req"], dep["features"], dep["uses_default_features"], dep["kind"]) == (
                e["version"],
                e["features"],
                e["default_features"],
                e.get("kind"),
            )
        if view == "full":
            for p in final:
                deps = set()
                for dep in p.get("dependencies", []):
                    parts = dep.split()
                    matches = [
                        key(e)
                        for e in final
                        if e["name"] == parts[0] and (len(parts) == 1 or e["version"] == parts[1])
                    ]
                    assert len(matches) == 1
                    deps.add(matches[0])
                assert deps == {e[1] for e in g[key(p)]["edges"]}
        graphs[view] = {
            "nodes": len(g),
            "edges": sum(len(v["edges"]) for v in g.values()),
            "metadata_sha256": sha((package / f"metadata-{view}.stdout").read_bytes()),
            "baseline_nodes_compared": len(graph(baseline)),
            "normalized_graph_sha256": sha(
                json.dumps(
                    [{"name": k[0], "version": k[1], **v} for k, v in sorted(g.items())],
                    sort_keys=True,
                ).encode()
            ),
            "new_nodes": [
                {"name": k[0], "version": k[1], **v}
                for k, v in sorted(g.items())
                if k not in graph(baseline)
            ],
            "old_deltas": ["uarch-engine -> sha2@0.10.9", "serde_json + arbitrary_precision"],
        }
    full = read(package / "metadata-full.stdout")
    meta_by_key = {key(p): p for p in full["packages"]}
    archives = read(package / "archives.json")
    assert {key(a) for a in archives} == {key(p) for p in final if "checksum" in p}
    audit = []
    for a in archives:
        archive = private / "cargo-home" / a["path"]
        expected = next(p["checksum"] for p in final if key(p) == key(a))
        assert sha(archive.read_bytes()) == expected == a["sha256"]
        prefix = f"{a['name']}-{a['version']}"
        files = {}
        members = 0
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                assert not member.issym() and not member.islnk()
                if not member.isfile():
                    continue
                rel = Path(member.name).relative_to(prefix)
                assert ".." not in rel.parts
                data = tar.extractfile(member).read()
                actual = (
                    private
                    / "cargo-home/registry/src/index.crates.io-1949cf8c6b5b557f"
                    / prefix
                    / rel
                )
                assert data == actual.read_bytes(), str(actual)
                members += 1
                if any(
                    w in rel.name.upper()
                    for w in ("LICENSE", "LICENCE", "COPYING", "COPYRIGHT", "NOTICE", "AUTHORS")
                ):
                    files[str(rel)] = data
                if str(rel) in ("Cargo.toml", "README.md"):
                    files[str(rel)] = data
        declared = tomllib.loads(files["Cargo.toml"].decode())["package"]["license"]
        assert declared == meta_by_key[key(a)]["license"]
        chosen = licence_texts(files)
        if a["name"] == "r-efi":
            assert "See AUTHORS file for details" in files["README.md"].decode()
            assert (
                sha(files["AUTHORS"])
                == "d027e91dbc9cdbb2f1190068e498bd6b61cff022b6a032b191021ba658d96111"
            )
        if a["name"] == "unicode-ident":
            assert "UNICODE LICENSE V3" in files["LICENSE-UNICODE"].decode()
        audit.append(
            {
                "name": a["name"],
                "version": a["version"],
                "archive_sha256": expected,
                "members_verified": members,
                "expression": declared,
                "selected": "MIT AND Unicode-3.0" if a["name"] == "unicode-ident" else "MIT",
                "selected_file": chosen,
                "notices": {
                    n: sha(b)
                    for n, b in sorted(files.items())
                    if n != "Cargo.toml" and (n != "README.md" or a["name"] == "r-efi")
                },
            }
        )
    receipts = read(package / "private-receipts.json")["files"]
    for name, record in receipts.items():
        data = (private / name).read_bytes()
        assert sha(data) == record["sha256"] and len(data) == record["bytes"]
    cache = read(package / "cache-inventory.json")["files"]
    for name, record in cache.items():
        data = (private / "cargo-home" / name).read_bytes()
        assert sha(data) == record["sha256"] and len(data) == record["bytes"]
    net = read(package / "network.json")
    assert len(net["requests"]) == 35 and net["new_index_requests"] == 0
    assert {r["url"] for r in net["requests"]} == {
        f"https://static.crates.io/crates/{a['name']}/{a['version']}/download" for a in archives
    }
    assert all(r["http_status"] == 200 for r in net["requests"])
    return {
        "publication": PUBLICATION,
        "experiment_source": SOURCE,
        "lock_sha256": LOCK,
        "plan_sha256": PLAN,
        "unchanged_predicate_passed": True,
        "transitions": transitions,
        "graphs": graphs,
        "archives": audit,
        "private_receipts_hashed": len(receipts),
        "cache_files_hashed": len(cache),
        "network_evidence": "A recorded 35 exact archive URLs; B did not repeat online access",
        "project_imports": [],
        "dependency_execution": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject-root", type=Path, required=True)
    parser.add_argument("--private-inputs", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(review(args.subject_root.resolve(), args.private_inputs.resolve()), indent=2))
