"""Independent final consumer pair and refreshed F4 source identity controls."""

import hashlib
import json
import runpy
import sys
from copy import deepcopy
from pathlib import Path

from uarch_contract.hashing import canonical_json, content_hash
from uarch_contract.mapped import MappedEngineJob, validate_result
from validation.component.observations_v3 import check_v3

source, repo, out = map(Path, sys.argv[1:])
a = repo / "docs/reviews/U4-A-issue-edge-F2-F3-v1"
fixture = source / "contract/tests/mapped/fixtures/issue_capacity"
job = json.loads((fixture / "sr2-v3-job.json").read_bytes())
result = json.loads((fixture / "sr2-v3-result.json").read_bytes())
expected = json.loads(
    (source / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_bytes()
)["observation_contract"]
forged = deepcopy(result)
ops = {r["event_cursor"]: r for r in forged["observations"]["reservation_opportunities"]["records"]}
assert ops[52]["granted_request_ids"] == [] and ops[54]["granted_request_ids"] == ["r02.00"]
ops[52]["granted_request_ids"], ops[54]["granted_request_ids"] = ["r02.00"], []
forged["result_hash"] = content_hash(forged, exclude=("result_hash",))
forgery_hash = hashlib.sha256(canonical_json(forged).encode()).hexdigest()
assert forgery_hash == "4917188c882737737192445e32265786eb39bd71c9e937cda782ab415e46936e"
rows = []
for name, value in [("valid-sr2-v3", result), ("A1b", forged)]:
    row = dict(case=name)
    for label, fn in [
        (
            "structural",
            lambda value=value: validate_result(value, MappedEngineJob.model_validate(job)),
        ),
        ("independent", lambda value=value: check_v3(job, value, expected)),
    ]:
        try:
            fn()
            row[label] = "pass"
        except (ValueError, AssertionError) as error:
            row[label] = type(error).__name__ + ": " + str(error)
    rows.append(row)
assert rows[0] == dict(case="valid-sr2-v3", structural="pass", independent="pass")
assert rows[1] == dict(
    case="A1b",
    structural="ValueError: IncompleteObservations: reservation cursor capacity",
    independent="CheckFailure: opportunity eligible grants / ready tie",
)
recipe = runpy.run_path(str(source / "docs/reviews/U4-B-issue-edge-stage2-v1/first_use.py"))
pins = json.loads((a / "consumer-bindings.json").read_bytes())["closure"]
checker = "validation.component.observations_v3:check_v3"
recipe["consume"](job, result, checker, expected, source, pins)
wrong = dict(pins)
wrong["validation/component/installation_identity.py"] = hashlib.sha256(
    Path("/tmp/u4-b-f2f3-source-01/validation/component/installation_identity.py").read_bytes()
).hexdigest()
try:
    recipe["consume"](job, result, checker, expected, source, wrong)
except ValueError as error:
    assert (
        str(error) == "prospective consumer source identity mismatch: "
        "validation/component/installation_identity.py"
    )
    wrong_source = str(error)
else:
    raise AssertionError("wrong source admitted")
try:
    recipe["required_route"](job, result, "validation.component.observations_v2:check_v2")
except ValueError as error:
    assert str(error) == "prospective model / observation format / independent checker mismatch"
    wrong_route = str(error)
else:
    raise AssertionError("wrong checker admitted")
report = dict(
    consumers=rows,
    A1b_sha256=forgery_hash,
    F4_matching="pass",
    F4_wrong_source=wrong_source,
    F4_wrong_checker=wrong_route,
    scope="fresh Python consumer controls on synthetic reconstructed fixture; "
    "source refresh, not native evidence",
    native_builds=0,
    native_runs=0,
)
out.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
