"""Sequential, guarded U5 archive recovery; developer telemetry is not chip timing.

The historical freeze.py is preserved byte-for-byte. Workers retain the installed
ordinary loader/transport and every consumer check,
with result validation and independent checking in separate workers.
Only wrapper lifetimes and archive serialization differ. No model changes.
"""

from __future__ import annotations

import argparse
import gc
import gzip
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import freeze

MIB = 1024**2
GIB = 1024**3


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(MIB):
            h.update(block)
    return "sha256:" + h.hexdigest()


def memory():
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        if key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            values[key] = int(value.split()[0]) * 1024
    values["swap_used_bytes"] = values["SwapTotal"] - values["SwapFree"]
    return values


def record(args, event, **fields):
    row = dict(
        case=args.id,
        event=event,
        timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **fields,
    )
    args.journal.parent.mkdir(parents=True, exist_ok=True)
    with args.journal.open("a") as stream:
        stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def timed(args, phase, *, includes=None):
    start = time.monotonic()
    record(args, "stage_start", phase=phase, includes=includes or [])
    try:
        yield
    except BaseException as error:
        record(
            args,
            "stage_end",
            phase=phase,
            status="failure",
            wall_s=time.monotonic() - start,
            error=str(error),
        )
        raise
    else:
        record(
            args,
            "stage_end",
            phase=phase,
            status="complete",
            wall_s=time.monotonic() - start,
            python_process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            rss_scope="worker lifetime high-water mark, not a separate per-stage peak",
        )


def save(path, value):
    freeze.write_new(path, freeze.json_bytes(value))


def stream_json(args, path, value, phase):
    from uarch_contract.reference_json import blocks

    with timed(args, phase):
        with path.open("xb") as stream:
            for block in blocks(value):
                stream.write(block)
            stream.flush()
            os.fsync(stream.fileno())


def mapping(args):
    from uarch_contract.rotary_v2 import RotaryCoefficients

    from rkuarch.mapping.reference import map_reference
    from rkuarch.workload.reference import nominal_hardware, suite_source

    with timed(args, "mapping", includes=["source construction", "mapping", "bundle validation"]):
        base = args.source / "validation/L3_silicon/tpu-v5e/u4b"
        rows = json.loads((base / "suite-proposed.json").read_text())["benchmarks"]
        row = next(r for r in rows if r["id"] == args.id)
        coefficients = RotaryCoefficients.model_validate_json(
            gzip.decompress((base / "inputs/rotary-coefficients.json.gz").read_bytes())
        )
        indices = json.loads((base / "inputs/gather-page-indices.json").read_text()).get(args.id)
        source = suite_source(row, coefficients=coefficients, page_indices=indices)
        bundle = map_reference(source, nominal_hardware(), priming_iterations=1)
        del source, coefficients, indices
    stream_json(args, args.case / "bundle.json", bundle, "bundle_serialization")


def prepare(args):
    # Same statements/validators as installed prepare_job at the recorded source
    # commit, with the mapped bundle persisted between processes and released
    # before the final ReferenceJob validation. No input semantics are changed.
    from importlib.metadata import version

    from uarch_contract.hashing import strict_json_loads
    from uarch_contract.reference import ReferenceBundle, ReferenceJob

    from rkuarch.workload.reference import sealed

    with timed(
        args, "preparation", includes=["bundle revalidation", "job construction and validation"]
    ):
        bundle = ReferenceBundle.model_validate(
            strict_json_loads((args.case / "bundle.json").read_bytes())
        )
        raw = dict(
            protocol="uarch-engine/5",
            bundle_hash=bundle.bundle_hash,
            point_hash=bundle.points[0].payload_hash,
            engine=dict(
                name="native",
                version="native-stage/3",
                package_version=version("rk-uarch"),
                model=dict(name="native-intervals", version="3"),
            ),
            workload_closure=bundle.model_dump(mode="json"),
            admission=bundle.admission.model_dump(mode="json"),
            seed=0,
        )
        del bundle
        gc.collect()
        job = ReferenceJob.model_validate(sealed(raw, "job_hash"))
        del raw
    stream_json(args, args.case / "job.json", job, "input_serialization")


