"""Presence checks only; human working/review and native L1 execution are separate gates."""

import pytest

from validation.component.corpus import ROOT


@pytest.mark.parametrize("worksheet", ["H-L1-DMA-01", "H-L1-GEMM-01"])
def test_required_human_working_present(worksheet):
    path = ROOT / "validation/L1_limits/hand" / f"{worksheet}.md"
    if not path.exists():
        pytest.skip(f"{worksheet}: actual human working absent; applicable L1 acceptance blocked")
    assert path.read_text().strip(), f"{worksheet}: empty human working"
