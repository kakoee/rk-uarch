"""Contract-only primitives; no runtime or rk imports."""

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

CONTRACT_VERSION = "uarch-contract/0.2"
RK_SCHEMA_SNAPSHOT = "1e5706e0ebfcc67c1a7333079a35b75f693e9963"
PositiveInt = Annotated[int, Field(ge=1)]
NonNegativeInt = Annotated[int, Field(ge=0)]
NonNegativeFloat = Annotated[float, Field(ge=0, allow_inf_nan=False)]
PositiveFloat = Annotated[float, Field(gt=0, allow_inf_nan=False)]
Ratio = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
NonEmpty = Annotated[str, Field(min_length=1, pattern=r"\S")]
Hash = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
Sha = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]


def json_number(value: Any) -> Any:
    """JSON numeric fields do not reinterpret booleans or strings as numbers."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected a JSON number, not a boolean or string.")
    return value


# Keep the original aliases for the pinned ModelSpec and generic SourcedValue semantics.
JsonFloat = Annotated[float, BeforeValidator(json_number)]
JsonPositiveInt = Annotated[PositiveInt, BeforeValidator(json_number)]
JsonNonNegativeInt = Annotated[NonNegativeInt, BeforeValidator(json_number)]
JsonPositiveFloat = Annotated[PositiveFloat, BeforeValidator(json_number)]
JsonNonNegativeFloat = Annotated[NonNegativeFloat, BeforeValidator(json_number)]
JsonRatio = Annotated[Ratio, BeforeValidator(json_number)]


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)


def reject_cycles(value: Any, path: str = "") -> None:
    """The exchange boundary also rejects cycles hidden inside provenance carriers."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key.endswith("_cycles") or (
                key == "unit" and isinstance(child, str) and "cycle" in child.lower()
            ):
                raise ValueError(f"{child_path}: cycles cannot cross the request/table boundary.")
            reject_cycles(child, child_path)
    elif isinstance(value, (tuple, list)):
        for index, child in enumerate(value):
            reject_cycles(child, f"{path}[{index}]")
