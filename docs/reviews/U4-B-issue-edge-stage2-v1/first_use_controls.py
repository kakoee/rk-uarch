"""F2/F4 private consumer controls. No public jobs, selector, or authority creation."""

import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

from uarch_contract.hashing import content_hash
from uarch_contract.mapped import MappedEngineJob, validate_result

from validation.component.observations_v2 import check_v2

source, runs, out = map(Path, sys.argv[1:])
spec = importlib.util.spec_from_file_location(
    "prospective", Path(__file__).with_name("first_use.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
expected = json.loads(
    (source / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_text()
)["observation_contract"]
# Pin complete Python consumer directories, including their arithmetic/transition dependencies.
pins = {
    str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
    for base in ("contract/uarch_contract", "validation/component")
    for p in (source / base).glob("*.py")
    if not p.name.startswith("test_")
}


def result(fn):
    try:
        fn()
        return "pass"
    except Exception as e:
        return type(e).__name__ + ": " + str(e)


def load(name):
    return (
        json.loads((runs / name / "job.json").read_text()),
        json.loads((runs / name / "debug/result.json").read_text())["result"],
    )


report = {"closure": pins, "cases": {}}
j, r = load("r00-v1")
id2 = module.ROUTES[("native-intervals", "1")][1]
id3 = module.ROUTES[("native-intervals", "2")][1]
report["cases"]["valid-v2"] = result(lambda: module.consume(j, r, id2, expected, source, pins))
assert report["cases"]["valid-v2"] == "pass"
badjob = deepcopy(j)
badjob["engine"]["model"]["version"] = "2"
badjob["job_hash"] = content_hash(badjob, exclude=("job_hash",))
bad = deepcopy(r)
bad.update(job_hash=badjob["job_hash"], engine=badjob["engine"], admission=badjob["admission"])
bad["result_hash"] = content_hash(bad, exclude=("result_hash",))
report["cases"]["A6c"] = {
    "frozen_check_v2": result(lambda: check_v2(badjob, bad, expected)),
    "structural": result(lambda: validate_result(bad, MappedEngineJob.model_validate(badjob))),
    "route_wrong_checker": result(lambda: module.required_route(badjob, bad, id2)),
    "route_wrong_format": result(lambda: module.required_route(badjob, bad, id3)),
}
assert report["cases"]["A6c"]["frozen_check_v2"] == "pass"
assert all(v != "pass" for k, v in report["cases"]["A6c"].items() if k != "frozen_check_v2")
j, r = load("cc0-v1")
report["cases"]["F2-original"] = {
    "structural": result(lambda: validate_result(r, MappedEngineJob.model_validate(j))),
    "frozen_check_v2": result(lambda: check_v2(j, r, expected)),
}
assert report["cases"]["F2-original"] == {
    "structural": "pass",
    "frozen_check_v2": "CheckFailure: complete eligible causes",
}
j, r = load("cc0-v3")
report["cases"]["v3-matching-route"] = result(lambda: module.required_route(j, r, id3))
report["cases"]["v3-check_v2-no-credit"] = result(lambda: module.required_route(j, r, id2))
report["cases"]["v3-combined"] = result(lambda: module.consume(j, r, id3, expected, source, pins))
assert (
    report["cases"]["v3-matching-route"] == "pass"
    and report["cases"]["v3-check_v2-no-credit"] != "pass"
)
wrong = deepcopy(pins)
key = "validation/component/observations_v2.py"
wrong[key] = "0" * 64
report["cases"]["wrong-checker-bytes"] = result(lambda: module.verify_files(source, wrong))
assert report["cases"]["wrong-checker-bytes"] != "pass"
out.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report["cases"], indent=2))
