"""Freeze prospective input selection in a private exact candidate. No engine authority."""

from __future__ import annotations

import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path

from uarch_contract.hashing import content_hash
from uarch_contract.mapped import MappedBundle, validate_resources

from validation.component.corpus import build, graph, manifest, materialize, seal
from validation.component.join_inputs import prospective_inputs

ROOT = Path(__file__).resolve().parents[3]
DEST = ROOT / "docs/reviews/U4-B-component-joins-v2"
A = ROOT / "docs/reviews/U4-A-component-release-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze():
    proposal = json.loads((A / "postimages.json").read_text())
    for row in proposal["files"]:
        assert sha(ROOT / row["path"]) == row["postimage_sha256"]
    assert manifest() == json.loads((ROOT / "validation/component/cases.json").read_text())
    inputs = prospective_inputs()
    corpus = build()
    rows = []
    for old in manifest()["cases"]:
        row = deepcopy(old)
        row.update(
            origin="B historical corpus/1, bytes unchanged",
            historical_identity=True,
            expected_layer="result" if old["expected"]["outcome"] == "success" else "profile",
            expected_public_code="success"
            if old["expected"]["outcome"] == "success"
            else "TestVariantNotAdmitted",
        )
        rows.append(row)
    negatives = []
    for name, item in corpus["items"].items():
        if item["expected"]["outcome"] != "success":
            negatives.append(
                ("B2-resource-" + name, deepcopy(item["bundle"]), item["expected"]["outcome"], name)
            )
    for name, code in [
        ("no-order", "LiveBufferAlias"),
        ("false-writer", "InvalidDependency"),
        ("missing-consumer", "InvalidDependency"),
        ("wrong-owner", "InvalidResource"),
    ]:
        b = deepcopy(inputs["B2-C04-transient"]["bundle"])
        g = graph(b)
        a = next(x for x in g["buffers"] if x["id"] == "acc")
        z = next(x for x in g["buffers"] if x["id"] == "zacc")
        if name == "no-order":
            g["dependencies"] = []
        if name == "false-writer":
            z["producer_id"] = "c"
        if name == "missing-consumer":
            a["final_consumer_ids"] = []
        if name == "wrong-owner":
            z["core_id"] = 1
        negatives.append(("B2-lifetime-" + name, b, code, "B2-C04-transient"))
    for name, b, code, parent in negatives:
        item = materialize(name, b, dict(outcome="success"))
        item["expected"] = dict(outcome=code, admission_outcome="success", parent_case=parent)
        item["bundle"]["producer"] = dict(
            name="B-independent-negative-proposal",
            version="2",
            implementation_hash="sha256:" + sha(Path(__file__)),
        )
        seal(item["bundle"], "bundle_hash")
        inputs[name] = item
    a_module = runpy.run_path(str(A / "proposal_inputs.py"))
    a_inputs = a_module["inputs"]()
    assert a_module["manifest"]() == json.loads((A / "fixture-identities.json").read_text())
    for name, item in a_inputs.items():
        item["expected"].update(useful_ops=66977792, issued_ops=67108864)
        if "fixture_resident" in name:
            item["expected"].update(
                duration_ps=2364000, sram_read_bytes=523776, sram_write_bytes=261632
            )
        else:
            item["expected"].update(
                read_payload_bytes=523776,
                read_transaction_bytes=523776,
                write_payload_bytes=261632,
                write_transaction_bytes=261632,
            )
        inputs[name] = item
    fixture_dir = DEST / "fixtures"
    fixture_dir.mkdir(exist_ok=True)
    for name, item in sorted(inputs.items()):
        b = item["bundle"]
        p = b["points"][0]
        parsed = MappedBundle.model_validate(b)
        code = item["expected"]["outcome"]
        try:
            validate_resources(parsed, parsed.points[0])
            actual = "success"
        except ValueError as exc:
            actual = str(exc).split(":", 1)[0]
        assert actual == code, (name, actual, code)
        path = fixture_dir / (name + ".json")
        path.write_text(json.dumps(item, sort_keys=True, indent=2) + "\n")
        rows.append(
            dict(
                case_id=name,
                origin="A2 distinct mapper proposal"
                if name.startswith("A2")
                else "B2 independent proposal",
                historical_identity=False,
                hardware_spec_hash=b["hardware_spec_hash"],
                bundle_hash=b["bundle_hash"],
                graph_hash=p["task_graph"]["graph_hash"],
                point_hash=p["payload_hash"],
                profile_hash=item["profile"]["profile_hash"],
                input_path=str(path.relative_to(ROOT)),
                input_sha256=sha(path),
                expected=item["expected"],
                expected_hash=content_hash(item["expected"]),
                expected_layer="result" if code == "success" else "resource-preflight",
                expected_public_code=code,
                native_refusal_mechanism=None
                if code == "success"
                else "uarch-component-refusal-selection/1 proposed, unimplemented",
                engine_identity=None,
                build_identity=None,
                authority=None,
                job_hash=None,
                raw_request_sha256=None,
                native_status="not_run",
            )
        )
    old_a = ROOT / "docs/reviews/U4-A-component-mapper-v1/fixtures"
    for name, time in [
        ("A-C01-resident", 702000),
        ("A-C02-resident", 547000),
        ("A-C03-resident", 1182000),
        ("A-C02-cold", 656000),
    ]:
        path = old_a / (name + ".json")
        b = json.loads(path.read_text())
        p = b["points"][0]
        parsed = MappedBundle.model_validate(b)
        validate_resources(parsed, parsed.points[0])
        rows.append(
            dict(
                case_id=name,
                origin="A6d30e36 distinct fixture, bytes unchanged",
                historical_identity=True,
                bundle_hash=b["bundle_hash"],
                point_hash=p["payload_hash"],
                graph_hash=p["task_graph"]["graph_hash"],
                hardware_spec_hash=b["hardware_spec_hash"],
                profile_hash=b["admission"]["profile_hash"],
                input_path=str(path.relative_to(ROOT)),
                input_sha256=sha(path),
                expected=dict(outcome="success", duration_ps=time),
                expected_layer="result",
                expected_public_code="success",
                engine_identity=None,
                build_identity=None,
                authority=None,
                job_hash=None,
                native_status="not_run",
            )
        )
    checker_files = [
        "validation/component/" + name + ".py"
        for name in (
            "arithmetic",
            "checks",
            "observations",
            "observations_v2",
            "phase_laws",
            "selection",
            "reduction",
            "join_inputs",
            "corpus",
        )
    ]
    result = dict(
        format="B-component-execution-selection/2",
        status="immutable prospective inputs; not authority or execution",
        candidate_patch_sha256=proposal["patch_sha256"],
        candidate_postimages=proposal["files"],
        cases=sorted(rows, key=lambda x: x["case_id"]),
        checker_bindings={p: sha(ROOT / p) for p in checker_files},
        observation_contract=dict(
            format="uarch-native-observations/2",
            unrepresented=sorted(
                [
                    "diagnostics/dram_row_hit_ratio",
                    "diagnostics/energy_pj",
                    "diagnostics/noc_max_link_util_ratio",
                    "diagnostics/sram_bank_conflict_stall_ratio",
                    "diagnostics/vector_util_ratio",
                    "ext_counts/noc_flit_hop_count",
                    "u_c0_duration_ps",
                ]
            ),
        ),
        obligations=dict(
            positive_replays="3 debug + 3 release "
            "actual public calls; full byte identity; producer disabled",
            inherited_fault_controls_sha256=sha(
                ROOT / "docs/reviews/U4-B-component-verification-v1/controls.json"
            ),
            required_faults=[
                "wrong accumulator producer",
                "missing final consumer",
                "live alias",
                "wrong owner",
                "ordinary clock bypass",
                "request/channel/engine substitution",
                "rounded channel carry",
                "wrong receiving edge",
                "fake busy wait",
                "wrong causal predecessor",
            ],
            restoration="retain positive/fault/reverted/restored receipts and exact original "
            "source/input hashes; affected controls only",
            reduction="failed control or surviving mutant => failed; "
            "missing genuine call/build/authority => not_run",
            negative_layers=[
                "stale content hash",
                "profile refusal",
                "resource preflight under reviewed success context",
                "future immutable raw-byte Rust refusal",
            ],
            native_calls_executed=0,
            synthetic_unit_controls="excluded from native execution selection",
            human_L1="H-L1-GEMM-01/H-L1-DMA-01 pending actual human workings",
            release="no accepted engine/build/host/authority; "
            "external release manifest must bind this immutable selection "
            "and all required real identities",
        ),
    )
    result["selection_hash"] = content_hash(result)
    (DEST / "execution-selection.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(len(rows), "cases frozen; native calls 0")


if __name__ == "__main__":
    freeze()
