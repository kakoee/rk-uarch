"""Check candidate plan against retained metadata/lock; do not resolve/download crates."""

import hashlib
import json
import tomllib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]


def test_candidate_constraints_are_exact_retained_inputs():
    plan = json.loads((PACKAGE / "construction-plan.json").read_text())
    lock_bytes = (REPO / "native/Cargo.lock").read_bytes()
    assert hashlib.sha256(lock_bytes).hexdigest() == plan["existing_lock_sha256"]
    lock = tomllib.loads(lock_bytes.decode())
    external = [
        {k: p[k] for k in ("name", "version", "source", "checksum") if k in p}
        for p in lock["package"]
    ]
    assert external == plan["existing_packages_must_retain"]
    metadata_bytes = (REPO / plan["candidate_metadata_file"]).read_bytes()
    assert hashlib.sha256(metadata_bytes).hexdigest() == plan["candidate_metadata_sha256"]
    metadata = json.loads(metadata_bytes)
    assert len(plan["only_permitted_additional_packages"]) == 8
    for candidate in plan["only_permitted_additional_packages"]:
        matching = [
            c
            for c in metadata["crates"]
            if c["name"] == candidate["name"] and c["version"] == candidate["version"]
        ]
        assert len(matching) == 1
        assert all(candidate[k] == matching[0][k] for k in ("checksum", "license", "source"))
    assert plan["direct_dependencies"]["sha2"] == dict(
        version="=0.10.9", default_features=False, features=["std", "force-soft"]
    )
    assert plan["direct_dependencies"]["serde_json"]["features"] == [
        "std",
        "float_roundtrip",
        "arbitrary_precision",
    ]
    assert plan["new_git_dependencies"] is False
