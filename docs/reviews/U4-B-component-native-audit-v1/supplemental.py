"""Independent corrected D13 and exact A issue-gap probes; synthetic private Trust only."""

import argparse
import hashlib
import json
import subprocess
import uuid
from copy import deepcopy
from pathlib import Path

from uarch_contract.hashing import canonical_json
from uarch_contract.mapped import MappedEngineJob

from rkuarch.workload.mapped import validate_component_completeness
from validation.component.join_inputs import reseal
from validation.component.native_check import check_native
from validation.component.native_inputs import policy_item, private_job, prospective_inputs

ROOT = Path(__file__).resolve().parents[3]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("development_run", type=Path)
    parser.add_argument("build", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build = args.build.resolve()
    meta = json.loads((build / "build.json").read_text())
    source = meta["source_commit"]
    out = args.output.resolve()
    assert out.is_relative_to(Path("/tmp"))
    out.mkdir(exist_ok=False)
    (out / "jobs").mkdir()
    (out / "trust").mkdir()
    corpus = prospective_inputs()
    old = corpus["items"]["D13-barrier"]
    b = deepcopy(old["bundle"])
    barrier = next(j for j in b["points"][0]["task_graph"]["jobs"] if j["kind"] == "barrier")
    assert barrier["owner_id"] == 44
    barrier["owner_id"] = 52
    reseal(b)
    item = policy_item(b, old["expected"], "B-native-D13-canonical-owner")
    d13 = private_job(item, corpus["registry"])
    path = "native/crates/uarch-engine/testdata/synthetic-issue-core-gap.json"
    original_gap = subprocess.check_output(["git", "show", source + ":" + path], cwd=ROOT)
    gap = json.loads(original_gap)
    jobs = {"B-native-D13-canonical-owner": d13, "A-issue-core-gap": gap}
    report = dict(
        source_commit=source,
        build_sha256=sha((build / "build.json").read_bytes()),
        recipe_sha256=sha(Path(__file__).read_bytes()),
        original_gap_file_sha256=sha(original_gap),
        historical_D13_unchanged=True,
        corrected_D13_expected=old["expected"],
        observations=[],
        private_synthetic_anchors=True,
        public_calls=0,
    )
    previous = json.loads((args.development_run / "checks.json").read_text())
    for name, job in jobs.items():
        parsed = MappedEngineJob.model_validate(job)
        validate_component_completeness(parsed.workload_closure)
        raw = canonical_json(job).encode()
        (out / "jobs" / (name + ".json")).write_bytes(raw)
        anchor = dict(
            registry=job["registry"]["registry_hash"],
            profile=job["profile"]["profile_hash"],
            case=job["admission"]["case_id"],
            engine=job["engine"],
        )
        (out / "trust" / (name + ".json")).write_text(canonical_json(anchor))
        for mode in ("debug", "release"):
            target = build / (mode + "-target")
            executable = target / meta["commands"][mode]["test_executable"]
            assert sha(executable.read_bytes()) == meta["commands"][mode]["test_executable_sha256"]
            receipt = out / (name + "-" + mode)
            receipt.mkdir()
            baseline = next(
                r for r in previous["observations"] if r["case"] == "D01" and r["mode"] == mode
            )
            argv = deepcopy(baseline["argv"])
            argv[argv.index("--name") + 1] = "u4-b-component-supplement-" + uuid.uuid4().hex
            for i, value in enumerate(argv):
                if value.startswith("type=bind,") and ",dst=/target," in value:
                    argv[i] = f"type=bind,src={target},dst=/target,readonly"
                if value.startswith("/target/"):
                    argv[i] = "/target/" + meta["commands"][mode]["test_executable"]
                if value.startswith("type=bind,") and ",dst=/vectors," in value:
                    argv[i] = f"type=bind,src={out},dst=/vectors,readonly"
                if value.startswith("type=bind,") and value.endswith(",dst=/output"):
                    argv[i] = f"type=bind,src={receipt},dst=/output"
                if value.startswith("B_COMPONENT_JOB="):
                    argv[i] = f"B_COMPONENT_JOB=/vectors/jobs/{name}.json"
                if value.startswith("B_COMPONENT_TRUST="):
                    argv[i] = f"B_COMPONENT_TRUST=/vectors/trust/{name}.json"
            process = subprocess.run(
                argv,
                capture_output=True,
                timeout=30,
                env={
                    "PATH": "/usr/bin:/bin",
                    "DOCKER_CONFIG": str(build / "docker-config"),
                },
            )
            (receipt / "stdout").write_bytes(process.stdout)
            (receipt / "stderr").write_bytes(process.stderr)
            assert process.returncode == 0, process.stderr
            output = (receipt / "result.json").read_bytes()
            result = json.loads(output)
            row = dict(
                case=name,
                mode=mode,
                argv=argv,
                job_hash=job["job_hash"],
                raw_job_sha256=sha(raw),
                binary_sha256=sha(executable.read_bytes()),
                output_sha256=sha(output),
                actual=result["outcome"],
            )
            if name.startswith("B-native-D13"):
                assert result["outcome"] == "success", result
                check_native(job, result["result"], item)
                assert result["result"]["duration_ps"] == 94000
                row["independent_check"] = "pass; unchanged 94000 ps literal"
            else:
                assert (
                    result["outcome"] == "refusal" and result["code"] == "IncompleteObservations"
                ), result
                assert result["message"] == "activity requires actual tight earlier cause"
                row.update(
                    code=result["code"],
                    detail=result["message"],
                    classification=(
                        "admitted input; post-execution observation-construction refusal"
                    ),
                )
            report["observations"].append(row)
            (out / "supplemental.json").write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n"
            )
            print(
                name,
                mode,
                row["actual"],
                row.get("independent_check", row.get("detail")),
                flush=True,
            )


if __name__ == "__main__":
    main()
