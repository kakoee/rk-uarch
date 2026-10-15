"""Audit saved human generation without requiring its expired temporary oracle venv."""

import hashlib
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert sys.flags.isolated and sys.dont_write_bytecode
    p = runpy.run_path(str(ROOT / "docs/reviews/U4-M-policy-freeze-generation-v1/preflight.py"))
    spec = p["SPEC"]
    p["check_package"]("ccf19227d06a3c520f2599729b5db31297e436ad")
    p["source_guard"]()
    u, policy, v = p["load_source"]()

    def forbidden(*args, **kwargs):
        raise AssertionError("producer/oracle forbidden")

    u.prepare_inputs = forbidden
    v.run_oracle = v.collect_snapshot = v.publish_snapshot = forbidden
    from tests import u2_refresh

    assert Path(u2_refresh.__file__).resolve().is_relative_to(p["SOURCE"])
    old = json.loads(
        (ROOT / "docs/reviews/U4-M-policy-artifact-adoption-v1/audit.json").read_text()
    )
    candidate = p["OUTPUT"] / "candidate"
    assert sha(candidate / "MANIFEST.json") == old["candidate_manifest_sha256"]
    assert sha(u.ADOPTED / "MANIFEST.json") == old["old_manifest_sha256"]
    receipts = p["OUTPUT"] / "receipts"
    actual = {
        q.relative_to(receipts).as_posix(): sha(q) for q in receipts.rglob("*") if q.is_file()
    }
    assert actual == old["receipt_hashes"]
    assert policy.inventory() == spec["inventory"] and policy.POLICY == spec["policy"]
    assert sha(Path(v.__file__)) == spec["generator_sha256"]
    assert hashlib.sha256(v.ORACLE_PROGRAM.encode()).hexdigest() == spec["oracle_program_sha256"]
    inputs = u.load_inputs(Path(spec["inputs"]), spec["input_manifest_sha256"])
    assert inputs.manifest_sha256 == spec["input_manifest_sha256"]
    assert sha(Path(spec["inputs"]).parent / "receipt.json") == spec["input_receipt_sha256"]
    assert sha(p["SOURCE"] / "uv.lock") == spec["lock_sha256"]
    v.check_manifest(u.ADOPTED)
    result = u2_refresh.audit_candidate(candidate)
    assert result["rows"] == 1008 and result["adopted"] is False
    generator = v.check_generator(candidate, current=True)
    assert generator["environment"] == spec["oracle_metadata"]
    v.validate_environment_metadata(generator["environment"], (candidate / "uv.lock").read_bytes())
    assert sha(candidate / "uv.lock") == spec["oracle_metadata"]["uv_lock_sha256"]
    for name in ("parity/fixtures.json", "parity/refusals.json"):
        assert (candidate / name).read_bytes() == (u.ADOPTED / name).read_bytes()
    for name in old["changed"] + old["added"]:
        assert sha(candidate / name) == old["file_delta"][name]["after"]
    input_files = {
        q.relative_to(Path(spec["inputs"])).as_posix(): sha(q)
        for q in Path(spec["inputs"]).rglob("*")
        if q.is_file()
    }
    copied = {
        q.relative_to(candidate / "u2-inputs").as_posix(): sha(q)
        for q in (candidate / "u2-inputs").rglob("*")
        if q.is_file()
    }
    assert copied == input_files
    p["source_guard"]()
    print(
        json.dumps(
            {
                "status": (
                    "saved candidate, source, inputs and generation receipts verified; NOT adopted"
                ),
                "candidate_manifest_sha256": old["candidate_manifest_sha256"],
                "source_commit": spec["source_commit"],
                "strict_candidate_audit": result,
                "generation_receipts_unchanged": True,
                "nominal_rows_identical": 1008,
                "refusals_identical": 4,
                "frozen_source_clean": True,
                "oracle_environment_currently_present": Path(spec["oracle_environment"]).exists(),
                "oracle_environment_validation": (
                    "recorded generation metadata and candidate lock verified; "
                    "temporary live oracle environment not required or recreated for "
                    "saved-artifact adoption"
                ),
                "production_or_generation_executed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
