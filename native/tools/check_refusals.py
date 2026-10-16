"""Execute only frozen invalid-input controls in the exact offline candidate image.

No valid MappedEngineJob is sent. These observations do not qualify public execution.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_candidate import BIN, base, command, digest, write
from uarch_contract.hashing import canonical_json, sha256, strict_json_loads

from rkuarch.engines.native.records import BuildInputs

# B's published nine explicit byte controls, plus argument and root-type controls.
CASES = (
    ("empty", b"", "InvalidJson"),
    ("invalid-utf8", b"\xff", "InvalidJson"),
    ("truncated", b"{", "InvalidJson"),
    ("duplicate", b'{"protocol":"uarch-engine/3","protocol":"uarch-engine/3"}', "InvalidJson"),
    ("reserved-marker", b'{"$serde_json::private::Number":"1"}', "InvalidJson"),
    ("trailing-object", b"{} {}", "InvalidJson"),
    ("empty-object", b"{}", "UnsupportedProtocol"),
    ("foreign-protocol", b'{"protocol":"foreign"}', "UnsupportedProtocol"),
    ("incomplete-job", b'{"protocol":"uarch-engine/3"}', "UnsupportedCheckpointScope"),
    ("root-array", b"[]", "UnsupportedProtocol"),
    ("wrong-args", b"", "UnsupportedProtocol"),
)


def check(scratch: Path, mode: str) -> None:
    build = BuildInputs.model_validate_json((scratch / "BuildInputs.json").read_bytes())
    binary = scratch / "targets" / mode / mode / "uarch-engine"
    expected = json.loads((scratch / (mode + "-binaries.json")).read_bytes())
    assert digest(binary) == expected["executable_byte_hash"]
    frozen = [{"name": n, "input_hex": b.hex(), "code": c} for n, b, c in CASES]
    write(scratch / (mode + "-refusal-freeze.json"), frozen)
    rows = []
    for name, payload, code in CASES:
        argv = base(scratch, mode, "refusal-" + name, build)
        argv.insert(argv.index("--entrypoint"), "--interactive")
        argv += [f"/target/{mode}/uarch-engine"]
        if name != "wrong-args":
            argv += ["--protocol", "uarch-engine/3"]
        status, stdout, stderr = command(scratch, mode + "-refusal-" + name, argv, stdin=payload)
        value = strict_json_loads(stderr)
        assert status == 2 and stdout == b"", (name, status, stdout, stderr)
        assert set(value) == {"code", "message", "pointer"} and value["code"] == code
        assert isinstance(value["message"], str)
        assert value["pointer"] is None or isinstance(value["pointer"], str)
        assert canonical_json(value).encode() == stderr
        rows.append({"name": name, "code": code, "stderr_byte_hash": sha256(stderr)})
    # Static executable-origin observation; never load an untrusted interpreter.
    status, _, _ = command(
        scratch,
        mode + "-origin",
        base(scratch, mode, "origin", build)
        + ["/usr/bin/readelf", "-h", "-l", "-d", f"/target/{mode}/uarch-engine"],
    )
    assert status == 0
    assert digest(binary) == expected["executable_byte_hash"]
    write(
        scratch / (mode + "-refusals.json"),
        {
            "binary_byte_hash": digest(binary),
            "cases": rows,
            "successful_public_jobs": 0,
            "image_network": "none",
            "cargo_bin": BIN,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=["debug", "release"])
    args = parser.parse_args()
    check(args.scratch, args.mode)
