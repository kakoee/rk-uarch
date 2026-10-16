"""Saved-output developer checks; never produces authority or campaign completion."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from parallel_core import Store, digest, require

SMOKE = ["K01", "K02", "K03-owner", "K04", "K05-chain", "K05", "K06-00", "K06-01"]


def selection(plan, profile):
    cases = {c["case_id"]: c for c in plan["case_membership"]}
    require(len(cases) == 133, "exact current corpus required")
    require(profile in ("fast", "regression"), "explicit developer profile")
    names = SMOKE if profile == "fast" else list(cases)
    modes = ["debug"] if profile == "fast" else ["debug", "release"]
    return [(mode, 0, cases[name]) for mode in modes for name in names]


def forbid(*args, **kwargs):
    raise RuntimeError("developer saved checks forbid authority and native execution")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", choices=["fast", "regression"])
    parser.add_argument("--saved", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "new developer output required")
    require(
        not args.output.resolve().is_relative_to(args.saved.resolve()), "preserve saved evidence"
    )
    sys.path.insert(0, "/campaign")
    import entrypoint as base

    started = time.monotonic()
    context = base.common()
    _, plan, _, host, runner, canonical, _, job_model, checker = context
    host.resolve_host = forbid
    runner._exchange = forbid
    subprocess.Popen = forbid
    answers = base.read_json(
        base.ROOT / "docs/reviews/U4-A-K2-construction-v1/corpus/expectations.json"
    )
    work = selection(plan, args.profile)
    samples = []
    # Fail missing coverage before validating any selected result. Never substitute
    # debug bytes for an absent release receipt or reduce the requested selection.
    for mode, repetition, case in work:
        slot = f"{mode}-{repetition}-{case['case_id']}"
        file = args.saved / "calls" / (slot + ".json")
        row = json.loads(file.read_bytes())
        require(
            (row["mode"], row["repetition"], row["case_id"]) == (mode, repetition, case["case_id"]),
            "slot binding",
        )
        require(
            row["executable_hash"]
            == plan["subject"]["executable_byte_hashes"][plan["modes"].index(mode)],
            "saved executable binding",
        )
        streams = []
        for field in ("request", "stdout", "stderr"):
            path = (args.saved / row[field]).resolve()
            require(path.is_relative_to(args.saved.resolve()), "saved stream escape")
            data = path.read_bytes()
            require(digest(data) == row[field + "_hash"], "saved stream drift")
            streams.append(data)
        require(digest(streams[0]) == case["file"]["byte_hash"], "corpus request binding")
        samples.append((slot, case, row, streams, digest(file.read_bytes())))
    setup_seconds = time.monotonic() - started
    checked = []
    for slot, case, row, (request, out, err), row_hash in samples:
        job = job_model.model_validate_json(request)
        value = runner._decode_envelope(out, err, row["status"])
        if row["status"] == 2:
            require(
                case["outcome"] == "TimeOverflow" and value["code"] == "TimeOverflow",
                "wrong refusal",
            )
        else:
            require(case["outcome"] == "success", "expected refusal succeeded")
            result = runner.validate_result(value, job)
            checker(result, job_model.model_validate_json(request), answers[case["case_id"]])
            require(canonical(result).encode() == out, "saved canonical bytes changed")
        checked.append({"slot": slot, "source_row_hash": row_hash, "stdout_hash": digest(out)})
    checks_seconds = time.monotonic() - started - setup_seconds
    base.common()
    origins = {
        name: module.__file__
        for name, module in sys.modules.copy().items()
        if name.startswith(("rkuarch", "uarch_contract")) and getattr(module, "__file__", None)
    }
    args.output.mkdir()
    Store(args.output, 16 * 1024**2).json(
        "developer-" + args.profile + ".json",
        {
            "format": "uarch-k2-saved-developer-check/1",
            "profile": args.profile,
            "scope": (
                "saved response validation and independent expectations; "
                "no host/job admission, fresh execution or qualification"
            ),
            "subject": plan["subject"],
            "checks": checked,
            "native_calls": 0,
            "authority_resolutions": 0,
            "project_origins": origins,
            "complete_campaign": False,
            "setup_seconds": setup_seconds,
            "checks_seconds": checks_seconds,
            "total_seconds": time.monotonic() - started,
        },
    )


if __name__ == "__main__":
    main()
