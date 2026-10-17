"""One native admission guard fault in an isolated export, with exact restoration."""

import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GUARD = b"""                // /2 uses one request inventory for DMA fragments and unicasts.
                require(
                    request_ids.insert(id),
                    "InvalidTransfer",
                    "duplicate request",
                )?;
"""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("build", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(Path("/tmp"))
    out.mkdir(exist_ok=False)
    meta = json.loads((args.build / "build.json").read_text())
    for name in ("source", "cache", "controls", "diagnostics"):
        shutil.copytree(args.build / name, out / name, symlinks=True)
    for name in ("receipts", "canary", "docker-config", "output"):
        (out / name).mkdir()
    for path, digest in meta["private_postimages"].items():
        assert sha((out / "source" / path).read_bytes()) == digest
    monitor_path = ROOT / "docs/reviews/U4-B-K2-construction-audit-v1/trace_monitor.py"
    spec = importlib.util.spec_from_file_location("approved_monitor", monitor_path)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    path = out / "source/native/crates/uarch-engine/src/component_admission.rs"
    before = path.read_bytes()
    assert before.count(GUARD) == 1
    changed = before.replace(GUARD, b"")
    report = dict(
        source_commit=meta["source_commit"],
        synthetic_unit_anchors=True,
        preimage_sha256=sha(before),
        mutant_sha256=sha(changed),
        recipe_sha256=sha(Path(__file__).read_bytes()),
        monitor_sha256=sha(monitor_path.read_bytes()),
        observations=[],
    )
    # One filter selects exactly the negative and its distinct-identity valid control.
    # The shared substring is 'request_identity'.
    command = [
        monitor.TOOL + "cargo",
        "test",
        "--offline",
        "--locked",
        "-p",
        "uarch-engine",
        "--lib",
        "request_identity",
        "--",
        "--nocapture",
    ]
    try:
        path.write_bytes(changed)
        result = monitor.run(out, "removed", command, build=True)
        stdout = (out / "receipts/removed/stdout").read_text()
        assert result["exit_code"] != 0 and result["stop_reason"] is None
        assert (
            "synthetic_distinct_transport_request_identity_restores_complete_inventory ... ok"
            in stdout
        )
        stderr = (out / "receipts/removed/stderr").read_text()
        assert "called `Result::unwrap_err()` on an `Ok` value" in stderr
        report["observations"].append(
            dict(
                stage="removed",
                receipt=result,
                classification="unsafe Rust admission; valid distinct-identity execution still passes",  # noqa: E501
            )
        )
    finally:
        path.write_bytes(before)
        report["exact_restoration"] = path.read_bytes() == before
        (out / "fault.json").write_text(json.dumps(report, indent=2) + "\n")
    result = monitor.run(out, "restored", command, build=True)
    assert result["exit_code"] == 0 and result["stop_reason"] is None
    report["observations"].append(
        dict(
            stage="restored",
            receipt=result,
            classification="both relevant controls pass after exact source restoration",
        )
    )
    assert all(
        sha((out / "source" / p).read_bytes()) == h for p, h in meta["private_postimages"].items()
    )
    report["all_source_postimages_restored"] = True
    (out / "fault.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        "unsafe admission distinguished; valid control passes; exact restoration and two controls pass"  # noqa: E501
    )


if __name__ == "__main__":
    main()
