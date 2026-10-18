"""B actual-output positives and joined attacks; private synthetic anchors, no authority.
Run under the preserved isolated runner: consume.py SOURCE RUNS A7 OUT.
"""

import hashlib
import importlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from uarch_contract.hashing import content_hash
from uarch_contract.mapped import MappedEngineJob, validate_result
from validation.component.observations_v3 import check_v3

source, runs, a7, out = map(Path, sys.argv[1:])
expected = json.loads(
    (source / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_text()
)["observation_contract"]


def outcome(fn):
    try:
        fn()
        return "pass"
    except Exception as e:
        return type(e).__name__ + ": " + str(e)


def seal(r):
    r["result_hash"] = content_hash(r, exclude=("result_hash",))
    return r


report = {
    "label": "private native outputs with synthetic unit anchors; no public execution",
    "origins": {},
    "cases": [],
}
for module in (
    "uarch_contract.mapped_issue",
    "validation.component.issue_checks",
    "validation.component.transition_checks_v3",
    "validation.component.observations_v3",
):
    p = Path(importlib.import_module(module).__file__).resolve()
    assert p.is_relative_to(source.resolve())
    report["origins"][module] = {
        "path": str(p),
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
    }


def consume(name, j, r):
    row = {
        "case": name,
        "result_hash": r["result_hash"],
        "structural": outcome(lambda: validate_result(r, MappedEngineJob.model_validate(j))),
        "independent": outcome(lambda: check_v3(j, r, expected)),
    }
    report["cases"].append(row)
    print(name, row["structural"], row["independent"])


for name in ("cc0-v3", "cc-v3", "sr-v3"):
    j = json.loads((runs / name / "job.json").read_text())
    for mode in ("debug", "release"):
        r = json.loads((runs / name / mode / "result.json").read_text())["result"]
        consume(name + "-" + mode, j, r)
j = json.loads((runs / "cc0-v3/job.json").read_text())
consume("A7-post-reservation-credit", j, json.loads(a7.read_text()))
r = json.loads((runs / "cc0-v3/debug/result.json").read_text())["result"]
for label in ("omit-earlier-opportunity-release", "omit-current-release"):
    bad = deepcopy(r)
    first = next(
        a
        for a in bad["observations"]["activities"]["records"]
        if a["request_id"] == "r03.00" and a["subphase"] == "dma_issue" and a["kind"] == "alignment"
    )
    first["predecessors"].pop(0 if label == "omit-earlier-opportunity-release" else 1)
    consume(label, j, seal(bad))
j = json.loads((runs / "sr-v3/job.json").read_text())
r = json.loads((runs / "sr-v3/debug/result.json").read_text())["result"]
early, late = [
    o for o in r["observations"]["reservation_opportunities"]["records"] if o["t_ps"] == 86000
]
assert (early["event_cursor"], late["event_cursor"]) == (52, 54)
early["granted_request_ids"], late["granted_request_ids"] = ["r02.00"], []
consume("A1-pre-release-grant", j, seal(r))
out.write_text(json.dumps(report, indent=2) + "\n")