def validate_input(args):
    from uarch_contract.reference import ReferenceJob

    from rkuarch.engines.native.ordinary import REFERENCE_LIMITS, _read, load_job

    with timed(
        args, "input_validation", includes=["canonical check", "schema and admission validation"]
    ):
        job = load_job(_read(args.case / "job.json", REFERENCE_LIMITS.stdin_bytes))
    with timed(
        args, "job_revalidation", includes=["same mutable-job revalidation as consume_reference"]
    ):
        value = job.model_dump(mode="json")
        del job
        gc.collect()
        job = ReferenceJob.model_validate(value)
        del value
    bundle = job.workload_closure
    save(
        args.case / "job-summary.json",
        dict(
            binding={k: getattr(job, k) for k in ("job_hash", "bundle_hash", "point_hash")},
            protocol=job.protocol,
            engine=job.engine.model_dump(mode="json"),
            mapping_policy=bundle.mapping_policy.model_dump(mode="json"),
            seed=job.seed,
            spec_hash=bundle.hardware_spec_hash,
            prepared_input=dict(
                job_hash=job.job_hash,
                bundle_hash=job.bundle_hash,
                point_hash=job.point_hash,
                source_hash=bundle.source.source_hash,
                producer=bundle.producer.model_dump(mode="json"),
                assumptions_hash=bundle.assumptions_hash,
            ),
            limitations=list(bundle.assumptions.limitations),
        ),
    )


def native(args):
    from rkuarch.engines.native.ordinary import REFERENCE_LIMITS, _read
    from rkuarch.engines.native.transport import _exchange

    meta = json.loads((args.case / "job-summary.json").read_text())
    raw = _read(args.case / "job.json", REFERENCE_LIMITS.stdin_bytes)
    with timed(
        args,
        "native_invocation",
        includes=["bounded transport", "native process startup and execution"],
    ):
        fd = os.open(args.executable, os.O_RDONLY)
        try:
            stdout, stderr, status = _exchange(
                fd, raw, REFERENCE_LIMITS, protocol=meta["protocol"], test_only=False
            )
        finally:
            os.close(fd)
            record(
                args,
                "native_rss",
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * 1024,
                scope="sole native child of this fresh worker; Linux wait rusage",
            )
    del raw
    with timed(args, "native_output_persistence"):
        for name, data in (("native.json", stdout), ("native.stderr", stderr)):
            with (args.case / name).open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        save(args.case / "native-status.json", dict(status=status))
    record(
        args,
        "raw_sizes",
        input_bytes=(args.case / "job.json").stat().st_size,
        output_bytes=len(stdout),
        stderr_bytes=len(stderr),
    )


def validate_output(args):
    from uarch_contract.mapped import require
    from uarch_contract.reference import ReferenceResult
    from uarch_contract.reference_json import blocks

    from rkuarch.engines.native.ordinary import CODES, REFERENCE_LIMITS, _read
    from rkuarch.engines.native.transport import NativeRefusal, ProtocolViolation, _decode_envelope

    meta = json.loads((args.case / "job-summary.json").read_text())
    status = json.loads((args.case / "native-status.json").read_text())["status"]
    with timed(
        args, "output_validation", includes=["envelope", "result schema", "identity binding"]
    ):
        stdout = _read(args.case / "native.json", REFERENCE_LIMITS.stdout_bytes)
        stderr = _read(args.case / "native.stderr", REFERENCE_LIMITS.stderr_bytes)
        value = _decode_envelope(stdout, stderr, status, codes=CODES)
        del stdout, stderr
        if status == 2:
            raise NativeRefusal(value)
        result = ReferenceResult.model_validate(value)
        del value
        for key, expected in meta["binding"].items():
            require(getattr(result, key) == expected, "ContentHashMismatch", key)
        require(
            result.engine.model_dump(mode="json") == meta["engine"], "ContentHashMismatch", "engine"
        )
    # Same byte equality as canonical_json(result).encode() == stdout, streamed.
    with timed(args, "output_serialization_check"):
        with (args.case / "native.json").open("rb") as stream:
            for block in blocks(result):
                if stream.read(len(block)) != block:
                    raise ProtocolViolation("canonical saved result required")
            if stream.read(1):
                raise ProtocolViolation("canonical saved result required")
    save(
        args.case / "native-summary.json",
        {
            key: getattr(result, key)
            for key in ("duration_ps", "counts", "per_op_counts", "consumed_stubs", "result_hash")
        },
    )


def independent_check(args):
    from uarch_contract.hashing import strict_json_loads

    from rkuarch.engines.native.ordinary import REFERENCE_LIMITS, _read
    from rkuarch.verification.component.reference import check_reference

    with timed(
        args, "independent_check", includes=["saved JSON decoding", "unchanged check_reference"]
    ):
        job = strict_json_loads(_read(args.case / "job.json", REFERENCE_LIMITS.stdin_bytes))
        result = strict_json_loads(_read(args.case / "native.json", REFERENCE_LIMITS.stdout_bytes))
        check_reference(job, result)


