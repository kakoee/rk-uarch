"""Local preparation may skip absent inputs; contract CI explicitly requires them."""

from pathlib import Path
from typing import Any

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--pre-contract",
        action="store_true",
        help="Explicit preparation: permit absent U0001/Lane A contract pin",
    )
    parser.addoption(
        "--require-vendor",
        action="store_true",
        help="Fail, rather than skip, when human snapshot or Lane A is absent",
    )


def require_dependency(request: pytest.FixtureRequest, available: bool, reason: str) -> None:
    if available:
        return
    if request.config.getoption("--require-vendor"):
        pytest.fail(reason)
    pytest.skip(reason)


@pytest.fixture
def snapshot(request: pytest.FixtureRequest) -> Path:
    from scripts.vendor_rk import PIN, ROOT, check_manifest

    root = ROOT / "contract/vendor" / f"rk-sim@{PIN}"
    require_dependency(request, root.exists(), "BLOCKED: Javid must run the human vendor command")
    check_manifest(root)
    return root


@pytest.fixture
def lane_a(request: pytest.FixtureRequest) -> dict[str, Any]:
    from uarch_contract import model_shape, precision, sourced, table

    modules = {
        "model_shape": model_shape,
        "precision": precision,
        "sourced": sourced,
        "table": table,
    }
    missing = [
        f"{module}.{name}"
        for module, name in (
            ("model_shape", "ModelSpec"),
            ("model_shape", "ModelShape"),
            ("model_shape", "check_parity"),
            ("precision", "PrecisionFormat"),
            ("sourced", "SourcedValue"),
            ("table", "Row"),
            ("table", "Counts"),
            ("table", "UarchCostTable"),
        )
        if not hasattr(modules[module], name)
    ]
    require_dependency(
        request, not missing, "BLOCKED: Lane A interfaces absent: " + ", ".join(missing)
    )
    return modules


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--require-vendor") and config.getoption("--pre-contract"):
        raise pytest.UsageError("--require-vendor cannot use pre-contract preparation mode")
