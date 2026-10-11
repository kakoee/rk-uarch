"""Stage 2 F1: public boundaries reject rehashed unsupported card assertions.

Captures are actual local analytic test computations; administrative reviews and evidence
are explicitly synthetic scaffolding and never positive accuracy evidence.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from uarch_contract.hashing import artifact_identity, canonical_json, content_hash, sha256
from uarch_contract.model_card import ModelCard
from uarch_contract.report_context import ReportContext
from uarch_contract.table import UarchCostTable

from rkuarch.table.artifacts import load_verified_report_inputs, verify_report_inputs
from rkuarch.table.build import build_table, captured_artifacts
from tests.fixtures.u2_b.b2_support import review
from tests.integration.test_u2_a_replay import captured, companions


@pytest.fixture(scope="module", params=["reference", "proposed"])
def control(request):
    c = captured()
    if request.param == "proposed":
        from rkuarch.table.build import capture
        from tests.unit.test_u2_a_shapes import inputs, prepare

        intent, hardware = inputs()
        hardware = hardware.model_copy(update={"design_status": "proposed"})
        intent = intent.model_copy(update={"hardware_spec_hash": content_hash(hardware)})
        c = capture(prepare(intent, hardware), assumptions=c.assumptions)
    ctx, card, store = companions(c)
    if request.param == "proposed":
        registry = store[ctx.family_registry_hash]
        registry["entries"][0]["hardware_spec_hash"] = c.request.hardware_spec_hash
        # Replace only this new synthetic fixture's registry; preserve original artifacts.
        old_hash = ctx.family_registry_hash
        old_review_hash = registry["review_hash"]
        review(store, registry, "registry_hash")
        del store[old_hash]
        del store[old_review_hash]
        context = ctx.model_dump(mode="json")
        context["family_registry_hash"] = registry["registry_hash"]
        context["context_hash"] = content_hash(context, exclude=("context_hash",))
        ctx = ReportContext.model_validate(context)
    store.update(captured_artifacts(c))
    store[c.request.hardware_spec_hash] = c.bundle.hardware_spec.model_dump(mode="json")
    return c, ctx, card, store


def altered(control, attack):
    c, ctx, card, original = control
    store = dict(original)
    data = card.model_dump(mode="json")
    if attack in ("measured", "estimated", "synthetic", "wrong-model", "wrong-scope"):
        directory = Path(__file__).parents[1] / "fixtures/u2_b"
        for name in (
            "evidence-no-band.json",
            "evidence-source.json",
            "actual-evidence-review.json",
        ):
            value = json.loads((directory / name).read_text())
            store[artifact_identity(value)] = value
        raw = (directory / "source-literals.json").read_bytes()
        store[sha256(raw)] = raw
        evidence = json.loads((directory / "evidence-no-band.json").read_text())
        if attack not in ("measured", "estimated"):
            from rkuarch.table.build import source_scopes

            family = store[ctx.family_registry_hash]["entries"][0]["family"]
            scope = source_scopes(c, family=family)[(c.results[0].result_hash, "/duration_ps")][0]
            evidence.update(
                purpose="duration",
                channel="duration_s",
                granularity="operator",
                rung="L4",
                scope=[scope.model_dump(mode="json")],
            )
            if attack == "wrong-model":
                evidence["scope"][0]["model_identity_hash"] = content_hash("other source model")
            if attack == "wrong-scope":
                evidence["scope"][0]["frequency_ratio"] = 0.5
            review(store, evidence, "evidence_hash")
        # Real public closure, with the synthetic evidence's own valid review/source.
        ctxdata = ctx.model_dump(mode="json")
        ctxdata["evidence_index"] = {evidence["evidence_id"]: evidence["evidence_hash"]}
        ctxdata["context_hash"] = content_hash(ctxdata, exclude=("context_hash",))
        ctx = ReportContext.model_validate(ctxdata)
        data.update(
            badge="measured" if attack == "measured" else "estimated",
            evidence=[evidence["evidence_id"]],
        )
    elif attack == "band":
        data["validated_error_band"] = dict(
            low_rel=0.0,
            high_rel=0.02,
            scope=dict(
                family="test",
                op_classes=["q_projection"],
                precisions=["fp16"],
                shape_regimes=["full"],
                load_regimes=["low"],
                mapping_match="compiler-chosen",
            ),
        )
    elif attack == "energy":
        data["energy_verification"] = {
            k: {f: None for f in ("mac", "sram", "noc_hop", "dram", "static")} for k in ("L0", "L2")
        }
    else:
        raise AssertionError(attack)
    return c, ctx, ModelCard.model_validate(data), store


def disk_package(path, table, store):
    path.parent.mkdir(parents=True, exist_ok=True)
    art = path.parent / "artifacts"
    art.mkdir(exist_ok=True)
    path.write_text(canonical_json(table))
    for identity, value in store.items():
        (art / (identity[7:] + ".json")).write_bytes(
            value if isinstance(value, bytes) else canonical_json(value).encode()
        )


@pytest.mark.parametrize(
    "attack", ["measured", "estimated", "synthetic", "wrong-model", "wrong-scope", "band", "energy"]
)
@pytest.mark.parametrize("boundary", ["build", "memory", "disk", "cli"])
def test_forged_cards_refuse(control, attack, boundary, tmp_path):
    c, ctx, card, store = altered(control, attack)
    if boundary == "build":
        with pytest.raises(ValueError, match="UnsupportedModelCardAssertion"):
            build_table(c, context=ctx, model_card=card, artifacts=store)
        return
    if boundary == "cli":
        for name, value in (
            ("bundle", c.bundle),
            ("assumptions", c.assumptions),
            ("context", ctx),
            ("card", card),
        ):
            (tmp_path / (name + ".json")).write_text(canonical_json(value))
        art = tmp_path / "inputs"
        art.mkdir()
        for identity, value in store.items():
            (art / (identity[7:] + ".json")).write_bytes(
                value if isinstance(value, bytes) else canonical_json(value).encode()
            )
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "rkuarch.cli",
                "table",
                "--prepared-input",
                str(tmp_path / "bundle.json"),
                "--assumptions",
                str(tmp_path / "assumptions.json"),
                "--context",
                str(tmp_path / "context.json"),
                "--model-card",
                str(tmp_path / "card.json"),
                "--artifact-dir",
                str(art),
                "--output",
                str(tmp_path / "out/table.json"),
            ],
            env=dict(os.environ),
            text=True,
            capture_output=True,
        )
        assert result.returncode != 0 and "UnsupportedModelCardAssertion" in result.stderr
        assert not (tmp_path / "out/table.json").exists()
        return
    # Start from a genuine allowed public table, then rehash every affected carrier.
    base = build_table(control[0], context=control[1], model_card=control[2], artifacts=control[3])
    store.update(base.artifacts)
    store[ctx.context_hash] = ctx.model_dump(mode="json")
    store[content_hash(card)] = card.model_dump(mode="json")
    data = base.table.model_dump(mode="json")
    data["artifacts"].update(
        report_context_hash=ctx.context_hash, model_card_hash=content_hash(card)
    )
    data["provenance"]["model_card"] = dict(
        card.model_dump(mode="json", exclude={"model_id", "verification"}), hash=content_hash(card)
    )
    data["table_hash"] = content_hash(data, exclude=("table_hash",))
    table = UarchCostTable.model_validate(data)
    with pytest.raises(ValueError, match="UnsupportedModelCardAssertion"):
        if boundary == "memory":
            verify_report_inputs(table, store)
        else:
            path = tmp_path / "table.json"
            disk_package(path, table, store)
            load_verified_report_inputs(path)


def test_genuine_stub_roundtrip(control, tmp_path):
    c, ctx, card, store = control
    package = build_table(c, context=ctx, model_card=card, artifacts=store)
    verified = verify_report_inputs(package.table, package.artifacts)
    path = tmp_path / "table.json"
    disk_package(path, package.table, package.artifacts)
    assert load_verified_report_inputs(path) == verified
    assert verified.model_card.badge == "stub"
    assert verified.model_card.validated_error_band is None
    assert verified.model_card.energy_verification is None


@pytest.mark.parametrize(
    "attack", ["measured", "estimated", "synthetic", "wrong-model", "wrong-scope", "band", "energy"]
)
def test_b_owned_validator_refuses_without_an_adapter(control, attack):
    from rkuarch.provenance.model_card import validate_production_model_card

    c, ctx, card, store = altered(control, attack)
    with pytest.raises(ValueError, match="UnsupportedModelCardAssertion"):
        validate_production_model_card(card, captured=c, context=ctx, artifacts=store)


def test_b_owned_validator_allows_stub(control):
    from rkuarch.provenance.model_card import validate_production_model_card

    c, ctx, card, store = control
    validate_production_model_card(card, captured=c, context=ctx, artifacts=store)
