"""Negative read substitution only; real checks run, no altered authority is admitted."""

import contextlib
import json
from pathlib import Path

from parallel_core import digest, require


def check_bound_reads(host, select, bindings):
    binding = bindings["release"]
    record, root = binding.record, binding.root

    def read(file):
        return json.loads((root / file.path).read_bytes())

    trust = read(record.trust_file)
    build = read(record.build_input_file)
    jobs = read(record.jobs_inventory)
    hardware = next(
        f["path"]
        for f in build["source_files"]
        if f["path"] == "contract/uarch_contract/hardware.py"
    )
    targets = [
        ("HostRecord", binding.selector.record_path, b"{}"),
        ("approval", record.decision.path, b"{}"),
        ("independent-review", record.independent_review.path, b"{}"),
        ("trust", record.trust_file.path, b"{}"),
        ("registry", trust["registry_file"]["path"], b"{}"),
        ("profile", trust["profiles"][0]["file"]["path"], b"{}"),
        ("bound-hardware-source", hardware, b"changed source"),
        ("corpus", record.corpus_inventory.path, b"{}"),
        ("job", jobs["jobs"][0]["file"]["path"], b"{}"),
        (
            "missing-job",
            record.jobs_inventory.path,
            json.dumps({**jobs, "jobs": jobs["jobs"][1:]}).encode(),
        ),
        (
            "extra-job",
            record.jobs_inventory.path,
            json.dumps({**jobs, "jobs": jobs["jobs"] + jobs["jobs"][:1]}).encode(),
        ),
        (
            "cross-mode-receipt",
            record.executables[1].build_receipt.path,
            (root / record.executables[0].build_receipt.path).read_bytes(),
        ),
        (
            "cross-mode-executable",
            record.executables[0].executable.path,
            (root / record.executables[1].executable.path).read_bytes(),
        ),
        ("release-executable", record.executables[1].executable.path, b"changed ELF"),
    ]
    original_open = host._open
    fault = Path("/tmp/B-session-negative-bytes")
    rows = []
    try:
        for label, target, data in targets:
            fault.write_bytes(data)

            @contextlib.contextmanager
            def changed_open(base, relative, target=target):
                # Original path/security checks still execute. Only a negative
                # read receives private altered bytes; the actual digest validator
                # must refuse them against its original captured identity.
                with original_open(base, relative) as fd:
                    if relative == target:
                        with fault.open("rb") as bad:
                            yield bad.fileno()
                    else:
                        yield fd

            host._open = changed_open
            try:
                try:
                    select(mode="debug")
                except host.HostBindingError as error:
                    require(
                        str(error) == "bound file digest mismatch: " + target,
                        "wrong bound-file refusal",
                    )
                    rows.append(
                        {
                            "control": label,
                            "path": target,
                            "fault_hash": digest(data),
                            "type": type(error).__name__,
                            "reason": str(error),
                        }
                    )
                else:
                    raise AssertionError("mutated bound input admitted: " + label)
            finally:
                host._open = original_open
        require(
            select(mode="debug").executable == bindings["debug"].executable,
            "restored actual bound files must pass",
        )
    finally:
        host._open = original_open
        fault.unlink(missing_ok=True)
    require(len(rows) == 14, "complete declared read controls")
    return {
        "negative_controls": rows,
        "restored_positive": True,
        "limitation": (
            "file observations/explicit bound identities, not semantic dependency "
            "or environment completeness; generator artifact currentness is separate"
        ),
    }
