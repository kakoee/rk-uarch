"""Offline verification of the actual C1 refusal; never resolves, fetches or builds."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
SOURCE = "0718955cc0656e5bac4688d4696abbd547cb4186"
PLAN = "docs/reviews/U4-A-K2-semantic-construction-v1/construction-plan.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(package):
    return {
        key: package[key] for key in ("name", "version", "source", "checksum") if key in package
    }


def main():
    plan_bytes = subprocess.check_output(["git", "show", SOURCE + ":" + PLAN], cwd=REPO)
    assert digest(plan_bytes) == "4a5cbb16f5f249234d8ffc0a0e01476c89f4769a57ab96f422ff3c10093eebd5"
    plan = json.loads(plan_bytes)
    original = (PACKAGE / "starting.Cargo.lock").read_bytes()
    candidate = (PACKAGE / "after-root-update.Cargo.lock").read_bytes()
    assert original == subprocess.check_output(
        ["git", "show", SOURCE + ":native/Cargo.lock"], cwd=REPO
    )
    assert digest(original) == plan["existing_lock_sha256"]
    assert digest(candidate) == "d2b744a9045a124c5edb097c821d2b69e9f0dd5e734554542fdfee6b5a4c6211"
    old = [identity(p) for p in tomllib.loads(original.decode())["package"]]
    new = [identity(p) for p in tomllib.loads(candidate.decode())["package"]]
    assert len(old) == 28 and all(p in new for p in old)
    assert len(new) == len({(p["name"], p["version"]) for p in new}) == 36
    allowed = [
        {k: p[k] for k in ("name", "version", "checksum")}
        | {"source": "registry+https://github.com/rust-lang/crates.io-index"}
        for p in plan["only_permitted_additional_packages"]
    ]
    drift = [p for p in new if p not in old and p not in allowed]
    assert {(p["name"], p["version"]) for p in drift} == {
        ("crypto-common", "0.1.7"),
        ("typenum", "1.20.1"),
    }
    assert drift == json.loads((PACKAGE / "lock-gate.json").read_text())["unpermitted_additions"]
    preflight = json.loads((PACKAGE / "preflight.json").read_text())
    assert preflight["image_inspect_passed"] and preflight["tools_passed"]
    assert all(row["exit_code"] == 0 for row in preflight["commands"])
    assert preflight["source_commit"] == SOURCE and not preflight["copied_cache"]
    for name in ("rustc", "cargo-deny", "rustfmt", "clippy"):
        assert (PACKAGE / (name + ".stdout")).read_bytes() == (
            REPO / "docs/reviews/U4-A-toolchain-v1/version-receipts" / (name + ".txt")
        ).read_bytes()
    # Cargo's accepted receipt is short; the actual full verbose output is also retained.
    assert (PACKAGE / "cargo.stdout").read_text().splitlines()[0] == (
        REPO / "docs/reviews/U4-A-toolchain-v1/version-receipts/cargo.txt"
    ).read_text().strip()
    root = Path(preflight["scratch"])
    if root.exists():
        source = root / "source"
        sys.path[:0] = [
            str(source),
            str(source / "contract"),
            str(source / "docs/reviews/U4-A-K2-semantic-construction-v1"),
        ]
        subject = source / "docs/reviews/U4-B-A-addendum-reconciliation-v1/test_records_and_plan.py"
        spec = importlib.util.spec_from_file_location("retained_b_c1_predicate", subject)
        assert spec is not None and spec.loader is not None
        peer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(peer)
        peer.entries_allowed(old + allowed, plan)  # synthetic predicate control only, not a lock
        try:
            peer.entries_allowed(new, plan)  # actual pinned-Cargo output
        except AssertionError:
            peer_refusal = True
        else:
            raise AssertionError("B's retained predicate must refuse the actual lock")
        peer.entries_allowed(old + allowed, plan)
        cache = json.loads((PACKAGE / "cache-inventory.json").read_text())
        for name, record in cache["files"].items():
            assert digest((root / "cargo-home" / name).read_bytes()) == record["sha256"]
        network = json.loads((PACKAGE / "network.json").read_text())
        assert digest(Path(network["source_trace"]).read_bytes()) == network["source_trace_sha256"]
    else:
        peer_refusal = "not rerun: private scratch absent"
    network = json.loads((PACKAGE / "network.json").read_text())
    assert len(network["requests"]) == 35
    assert all(
        r["url"].startswith("https://index.crates.io/") and r["http_status"] == 200
        for r in network["requests"]
    )
    assert network["archive_requests"] == 0
    candidate_paths = json.loads(
        (REPO / "docs/reviews/U4-K2-joint-candidate-v1/candidate.json").read_text()
    )
    for row in candidate_paths["paths"]:
        path = REPO / row["path"]
        if row["before_sha256"] is None:
            assert not path.exists()
        else:
            assert digest(path.read_bytes()) == row["before_sha256"]
    assert (REPO / "native/Cargo.lock").read_bytes() == original
    for path in PACKAGE.glob("*.json"):
        json.loads(path.read_text())
    print(
        json.dumps(
            dict(
                actual_candidate_refused=True,
                existing_identities_preserved=28,
                exact_unpermitted_additions=drift,
                peer_predicate_refusal=peer_refusal,
                network_index_gets=35,
                archives=0,
                semantic_candidate_uninstalled=True,
                live_lock_unchanged=True,
                dependency_operations=False,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
