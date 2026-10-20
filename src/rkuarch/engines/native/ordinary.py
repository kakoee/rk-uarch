"""Ordinary installed /4 execution and producer-disabled saved-result replay.

One request per process. No host selectors, approval records or source/build-file reads.
"""

from __future__ import annotations

import argparse
import os
import sys
from importlib.metadata import version
from pathlib import Path
from typing import get_args

from uarch_contract.hashing import canonical_json, strict_json_loads
from uarch_contract.mapped import ProfileEntry, require
from uarch_contract.ordinary import OrdinaryJob, OrdinaryResult, validate_result

from rkuarch.verification.component.observations_v3 import check_v3
from rkuarch.workload.mapped import validate_component_completeness

from .transport import (
    REFUSAL_CODES,
    Limits,
    NativeRefusal,
    OperationalFailure,
    ProtocolViolation,
    _decode_envelope,
    _exchange,
)

CODES = (
    REFUSAL_CODES
    | frozenset(get_args(ProfileEntry.model_fields["expected_outcome"].annotation))
    | {"InvalidBank", "InvalidPreparedGraph", "UnexpectedClosure", "TestOnlyHardware"}
) - {"success"}
DEFAULT_LIMITS = Limits()
UNREPRESENTED = [
    "diagnostics/dram_row_hit_ratio",
    "diagnostics/energy_pj",
    "diagnostics/noc_max_link_util_ratio",
    "diagnostics/sram_bank_conflict_stall_ratio",
    "diagnostics/vector_util_ratio",
    "ext_counts/noc_flit_hop_count",
    "u_c0_duration_ps",
]


def _read(path: Path, cap: int) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(cap + 1)
    if len(raw) > cap:
        raise OperationalFailure("FileLimit")
    return raw


def load_job(raw: bytes, *, test_only: bool = False) -> OrdinaryJob:
    job = OrdinaryJob.model_validate(strict_json_loads(raw))
    require(
        (job.admission.invocation == "test") == test_only,
        "AdmissionMismatch",
        "explicit test-only invocation must match job",
    )
    require(job.engine.package_version == version("rk-uarch"), "EngineIdentityMismatch")
    validate_component_completeness(job.workload_closure)
    if canonical_json(job).encode() != raw:
        raise ProtocolViolation("canonical saved job required")
    return job


def consume(stdout: bytes, stderr: bytes, status: int, *, job: OrdinaryJob) -> OrdinaryResult:
    # Revalidate mutable nested data before binding output to it.
    job = OrdinaryJob.model_validate(job.model_dump(mode="json"))
    value = _decode_envelope(stdout, stderr, status, codes=CODES)
    if status == 2:
        raise NativeRefusal(value)
    result = validate_result(value, job)
    check_v3(
        job.model_dump(mode="json"),
        result.model_dump(mode="json"),
        {"unrepresented": UNREPRESENTED},
    )
    if canonical_json(result).encode() != stdout:
        raise ProtocolViolation("normalized result changed bytes")
    return result


def run(
    saved: Path, *, executable: Path, test_only: bool = False, limits: Limits = DEFAULT_LIMITS
) -> OrdinaryResult:
    raw = _read(saved, limits.stdin_bytes)
    job = load_job(raw, test_only=test_only)
    # The user selects an ordinary installed executable. No executable digest is needed.
    fd = os.open(executable, os.O_RDONLY)
    try:
        stdout, stderr, status = _exchange(
            fd, raw, limits, protocol="uarch-engine/4", test_only=test_only
        )
    finally:
        os.close(fd)
    return consume(stdout, stderr, status, job=job)


def replay(
    saved: Path, output: Path, *, test_only: bool = False, limits: Limits = DEFAULT_LIMITS
) -> OrdinaryResult:
    job = load_job(_read(saved, limits.stdin_bytes), test_only=test_only)
    return consume(_read(output, limits.stdout_bytes), b"", 0, job=job)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "replay"):
        child = sub.add_parser(command)
        child.add_argument("--job", type=Path, required=True)
        child.add_argument("--output", type=Path, required=True)
        child.add_argument("--test-only", action="store_true")
        if command == "run":
            child.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "run":
            result = run(args.job, executable=args.executable, test_only=args.test_only)
            with args.output.open("xb") as stream:
                stream.write(canonical_json(result).encode())
        else:
            replay(args.job, args.output, test_only=args.test_only)
    except (ValueError, RuntimeError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
