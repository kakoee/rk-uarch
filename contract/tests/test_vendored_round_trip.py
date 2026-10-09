"""Cross-project contract checks; only committed bytes may enter this interpreter."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, get_args

import pytest
from pydantic import ValidationError

from .vendor_support import COUNT_CHANNELS, VendorLoader


def test_claim_round_trip(snapshot: Path, lane_a: dict[str, Any]) -> None:
    upstream = VendorLoader(snapshot).load("rk.provenance").SourcedValue
    claim = lane_a["sourced"].SourcedValue(
        value=2,
        unit="byte",
        provenance="spec_derived",
        source="https://example.org/datasheet",
        date="2026-10-04",
    )
    payload = claim.model_dump(mode="json", exclude={"kind", "rationale"})
    assert upstream.model_validate(payload).model_dump(mode="json") == payload
    assert lane_a["sourced"].SourcedValue.model_validate(payload) == claim


def test_stipulation_is_refused_by_actual_vendored_class(
    snapshot: Path, lane_a: dict[str, Any]
) -> None:
    upstream = VendorLoader(snapshot).load("rk.provenance").SourcedValue
    stipulation = lane_a["sourced"].SourcedValue(
        value=2, unit="byte", kind="stipulation", provenance=None, rationale="A design choice"
    )
    # Even stripping uarch-only fields must not launder a stipulation into a claim.
    with pytest.raises(ValidationError):
        upstream.model_validate(stipulation.model_dump(mode="json", exclude={"kind", "rationale"}))
    with pytest.raises(ValidationError):
        upstream.model_validate(stipulation.model_dump(mode="json"))


def test_modelspec_fields_and_precision_members_identical(
    snapshot: Path, lane_a: dict[str, Any]
) -> None:
    loader = VendorLoader(snapshot)
    upstream = loader.load("rk.schema.workloads").ModelSpec
    local = lane_a["model_shape"].ModelSpec
    assert set(local.model_fields) == set(upstream.model_fields)
    for key in ("properties", "required", "additionalProperties"):
        assert local.model_json_schema()[key] == upstream.model_json_schema()[key]
    upstream_precision = loader.load("rk.schema.execution").PrecisionFormat
    assert {key: member.value for key, member in upstream_precision.__members__.items()} == {
        key: member.value for key, member in lane_a["precision"].PrecisionFormat.__members__.items()
    }
    for path in sorted((snapshot / "model_shapes").glob("*.json")):
        payload = json.loads(path.read_text())["model"]
        assert local.model_validate(payload).model_dump(mode="json") == (
            upstream.model_validate(payload).model_dump(mode="json")
        )
    assert "rk" not in sys.modules


def test_row_count_keys_map_exactly_to_rk_channel_literals(
    snapshot: Path, lane_a: dict[str, Any]
) -> None:
    channels = set(get_args(VendorLoader(snapshot).load("rk.schema.channels").Channel))
    from scripts.vendor_rk import ROOT

    toy_path = ROOT / "contract/tests/fixtures/toy_table.json"
    assert toy_path.exists(), "Lane A toy table is required"
    toy = json.loads(toy_path.read_text())
    table = lane_a["table"].LegacyUarchCostTable.model_validate(toy)
    assert set(lane_a["table"].Counts.model_fields) == set(COUNT_CHANNELS)
    for row in table.rows:
        keys = set(row.model_dump(mode="json")["counts"])
        assert keys == set(COUNT_CHANNELS), (
            f"unmapped Row.counts fields: {keys ^ set(COUNT_CHANNELS)}"
        )
    assert len(set(COUNT_CHANNELS.values())) == len(COUNT_CHANNELS)
    assert set(COUNT_CHANNELS.values()) <= channels


@pytest.mark.parametrize("source", ["", " ", "\t\n"])
def test_proposed_stub_source_exception_is_explicit(
    snapshot: Path, lane_a: dict[str, Any], source: str
) -> None:
    """U0001/U0002 proposal: uarch is stricter; this is not exact validator parity."""
    upstream = VendorLoader(snapshot).load("rk.provenance").SourcedValue
    local = lane_a["sourced"].SourcedValue
    payload = {"value": 2, "unit": "byte", "provenance": "stub", "source": source, "date": None}
    # Pin actual upstream acceptance without silently normalizing its input to None.
    assert upstream.model_validate(payload).model_dump(mode="json") == payload
    with pytest.raises(ValidationError, match="provenance=stub requires source=None"):
        local.model_validate(payload)
    valid = payload | {"source": None}
    assert upstream.model_validate(valid).model_dump(mode="json") == valid
    assert (
        local.model_validate(valid).model_dump(mode="json", exclude={"kind", "rationale"}) == valid
    )
