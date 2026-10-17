"""Resource semantic discrimination under separately synthetic positive profile anchors."""

import pytest
from uarch_contract.mapped import MappedBundle, admit, validate_resources

from validation.component.corpus import build, materialize
from validation.component.lifetime_inputs import lifetime_inputs


@pytest.mark.parametrize(
    "name", ["B3-writer-control", "B3-terminal-control", "B3-shared-use-control"]
)
def test_lifetime_positive(name):
    b = MappedBundle.model_validate(lifetime_inputs()[name])
    validate_resources(b, b.points[0])


@pytest.mark.parametrize(
    "name,detail",
    [
        ("B3-false-writer-disjoint", "accumulator producer"),
        ("B3-terminal-partial-A1", "final consumers"),
        ("B3-use-before-A3b", "before production"),
        ("B3-use-unordered-A3c", "before production"),
    ],
)
def test_unmasked_lifetime(name, detail):
    raw = lifetime_inputs()[name]
    b = MappedBundle.model_validate(raw)
    with pytest.raises(ValueError, match="InvalidDependency: .*" + detail):
        validate_resources(b, b.points[0])
    synthetic = materialize("SYNTHETIC-" + name, raw, dict(outcome="success"))
    registry = build()["registry"]
    with pytest.raises(ValueError, match="InvalidDependency: .*" + detail):
        admit(
            synthetic["bundle"],
            invocation="test",
            checkpoint="B",
            registry=registry,
            profile=synthetic["profile"],
            trusted_registry_hash=registry["registry_hash"],
            trusted_profile_hash=synthetic["profile"]["profile_hash"],
        )
