"""Prospective P2 inputs and private SYNTHETIC jobs; never public authority.

Historical bundles, placements, policies and expected values are read-only inputs.
Only the admission/profile join changes. Resource negatives have an explicitly
synthetic positive profile so that profile refusal cannot mask the resource guard.
"""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from uarch_contract.hashing import content_hash
from uarch_contract.mapped import (
    MappedBundle,
    NativeTestProfile,
    canonical_owners,
    hardware_projection,
    resolve_frequencies,
)

from validation.component.corpus import build
from validation.component.synthetic_carrier import synthetic_job
from validation.component.transient_carrier import READY, SPANS, transient_control

ROOT = Path(__file__).resolve().parents[2]
HISTORY = ROOT / "docs/reviews/U4-B-component-stage2-v1/execution-selection.json"


def policy_item(
    bundle: dict[str, Any], expected: dict[str, Any], name: str, *, profile_outcome: str = "success"
) -> dict[str, Any]:
    b = deepcopy(bundle)
    p = b["points"][0]
    parsed = MappedBundle.model_validate(b)
    profile = dict(
        format="uarch-native-test-profile/2",
        semantics_revision="U0011-stage2/1",
        owner="B native preparation; unsigned proposal; synthetic private anchors only",
        entries=[
            dict(
                case_id=name,
                checkpoint="B",
                scope=b["scope"]["kind"],
                initial_state=p["initial_state"],
                priming_iterations=0,
                hardware_spec_hash=b["hardware_spec_hash"],
                hardware_spec=b["hardware_spec"],
                frequency_ratio=p["frequency_ratio"],
                freq_hz=resolve_frequencies(parsed.hardware_spec, p["frequency_ratio"]).model_dump(
                    mode="json"
                ),
                graph_hash=p["task_graph"]["graph_hash"],
                point_hash=p["payload_hash"],
                allowed_job_kinds=sorted({j["kind"] for j in p["task_graph"]["jobs"]}),
                expected_outcome=profile_outcome,
                seed=0,
                case_selection_revision="B-component-native-prospective/1",
                clock_setup_hash=content_hash([]),
                mapping_policy=deepcopy(b["mapping_policy"]),
            )
        ],
    )
    profile["profile_hash"] = content_hash(profile)
    NativeTestProfile.model_validate(profile)
    b["admission"] = dict(
        checkpoint="B",
        invocation="test",
        eligibility="verification_only",
        case_id=name,
        profile_hash=profile["profile_hash"],
    )
    b["bundle_hash"] = content_hash(b, exclude=("bundle_hash",))
    return dict(bundle=b, profile=profile, expected=deepcopy(expected))


def prospective_inputs() -> dict[str, Any]:
    old = json.loads(HISTORY.read_text())
    corpus = build()
    items = {}
    transitions = []
    for row in old["cases"]:
        name = row["case_id"]
        if "input_path" in row:
            source = ROOT / row["input_path"]
            assert hashlib.sha256(source.read_bytes()).hexdigest() == row["input_sha256"]
            raw = json.loads(source.read_text())
            b = raw.get("bundle", raw)
        else:
            b = corpus["items"][name]["bundle"]
        assert b["bundle_hash"] == row["bundle_hash"]
        item = policy_item(
            b,
            row["expected"],
            name,
            profile_outcome=row["expected"]["outcome"]
            if row["expected_layer"] == "profile"
            else "success",
        )
        item["expected_layer"] = row["expected_layer"]
        item["expected_public_code"] = row["expected_public_code"]
        items[name] = item
        transitions.append(
            dict(
                case_id=name,
                historical_bundle_hash=b["bundle_hash"],
                prospective_bundle_hash=item["bundle"]["bundle_hash"],
                historical_profile_hash=row["profile_hash"],
                prospective_profile_hash=item["profile"]["profile_hash"],
                graph_hash=row["graph_hash"],
                point_hash=row["point_hash"],
                expected_hash=content_hash(row["expected"]),
            )
        )
    # O2 graph and literal expectations were accepted independently before native code.
    job, _ = transient_control()
    expected = dict(
        outcome="success",
        duration_ps=2735000,
        useful_ops=1050,
        issued_ops=1966080,
        sram_read_bytes=500,
        sram_write_bytes=210,
        hbm_payload_bytes=0,
        job_times_ps={k: list(v) for k, v in SPANS.items()},
        job_ready_ps=READY,
        transient_bacc=[547000, 2188000],
    )
    items["B-native-O2"] = policy_item(
        job.workload_closure.model_dump(mode="json"), expected, "B-native-O2"
    )
    items["B-native-O2"].update(expected_layer="result", expected_public_code="success")
    # Separate unit-only positive-profile negatives. Historical early refusals remain above.
    for name in ("C04-carrier", "C06-small", "C07-hbm-1", "C07-sram-1"):
        old_item = corpus["items"][name]
        key = "B-native-resource-" + name
        item = policy_item(old_item["bundle"], old_item["expected"], key)
        item.update(
            expected_layer="resource-preflight",
            expected_public_code=old_item["expected"]["outcome"],
        )
        items[key] = item
    return dict(
        format="B-component-native-prospective/1",
        authority=None,
        historical_selection_hash=old["selection_hash"],
        historical_selection_sha256=hashlib.sha256(HISTORY.read_bytes()).hexdigest(),
        registry=corpus["registry"],
        items=items,
        transitions=transitions,
    )


def private_job(item: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    """Construct structural wire input without running Python resource admission.

    Necessary for Rust negatives: model validation and semantic admission are distinct.
    Synthetic engine/Trust anchors do not describe a deployed executable or authority.
    """
    b = MappedBundle.model_validate(item["bundle"])
    point = b.points[0]
    raw: dict[str, Any] = deepcopy(synthetic_job("C02").model_dump(mode="json"))
    raw.update(
        bundle_hash=b.bundle_hash,
        point_hash=point.payload_hash,
        assumptions_hash=b.assumptions_hash,
        mapped_point=point.model_dump(mode="json"),
        workload_closure=b.model_dump(mode="json"),
        assumptions=b.assumptions.model_dump(mode="json"),
        hardware=hardware_projection(b.hardware_spec).model_dump(mode="json"),
        hardware_spec_hash=b.hardware_spec_hash,
        rank=b.rank.model_dump(mode="json"),
        frequency_ratio=point.frequency_ratio,
        freq_hz=resolve_frequencies(b.hardware_spec, point.frequency_ratio).model_dump(mode="json"),
        initial_state=point.initial_state,
        admission=b.admission.model_dump(mode="json"),
        owners=[
            o.model_dump(mode="json") for o in canonical_owners(b.hardware_spec, point.task_graph)
        ],
        registry=deepcopy(registry),
        profile=deepcopy(item["profile"]),
    )
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    return raw
