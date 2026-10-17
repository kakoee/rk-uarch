"""Additive first-use definition selection; no public jobs, trust or authority."""

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path

from uarch_contract.hashing import content_hash

from validation.component.join_inputs import reseal
from validation.component.native_inputs import policy_item, private_job, prospective_inputs

SOURCE = "53ea633993a77b1f9d54698c6e8fb06aa123bd81"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--candidate", default=SOURCE)
    args = parser.parse_args()
    corpus = prospective_inputs()
    old = corpus["items"].pop("D13-barrier")
    bundle = deepcopy(old["bundle"])
    barrier = next(j for j in bundle["points"][0]["task_graph"]["jobs"] if j["kind"] == "barrier")
    assert barrier["owner_id"] == 44
    barrier["owner_id"] = 52
    reseal(bundle)
    name = "B-native-D13-canonical-owner"
    corpus["items"][name] = dict(
        policy_item(bundle, old["expected"], name),
        expected_layer="result",
        expected_public_code="success",
    )
    rows = []
    for name, item in sorted(corpus["items"].items()):
        job = private_job(item, corpus["registry"])
        rows.append(
            dict(
                case=name,
                profile_hash=job["profile"]["profile_hash"],
                bundle_hash=job["bundle_hash"],
                point_hash=job["point_hash"],
                graph_hash=job["mapped_point"]["task_graph"]["graph_hash"],
                policy=item["bundle"]["mapping_policy"],
                private_synthetic_job_hash=job["job_hash"],
                expected=item["expected"],
                expected_layer=item["expected_layer"],
                expected_code=item["expected_public_code"],
                public_raw_job=None,
            )
        )
    assert len(rows) == 111
    proposal = dict(
        format="B-component-first-use-definition-selection/1",
        status="proposal only",
        source_candidate=args.candidate,
        registry_hash=corpus["registry"]["registry_hash"],
        historical_selection_sha256=corpus["historical_selection_sha256"],
        historical_selection_hash=corpus["historical_selection_hash"],
        transition=dict(
            historical_case="D13-barrier",
            historical_owner=44,
            prospective_case="B-native-D13-canonical-owner",
            canonical_owner=52,
            historical_expectation_unchanged=old["expected"],
            historical_input_and_failure_preserved=True,
        ),
        public_binding_status="pending genuine build/runtime/authority; null is not accepted",
        public_binary=None,
        public_runtime=None,
        human_authority=None,
        D3="separate exact refusal-only production mechanism approval pending",
        schedule=dict(
            order=["case ascending", "debug then release", "repeat 0,1,2"],
            cases=111,
            calls=666,
            seconds_per_call=30,
            total_seconds_ceiling=20000,
            retained_bytes_ceiling=48 * 1024**3,
        ),
        rows=rows,
    )
    proposal["selection_hash"] = content_hash(proposal)
    args.output.write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n")
    print(proposal["selection_hash"], hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