class SavedBundle:
    """Supply the validated saved JSON to the resolver's unchanged model validator.

    This adapter replaces a retained model plus its dump with the canonical saved
    dump. resolve_reference still validates the entire ReferenceBundle itself.
    """

    def __init__(self, value):
        self.value = value

    def model_dump(self, *, mode):
        assert mode == "json"
        return self.value


def analytic(args):
    from uarch_contract.hashing import strict_json_loads

    from rkuarch.engines.analytic.reference import resolve_reference
    from rkuarch.engines.native.ordinary import REFERENCE_LIMITS, _read

    with timed(args, "analytic_input_decoding"):
        data = strict_json_loads(_read(args.case / "job.json", REFERENCE_LIMITS.stdin_bytes))
        bundle = data["workload_closure"]
        del data
        meta = json.loads((args.case / "job-summary.json").read_text())
    with timed(
        args,
        "analytic_resolution",
        includes=["resolver bundle validation", "U-C0 calculation", "source work accounting"],
    ):
        uc0 = resolve_reference(SavedBundle(bundle))
        work = freeze.semantic_work(bundle["source"])
        op_rows = {}
        for key, timing in uc0["ops"].items():
            op_rows[key] = dict(
                **work[key],
                predicted_bytes=timing["operand_hbm_bytes"],
                duration_ps=float(timing["duration_ps"]),
                duration_ps_exact=freeze.rational(timing["duration_ps"]),
                compute_ps_exact=freeze.rational(timing["compute_ps"]),
                memory_ps_exact=freeze.rational(timing["memory_ps"]),
            )
        totals = {
            k: sum(r[k] for r in op_rows.values())
            for k in ("predicted_flops", "predicted_integer_ops", "predicted_bytes")
        }
        modes = {
            name: dict(
                **totals,
                duration_ps=float(uc0[field]),
                duration_ps_exact=freeze.rational(uc0[field]),
            )
            for name, field in (("aggregate", "aggregate_ps"), ("per_op", "per_op_ps"))
        }
        save(
            args.case / "analytic-summary.json",
            dict(
                **{
                    k: meta[k]
                    for k in (
                        "mapping_policy",
                        "seed",
                        "spec_hash",
                        "engine",
                        "prepared_input",
                        "limitations",
                    )
                },
                totals=totals,
                u_c0=dict(
                    profile=uc0["profile"],
                    **modes,
                    ops=op_rows,
                    unrepresented=list(uc0["unrepresented"]),
                ),
            ),
        )


def archive(args, path, name):
    target = args.out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with timed(args, "compression_" + path.stem):
        with path.open("rb") as source, target.open("xb") as destination:
            with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as packed:
                while block := source.read(MIB):
                    packed.write(block)
            destination.flush()
            os.fsync(destination.fileno())
    record(
        args,
        "artifact_sizes",
        artifact=name,
        uncompressed_bytes=path.stat().st_size,
        compressed_bytes=target.stat().st_size,
    )
    return dict(path=name, sha256=file_hash(target), uncompressed_sha256=file_hash(path))


