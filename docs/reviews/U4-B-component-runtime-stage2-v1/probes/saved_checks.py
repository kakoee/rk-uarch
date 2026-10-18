"""Read-only saved-result reproduction. Current checker; inherited native execution."""

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

from uarch_contract.hashing import content_hash
from uarch_contract.mapped import MappedEngineJob, validate_result

from validation.component import observations_v3
from validation.component.runtime_checks import assert_literals

root = Path(sys.argv[1])
inventory = json.loads((root / "saved-inputs.json").read_bytes())
expected = json.loads((root / "observation-contract.json").read_bytes())
rows = {r["case_id"]: r for r in json.loads((root / "selection.json").read_bytes())["rows"]}


def load(bound):
    raw = Path(bound["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == bound["sha256"]
    return json.loads(raw)


reports = []
for entry in inventory:
    case = entry["case_id"]
    j, r = load(entry["job"]), load(entry["result"])
    validate_result(r, MappedEngineJob.model_validate(j))
    observations_v3.check_v3(j, r, expected)
    assert_literals(j, r, rows[case]["expected"])
    reports.append(dict(case=case, control="pass", native_execution="inherited", inputs=entry))
    for key in rows[case]["expected"]:
        if key in {
            "accumulator_bytes",
            "required_accumulator_bytes",
            "capacity_bytes",
            "payload_bytes",
            "transaction_bytes",
            "tile_durations_ps",
            "fragments",
        }:
            bad = deepcopy(rows[case]["expected"])
            if key == "fragments":
                bad[key][0][1] += 1
            elif key == "tile_durations_ps":
                bad[key][0] += 1
            else:
                bad[key] += 1
            try:
                assert_literals(j, r, bad)
            except ValueError as err:
                reports.append(dict(case=case, literal=key, refusal=str(err)))
            else:
                raise AssertionError("ignored literal " + key)
    if case in ("v3:C04-control", "v3:B3-terminal-control"):
        a, b, bufs = (
            ("c", "z", ("sy", "zsy"))
            if case.endswith("C04-control")
            else ("d", "e", ("dsy", "esy"))
        )
        bad = deepcopy(r)
        o = bad["observations"]
        jobs = {x["job_id"]: x for x in o["jobs"]["records"]}
        for k in ("start_ps", "end_ps"):
            jobs[a][k], jobs[b][k] = jobs[b][k], jobs[a][k]
        for sec, value in o.items():
            if sec in ("jobs", "allocations", "format") or not isinstance(value, dict):
                continue
            for row in value.get("records", []):
                for key in ("job_id", "item_id", "cause_job_id"):
                    if row.get(key) in (a, b):
                        row[key] = b if row[key] == a else a
        alloc = {x["buffer_id"]: x for x in o["allocations"]["records"]}
        for k in ("allocate_ps", "free_ps"):
            alloc[bufs[0]][k], alloc[bufs[1]][k] = alloc[bufs[1]][k], alloc[bufs[0]][k]
        bad["result_hash"] = content_hash(bad, exclude=("result_hash",))
        validate_result(bad, MappedEngineJob.model_validate(j))
        try:
            observations_v3.check_v3(j, bad, expected)
        except ValueError as err:
            assert "matrix FIFO-ready grant" in str(err)
            reports.append(
                dict(case=case, forgery="structurally accepted", checker_refusal=str(err))
            )
        else:
            raise AssertionError("wrong order accepted")
        guard = observations_v3.check_matrix_order
        try:
            observations_v3.check_matrix_order = lambda *_: None
            observations_v3.check_v3(j, bad, expected)
            assert_literals(j, bad, rows[case]["expected"])
            reports.append(
                dict(case=case, fault="only matrix guard disconnected", unsafe_acceptance=True)
            )
        finally:
            observations_v3.check_matrix_order = guard
        try:
            observations_v3.check_v3(j, bad, expected)
        except ValueError as err:
            assert "matrix FIFO-ready grant" in str(err)
        else:
            raise AssertionError("restoration failed")
        observations_v3.check_v3(j, r, expected)
print(json.dumps(reports, indent=2))
