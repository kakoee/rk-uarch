"""One local integration campaign; no device access, predictions, CI or hidden setup.

Use ordinary installed packages via --python; native paths are ordinary executable choices.
The receipt records implementation checks and sizes, never a prediction-duration table.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.abc
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def worker(args):
    from uarch_contract.reference_json import blocks, content_hash

    folder = Path(args.output)
    saved = folder / (args.unit + ".job.json")
    if args.worker == "prepare":
        from uarch_contract.rotary_v2 import RotaryCoefficients

        from rkuarch.mapping.reference import map_reference
        from rkuarch.workload.reference import nominal_hardware, prepare_job, suite_source

        row = next(
            x
            for x in json.loads(Path(args.suite).read_text())["benchmarks"]
            if x["id"] == args.unit
        )
        coefficients = RotaryCoefficients.model_validate_json(
            gzip.decompress(Path(args.coefficients).read_bytes())
        )
        page_indices = None
        if row["benchmark_class"] == "DRAM gather":
            supplied = json.loads(
                Path(args.coefficients).with_name("gather-page-indices.json").read_text()
            )
            page_indices = supplied[row["id"]]
        job = prepare_job(
            map_reference(
                suite_source(row, coefficients=coefficients, page_indices=page_indices),
                nominal_hardware(),
            )
        )
        with saved.open("wb") as stream:
            for block in blocks(job):
                stream.write(block)
        from math import ceil

        from rkuarch.engines.analytic.reference import resolve_reference

        baseline = resolve_reference(job.workload_closure)
        (folder / (args.unit + ".bounds.json")).write_text(
            json.dumps({key: ceil(baseline[key]) for key in ("aggregate_ps", "per_op_ps")})
        )

        print(
            json.dumps(
                dict(
                    tasks=len(job.workload_closure.points[0].task_graph.jobs),
                    input_bytes=saved.stat().st_size,
                )
            ),
            flush=True,
        )
    elif args.worker == "prime":
        data = json.loads(saved.read_bytes())
        bundle = data["workload_closure"]
        point = bundle["points"][0]
        point["priming_iterations"] = 2
        point["payload_hash"] = content_hash(point, exclude=("payload_hash",))
        bundle["bundle_hash"] = content_hash(bundle, exclude=("bundle_hash",))
        data["point_hash"] = point["payload_hash"]
        data["bundle_hash"] = bundle["bundle_hash"]
        data["job_hash"] = content_hash(data, exclude=("job_hash",))
        with (folder / (args.unit + ".prime.json")).open("wb") as stream:
            for block in blocks(data):
                stream.write(block)
        (folder / (args.unit + ".prime-bindings.json")).write_text(
            json.dumps({key: data[key] for key in ("job_hash", "point_hash", "bundle_hash")})
        )

    else:

        class NoProducer(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname.startswith(
                    (
                        "rkuarch.mapping",
                        "rkuarch.workload.reference",
                        "rkuarch.workload.producer",
                        "rkuarch.workload.prepared",
                        "rkuarch.workload.capacity",
                    )
                ):
                    raise ImportError("producer disabled: " + fullname)

        sys.meta_path.insert(0, NoProducer())
        from rkuarch.engines.native.ordinary import replay

        job = saved if args.worker == "check" else folder / (args.unit + ".prime.json")
        output = folder / (
            args.unit + (".result.json" if args.worker == "check" else ".prime-result.json")
        )
        excluded = ("result_hash", "job_hash", "point_hash", "bundle_hash")
        name = folder / (args.unit + ".convergence.json")
        if args.worker == "check":
            result = replay(job, output)
            assert result.observations.priming_iterations == 1
            normalized = result.model_copy(
                update={
                    "observations": result.observations.model_copy(update={"priming_iterations": 0})
                }
            )
            name.write_text(content_hash(normalized, exclude=excluded))
            bounds = json.loads((folder / (args.unit + ".bounds.json")).read_text())
            record = dict(
                status="checked",
                activities=len(result.observations.activities),
                output_bytes=output.stat().st_size,
                analytic_comparison={
                    key: result.duration_ps >= value for key, value in bounds.items()
                },
            )
        else:
            from uarch_contract.hashing import strict_json_loads
            from uarch_contract.reference_json import verify_identity

            result = strict_json_loads(output.read_bytes())
            verify_identity(result, "result_hash")
            expected = json.loads((folder / (args.unit + ".prime-bindings.json")).read_text())
            assert all(result[key] == value for key, value in expected.items()), (
                "prime-result bindings"
            )
            assert result["observations"]["priming_iterations"] == 2
            result["observations"]["priming_iterations"] = 0
            # Exact equality of ALL remaining result content reuses the first result's
            # schema/local-law checks; only input identities and prime count may differ.
            assert content_hash(result, exclude=excluded) == name.read_text(), (
                "priming observation mismatch"
            )
            name.unlink()
            record = dict(status="checked", all_observations_equal=True)
        print(json.dumps(record), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--suite", required=True)
    p.add_argument("--coefficients", required=True)
    p.add_argument("--debug")
    p.add_argument("--release")
    p.add_argument("--output", required=True)
    p.add_argument("--python", default=sys.executable)
    p.add_argument("--ids", nargs="*")
    p.add_argument("--worker", choices=("prepare", "prime", "check", "check-prime"))
    p.add_argument("--unit")
    args = p.parse_args()
    if args.worker:
        from runtime_profile import profile_worker

        profile_worker(args, worker)
        return
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    rows = json.loads(Path(args.suite).read_text())["benchmarks"]
    assert len(rows) == 52 and len({r["benchmark_class"] for r in rows}) == 6
    if args.ids:
        rows = [r for r in rows if r["id"] in args.ids]
        assert len(rows) == len(args.ids)
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    # A caller may deliberately select source tools for development; final evidence
    # supplies a noneditable installed interpreter with no source-tree import path.
    def call(mode, unit):
        command = [
            args.python,
            str(Path(__file__).resolve()),
            "--worker",
            mode,
            "--unit",
            unit,
            "--suite",
            args.suite,
            "--coefficients",
            args.coefficients,
            "--output",
            str(out),
        ]
        done = subprocess.run(
            command, env=env, cwd=out, capture_output=True, text=True, timeout=2400
        )
        (out / (unit + "." + mode + ".log")).write_text(done.stdout + done.stderr)
        assert done.returncode == 0, (unit, mode, done.stderr[-2000:])
        return json.loads(done.stdout.splitlines()[-1]) if done.stdout.strip() else {}

    def native(binary, saved, result):
        start = time.perf_counter()
        with saved.open("rb") as source, result.open("wb") as target:
            done = subprocess.run(
                [binary, "--protocol", "uarch-engine/5"],
                stdin=source,
                stdout=target,
                stderr=subprocess.PIPE,
                timeout=600,
                env=env,
                cwd=out,
            )
        assert done.returncode == 0, (saved.name, done.returncode, done.stderr[:2000])
        with (out / "native-timings.jsonl").open("a") as stream:
            stream.write(
                json.dumps(
                    dict(
                        input=saved.name,
                        output=result.name,
                        executable=str(binary),
                        wall_s=time.perf_counter() - start,
                        kind="measured_wall_seconds",
                        scope="process: admission, execution and output serialization",
                    )
                )
                + "\n"
            )

    for row in rows:
        unit = row["id"]
        record = dict(id=unit, benchmark_class=row["benchmark_class"], status="running")
        print(json.dumps(record), flush=True)
        record.update(call("prepare", unit))
        saved = out / (unit + ".job.json")
        result = out / (unit + ".result.json")
        extra = out / (unit + ".repeat.json")
        native(args.release, saved, result)
        expected = digest(result)
        for binary in (args.release, args.release, args.debug):
            native(binary, saved, extra)
            assert digest(extra) == expected, "fresh-process/debug-release mismatch"
        extra.unlink()
        record.update(call("check", unit))
        call("prime", unit)
        native(args.release, out / (unit + ".prime.json"), out / (unit + ".prime-result.json"))
        call("check-prime", unit)
        record.update(
            status="passed",
            fresh_process_runs=3,
            debug_release_equal=True,
            producer_disabled_replay=True,
            analytic_comparison_recorded=True,
            priming_1_2_equal=True,
            job_sha256=digest(saved),
            result_sha256=expected,
        )
        with (out / "receipt.jsonl").open("a") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
        # Keep hashes/receipts; release large nominal outputs after all checks.
        for suffix in (".job.json", ".result.json", ".prime.json", ".prime-result.json"):
            (out / (unit + suffix)).unlink()
        print(json.dumps(record), flush=True)
    (out / "complete.json").write_text(
        json.dumps(
            dict(status="passed", units=len(rows), scope="all52" if len(rows) == 52 else "focused"),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
