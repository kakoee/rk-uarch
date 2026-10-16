"""Independent Python semantics/coverage derivation; no producer imports or Rust edits."""

# ruff: noqa: E402 -- Install explicit private roots before contract imports under -I -S.
import sys
from pathlib import Path

R = Path("/tmp/u4-b-c2-review")
REF = R / "reference"
sys.path[:0] = [
    str(REF / "contract"),
    "/home/jjaff/AI-infra-simulation/rk-uarch/.venv/lib/python3.12/site-packages",
]
import collections
import gzip
import hashlib
import json
import math
import random
import struct
import time
from typing import Annotated

import pydantic
from pydantic import Field, TypeAdapter
from uarch_contract import hashing as h
from uarch_contract import mapped as m
from uarch_contract.common import JsonFloat
from uarch_contract.sourced import SourcedValue

P = R / "subject/docs/reviews/U4-A-K2-C2-probes-v1"
U128 = TypeAdapter(Annotated[int, Field(strict=True, ge=0, lt=2**128)])


def sha(b):
    return hashlib.sha256(b).hexdigest()


def lines(b):
    assert b.endswith(b"\n")
    return [json.loads(x) for x in b[:-1].split(b"\n")]


def expected(row):
    layer = "decode"
    try:
        op = row["op"]
        if op == "sha":
            return {"status": "ok", "sha256": sha(bytes.fromhex(row["hex"]))}
        value = (
            struct.unpack(">d", bytes.fromhex(row["bits"]))[0]
            if op == "float"
            else h.strict_json_loads(bytes.fromhex(row["hex"]))
        )
        layer = "carrier"
        if op == "u128":
            value = U128.validate_python(value)
        if op in ("rational", "leaf", "sourced"):
            cls = {"rational": m.RationalValue, "leaf": m.NumericLeaf, "sourced": SourcedValue}[op]
            value = cls.model_validate(value).model_dump(mode="json")
        if op == "json-float":
            value = TypeAdapter(JsonFloat).validate_python(value)
        if op == "marker":
            # Additional protocol guard, not a Python JSON/parser refusal.
            assert isinstance(value, dict)
            return {"status": "refuse", "layer": "carrier", "error_type": "ValueError"}
        if op == "identity":
            layer = "identity"
            h.verify_identity(value, row["field"])
        if op in ("identity", "exclude"):
            value = {k: v for k, v in value.items() if k != row["field"]}
        layer = "canonical"
        canonical = h.canonical_json(value)
        layer = "utf8"
        data = canonical.encode()
        return {"status": "ok", "canonical": canonical, "sha256": sha(data)}
    except Exception as e:
        return {"status": "refuse", "layer": layer, "error_type": type(e).__name__}


vectors = lines(gzip.decompress((P / "vectors.jsonl.gz").read_bytes()))
assert len(vectors) == 20965 and len({v["id"] for v in vectors}) == 20965
for v in vectors:
    got = expected(v)
    assert all(v["expected"][k] == x for k, x in got.items()), v["id"]
assert [v["expected"]["sha256"] for v in vectors if v["family"] == "SHA-known-answer"] == [
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1",
    "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0",
]
# Derive finite coverage independently from IEEE field widths.
actual = [v["bits"] for v in vectors if v["family"] == "binary-exponent-boundary"]
wanted = [
    f"{b | sign:016x}"
    for e in range(2047)
    for b in sorted({max(0, (e << 52) - 1), e << 52, (e << 52) + 1})
    for sign in (0, 1 << 63)
]
assert actual == wanted and len(actual) == 12280
rng = random.Random(0x5534433250524F42)
sweep = []
seen = set()
discarded = 0
while len(sweep) < 4096:
    b = rng.getrandbits(64)
    if b in seen or (b >> 52) & 2047 == 2047:
        discarded += 1
        continue
    seen.add(b)
    sweep.append(f"{b:016x}")
assert sweep == [v["bits"] for v in vectors if v["family"] == "finite-sweep"]
decimal = []
for exponent in range(-324, 309):
    x = float(f"1e{exponent}")
    for f in (math.nextafter(x, -math.inf), x, math.nextafter(x, math.inf)):
        if math.isfinite(f):
            decimal += [struct.pack(">d", y).hex() for y in (f, -f)]
assert decimal == [v["bits"] for v in vectors if v["family"] == "decimal-exponent-boundary"]
# Rejoin all installed fixture bytes to their actual Python normalized carriers.
for v in vectors:
    if v["family"] not in ("installed-M", "B113"):
        continue
    path = REF / v["source_path"]
    assert sha(path.read_bytes()) == v["source_sha256"]
    cls = getattr(m, v["reference_carrier"])
    norm = cls.model_validate(h.strict_json_loads(path.read_bytes())).model_dump(mode="json")
    assert h.canonical_json(norm) == v["expected"]["canonical"]
# Rejoin each of the 488 identity subobjects to its actual normalized fixture pointer.
normalized_by_path = {}
for v in vectors:
    if v["family"] in ("installed-M", "B113"):
        normalized_by_path[v["source_path"]] = (
            getattr(m, v["reference_carrier"])
            .model_validate(h.strict_json_loads((REF / v["source_path"]).read_bytes()))
            .model_dump(mode="json")
        )
