"""Prospective /3 definitions. Produces private synthetic inputs, never authority."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from uarch_contract.hashing import canonical_json, content_hash

from validation.component.join_inputs import reseal
from validation.component.native_inputs import policy_item, private_job, prospective_inputs

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "docs/reviews/U4-B-component-runtime-preparation-v1"
HISTORY = "docs/reviews/U4-B-component-stage2-v1/execution-selection.json"
PRIOR = "docs/reviews/U4-B-component-native-audit-v1/first-use-selection-final.json"
MODEL = ("native-intervals", "2")
FORMAT = "uarch-native-observations/3"
CHECKER = "validation.component.observations_v3:check_v3"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extra_sources() -> dict[str, str]:
    a = "docs/reviews/U4-A-issue-edge-amendment-v1/evidence/native/inputs/"
    rows = {
        f"issue-{n}": a + n + ".json"
        for n in (
            "issue-gap",
            "gap-cap1",
            "gap-cap2",
            "gap-cap2-pair",
            "gap-independent",
            "gap-write",
        )
    }
    rows.update(
        {
            f"order-{n}": f"native/crates/uarch-engine/testdata/synthetic-issue-order-{n}.json"
            for n in ("r00", "r01")
        }
    )
    rows.update(
        {
            n: f"docs/reviews/U4-B-issue-edge-stage2-v1/private-probes/{n}/job.json"
            for n in ("cc0-v3", "cc-v3", "sr-v3")
        }
    )
    # ww /3 is the preserved /2 reproducer re-bound prospectively, never a /2 repair.
    rows["ww0-v3"] = "docs/reviews/U4-B-issue-edge-F2-F3-v1/reproducers/ww0-v1.json"
    rows["sr2-v3"] = "contract/tests/mapped/fixtures/issue_capacity/sr2-v3-job.json"
    return rows


def definitions() -> dict[str, Any]:
    corpus = prospective_inputs()
    items = corpus["items"]
    historical = {r["case_id"]: r for r in json.loads((ROOT / HISTORY).read_bytes())["cases"]}
    prior = {r["case"]: r for r in json.loads((ROOT / PRIOR).read_bytes())["rows"]}
    old = items.pop("D13-barrier")
    bundle = deepcopy(old["bundle"])
    barrier = next(j for j in bundle["points"][0]["task_graph"]["jobs"] if j["kind"] == "barrier")
    assert barrier["owner_id"] == 44
    barrier["owner_id"] = 52
    reseal(bundle)
    name = "B-native-D13-canonical-owner"
    items[name] = dict(
        policy_item(bundle, old["expected"], name),
        expected_layer="result",
        expected_public_code="success",
    )
    assert set(items) == set(prior)
    for key, item in items.items():
        assert item["expected"] == prior[key]["expected"]
        assert item["bundle"]["bundle_hash"] == prior[key]["bundle_hash"]
    sources = extra_sources()
    extra_literals = json.loads((ROOT / PACKAGE / "extra-literals.json").read_bytes())
    for key, path in sources.items():
        raw = json.loads((ROOT / path).read_bytes())
        items[key] = dict(
            policy_item(raw["workload_closure"], extra_literals[key], key),
            expected_layer="result",
            expected_public_code="success",
        )
    rows, jobs = [], {}
    for old_name, item in sorted(items.items()):
        name = "v3:" + old_name
        # Keep profile identity changes explicit: new selection ID and exact policy promise.
        item = dict(
            policy_item(
                item["bundle"],
                item["expected"],
                name,
                profile_outcome=item["expected"]["outcome"]
                if item["expected_layer"] == "profile"
                else "success",
            ),
            expected_layer=item["expected_layer"],
            expected_public_code=item["expected_public_code"],
        )
        job = private_job(item, corpus["registry"])
        job["engine"]["model"]["version"] = "2"
        job["job_hash"] = content_hash(job, exclude=("job_hash",))
        raw_bytes = canonical_json(job).encode()
        jobs[name] = dict(job=job, item=item)
        old_key = "D13-barrier" if old_name == "B-native-D13-canonical-owner" else old_name
        source = sources.get(old_name)
        rows.append(
            dict(
                case_id=name,
                historical_case=old_key if old_key in historical else None,
                prior_case=old_name if old_name in prior else None,
                historical_row=historical.get(old_key),
                prior_row=prior.get(old_name),
                source_input=dict(path=source, sha256=sha(ROOT / source)) if source else None,
                expected=item["expected"],
                expected_layer=item["expected_layer"],
                expected_code=item["expected_public_code"],
                profile=item["profile"],
                policy=item["bundle"]["mapping_policy"],
                graph_hash=job["mapped_point"]["task_graph"]["graph_hash"],
                point_hash=job["point_hash"],
                bundle_hash=job["bundle_hash"],
                synthetic_raw_sha256=hashlib.sha256(raw_bytes).hexdigest(),
                synthetic_job_hash=job["job_hash"],
                public_raw_sha256=None,
                required_checks=[
                    "structural validate_result",
                    CHECKER,
                    "literal expectations",
                    "six-way canonical bytes",
                    "producer-disabled replay",
                ]
                if item["expected_layer"] == "result"
                else [
                    "exact refusal code/pointer",
                    "actual native reach separately witnessed",
                    "zero dispatch separately witnessed",
                ],
                authority=None,
            )
        )
    counts = Counter(r["expected_layer"] for r in rows)
    selection = dict(
        format="B-component-prospective-v3-selection/1",
        status="definition freeze; not authority",
        model=list(MODEL),
        observations=FORMAT,
        checker=CHECKER,
        historical_selection_sha256=sha(ROOT / HISTORY),
        prior_selection_sha256=sha(ROOT / PRIOR),
        registry_hash=corpus["registry"]["registry_hash"],
        rows=rows,
        counts=dict(counts),
        cases=len(rows),
        six_way_calls=6 * len(rows),
        replay_calls=6 * counts["result"],
        total_planned_native_calls=6 * (len(rows) + counts["result"]),
        D13="historical owner44 mismatch preserved; distinct owner52 prospective correction",
        F2="historical /2 restriction preserved; /3 selection does not repair /2",
        runtime_candidate=None,
        public_authority=None,
        missing=[
            "A final runtime candidate and D3 adapter",
            "exact actual build bindings",
            "independent review",
            "human runtime/placement/authority decisions",
        ],
        typed_tests=[
            "component_tests::synthetic_rational_overflow_is_checked",
            "issue_proposal_tests release-edge/atomic-conversion typed tests",
        ],
        timing_overflow_mapped_cases=0,
        timing_overflow_note=(
            "typed arithmetic guard evidence is separate; no invented mapped overflow input"
        ),
        human_L1=["H-L1-GEMM-01 pending actual workings", "H-L1-DMA-01 pending actual workings"],
    )
    selection["selection_hash"] = content_hash(selection)
    return dict(selection=selection, jobs=jobs)


def write_private(out: Path) -> dict[str, Any]:
    if not out.resolve().is_relative_to(Path("/tmp")):
        raise ValueError("private synthetic export must be in /tmp")
    out.mkdir(exist_ok=False)
    value = definitions()
    for name, payload in value["jobs"].items():
        (out / (name + ".json")).write_text(canonical_json(payload["job"]))
    (out / "selection.json").write_text(
        json.dumps(value["selection"], indent=2, sort_keys=True) + "\n"
    )
    return value["selection"]
