"""Protected proposal tests: carrier semantics only; runtime admission remains pending."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from uarch_contract.assumptions import AssumptionSet
from uarch_contract.generate import generate as generate_v1
from uarch_contract.generate_rotary_v2 import generate, schemas
from uarch_contract.hashing import content_hash, strict_json_loads, verify_identity
from uarch_contract.operators import OpSpec
from uarch_contract.prepared import PreparedBundle, PreparedOp
from uarch_contract.request import CharacterizationRequest
from uarch_contract.rotary_v2 import (
    SCHEMA_ROOTS,
    CharacterizationRequestV3,
    PreparedBundleV2,
    PreparedOpV2,
    RotaryCoefficients,
)

from contract.tests.rotary_v2_cases import examples, literal, rehash, seal


@pytest.mark.parametrize("mode", ["aggregate", "per_op"])
@pytest.mark.parametrize("pairing", ["adjacent", "split_halves"])
def test_complete_positive_contract_closure(mode: str, pairing: str) -> None:
    data = examples(mode, pairing)
    b = PreparedBundleV2.model_validate(data["bundle"])
    r = CharacterizationRequestV3.model_validate(data["request"])
    a = AssumptionSet.model_validate(data["assumptions"])
    assert b.model_dump(mode="json") == data["bundle"]
    assert r.model_dump(mode="json") == data["request"]
    assert r.prepared_input_hash == verify_identity(b, "bundle_hash")
    assert (
        b.intent_hash == content_hash(b.intent) == content_hash(r, exclude=("prepared_input_hash",))
    )
    assert r.assumptions_hash == verify_identity(a, "assumptions_hash")
    assert a.model.version == "2"
    assert len(b.points) == 2 and b.rank.tp == 1
    assert b.intent.model.total_params == 372  # Existing independent synthetic model, unchanged.
    assert b.coefficients.position_count == 17
    for point in b.points:
        verify_identity(point, "payload_hash")
        assert point.graph.kv_key_encoding == b.intent.position_encoding
        decoder = point.graph.groups[1]
        assert decoder.repeat == 2
        ops = {op.id: op for op in decoder.ops}
        for target, heads in (("q", 2), ("k", 1)):
            op = ops["rope_" + target]
            binding = op.rotary
            assert binding is not None
            assert binding.coefficients_hash == b.coefficients.coefficients_hash
            assert binding.pairing == pairing and binding.input_op_id == target
            assert binding.position_ids == (((16,),) if point.query.phase == "decode" else ((0,),))
            assert op.depends_on == (target,)
            assert op.spec.dimensions == dict(B=1, H=heads, S=1, D=2, R=2, P=1)
        assert ops["kv"].depends_on == ("rope_k", "v")
        assert ops["attn"].depends_on == ("rope_q", "rope_k", "v", "kv")


@pytest.mark.parametrize(
    "bits",
    [
        "00000000",
        "80000000",
        "00000001",
        "007fffff",
        "00800000",
        "7f7fffff",
        "ff7fffff",
        "3f800000",
    ],
)
def test_finite_bits_with_independent_rehash(bits: str) -> None:
    c = examples()["bundle"]["coefficients"]
    c["cos_bits"][0][0] = bits
    seal(c, "coefficients_hash")
    parsed = RotaryCoefficients.model_validate(c)
    assert parsed.cos_bits[0][0] == bits


@pytest.mark.parametrize("bits", ["7f800000", "ff800000", "7fc00000", "7f800001", "ffc00000"])
def test_nonfinite_bits_refuse_after_rehash(bits: str) -> None:
    c = examples()["bundle"]["coefficients"]
    c["sin_bits"][0][0] = bits
    seal(c, "coefficients_hash")
    with pytest.raises(ValidationError, match="nonfinite binary32"):
        RotaryCoefficients.model_validate(c)


@pytest.mark.parametrize("bits", ["3F800000", "0x00000000", "0000000", "000000000", "gggggggg"])
def test_bad_bit_syntax_refuses(bits: str) -> None:
    c = examples()["bundle"]["coefficients"]
    c["cos_bits"][0][0] = bits
    seal(c, "coefficients_hash")
    with pytest.raises(ValidationError, match="pattern"):
        RotaryCoefficients.model_validate(c)


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("rotary_dim", 3, "even"),
        ("rotary_dim", 1, "even"),
        ("position_count", 18, "position_count mismatch"),
        ("cos_bits", [["00000000", "3f800000"]] * 17, "row width"),
        ("sin_bits", [["00000000"]] * 16, "position_count mismatch"),
        ("position_count", True, "JSON number"),
        ("dtype", "bf16", "fp32"),
    ],
)
def test_coefficient_shape_refuses_after_rehash(key: str, value: Any, message: str) -> None:
    c = examples()["bundle"]["coefficients"]
    c[key] = value
    seal(c, "coefficients_hash")
    with pytest.raises(ValidationError, match=message):
        RotaryCoefficients.model_validate(c)


def test_finite_tamper_requires_new_identity_and_signed_zero_is_preserved() -> None:
    c = examples()["bundle"]["coefficients"]
    old = c["coefficients_hash"]
    c["sin_bits"][0][0] = "80000000"
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        RotaryCoefficients.model_validate(c)
    seal(c, "coefficients_hash")
    assert RotaryCoefficients.model_validate(c).coefficients_hash != old


@pytest.mark.parametrize("field", ["coefficients", "intent", "rank", "points"])
def test_bundle_fields_are_required(field: str) -> None:
    b = examples()["bundle"]
    del b[field]
    with pytest.raises(ValidationError, match="Field required"):
        PreparedBundleV2.model_validate(b)


def test_explicit_null_binding_required_on_nonrotary_nodes() -> None:
    old = literal("independent-bundle.json")["points"][0]["graph"]["groups"][1]["ops"][1]
    PreparedOp.model_validate(old)
    with pytest.raises(ValidationError, match="rotary"):
        PreparedOpV2.model_validate(old)
    old["rotary"] = None
    PreparedOpV2.model_validate(old)
    with pytest.raises(ValidationError, match="extra_forbidden"):
        PreparedOp.model_validate(old)


@pytest.mark.parametrize(
    "version", ["uarch-contract/0.1", "uarch-contract/0.2", "uarch-contract/1"]
)
def test_v3_request_refuses_other_contract_tags(version: str) -> None:
    r = examples()["request"]
    r["contract"] = version
    with pytest.raises(ValidationError, match="uarch-contract/0.3"):
        CharacterizationRequestV3.model_validate(r)


@pytest.mark.parametrize("key", ["position_encoding", "mapping_policy", "accounting"])
def test_no_implicit_request_upgrade(key: str) -> None:
    r = examples()["request"]
    del r[key]
    with pytest.raises(ValidationError, match="Field required"):
        CharacterizationRequestV3.model_validate(r)


def test_old_and_new_roots_refuse_cross_version_inputs() -> None:
    new = examples()
    old_bundle, old_request = literal("independent-bundle.json"), literal("request.json")
    PreparedBundle.model_validate(old_bundle)
    CharacterizationRequest.model_validate(old_request)
    for model, value in (
        (PreparedBundle, new["bundle"]),
        (CharacterizationRequest, new["request"]),
        (PreparedBundleV2, old_bundle),
        (CharacterizationRequestV3, old_request),
    ):
        with pytest.raises(ValidationError):
            model.model_validate(value)
    rope = new["bundle"]["points"][0]["graph"]["groups"][1]["ops"][2]
    assert rope["id"] == "rope_q"
    with pytest.raises(ValidationError, match="operator"):
        OpSpec.model_validate(rope["spec"])


def test_legacy_schema_bytes_and_roots_unchanged() -> None:
    assert generate_v1(check=True) == []
    assert len(SCHEMA_ROOTS) == 11
    assert set(schemas()) == {m.__name__ + ".json" for m in SCHEMA_ROOTS}
    assert all(m.model_json_schema()["additionalProperties"] is False for m in SCHEMA_ROOTS)
    assert generate(check=True) == []


def test_generator_read_only_check_and_unexpected_file(tmp_path: Path) -> None:
    absent = tmp_path / "absent"
    assert len(generate(absent, check=True)) == 11
    assert not absent.exists()
    generate(absent)
    assert generate(absent, check=True) == []
    first = {p.name: p.read_bytes() for p in absent.iterdir()}
    generate(absent)
    assert {p.name: p.read_bytes() for p in absent.iterdir()} == first
    unexpected = absent / "unknown.json"
    unexpected.write_text("{}\n")
    assert generate(absent, check=True) == ["unknown.json"]
    assert unexpected.read_text() == "{}\n"
    with pytest.raises(ValueError, match="unexpected schema"):
        generate(absent)


def test_strict_json_not_silently_replaced_by_pydantic_parser() -> None:
    for text in ('{"position_count":1,"position_count":2}', '{"x":NaN}'):
        with pytest.raises(ValueError):
            strict_json_loads(text)


def test_carriers_do_not_claim_runtime_graph_admission() -> None:
    # Demonstrate the exact gap; this is NOT a positive execution-admission test.
    b = deepcopy(examples()["bundle"])
    ops = b["points"][0]["graph"]["groups"][1]["ops"]
    ops[:] = [op for op in ops if op["id"] != "rope_q"]
    rehash(b)
    parsed = PreparedBundleV2.model_validate(b)
    assert all(op.id != "rope_q" for op in parsed.points[0].graph.groups[1].ops)
