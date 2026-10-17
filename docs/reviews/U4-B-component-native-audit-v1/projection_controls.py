"""Exact published mixed-request controls for the final one-line observation sort."""

import argparse
import hashlib
import json
import subprocess
import uuid
from copy import deepcopy
from pathlib import Path

from uarch_contract.mapped import MappedEngineJob, validate_result

from validation.component.arithmetic import dma
from validation.component.native_check import CONTRACT
from validation.component.observations_v2 import check_v2

ROOT = Path(__file__).resolve().parents[3]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("build", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prior-unsorted", action="store_true")
    args = parser.parse_args()
    build = args.build.resolve()
    meta = json.loads((build / "build.json").read_text())
    out = args.output.resolve()
    assert out.is_relative_to(Path("/tmp"))
    out.mkdir(exist_ok=False)
    evidence = ROOT / "docs/reviews/U4-A-component-native-v1/evidence/collision"
    baseline = json.loads(Path("/tmp/u4-b-component-native-dev-01/checks.json").read_text())
    rows = []
    assert dma(noc=1_200_000_000)[-1] == 60000
    names = ["distinct"] if args.prior_unsorted else ["distinct", "collision"]
    for name in names:
        job = json.loads((evidence / (name + ".json")).read_text())
        outputs = []
        for mode in ["debug"] if args.prior_unsorted else ["debug", "release"]:
            target = build / (mode + "-target")
            command = meta["commands"][mode]
            binary = target / command["test_executable"]
            assert sha(binary.read_bytes()) == command["test_executable_sha256"]
            for repeat in range(1 if args.prior_unsorted else 3):
                receipt = out / f"{name}-{mode}-{repeat}"
                receipt.mkdir()
                argv = deepcopy(
                    next(r for r in baseline["observations"] if r["mode"] == mode)["argv"]
                )
                container = "u4-b-projection-" + uuid.uuid4().hex
                argv[argv.index("--name") + 1] = container
                for i, value in enumerate(argv):
                    if value.startswith("type=bind,"):
                        if ",dst=/target," in value:
                            argv[i] = f"type=bind,src={target},dst=/target,readonly"
                        elif ",dst=/vectors," in value:
                            argv[i] = f"type=bind,src={evidence},dst=/vectors,readonly"
                        elif ",dst=/output" in value:
                            argv[i] = f"type=bind,src={receipt},dst=/output"
                    elif value.startswith("/target/"):
                        argv[i] = "/target/" + command["test_executable"]
                    elif value.startswith("B_COMPONENT_JOB="):
                        argv[i] = f"B_COMPONENT_JOB=/vectors/{name}.json"
                    elif value.startswith("B_COMPONENT_TRUST="):
                        argv[i] = f"B_COMPONENT_TRUST=/vectors/{name}-trust.json"
                env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": str(build / "docker-config")}
                try:
                    process = subprocess.run(argv, env=env, capture_output=True, timeout=30)
                except subprocess.TimeoutExpired:
                    subprocess.run(
                        argv[:3] + ["kill", container], env=env, capture_output=True, timeout=5
                    )
                    raise
                (receipt / "stdout").write_bytes(process.stdout)
                (receipt / "stderr").write_bytes(process.stderr)
                assert process.returncode == 0
                raw = (receipt / "result.json").read_bytes()
                result = json.loads(raw)
                row = dict(
                    case=name,
                    mode=mode,
                    repeat=repeat,
                    argv=argv,
                    binary_sha256=sha(binary.read_bytes()),
                    job_sha256=sha((evidence / (name + ".json")).read_bytes()),
                    output_sha256=sha(raw),
                )
                if name == "collision":
                    assert result["outcome"] == "refusal" and result["code"] == "InvalidTransfer"
                    row["result"] = "intended Rust InvalidTransfer; no successful execution"
                else:
                    assert result["outcome"] == "success"
                    actual = result["result"]
                    assert actual["duration_ps"] == 60000
                    try:
                        validate_result(actual, MappedEngineJob.model_validate(job))
                        structural = "pass"
                    except ValueError as error:
                        structural = str(error)
                    if args.prior_unsorted:
                        assert (
                            structural == "IncompleteObservations: sorted unique inventory required"
                        )
                        row["result"] = (
                            "native success, real structural validator refuses ordering: "
                            + structural
                        )
                    else:
                        assert structural == "pass", structural
                        check_v2(job, actual, CONTRACT)
                        assert [
                            r["request_id"] for r in actual["observations"]["dma"]["records"]
                        ] == ["r00.00", "synthetic-distinct-fragment"]
                        assert actual["traffic_counts"]["read_payload_bytes"] == 256
                        assert actual["traffic_counts"]["unicast_payload_bytes"] == 256
                        row["result"] = (
                            "real validation and independent /2 check pass; 60000 ps literal"
                        )
                outputs.append(raw)
                rows.append(row)
                (out / "checks.json").write_text(
                    json.dumps(
                        dict(
                            source_commit=meta["source_commit"],
                            recipe_sha256=sha(Path(__file__).read_bytes()),
                            synthetic_unit_anchors=True,
                            prior_unsorted=args.prior_unsorted,
                            observations=rows,
                        ),
                        indent=2,
                    )
                    + "\n"
                )
                print(name, mode, repeat, row["result"], flush=True)
        assert len(set(outputs)) == 1


if __name__ == "__main__":
    main()