def assemble(args):
    a = json.loads((args.case / "analytic-summary.json").read_text())
    n = json.loads((args.case / "native-summary.json").read_text())
    suite_bytes = (
        args.source / "validation/L3_silicon/tpu-v5e/u4b/suite-proposed.json"
    ).read_bytes()
    row = next(r for r in json.loads(suite_bytes)["benchmarks"] if r["id"] == args.id)
    provenance = json.loads(args.environment.read_text())
    provenance["suite_sha256"] = freeze.digest(suite_bytes)
    if (args.case / "reused-input.json").exists():
        provenance["reused_prepared_input"] = json.loads(
            (args.case / "reused-input.json").read_text()
        )
    provenance["generator_sha256"] = file_hash(Path(__file__))
    provenance["generator_helper_sha256"] = file_hash(Path(freeze.__file__))
    n.update(
        duration_s=n["duration_ps"] / 10**12,
        predicted_flops=a["totals"]["predicted_flops"],
        predicted_integer_ops=a["totals"]["predicted_integer_ops"],
        predicted_bytes=n["counts"].get("hbm_read_bytes", 0)
        + n["counts"].get("hbm_write_bytes", 0),
        diagnostics="complete observations in artifacts.native_output; F3/F6 causal limits apply",
    )
    artifacts = dict(
        prepared_job=archive(args, args.case / "job.json", f"artifacts/{args.id}.job.json.gz"),
        native_output=archive(
            args, args.case / "native.json", f"artifacts/{args.id}.native.json.gz"
        ),
    )
    value = dict(
        format="uarch-tpu-v5e-frozen-prediction/1",
        id=args.id,
        benchmark_class=row["benchmark_class"],
        measurement_unit=row["measurement_unit"],
        benchmark=row,
        mapping_match="compiler-chosen",
        initial_state="steady",
        mapping_policy=a["mapping_policy"],
        run_conditions=dict(
            seed=a["seed"],
            priming_iterations=1,
            timed_invocations=1,
            timing=row["timing"],
            state_procedure=row["state_procedure"],
        ),
        compiler_reported=dict(status="not_observed", flops=None, bytes=None),
        spec_hash=a["spec_hash"],
        engine=a["engine"],
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
        prepared_input=a["prepared_input"],
        artifacts=artifacts,
        native=n,
        u_c0=a["u_c0"],
        work_convention="source-level FMA=2, scalar arithmetic/special function=1; casts, "
        "broadcasts, comparisons/selects/index work excluded; INT8 dot is integer_ops, not FLOPs",
        bytes_convention="native=executed HBM payload read+write; U-C0=logical operand HBM "
        "bytes; local VMEM bytes separate; physical transactions unavailable",
        limitations=a["limitations"]
        + [
            "F3 non-HBM arbitration and F6 critical-path causal adjacency incompletely verified",
            "F4 direct oversized /4 error-code difference retained",
            "F5 gather/attention/activation packing serialized through one staging slot",
            "No silicon evidence or error estimate; compiler correspondence "
            "is future measurement work",
        ],
    )
    with timed(args, "summary_serialization"):
        save(args.out / (args.id + ".json"), value)


def tree_rss(root):
    """Approximate sum: shared pages may be counted more than once."""
    pending, found, rss = [root], [], 0
    while pending:
        pid = pending.pop()
        try:
            status = Path(f"/proc/{pid}/status").read_text()
            for line in status.splitlines():
                if line.startswith("VmRSS:"):
                    rss += int(line.split()[1]) * 1024
            pending.extend(
                int(p) for p in Path(f"/proc/{pid}/task/{pid}/children").read_text().split()
            )
            found.append(pid)
        except (FileNotFoundError, ProcessLookupError):
            pass
    return rss, found


def stop_tree(pid):
    _, children = tree_rss(pid)
    # Native transport starts a separate session; enumerate descendants, not only PGID.
    for child in reversed(children):
        try:
            os.kill(child, signal.SIGKILL)
        except ProcessLookupError:
            pass


def supervise(args, phase):
    command = [sys.executable, str(Path(__file__).resolve()), "worker", "--phase", phase]
    for key in ("source", "id", "work", "out", "environment", "executable", "journal"):
        command += ["--" + key, str(getattr(args, key))]
    start = time.monotonic()
    peak = 0
    record(
        args,
        "worker_start",
        phase=phase,
        memory=memory(),
        wall_scope="inclusive worker lifetime; stage timings are nested, do not add to this",
    )
    with (args.case / (phase + ".log")).open("xb") as log:
        child = subprocess.Popen(
            command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
        )
        try:
            while True:
                rss, _ = tree_rss(child.pid)
                peak = max(peak, rss)
                mem = memory()
                record(
                    args,
                    "memory_sample",
                    phase=phase,
                    combined_rss_bytes_approx=rss,
                    memory=mem,
                    caveat="sum of active worker process tree RSS; shared pages may be "
                    "counted more than once; 1 s sampling",
                )
                pid, status, usage = os.wait4(child.pid, os.WNOHANG)
                if pid:
                    child.returncode = os.waitstatus_to_exitcode(status)
                    break
                if mem["MemAvailable"] < 2 * GIB or mem["swap_used_bytes"] > GIB:
                    raise RuntimeError(
                        "resource guard: MemAvailable below 2 GiB or swap use above 1 "
                        "GiB; no automatic retry"
                    )
                time.sleep(1)
        except BaseException as error:
            stop_tree(child.pid)
            child.wait()
            record(
                args,
                "worker_end",
                phase=phase,
                status="interrupted",
                reason=str(error),
                wall_s=time.monotonic() - start,
                combined_peak_rss_bytes_approx=peak,
                memory=memory(),
            )
            raise
    record(
        args,
        "worker_end",
        phase=phase,
        status="complete" if child.returncode == 0 else "failure",
        exit_status=child.returncode,
        wall_s=time.monotonic() - start,
        worker_wait4_peak_rss_bytes=usage.ru_maxrss * 1024,
        combined_peak_rss_bytes_approx=peak,
        memory=memory(),
        rss_scope="wait4 worker rusage may include reaped child high-water marks; "
        "stage_end SELF reports Python separately",
    )
    if child.returncode:
        raise RuntimeError(f"{phase} failed: see {args.case / (phase + '.log')}")


