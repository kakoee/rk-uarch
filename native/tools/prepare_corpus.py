"""Reproduce B's published finite input proposal exactly; no execution or adoption.

Only declared input/expectation snapshots are written. Historical peer fixtures and
all native result authority remain untouched. The hashes come from B's published
manifest, not an untracked private directory or an A runtime result.
"""

import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

from uarch_contract.hashing import canonical_json, sha256

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/reviews/U4-A-K2-construction-v1"
PEER = ROOT / "docs/reviews/U4-B-K2-construction-audit-v1"


def binding(path):
    return {"path": str(path.relative_to(ROOT)), "byte_hash": sha256(path.read_bytes())}


def main():
    freeze = json.loads((PEER / "first-use-freeze.json").read_bytes())
    for name, digest in freeze["helper_sha256"].items():
        assert hashlib.sha256((PEER / name).read_bytes()).hexdigest() == digest
    published = json.loads((PEER / "first-use-candidate.json").read_bytes())
    assert (
        hashlib.sha256((PEER / "first-use-candidate.json").read_bytes()).hexdigest()
        == freeze["candidate_sha256"]
    )
    spec = importlib.util.spec_from_file_location(
        "published_B_first_use", PEER / "prepare_first_use.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scratch = Path(tempfile.mkdtemp(prefix="u4-a-peer-corpus.")) / "fixtures"
    actual = module.prepare(ROOT, scratch)
    assert actual == published
    out = PACKAGE / "corpus"
    out.mkdir(exist_ok=True)
    for name, digest in published["files"].items():
        source = scratch / name
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
        target = out / name
        target.parent.mkdir(exist_ok=True)
        if target.exists():
            assert target.read_bytes() == source.read_bytes()
        else:
            shutil.copyfile(source, target)
    expectations = json.loads((out / "expectations.json").read_bytes())
    rows = [
        {
            "case_id": case,
            "bundle": binding(out / "bundles" / (case + ".json")),
            "profile": binding(out / "profile.json"),
            "clock_setup": expectations[case]["clock_setup"],
            "execution_outcome": entry["execution_expected"],
        }
        for case, entry in sorted(published["cases"].items())
    ]
    inventory = {
        "format": "uarch-k2-construction-corpus/1",
        "status": "pending-final-human-first-use",
        "registry": binding(out / "registry.json"),
        "cases": rows,
        "expectation_sources": [
            binding(PEER / "first-use-candidate.json"),
            binding(out / "expectations.json"),
            binding(PEER / "first_use_checks.py"),
        ],
        "private_wheel_inventory": published["private_wheel_inventory"],
        "peer_proposal_join": (
            "exact independently reproduced bytes; no native results or authority"
        ),
    }
    (out / "inventory.json").write_text(canonical_json(inventory))
    print("Reproduced and verified", len(rows), "B pending cases; no execution or adoption")


if __name__ == "__main__":
    main()
