"""Reviewer-prepared /4 inputs (preparation side; reads source fixtures, never runs a mapper).

Usage: RUNTIME_PYTHON -I prepare_inputs.py RECONSTRUCTED_TREE OUT_DIR
* production.json: existing mapped point from contract/fixtures/mapped/component.json,
  assembled through the *installed* rkuarch.workload.ordinary.prepare_bundle/prepare_job.
* test-<name>.json: reviewer's own explicit /3 -> /4 development migration of native
  testdata (test invocation, verification_only), independent of the author's job_data().
"""

import json
import sys
from pathlib import Path

from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, content_hash
from uarch_contract.mapped import MappedAssumptions, MappedPoint
from uarch_contract.ordinary import OrdinaryAdmission, OrdinaryJob, SoftwareProducer
from uarch_contract.prepared import PreparedOp, RankScope

import rkuarch.workload.ordinary as ordinary

root, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
assert not str(Path(ordinary.__file__)).startswith(str(root)), ordinary.__file__

b = json.loads((root / "contract/fixtures/mapped/component.json").read_text())
bundle = ordinary.prepare_bundle(
    [PreparedOp.model_validate(x) for x in b["scope"]["ops"]],
    HardwareSpec.model_validate(b["hardware_spec"]),
    MappedPoint.model_validate(b["points"][0]),
    producer=SoftwareProducer(name="independent-review-prepare", version="1"),
    assumptions=MappedAssumptions.model_validate(b["assumptions"]),
    rank=RankScope.model_validate(b["rank"]),
    admission=OrdinaryAdmission(checkpoint="B", invocation="production", eligibility="component_only"),
    mapping_version=b["mapping_policy"]["version"],
)
job = ordinary.prepare_job(bundle, point_hash=bundle.points[0].payload_hash)
(out / "production.json").write_text(canonical_json(job))
summary = {"production": {"job_hash": job.job_hash, "bundle_hash": job.bundle_hash,
                          "point_hash": job.point_hash, "engine": job.engine.model_dump()}}

TEST_ADMISSION = {"checkpoint": "B", "invocation": "test", "eligibility": "verification_only"}
for name in ("synthetic-runtime-cc0-v3", "synthetic-stage2-cc-v3", "synthetic-stage2-cc0-v3",
             "synthetic-stage2-sr-v3"):
    raw = json.loads((root / f"native/crates/uarch-engine/testdata/{name}.json").read_text())
    del raw["profile"], raw["registry"]
    raw["protocol"] = "uarch-engine/4"
    raw["engine"] = ordinary.software_identity().model_dump(mode="json")
    raw["admission"] = dict(TEST_ADMISSION)
    closure = raw["workload_closure"]
    closure["format"] = "uarch-prepared/4"
    closure["admission"] = dict(TEST_ADMISSION)
    closure["producer"] = {"name": closure["producer"]["name"], "version": closure["producer"]["version"]}
    closure["bundle_hash"] = content_hash(closure, exclude=("bundle_hash",))
    raw["bundle_hash"] = closure["bundle_hash"]
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    parsed = OrdinaryJob.model_validate(raw)
    (out / f"test-{name}.json").write_text(canonical_json(parsed))
    summary[name] = {"job_hash": parsed.job_hash, "scope": closure["scope"]["kind"],
                     "hardware_spec_hash": parsed.hardware_spec_hash,
                     "initial_state": parsed.initial_state}
print(json.dumps(summary, indent=1, sort_keys=True))