for v in vectors:
    if v["family"] != "fixture-identities":
        continue
    value = normalized_by_path[v["source_path"]]
    for token in v["pointer"].split("/")[1:]:
        value = value[int(token)] if isinstance(value, list) else value[token]
    assert value == h.strict_json_loads(bytes.fromhex(v["hex"]))
supplement = lines(gzip.decompress((P / "identity-supplement.jsonl.gz").read_bytes()))
for v in supplement:
    path = REF / v["source_path"]
    assert sha(path.read_bytes()) == v["source_sha256"]
    norm = (
        getattr(m, v["reference_carrier"])
        .model_validate(h.strict_json_loads(path.read_bytes()))
        .model_dump(mode="json")
    )
    assert h.canonical_json(norm).encode() == bytes.fromhex(v["hex"])
    assert expected(v) == v["expected"]
# B-only prospective discriminators; frozen separately, never inserted into A's corpus.
extra = []


def case(name, op, text):
    row = {
        "id": "B:" + name,
        "family": "B-field-discriminator",
        "op": op,
        "hex": text.encode().hex(),
    }
    row["expected"] = expected(row)
    extra.append(row)


for text in [
    '{"numerator":1,"denominator":2}',
    '{"numerator":0,"denominator":2}',
    '{"numerator":2,"denominator":4}',
    '{"numerator":-0,"denominator":1}',
    '{"numerator":-0.0,"denominator":1}',
    '{"numerator":1,"denominator":0}',
    '{"numerator":1,"denominator":340282366920938463463374607431768211455}',
    '{"numerator":340282366920938463463374607431768211456,"denominator":1}',
    '{"numerator":1,"denominator":1,"denominator":1}',
    '{"numerator":1,"denominator":1,"extra":0}',
    '{"numerator":true,"denominator":1}',
    '{"numerator":"1","denominator":1}',
    '{"numerator":1e0,"denominator":1}',
]:
    case(f"ratio-{len(extra)}", "rational", text)
    case(f"ratio-union-{len(extra)}", "leaf", '{"path":"test","value":' + text + "}")
for text in [
    "0",
    "-1",
    "340282366920938463463374607431768211456",
    "-170141183460469231731687303715884105729",
    "true",
    '"1"',
    "null",
    "1.0",
]:
    case(f"leaf-scalar-{len(extra)}", "leaf", '{"path":"test","value":' + text + "}")
for token in ["false", '" 1.0 "', '"1e0"', '"1_0"', '"NaN"', '"Infinity"', "null", "{}"]:
    case(
        f"legacy-{len(extra)}",
        "sourced",
        '{"value":' + token + ',"unit":"Hz","kind":"stipulation","rationale":"B test only"}',
    )
for token in ["true", '"1.0"', "-0.0", "1e0", "340282366920938463463374607431768211456"]:
    case(f"strict-int-{len(extra)}", "u128", token)
for token in ["true", '"1.0"', "1.0"]:
    case(f"json-float-{len(extra)}", "json-float", token)
for text in [
    '{"$serde_json::private::Number":"1"}',
    '{"x":{"\\u0024serde_json::private::Number":"1"}}',
]:
    case(f"marker-{len(extra)}", "marker", text)
origins = {}
freeze = json.loads((P / "freeze.json").read_bytes())
for name, module in sys.modules.copy().items():
    if name.startswith("uarch_contract"):
        file = Path(module.__file__).resolve()
        assert file.is_relative_to(REF / "contract")
        assert sha(file.read_bytes()) == freeze["reference"]["import_origins"][name]["sha256"]
        origins[name] = {"path": str(file), "sha256": sha(file.read_bytes())}
assert not any(name == "rk" or name.startswith(("rk.", "rkuarch")) for name in sys.modules)
assert pydantic.__version__ == freeze["reference"]["pydantic"]
assert sha(Path(sys.executable).resolve().read_bytes()) == freeze["reference"]["executable_sha256"]
(R / "output/B-expectations.json").write_text(json.dumps(extra, indent=2) + "\n")
record = {
    "reference_source": "ce732f5bedccdde629edcf278fa76ea772d0ea82",
    "python": sys.version,
    "python_realpath": str(Path(sys.executable).resolve()),
    "pydantic": pydantic.__version__,
    "module_origins": origins,
    "original_expected_rows_rederived": len(vectors),
    "original_families": dict(collections.Counter(v["family"] for v in vectors)),
    "supplement_rederived": len(supplement),
    "finite_sweep_discarded": discarded,
    "counterexamples_rederived": json.loads((P / "counterexample-inputs.json").read_bytes()),
    "B_prospective_discriminators": len(extra),
    "B_expectations_sha256": sha((R / "output/B-expectations.json").read_bytes()),
    "B_freeze_time_ns": time.time_ns(),
    "B_extra_Rust_execution": False,
}
(R / "output/python-derivation.json").write_text(json.dumps(record, indent=2) + "\n")
print(
    "Re-derived all original expectations, three supplement expectations and",
    len(extra),
    "separate B prospective cases.",
)
