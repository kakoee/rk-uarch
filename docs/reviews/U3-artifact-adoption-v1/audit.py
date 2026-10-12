"""Read-only audit of the human-generated U3 candidate; no adoption or oracle calls."""

import hashlib
import json
import runpy
from collections import Counter
from pathlib import Path


def main():
    root = Path("/home/jjaff/AI-infra-simulation/rk-uarch")
    proposal = root / "docs/reviews/U3-combined-freeze-proposal-v1"
    p = runpy.run_path(str(proposal / "preflight.py"))
    current = json.loads(
        json.dumps(
            p["preflight"](
                proposal_commit="70adf0988b218aed895fcf5d2d8b039ca2ba0566", stage="during"
            )
        )
    )
    a = p["A"]
    out = p["OUTPUT"]
    source = a / "tables/U3-rope-generation-v1/candidate"
    from scripts import u2_inputs as ui
    from scripts import vendor_rk as v
    from tests.u2_refresh import audit_candidate

    report = audit_candidate(source)
    assert report["adopted"] is False and report["rows"] == 1008
    manifest = hashlib.sha256((source / "MANIFEST.json").read_bytes()).hexdigest()
    assert manifest == "1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a"
    diff = ui.compare_snapshots(ui.ADOPTED, source)
    assert [f["path"] for f in diff["files"]] == [
        "MANIFEST.json",
        "u2-inputs/SHA256SUMS",
        "u2-inputs/support-files.json",
    ]
    rows = json.loads((source / "parity/fixtures.json").read_bytes())
    refusals = json.loads((source / "parity/refusals.json").read_bytes())
    assert len(rows) == len({r["id"] for r in rows}) == 1008
    phases = Counter(r["query"]["phase"] for r in rows)
    assert phases == {"decode": 504, "prefill": 504}
    assert all("vector_ops" not in r["counts"] for r in rows)
    assert all(
        r["counts"]["memory_write_bytes"] is None for r in rows if r["query"]["phase"] == "decode"
    )
    assert len(refusals) == 4
    assert (source / "parity/fixtures.json").read_bytes() == (
        ui.ADOPTED / "parity/fixtures.json"
    ).read_bytes()
    assert (source / "parity/refusals.json").read_bytes() == (
        ui.ADOPTED / "parity/refusals.json"
    ).read_bytes()
    logs = out / "receipts"
    receipt = json.loads((logs / "generation-receipt.json").read_bytes())
    assert receipt["candidate_manifest_sha256"] == manifest and receipt["runs"] == 2
    for key in ("source_commit", "source_tree", "input_manifest_sha256"):
        assert receipt[key] == current[key]
    assert receipt["proposal_commit"] == "70adf0988b218aed895fcf5d2d8b039ca2ba0566"
    assert receipt["candidate"] == str(source)
    preflights = {}
    for name in (
        "preflight-before.json",
        "preflight-run-1.json",
        "postflight-run-1.json",
        "preflight-run-2.json",
        "postflight-run-2.json",
    ):
        data = json.loads((logs / name).read_bytes())
        expected = dict(current, output_absent=name == "preflight-before.json")
        assert data == expected, (name, data, expected)
        preflights[name] = hashlib.sha256((logs / name).read_bytes()).hexdigest()
    commands = []
    for i, status in ((1, "created"), (2, "verified-identical")):
        r = json.loads((logs / f"run-{i}.json").read_bytes())
        assert (
            r["exit_code"] == 0
            and r["expected_status"] == status
            and r["proposal_commit"] == receipt["proposal_commit"]
        )
        assert (logs / f"run-{i}.stdout").read_text() == f"{status}: 48 files at {source}\n"
        assert not (logs / f"run-{i}.stderr").read_bytes()
        commands.append(r["command"])
    assert commands[0] == commands[1]
    assert commands[0][:4] == [str(a / ".venv/bin/python"), "-I", "-B", "-c"]
    assert commands[0][5:] == [
        "--sha",
        v.PIN,
        "--rk",
        p["SPEC"]["upstream_root"],
        "--inputs",
        str(out / "inputs"),
        "--input-manifest-sha256",
        current["input_manifest_sha256"],
        "--output-root",
        str(source),
    ]
    assert v.check_generator(source)["environment"] == current["oracle_environment"]
    payloads = {f.relative_to(source).as_posix() for f in source.rglob("*") if f.is_file()}
    assert len(payloads) == 48
    result = dict(
        status="candidate audited; NOT adopted",
        proposal_commit=receipt["proposal_commit"],
        source_commit=current["source_commit"],
        source_tree=current["source_tree"],
        candidate=str(source),
        candidate_manifest_sha256=manifest,
        input_manifest_sha256=current["input_manifest_sha256"],
        inventory_files=len(payloads),
        rows=len(rows),
        phases=dict(phases),
        real_refusals=len(refusals),
        fixtures_and_refusals_byte_identical=True,
        strict_candidate_audit=report,
        semantic_comparison=diff,
        receipts_verified=True,
        preflight_receipt_hashes=preflights,
        executed_oracle=False,
        current_preflight=current,
    )
    (root / "docs/reviews/U3-artifact-adoption-v1/audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "status",
                    "candidate_manifest_sha256",
                    "rows",
                    "real_refusals",
                    "inventory_files",
                    "fixtures_and_refusals_byte_identical",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
