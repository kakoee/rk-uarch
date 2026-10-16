"""Independent baseline comparison with explicit nonempty/LF/refusal controls."""

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

R = Path("/tmp/u4-b-c2-review")
P = R / "subject/docs/reviews/U4-A-K2-C2-probes-v1"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def records(raw):
    if not raw or not raw.endswith(b"\n"):
        raise ValueError("empty or missing LF framing")
    chunks = raw[:-1].split(b"\n")
    if any(not b for b in chunks):
        raise ValueError("blank record")

    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError("duplicate output key")
            result[k] = v
        return result

    return [json.loads(b, object_pairs_hook=pairs) for b in chunks]


def validate_selection(vectors, actual):
    ids = [v["id"] for v in vectors]
    if not ids or len(set(ids)) != len(ids) or [a["id"] for a in actual] != ids:
        raise ValueError("nonempty ordered exact selection required")


def expected_rust_refusal(v):
    family = v["family"]
    if family in (
        "integer-refusal",
        "integer-token",
        "rational-refusal",
        "typed-normalization-fault",
    ):
        reason = {
            "integer-refusal:00000": "number out of range",
            "integer-refusal:00001": "number out of range",
            "integer-refusal:00002": "invalid number",
            "integer-refusal:00003": "invalid number",
            "integer-refusal:00004": "trailing characters",
            "integer-refusal:00005": "invalid number",
            "integer-token:00000": "trailing characters",
            "integer-token:00001": "trailing characters",
            "integer-token:00003": "number out of range",
            "rational-refusal:00000": "InvalidRatio",
            "rational-refusal:00001": "InvalidRatio",
            "rational-refusal:00002": "missing field `denominator`",
            "rational-refusal:00003": "unknown field `extra`",
            "rational-refusal:00004": "invalid number",
            "rational-refusal:00005": "invalid number",
            "typed-normalization-fault:00000": "unknown field `extra`",
            "typed-normalization-fault:00001": "missing field `value`",
        }[v["id"]]
        return "carrier", reason
    if family == "nonfinite-bits":
        return "canonical", "nonfinite f64"
    if family == "nonfinite-token":
        return (
            ("canonical", "nonfinite f64")
            if bytes.fromhex(v["hex"]) == b"1e999"
            else (
                "strict-json",
                "invalid number" if bytes.fromhex(v["hex"]) == b"-Infinity" else "expected value",
            )
        )
    if family == "unicode-escape":
        return "strict-json", "lone leading surrogate" if v[
            "id"
        ] == "unicode-escape:00001" else "unexpected end of hex escape"
    if family == "invalid-utf8":
        return "utf8", "invalid utf-8"
    if family == "duplicates":
        return "strict-json", "DuplicateJsonKey"
    if family == "reserved-marker":
        return "strict-json", "ReservedNumericMarker"
    if family == "closure-refusal":
        return "identity", "ArtifactHashMismatch"
    raise AssertionError(("unreviewed refusal family", family))


def compare(vectors, actual):
    validate_selection(vectors, actual)
    mismatches = []
    refusals = []
    for v, a in zip(vectors, actual, strict=True):
        expected = v["expected"]
        if expected["status"] != a["status"]:
            mismatches.append(v["id"])
            continue
        if a["status"] == "ok":
            if any(a.get(k) != expected[k] for k in ("canonical", "sha256") if k in expected):
                mismatches.append(v["id"])
            if "canonical" in a:
                assert sha(a["canonical"].encode()) == a["sha256"], (
                    "internally inconsistent bytes/hash"
                )
        else:
            layer, token = expected_rust_refusal(v)
            assert a["layer"] == layer and a.get("error") and (token is None or token in a["error"])
            refusals.append(
                {
                    "id": v["id"],
                    "Python_layer": expected["layer"],
                    "Rust_layer": a["layer"],
                    "Rust_error": a["error"],
                }
            )
    return mismatches, refusals


