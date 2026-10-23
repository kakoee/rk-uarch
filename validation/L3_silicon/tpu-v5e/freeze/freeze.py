"""Prepare once, freeze simulator predictions, or replay saved bytes without producers.

This is a validation archive utility, not an engine or a measurement kit. Output files
are exclusive-create. A replay imports no workload or mapping producer.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import tempfile
from fractions import Fraction
from pathlib import Path

from uarch_contract.reference_json import canonical_json


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def write_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def archive(out, name, raw):
    packed = gzip.compress(raw, mtime=0)
    write_new(out / name, packed)
    return dict(path=name, sha256=digest(packed), uncompressed_sha256=digest(raw))


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def rational(value):
    f = Fraction(value)
    return dict(numerator=f.numerator, denominator=f.denominator)


def semantic_work(source):
    """Disclosed source-level operation convention, independent of mapped padding.

    FMA = 2; scalar arithmetic/transcendentals = 1; casts, broadcasts, comparisons,
    selects and index operations are separate. Raw INT8 dot work is integer work.
    """
    from uarch_contract.reference_laws import DOTS, expected_primitives

    arithmetic = {
        "add",
        "subtract",
        "multiply",
        "negate",
        "exp",
        "reciprocal",
        "rsqrt",
        "reduction_sum",
    }
    rows = {}
    for op in source["ops"]:
        spec = op["spec"]
        d, kind = spec["dimensions"], spec["operator"]
        matrix = 0
        if kind in DOTS:
            matrix = 2 * d["M"] * d["K"] * d["N"]
        elif kind == "attention_fused":
            pairs = d["S"] * (d["S"] + 1) // 2 if d["S"] == d["T"] else d["S"] * d["T"]
            matrix = 4 * d["B"] * d["Hq"] * pairs * d["D"]
        integer = matrix if kind in DOTS and spec["operands"]["X"]["dtype"] == "int8" else 0
        primitives = expected_primitives(op, source)
        rows[op["id"]] = dict(
            predicted_flops=matrix
            - integer
            + sum(v for k, v in primitives.items() if k in arithmetic),
            predicted_integer_ops=integer,
            useful_matrix_ops=matrix,
            useful_primitives=primitives,
        )
    return rows


def prepare(args):
    from uarch_contract.rotary_v2 import RotaryCoefficients

    from rkuarch.mapping.reference import map_reference
    from rkuarch.workload.reference import nominal_hardware, prepare_job, suite_source

    base = args.source / "validation/L3_silicon/tpu-v5e/u4b"
    rows = json.loads((base / "suite-proposed.json").read_text())["benchmarks"]
    row = next(r for r in rows if r["id"] == args.id)
    coefficients = RotaryCoefficients.model_validate_json(
        gzip.decompress((base / "inputs/rotary-coefficients.json.gz").read_bytes())
    )
    indices = json.loads((base / "inputs/gather-page-indices.json").read_text()).get(args.id)
    src = suite_source(row, coefficients=coefficients, page_indices=indices)
    job = prepare_job(map_reference(src, nominal_hardware(), priming_iterations=1))
    write_new(args.jobs / (args.id + ".json"), canonical_json(job).encode())
    print("prepared", args.id, flush=True)


def predict(args):
    from rkuarch.engines.analytic.reference import resolve_reference
    from rkuarch.engines.native.ordinary import load_job, run

    saved = args.jobs / (args.id + ".json")
    raw = saved.read_bytes()
    job = load_job(raw)
    bundle = job.workload_closure
    result = run(saved, executable=args.executable)
    native_raw = canonical_json(result).encode()
    uc0 = resolve_reference(bundle)
    work = semantic_work(bundle.source.model_dump(mode="json"))
    op_rows = {}
    for key, timing in uc0["ops"].items():
        op_rows[key] = dict(
            **work[key],
            predicted_bytes=timing["operand_hbm_bytes"],
            duration_ps=float(timing["duration_ps"]),
            duration_ps_exact=rational(timing["duration_ps"]),
            compute_ps_exact=rational(timing["compute_ps"]),
            memory_ps_exact=rational(timing["memory_ps"]),
        )
    totals = {
        k: sum(r[k] for r in op_rows.values())
        for k in ("predicted_flops", "predicted_integer_ops", "predicted_bytes")
    }
    modes = {
        name: dict(**totals, duration_ps=float(uc0[field]), duration_ps_exact=rational(uc0[field]))
        for name, field in (("aggregate", "aggregate_ps"), ("per_op", "per_op_ps"))
    }
    base = args.source / "validation/L3_silicon/tpu-v5e"
    suite_bytes = (base / "u4b/suite-proposed.json").read_bytes()
    row = next(r for r in json.loads(suite_bytes)["benchmarks"] if r["id"] == args.id)
    provenance = json.loads(args.environment.read_text())
    provenance["suite_sha256"] = digest(suite_bytes)
    native = dict(
        duration_ps=result.duration_ps,
        duration_s=result.duration_ps / 10**12,
        predicted_flops=totals["predicted_flops"],
        predicted_integer_ops=totals["predicted_integer_ops"],
        predicted_bytes=result.counts.get("hbm_read_bytes", 0)
        + result.counts.get("hbm_write_bytes", 0),
        counts=result.counts,
        per_op_counts=result.per_op_counts,
        consumed_stubs=list(result.consumed_stubs),
        result_hash=result.result_hash,
        diagnostics="complete observations in artifacts.native_output; F3/F6 causal limits apply",
    )
    value = dict(
        format="uarch-tpu-v5e-frozen-prediction/1",
        id=args.id,
        benchmark_class=row["benchmark_class"],
        measurement_unit=row["measurement_unit"],
        benchmark=row,
        mapping_match="compiler-chosen",
        initial_state="steady",
        mapping_policy=bundle.mapping_policy.model_dump(mode="json"),
        run_conditions=dict(
            seed=job.seed,
            priming_iterations=1,
            timed_invocations=1,
            timing=row["timing"],
            state_procedure=row["state_procedure"],
        ),
        compiler_reported=dict(status="not_observed", flops=None, bytes=None),
        spec_hash=bundle.hardware_spec_hash,
        engine=job.engine.model_dump(mode="json"),
        native_level=dict(
            checkpoint="R",
            eligibility="reference_suite",
            composite_ceiling="C1",
            description="native interval model/3; no physical channel, bank or NoC model",
        ),
        calibration="stub",
        error="unknown",
        energy="unverified",
        provenance=provenance,
        prepared_input=dict(
            job_hash=job.job_hash,
            bundle_hash=job.bundle_hash,
            point_hash=job.point_hash,
            source_hash=bundle.source.source_hash,
            producer=bundle.producer.model_dump(mode="json"),
            assumptions_hash=bundle.assumptions_hash,
        ),
        artifacts=dict(
            prepared_job=archive(args.out, f"artifacts/{args.id}.job.json.gz", raw),
            native_output=archive(args.out, f"artifacts/{args.id}.native.json.gz", native_raw),
        ),
        native=native,
        u_c0=dict(
            profile=uc0["profile"], **modes, ops=op_rows, unrepresented=list(uc0["unrepresented"])
        ),
        work_convention="source-level FMA=2, scalar arithmetic/special function=1; "
        "casts, broadcasts, "
        "comparisons/selects/index work excluded; INT8 dot is integer_ops, not FLOPs",
        bytes_convention="native=executed HBM payload read+write; U-C0=logical operand HBM bytes; "
        "local VMEM bytes separate; physical transactions unavailable",
        limitations=list(bundle.assumptions.limitations)
        + [
            "F3 non-HBM arbitration and F6 critical-path causal adjacency incompletely verified",
            "F4 direct oversized /4 error-code difference retained",
            "F5 gather/attention/activation packing serialized through one staging slot",
            "No silicon evidence or error estimate; "
            "compiler correspondence is future measurement work",
        ],
    )
    write_new(args.out / (args.id + ".json"), json_bytes(value))
    print("predicted", args.id, flush=True)


def replay(args):
    from rkuarch.engines.analytic.reference import resolve_reference
    from rkuarch.engines.native.ordinary import load_job, run
    from rkuarch.engines.native.ordinary import replay as replay_native

    p = json.loads(args.prediction.read_text())
    decoded = {}
    for name, ref in p["artifacts"].items():
        packed = (args.prediction.parent / ref["path"]).read_bytes()
        if digest(packed) != ref["sha256"]:
            raise ValueError("archive hash mismatch")
        raw = gzip.decompress(packed)
        if digest(raw) != ref["uncompressed_sha256"]:
            raise ValueError("payload hash mismatch")
        decoded[name] = raw
    with tempfile.TemporaryDirectory(prefix="u5-replay-") as directory:
        saved, output = Path(directory) / "job.json", Path(directory) / "native.json"
        saved.write_bytes(decoded["prepared_job"])
        output.write_bytes(decoded["native_output"])
        result = replay_native(saved, output)
        if (
            result.duration_ps != p["native"]["duration_ps"]
            or result.counts != p["native"]["counts"]
        ):
            raise ValueError("prediction/output mismatch")
        if (
            args.executable
            and canonical_json(run(saved, executable=args.executable)).encode()
            != output.read_bytes()
        ):
            raise ValueError("native execution differs")
        uc0 = resolve_reference(load_job(saved.read_bytes()).workload_closure)
        for mode, key in (("aggregate", "aggregate_ps"), ("per_op", "per_op_ps")):
            if rational(uc0[key]) != p["u_c0"][mode]["duration_ps_exact"]:
                raise ValueError("analytic replay differs")
    print("replayed", p["id"], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("prepare", "predict"):
        cmd = sub.add_parser(mode)
        cmd.add_argument("--source", type=Path, required=True)
        cmd.add_argument("--id", required=True)
        cmd.add_argument("--jobs", type=Path, required=True)
        if mode == "predict":
            cmd.add_argument("--executable", type=Path, required=True)
            cmd.add_argument("--environment", type=Path, required=True)
            cmd.add_argument("--out", type=Path, required=True)
    cmd = sub.add_parser("replay")
    cmd.add_argument("prediction", type=Path)
    cmd.add_argument("--executable", type=Path)
    args = parser.parse_args()
    {"prepare": prepare, "predict": predict, "replay": replay}[args.mode](args)


if __name__ == "__main__":
    main()
