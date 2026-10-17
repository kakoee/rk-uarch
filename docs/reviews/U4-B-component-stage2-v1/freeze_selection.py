"""Freeze revision /3 from exact reconstructed final files. No engine or authority."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from uarch_contract.hashing import content_hash
from uarch_contract.mapped import MappedBundle, validate_resources
from validation.component.lifetime_inputs import lifetime_inputs

from validation.component.corpus import materialize

ROOT = Path.cwd()
PACKAGE = ROOT / "docs/reviews/U4-B-component-stage2-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(candidate):
    old = json.loads(
        (ROOT / "docs/reviews/U4-B-component-joins-v2/execution-selection.json").read_text()
    )
    cases = deepcopy(old["cases"])
    for name, raw in lifetime_inputs().items():
        positive = name.endswith("control")
        expected = dict(outcome="success" if positive else "InvalidDependency")
        if positive:
            expected["duration_ps"] = {
                "B3-writer-control": 1094000,
                "B3-terminal-control": 4728000,
                "B3-shared-use-control": 2364000,
            }[name]
        item = materialize(name, raw, dict(outcome="success"))
        item["expected"] = expected
        item["synthetic_profile_context"] = True
        item["authority"] = None
        path = PACKAGE / "fixtures" / (name + ".json")
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n")
        b = MappedBundle.model_validate(item["bundle"])
        actual = "success"
        try:
            validate_resources(b, b.points[0])
        except ValueError as exc:
            actual = str(exc).split(":", 1)[0]
        assert actual == expected["outcome"], (name, actual)
        cases.append(
            dict(
                case_id=name,
                origin="B Stage 2 independent input",
                historical_identity=False,
                hardware_spec_hash=b.hardware_spec_hash,
                bundle_hash=b.bundle_hash,
                graph_hash=b.points[0].task_graph.graph_hash,
                point_hash=b.points[0].payload_hash,
                profile_hash=item["profile"]["profile_hash"],
                input_path=str(path.relative_to(ROOT)),
                input_sha256=sha(path),
                expected=expected,
                expected_hash=content_hash(expected),
                expected_layer="result" if positive else "resource-preflight",
                expected_public_code=expected["outcome"],
                native_status="not_run",
                engine_identity=None,
                build_identity=None,
                authority=None,
                job_hash=None,
                raw_request_sha256=None,
                host_identity=None,
                reason="valid unmasked control" if positive else "unmasked lifetime semantic guard",
                native_refusal_mechanism=None
                if positive
                else "uarch-component-refusal-selection/1 proposed, unimplemented",
            )
        )
    checker_paths = sorted(
        set(old["checker_bindings"]) | {"validation/component/transition_checks.py"}
    )
    tests = [
        row["path"]
        for row in candidate["files"]
        if row["path"].startswith(("validation/", "tests/", "contract/tests/"))
        and row["path"] not in checker_paths
    ]
    result = dict(
        format="B-component-execution-selection/3",
        status="immutable prospective selection; no authority or execution",
        historical_selection_hash=old["selection_hash"],
        historical_selection_byte_sha256=sha(
            ROOT / "docs/reviews/U4-B-component-joins-v2/execution-selection.json"
        ),
        old_to_new=[
            dict(
                old=x["case_id"],
                new=x["case_id"],
                meaning="unchanged historical input and refusal layer",
            )
            for x in old["cases"]
        ],
        cases=sorted(cases, key=lambda x: x["case_id"]),
        candidate_patch_sha256=candidate["patch_sha256"],
        candidate_files=candidate["files"],
        checker_bindings={p: sha(ROOT / p) for p in checker_paths},
        test_bindings={p: sha(ROOT / p) for p in tests},
        obligations=deepcopy(old["obligations"]),
        profile_promise="Historical and new synthetic profile/1 fixtures bind graph/point only. "
        "This selection additionally binds exact whole bundles. "
        "Future P2 authority/profile freeze pending human choice.",
        observations=dict(
            format="uarch-native-observations/2",
            unrepresented_job_blockers=[],
            unrepresented_critical_predecessor=None,
        ),
    )
    result["obligations"]["required_faults"] += [
        "missing occupied row",
        "false or omitted eligible cause",
        "same-ready port/channel order",
        "meaningful job/event field forgery",
        "unmasked A1/A3b/A3c and writer",
        "fully resealed mechanism timing/queue/null/diagnostic attacks",
    ]
    result["selection_hash"] = content_hash(result)
    (PACKAGE / "execution-selection.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    return result
