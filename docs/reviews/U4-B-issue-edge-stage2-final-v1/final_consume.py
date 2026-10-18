"""Final joined consumers and prospective F4 route/source controls; no authority."""

import hashlib
import importlib.util
import json
import runpy
import sys
from copy import deepcopy
from pathlib import Path

from uarch_contract.hashing import canonical_json, content_hash

source, repo, runs, out = map(Path, sys.argv[1:])
out.mkdir(exist_ok=False)
a = repo / "docs/reviews/U4-A-issue-edge-stage2-v1"
b = repo / "docs/reviews/U4-B-issue-edge-stage2-v1"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


assert (
    sha(b / "private-probes/A7.json")
    == sha(a / "private-probes/A7.json")
    == "58813767b0016bcf59bb954087e79484fc1bd8ea024e8d17f157541b0f6f2426"
)
sys.argv = [
    str(b / "consume.py"),
    str(source),
    str(runs),
    str(b / "private-probes/A7.json"),
    str(out / "consumers.json"),
]
runpy.run_path(str(b / "consume.py"), run_name="__main__")
cases = {x["case"]: x for x in json.loads((out / "consumers.json").read_text())["cases"]}
for name in ("cc0-v3", "cc-v3", "sr-v3"):
    for mode in ("debug", "release"):
        assert (
            cases[name + "-" + mode]["independent"]
            == cases[name + "-" + mode]["structural"]
            == "pass"
        )
        output = json.loads((runs / name / mode / "result.json").read_text())["result"]
        assert output == json.loads((a / "private-probes" / name / (mode + ".json")).read_text())
        assert sha(runs / name / mode / "result.json") == sha(
            b / "private-probes" / name / "result.json"
        )
assert (
    cases["A7-post-reservation-credit"]["independent"] == "CheckFailure: complete eligible causes"
)
assert (
    cases["A7-post-reservation-credit"]["structural"]
    == "ValueError: AttributionMismatch: credit predecessor before reservation opportunity"
)
assert (
    cases["A1-pre-release-grant"]["independent"]
    == "CheckFailure: opportunity eligible grants / ready tie"
)
assert (
    cases["A1-pre-release-grant"]["structural"]
    == "ValueError: IncompleteObservations: reservation cursor capacity"
)
for name in ("omit-earlier-opportunity-release", "omit-current-release"):
    assert cases[name]["independent"] != "pass" and cases[name]["structural"] != "pass"
# Verify B's own regenerated A1 bytes match the preserved reviewer attack exactly.

r = json.loads((runs / "sr-v3/debug/result.json").read_text())["result"]
early, late = [
    o for o in r["observations"]["reservation_opportunities"]["records"] if o["t_ps"] == 86000
]
early["granted_request_ids"], late["granted_request_ids"] = ["r02.00"], []
r["result_hash"] = content_hash(r, exclude=("result_hash",))
assert canonical_json(r).encode() == (a / "private-probes/A1.json").read_bytes()
assert (
    sha(a / "private-probes/A1.json")
    == "ac363071303e34061baed465c600687bcbea8aac7cd37a279efee4c9d81a3613"
)
# Exact existing offline prospective recipe; supplied final pins checked before consumption.
spec = importlib.util.spec_from_file_location("prospective", b / "first_use.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
pins = json.loads((a / "evidence/joined-checks/f4.json").read_text())["closure"]
expected = json.loads(
    (source / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_text()
)["observation_contract"]
j = json.loads((runs / "cc0-v3/job.json").read_text())
r = json.loads((runs / "cc0-v3/debug/result.json").read_text())["result"]
checker = "validation.component.observations_v3:check_v3"


def outcome(fn):
    try:
        fn()
        return "pass"
    except Exception as e:
        return type(e).__name__ + ": " + str(e)


f4 = {"recipe_sha256": sha(b / "first_use.py"), "closure": pins, "cases": {}}
f4["cases"]["matching-combined"] = outcome(
    lambda: module.consume(j, r, checker, expected, source, pins)
)
f4["cases"]["wrong-checker"] = outcome(
    lambda: module.consume(
        j, r, "validation.component.observations_v2:check_v2", expected, source, pins
    )
)
wrong = deepcopy(pins)
wrong["validation/component/issue_checks.py"] = "0" * 64
f4["cases"]["wrong-checker-source"] = outcome(
    lambda: module.consume(j, r, checker, expected, source, wrong)
)
wrong_struct = deepcopy(pins)
wrong_struct["contract/uarch_contract/mapped_issue.py"] = "0" * 64
f4["cases"]["wrong-structural-source"] = outcome(
    lambda: module.consume(j, r, checker, expected, source, wrong_struct)
)
assert f4["cases"]["matching-combined"] == "pass"
assert all(v != "pass" for k, v in f4["cases"].items() if k != "matching-combined")
f4["inherited"] = (
    "Original /2 mismatch, valid legacy and A6c controls: B3e7bf4e; "
    "original helper/legacy/structural model binding bytes unchanged; no /2 native replay"
)
(out / "f4.json").write_text(json.dumps(f4, indent=2) + "\n")
print("Six final outputs pass, exact A7/A1 and omissions refuse; F4 route/source controls pass")
