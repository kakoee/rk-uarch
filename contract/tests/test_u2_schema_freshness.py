"""One Python authority for current and explicitly historical schema roots."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel
from uarch_contract.generate import exported_models, generate

from contract.tests.nominal_candidate import NominalCounts, NominalInput, NominalOutput
from rkuarch.engines import protocol

PROPOSAL = Path(__file__).resolve().parents[2] / "docs/reviews/U2-U0003-proposal"
CATALOG = json.loads((PROPOSAL / "fixtures/amendment-fixture-catalog.json").read_text())
ROOTS: tuple[type[BaseModel], ...] = (
    *exported_models(),
    *protocol.SCHEMA_ROOTS,
    NominalInput,
    NominalOutput,
    NominalCounts,
)
MODELS = {model.__name__: model for model in ROOTS}


@pytest.mark.parametrize("entry", CATALOG, ids=lambda e: e["path"])
def test_accepted_literal_carrier(entry: dict[str, Any]) -> None:
    model = MODELS[entry["type"]]
    value = json.loads((PROPOSAL / entry["path"]).read_text())
    parsed = model.model_validate(value)
    assert parsed.model_dump(mode="json") == value


def test_schema_freshness() -> None:
    assert generate(check=True) == []
    assert protocol.generate(check=True) == []
