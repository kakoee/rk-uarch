"""Prepare exact coefficient/page-index data; no workload execution or timing prediction.

--write creates proposed inputs. --check validates saved data without regenerating it.
The supplied bit table is authoritative; different libm generations need not give identical bits.
"""

import gzip
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def write():
    INPUTS.mkdir(exist_ok=True)
    cos, sin = [], []
    for position in range(2048):
        phases = [position * 10000.0 ** (-2 * j / 128) for j in range(64)]
        cos.append([struct.pack(">f", math.cos(phase)).hex() for phase in phases])
        sin.append([struct.pack(">f", math.sin(phase)).hex() for phase in phases])
    value = {
        "format": "uarch-rotary-coefficients/1",
        "position_count": 2048,
        "rotary_dim": 128,
        "dtype": "fp32",
        "cos_bits": cos,
        "sin_bits": sin,
        "producer": {
            "name": "u4b-explicit-coefficient-input",
            "version": "1",
            # This is the existing coefficient carrier's producer field, not a runtime check.
            "implementation_hash": digest(Path(__file__).read_bytes()),
        },
    }
    value["coefficients_hash"] = digest(canonical(value))
    payload = canonical(value) + b"\n"
    (INPUTS / "rotary-coefficients.json.gz").write_bytes(gzip.compress(payload, mtime=0))
    pages = {}
    for p in (16, 32):
        for length in (2048, 2049):
            count = (length + p - 1) // p
            pages[f"gather-p{p}-c{length}"] = list(reversed(range(count)))
    (INPUTS / "gather-page-indices.json").write_bytes(canonical(pages) + b"\n")


def check():
    value = json.loads(gzip.decompress((INPUTS / "rotary-coefficients.json.gz").read_bytes()))
    assert value["format"] == "uarch-rotary-coefficients/1"
    assert value["coefficients_hash"] == digest(
        canonical({k: v for k, v in value.items() if k != "coefficients_hash"})
    )
    assert (value["position_count"], value["rotary_dim"], value["dtype"]) == (2048, 128, "fp32")
    assert value["cos_bits"][0] == ["3f800000"] * 64
    assert value["sin_bits"][0] == ["00000000"] * 64
    for table in (value["cos_bits"], value["sin_bits"]):
        assert len(table) == 2048
        for row in table:
            assert len(row) == 64
            assert all(len(bits) == 8 and int(bits, 16) & 0x7F800000 != 0x7F800000 for bits in row)
    for c_row, s_row in zip(value["cos_bits"], value["sin_bits"], strict=True):
        for c, s in zip(c_row, s_row, strict=True):
            x = struct.unpack(">f", bytes.fromhex(c))[0]
            y = struct.unpack(">f", bytes.fromhex(s))[0]
            assert abs(x * x + y * y - 1) < 2e-7
    pages = json.loads((INPUTS / "gather-page-indices.json").read_bytes())
    assert len(pages) == 4
    for p in (16, 32):
        for length in (2048, 2049):
            count = (length + p - 1) // p
            assert pages[f"gather-p{p}-c{length}"] == list(range(count - 1, -1, -1))
    print("PASS: saved 2048x64 cos/sin FP32 input and four exact page-index arrays;")
    print("coefficient data identity:", value["coefficients_hash"])


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        write()
    else:
        assert sys.argv[1:] == ["--check"], "use --write or --check"
    check()
