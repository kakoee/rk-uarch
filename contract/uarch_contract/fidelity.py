"""The same per-subsystem vector for requests, model identities and tables."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import (
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from .common import FrozenModel


def fidelity_schema(schema: dict[str, Any]) -> None:
    # None is an internal omission sentinel, never a legal wire value or default.
    schema["properties"]["shared_sram"] = {
        "title": "Shared Sram",
        "enum": [0, 1, "1+ts", "unrepresented"],
        "description": "Omit only when hardware has no shared SRAM; null is invalid.",
    }


class FidelityDetail(FrozenModel):
    model_config = ConfigDict(json_schema_extra=fidelity_schema)

    compute: Literal[0, 1, 2]
    noc: Literal[0, 1, "1+ts", 2]
    dram: Literal[0, 1, "1+ts", 2]
    shared_sram: Literal[0, 1, "1+ts", "unrepresented"] | None = None
    sync: Annotated[str, Field(pattern=r"^(exact|approx\(Q=[1-9][0-9]*\))$")]
    layer_reuse: bool

    @model_validator(mode="before")
    @classmethod
    def exact_level_types(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in ("compute", "noc", "dram", "shared_sram"):
                if key in data and (isinstance(data[key], bool) or data[key] is None):
                    raise ValueError(f"{key} requires a legal level; omit absent shared_sram.")
        return data

    @model_serializer(mode="wrap")
    def omit_absent_resource(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data: dict[str, Any] = handler(self)
        if self.shared_sram is None:
            data.pop("shared_sram", None)
        return data

    def conservative_composite(self) -> Literal["C0", "C1", "C2"]:
        """Hardware detail determines C0; sync can only restrict higher fidelity.

        Omitted shared SRAM means physically absent; its C2 prerequisite applies
        only when present. Producers must emit a level (including unrepresented)
        whenever HardwareSpec declares shared SRAM. Contract 0.1 requires exact
        sync for C2. The detail vector, including unrepresented resources, is preserved.
        """
        if self.compute == self.noc == self.dram == 0 and self.shared_sram in (
            None,
            0,
            "unrepresented",
        ):
            return "C0"
        if (
            self.compute == 2
            and self.noc in (2, "1+ts")
            and self.dram in (2, "1+ts")
            and self.shared_sram in (None, "1+ts")
            and self.sync == "exact"
        ):
            return "C2"
        return "C1"