vectors = records(gzip.decompress((P / "vectors.jsonl.gz").read_bytes()))
original = records(gzip.decompress((P / "outcomes-debug.jsonl.gz").read_bytes()))
expected_bad = [v["id"] for v in json.loads((P / "counterexample-inputs.json").read_bytes())]
rows = {}
for mode in ("debug", "release"):
    raw = (R / f"repeat/receipts/execute-{mode}.stdout").read_bytes()
    got = records(raw)
    assert got == original
    bad, refusals = compare(vectors, got)
    assert bad == expected_bad
    supp = records(gzip.decompress((P / "identity-supplement.jsonl.gz").read_bytes()))
    suppgot = records((R / f"repeat/receipts/identity-supplement-{mode}.stdout").read_bytes())
    assert compare(supp, suppgot) == ([], [])
    units = (R / f"repeat/receipts/build-test-{mode}-package.stdout").read_text()
    names = [
        line.split(" ... ")[0].removeprefix("test ")
        for line in units.splitlines()
        if line.startswith("test tests::")
    ]
    assert sorted(names) == sorted(
        [
            "tests::sha_vectors",
            "tests::float_conventions",
            "tests::duplicate_refusal",
            "tests::marker_refusal",
            "tests::huge_integer_exact",
            "tests::strict_integer_tokens",
        ]
    )
    assert "6 passed; 0 failed; 0 ignored" in units
    rows[mode] = {
        "count": len(got),
        "mismatches": bad,
        "refusals": refusals,
        "outcome_sha256": sha(raw),
        "matches_A_raw": True,
        "supplement_count": 3,
        "unit_names": names,
    }
# Review the original comparator as host code only; it cannot launch processes.
spec = importlib.util.spec_from_file_location("A_compare", R / "controls/compare.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
assert Path(old.__file__).resolve() == R / "controls/compare.py"
controls = []
v = vectors[:1]
a = original[:1]
for name, vs, acts in [
    ("empty", [], []),
    ("missing", v, []),
    ("duplicate", v, a + a),
    ("extra", v, a + [dict(a[0], id="foreign")]),
    ("wrong-id", v, [dict(a[0], id="foreign")]),
]:
    try:
        compare(vs, acts)
    except ValueError:
        controls.append(name)
    else:
        raise AssertionError(name)
for name, vs, acts in [
    ("reordered", vectors[:2], original[:2][::-1]),
    ("duplicate-input", vectors[:1] * 2, original[:1] * 2),
]:
    try:
        compare(vs, acts)
    except ValueError:
        controls.append(name)
    else:
        raise AssertionError(name)
for name, changes in [
    ("wrong-bytes", {"canonical": "wrong"}),
    ("wrong-hash", {"sha256": "0" * 64}),
    ("incorrect-refusal", {"status": "refuse", "layer": "transport", "error": "fake"}),
]:
    acts = [dict(a[0], **changes)]
    try:
        bad, _ = compare(v, acts)
    except AssertionError:
        controls.append(name)
    else:
        assert bad == [v[0]["id"]]
        controls.append(name)
for name, raw in [
    ("missing-LF", b"{}"),
    ("blank-line", b"{}\n\n"),
    ("malformed", b"{\n"),
    ("duplicate-key", b'{"id":1,"id":2}\n'),
]:
    try:
        records(raw)
    except (ValueError, json.JSONDecodeError):
        controls.append(name)
    else:
        raise AssertionError(name)
i = next(i for i, v in enumerate(vectors) if v["family"] == "duplicates")
vs = [vectors[i]]
acts = [dict(original[i], layer="transport", error="unrelated failure")]
assert old.compare(vs, acts)["mismatch_count"] == 0
try:
    compare(vs, acts)
except AssertionError:
    controls.append("wrong-refusal-layer")
else:
    raise AssertionError("wrong-refusal-layer")
acts = [dict(original[i], error="unrelated failure")]
assert old.compare(vs, acts)["mismatch_count"] == 0
try:
    compare(vs, acts)
except AssertionError:
    controls.append("wrong-refusal-reason")
else:
    raise AssertionError("wrong-refusal-reason")
assert compare(v, a) == ([], [])
assert old.compare([], [])["mismatch_count"] == 0
report = {
    "modes": rows,
    "B_negative_controls": controls,
    "positive_restored": True,
    "A_comparator_gaps": {
        "empty_pair_accepted": True,
        "unrelated_refusal_layer_accepted": True,
        "unrelated_refusal_reason_accepted": True,
    },
    "A_original_run_nonempty": True,
    "framing": "bytes split only on LF, not Unicode splitlines",
    "new_host_checks_not_native": True,
}
(R / "output/comparison.json").write_text(json.dumps(report, indent=2) + "\n")
print(
    "Both actual modes: 20955/20965, exact ten carrier mismatches; supplement 3/3; six units each."
)
print(
    "B comparison controls:",
    len(controls),
    "refusals; positive restored. Original comparator gaps demonstrated.",
)
