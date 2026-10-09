"""One Python authority for current and explicitly historical schema roots."""

import json
from pathlib import Path

import pytest
from uarch_contract.generate import exported_models, generate

from contract.tests.nominal_candidate import NominalCounts, NominalInput, NominalOutput
from rkuarch.engines import protocol

PROPOSAL = Path(__file__).resolve().parents[2] / "docs/reviews/U2-U0003-proposal"
CATALOG = json.loads((PROPOSAL / "fixtures/amendment-fixture-catalog.json").read_text())
MODELS = {
    m.__name__: m
    for m in (
        *exported_models(),
        *protocol.SCHEMA_ROOTS,
        NominalInput,
        NominalOutput,
        NominalCounts,
    )
}


@pytest.mark.parametrize("entry", CATALOG, ids=lambda e: e["path"])
def test_accepted_literal_carrier(entry):
    model = MODELS[entry["type"]]
    value = json.loads((PROPOSAL / entry["path"]).read_text())
    parsed = model.model_validate(value)
    assert parsed.model_dump(mode="json") == value


def test_schema_freshness():
    assert generate(check=True) == []
    assert protocol.generate(check=True) == []
