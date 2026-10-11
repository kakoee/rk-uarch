"""Independent normative scalar examples, NOT a numerical analytic-engine kernel.

IEEE packing uses round-to-nearest-even; every FP32 multiply and add is rounded
separately. BF16 ties are explicit integer bit rounding. Input casts are explicit.
"""

from __future__ import annotations

import struct
from fractions import Fraction

import pytest


def fp32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def cast(x, dtype):
    if dtype == "fp16":
        return struct.unpack(">e", struct.pack(">e", x))[0]
    x = fp32(x)
    if dtype == "bf16":
        bits = int.from_bytes(struct.pack(">f", x), "big")
        bits = (bits + 0x7FFF + ((bits >> 16) & 1)) & 0xFFFF0000
        return struct.unpack(">f", bits.to_bytes(4, "big"))[0]
    return x


def rotate(x, cos, sin, r, pairing, dtype):
    y = [cast(v, dtype) for v in x]
    source = list(y)
    for p in range(r // 2):
        a, b = (2 * p, 2 * p + 1) if pairing == "adjacent" else (p, p + r // 2)
        left, right = fp32(source[a]), fp32(source[b])
        c, s = fp32(cos[p]), fp32(sin[p])
        y[a] = cast(fp32(fp32(left * c) - fp32(right * s)), dtype)
        y[b] = cast(fp32(fp32(left * s) + fp32(right * c)), dtype)
    return y


@pytest.mark.parametrize("dtype", ["fp32", "bf16", "fp16"])
def test_pairing_and_partial_tail_literal(dtype):
    assert rotate([1, 2, 3, 4], [0, 1], [1, 0], 4, "adjacent", dtype) == [-2, 1, 3, 4]
    assert rotate([1, 2, 3, 4], [0, 1], [1, 0], 4, "split_halves", dtype) == [-3, 2, 1, 4]
    assert rotate([1, 2, 3, 4], [0], [1], 2, "adjacent", dtype) == [-2, 1, 3, 4]


def test_rne_ties_and_cancellation_not_fma():
    assert fp32(1 + 2**-24) == 1
    assert fp32(1 + 3 * 2**-24) == 1 + 2**-22
    assert cast(1 + 2**-8, "bf16") == 1
    assert cast(1 + 3 * 2**-8, "bf16") == 1 + 2**-6
    assert cast(1 + 2**-11, "fp16") == 1
    assert cast(1 + 3 * 2**-11, "fp16") == 1 + 2**-9
    a, c = 1 + 2**-23, 1 - 2**-23
    assert rotate([a, 1], [c], [1], 2, "adjacent", "fp32")[0] == 0
    exact_fused = Fraction(a) * Fraction(c) - 1
    assert exact_fused == -Fraction(1, 2**46)
    assert fp32(exact_fused) != 0
