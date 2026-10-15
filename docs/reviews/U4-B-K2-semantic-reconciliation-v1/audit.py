"""Audit the actual private source, not proposed native implementation or authority."""

import hashlib
import json
import sys
from pathlib import Path


def main(root, output):
    root = root.resolve()
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
        if name.split(".")[0] in {"rkuarch", "uarch_contract"}:
            path = Path(module.__file__).resolve()
            assert path.is_relative_to(root), (name, path)
            origins[name] = str(path.relative_to(root))
    static = closure(root, "rkuarch.workload.mapped")
    assert set(static) == set(origins.values())
    old = json.loads((root / "docs/reviews/U4-B-K2-first-use-v1/peer-audit.json").read_bytes())
    assert static == old["static_local_loader_closure"]
    saved = root / "contract/fixtures/mapped/kernel-job.json"
    raw = json.loads(saved.read_bytes())
    # Synthetic unit anchors, captured before load; these authorize no execution.
    anchors = dict(
        trusted_registry_hash=raw["registry"]["registry_hash"],
        trusted_profile_hash=raw["profile"]["profile_hash"],
        expected_engine=NativeEngineIdentity.model_validate(raw["engine"]),
    )
    reads = []

    def record(event, args):
        if event == "open" and isinstance(args[0], str):
            reads.append(str(Path(args[0]).resolve()))

    sys.addaudithook(record)
    job = load_fixed_delay_job(saved, **anchors)
    load_reads = list(reads)
    assert load_reads == [str(saved)]
    from scripts import u2_support, vendor_rk

    selected = u2_support.inventory(root=root)
    adopted = root / "contract/vendor" / ("rk-sim@" + vendor_rk.PIN)
    vendor_rk.check_manifest(adopted, vendor_rk.PIN)
    vendor_rk.check_snapshot_inputs(adopted)
    vendor_rk.check_generator(adopted, current=True)
    selected_hash = content_hash(selected)
    assert selected_hash == old["selected_hash"]
    for name in ("contract/uarch_contract/mapped.py", "src/rkuarch/workload/mapped.py"):
        assert name not in selected
    old_fixture = root / "docs/reviews/U4-B-K2-first-use-v1/fixtures/identity.json"
    assert hashlib.sha256(old_fixture.read_bytes()).hexdigest() == (
        "2102824b0e998a674e7de9f0e55397c2e51b7685057e5c7c90438bd0cdf73d97"
    )
    receipt = dict(
        source_commit="418d6972f6bc367d648b811227b0e97829a8b292",
        python=sys.version,
        authority="synthetic host check only",
        runtime_origins=origins,
        loader_closure_count=len(static),
        loader_closure_hash=content_hash(static),
        old_loader_map_identical=True,
        load_reads=[str(saved.relative_to(root))],
        implicit_authority_reads=[],
        saved_job_hash=job.job_hash,
        selected_count=len(selected),
        selected_hash=selected_hash,
        selected_quota=None,
        strict_currentness="passed",
        lifecycle_required_for_actual_docs_delta=False,
        proposed_native_build_reads="not implemented; dynamic audit pending",
    )
    output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "runtime_origins"}, indent=2))


if __name__ == "__main__":
    main(*map(Path, sys.argv[1:]))
