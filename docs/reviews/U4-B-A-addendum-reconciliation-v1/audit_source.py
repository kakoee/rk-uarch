"""Audit actual isolated loader/import/data/support reads, with no assumed file quota."""

import hashlib
import json
import sys
from pathlib import Path


def main():
    root = Path(sys.argv[1]).resolve()
    assert root.is_relative_to(Path("/tmp")) and not (root / ".git").exists()
    sys.path[:0] = [
        str(root),
        str(root / "src"),
        str(root / "contract"),
        str(root / "docs/reviews/U4-B-K2-first-use-v1"),
    ]
    from peer_audit import closure
    from uarch_contract.hashing import content_hash
    from uarch_contract.mapped import NativeEngineIdentity

    from rkuarch.workload.mapped import load_fixed_delay_job

    origins = {}
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] in ("rkuarch", "uarch_contract"):
            path = Path(module.__file__).resolve()
            assert path.is_relative_to(root), (name, path)
            origins[name] = str(path.relative_to(root))
    static = closure(root, "rkuarch.workload.mapped")
    assert set(static) == set(origins.values())
    prior = json.loads(
        (root / "docs/reviews/U4-A-K2-semantic-construction-v1/read-inventory.json").read_bytes()
    )
    old = prior["maps"]["static_local_import_closure"]
    assert set(static) == set(old)
    changed = {k: dict(before=old[k], after=static[k]) for k in old if old[k] != static[k]}
    assert set(changed) <= {"contract/uarch_contract/mapped.py"}
    saved = root / "contract/fixtures/mapped/kernel-job.json"
    raw = json.loads(saved.read_bytes())
    anchors = dict(
        trusted_registry_hash=raw["registry"]["registry_hash"],
        trusted_profile_hash=raw["profile"]["profile_hash"],
        expected_engine=NativeEngineIdentity.model_validate(raw["engine"]),
    )
    reads = []

    def audit(event, args):
        if event == "open" and isinstance(args[0], str):
            reads.append(str(Path(args[0]).resolve()))

    sys.addaudithook(audit)
    load_fixed_delay_job(saved, **anchors)
    assert reads == [str(saved)]
    from scripts import u2_support, vendor_rk

    support = u2_support.inventory(root=root)
    assert support == prior["maps"]["selected_generation_support"]
    adopted = root / "contract/vendor" / ("rk-sim@" + vendor_rk.PIN)
    vendor_rk.check_manifest(adopted, vendor_rk.PIN)
    vendor_rk.check_snapshot_inputs(adopted)
    vendor_rk.check_generator(adopted, current=True)
    result = dict(
        subject="1a52fa82f3aabc3eca5de4fa5597295a0fa04e27",
        export=str(root),
        mapped_sha256=hashlib.sha256(
            (root / "contract/uarch_contract/mapped.py").read_bytes()
        ).hexdigest(),
        origins=origins,
        loader_count=len(static),
        loader_hash=content_hash(static),
        loader_delta=changed,
        load_reads=[str(saved.relative_to(root))],
        implicit_authority_reads=[],
        authority="synthetic test arguments only",
        support_count=len(support),
        support_hash=content_hash(support),
        support_quota=None,
        currentness="passed",
        lifecycle_required_for_tested_delta=False,
        future_resolver_reads="unimplemented and not observed",
    )
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2) + "\n")
    print("Private origins, explicit reads, selected support and strict currentness verified.")


if __name__ == "__main__":
    main()