def run_case(args):
    args.case.mkdir(parents=True, exist_ok=True)
    if any(args.case.iterdir()):
        raise FileExistsError(
            "work directory is nonempty: inspect partial files; use a new "
            "attempt directory, never silently reuse"
        )
    for path in (
        args.out / (args.id + ".json"),
        args.out / f"artifacts/{args.id}.job.json.gz",
        args.out / f"artifacts/{args.id}.native.json.gz",
    ):
        if path.exists():
            raise FileExistsError(path)
    before = memory()
    record(
        args,
        "case_start",
        memory=before,
        generator_sha256=file_hash(Path(__file__)),
        helper_sha256=file_hash(Path(freeze.__file__)),
        inaccessible_phases={
            "native_internal_validation": "unmeasured",
            "native_serialization": "unmeasured (inside native_invocation)",
        },
    )
    start = time.monotonic()
    try:
        if before["MemAvailable"] < args.min_available_gib * GIB or before["swap_used_bytes"] > GIB:
            raise RuntimeError(
                f"resource preflight: require {args.min_available_gib} GiB "
                "available and at most 1 GiB swap used"
            )
        phases = (
            "mapping",
            "prepare",
            "validate_input",
            "native",
            "validate_output",
            "independent_check",
            "analytic",
            "assemble",
        )
        if args.prepared_job:
            if not args.prepared_job_sha256 or not args.preparation_generator_sha256:
                raise ValueError(
                    "reused job requires its inspected hash and preparation generator hash"
                )
            if file_hash(args.prepared_job) != args.prepared_job_sha256:
                raise ValueError("reused prepared input hash mismatch")
            with timed(args, "saved_input_copy"):
                with (
                    args.prepared_job.open("rb") as source,
                    (args.case / "job.json").open("xb") as target,
                ):
                    while block := source.read(MIB):
                        target.write(block)
                    target.flush()
                    os.fsync(target.fileno())
            save(
                args.case / "reused-input.json",
                dict(
                    path=str(args.prepared_job),
                    sha256=args.prepared_job_sha256,
                    preparation_generator_sha256=args.preparation_generator_sha256,
                ),
            )
            record(
                args,
                "reused_input",
                path=str(args.prepared_job),
                sha256=args.prepared_job_sha256,
                preparation_generator_sha256=args.preparation_generator_sha256,
            )
            phases = phases[2:]
        for phase in phases:
            supervise(args, phase)
        record(
            args,
            "case_end",
            status="complete",
            wall_s=time.monotonic() - start,
            memory=memory(),
            wall_scope="inclusive entire case; do not add nested worker/stage times",
        )
    except BaseException as error:
        record(
            args,
            "case_end",
            status="interrupted" if isinstance(error, KeyboardInterrupt) else "failure",
            error=str(error),
            wall_s=time.monotonic() - start,
            memory=memory(),
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["run", "worker"])
    parser.add_argument(
        "--phase",
        choices=(
            "mapping",
            "prepare",
            "validate_input",
            "native",
            "validate_output",
            "independent_check",
            "analytic",
            "assemble",
        ),
    )
    for key in ("source", "work", "out", "environment", "executable", "journal"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--prepared-job", type=Path)
    parser.add_argument("--prepared-job-sha256")
    parser.add_argument("--preparation-generator-sha256")
    parser.add_argument("--id", required=True)
    parser.add_argument("--min-available-gib", type=float, default=10)
    args = parser.parse_args()
    args.case = args.work / args.id
    if args.mode == "run":
        run_case(args)
    else:
        try:
            globals()[args.phase](args)
        finally:
            record(
                args,
                "python_worker_rss",
                phase=args.phase,
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                scope="Python worker only, excluding native subprocess",
            )


if __name__ == "__main__":
    main()
