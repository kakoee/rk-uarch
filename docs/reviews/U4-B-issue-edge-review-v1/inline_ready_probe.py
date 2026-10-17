"""Synthetic mapped first-eligibility/order discriminator; no authority."""

import copy
import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

from uarch_contract.hashing import canonical_json, content_hash
from uarch_contract.mapped import MappedEngineJob, validate_result
from validation.component.observations_v3 import check_v3

from rkuarch.workload.mapped import validate_component_completeness

ROOT = Path(__file__).resolve().parents[3]
out = Path(sys.argv[1])
dependent = sys.argv[2]
assert dependent in ("r00", "r01")
out.mkdir(exist_ok=False)
(out / "jobs").mkdir()
(out / "trust").mkdir()
v = json.loads(Path("/tmp/u4-b-issue-edge-runs-01/jobs/gap-cap1.json").read_text())
b = v["workload_closure"]
p = b["points"][0]
g = p["task_graph"]
# Keep every task/buffer/route and resource choice; only make r00 eligible via
# the existing zero-hop unicast at t=0 and r01 initially ready at t=0.
g["dependencies"] = [
    {"before": "a-unicast", "after": "b-barrier"},
    {"before": "a-unicast", "after": dependent},
]
g["graph_hash"] = content_hash(g, exclude=("graph_hash",))
p["payload_hash"] = content_hash(p, exclude=("payload_hash",))
e = v["profile"]["entries"][0]
e.update(
    case_id="SYNTHETIC-B-inline-ready-order",
    graph_hash=g["graph_hash"],
    point_hash=p["payload_hash"],
    case_selection_revision="B-issue-amendment-review/1",
)
v["profile"]["profile_hash"] = content_hash(v["profile"], exclude=("profile_hash",))
b["admission"].update(case_id=e["case_id"], profile_hash=v["profile"]["profile_hash"])
b["bundle_hash"] = content_hash(b, exclude=("bundle_hash",))
v.update(
    bundle_hash=b["bundle_hash"],
    mapped_point=p,
    point_hash=p["payload_hash"],
    admission=b["admission"],
)
v["job_hash"] = content_hash(v, exclude=("job_hash",))
j = MappedEngineJob.model_validate(v)
validate_component_completeness(j.workload_closure)
(out / "jobs/inline.json").write_text(canonical_json(v))
anchor = dict(
    registry=v["registry"]["registry_hash"],
    profile=v["profile"]["profile_hash"],
    case=v["admission"]["case_id"],
    engine=v["engine"],
)
(out / "trust/inline.json").write_text(canonical_json(anchor))
expected = json.loads(
    (ROOT / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_text()
)["observation_contract"]
previous = json.loads(Path("/tmp/u4-b-issue-edge-runs-01/runs.json").read_text())
report = dict(
    recipe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    dependent=dependent,
    label="synthetic private mapped first-eligibility probe",
    job_sha256=hashlib.sha256((out / "jobs/inline.json").read_bytes()).hexdigest(),
    runs=[],
)
for mode in ("debug", "release"):
    row = copy.deepcopy(
        next(x for x in previous["observations"] if x["case"] == "gap-cap1" and x["mode"] == mode)
    )
    argv = row["argv"]
    receipt = out / mode
    receipt.mkdir()
    argv[argv.index("--name") + 1] = "u4-b-inline-" + uuid.uuid4().hex
    for i, s in enumerate(argv):
        if s.startswith("type=bind,") and ",dst=/vectors," in s:
            argv[i] = f"type=bind,src={out},dst=/vectors,readonly"
        if s.startswith("type=bind,") and s.endswith(",dst=/output"):
            argv[i] = f"type=bind,src={receipt},dst=/output"
        if s.startswith("B_COMPONENT_JOB="):
            argv[i] = "B_COMPONENT_JOB=/vectors/jobs/inline.json"
        if s.startswith("B_COMPONENT_TRUST="):
            argv[i] = "B_COMPONENT_TRUST=/vectors/trust/inline.json"
    proc = subprocess.run(
        argv,
        capture_output=True,
        timeout=30,
        env={
            "PATH": "/usr/bin:/bin",
            "DOCKER_CONFIG": "/tmp/u4-b-issue-edge-build-01/docker-config",
        },
    )
    (receipt / "stdout").write_bytes(proc.stdout)
    (receipt / "stderr").write_bytes(proc.stderr)
    assert proc.returncode == 0, proc.stderr
    raw = (receipt / "result.json").read_bytes()
    r = json.loads(raw)
    row.update(output_sha256=hashlib.sha256(raw).hexdigest(), actual=r["outcome"])
    if r["outcome"] == "success":
        r = r["result"]
        for name, fn in [
            ("structural", lambda r=r: validate_result(r, j)),
            ("independent", lambda r=r: check_v3(v, r, expected)),
        ]:
            try:
                fn()
                row[name] = "pass"
            except Exception as err:
                row[name] = type(err).__name__ + ": " + str(err)
        row["dma"] = [
            {k: x[k] for k in ("request_id", "reservation_ps", "issue_ps", "complete_ps")}
            for x in r["observations"]["dma"]["records"]
        ]
    else:
        row["refusal"] = r
    report["runs"].append(row)
(out / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
