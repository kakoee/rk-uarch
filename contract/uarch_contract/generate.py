"""Generate all contract JSON Schemas, or check exact freshness without writing.

Run `python -m uarch_contract.generate [--check] [--output PATH]`.
No vendoring or CI configuration belongs to this module (U-P2 owns both).
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

from pydantic import BaseModel, TypeAdapter

MODULES = (
    "errors",
    "sourced",
    "hardware",
    "operators",
    "model_shape",
    "precision",
    "fidelity",
    "request",
    "model_card",
    "table",
)
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "schema"


def exported_models() -> tuple[type[BaseModel], ...]:
    models: set[type[BaseModel]] = set()
    for name in MODULES:
        module = importlib.import_module(f"uarch_contract.{name}")
        models.update(
            cls
            for cls in vars(module).values()
            if isinstance(cls, type)
            and issubclass(cls, BaseModel)
            and cls.__module__ == module.__name__
        )
    return tuple(sorted(models, key=lambda cls: cls.__name__))


def schemas() -> dict[str, str]:
    from .precision import PrecisionFormat

    result = {}
    for cls in exported_models():
        if cls.__name__ + ".json" in result:
            raise ValueError(f"Duplicate exported model name: {cls.__name__}")
        schema = cls.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        result[cls.__name__ + ".json"] = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    schema = TypeAdapter(PrecisionFormat).json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    result["PrecisionFormat.json"] = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    return result


def generate(output: Path = DEFAULT_OUTPUT, *, check: bool = False) -> list[str]:
    expected = schemas()
    actual = {path.name: path.read_text() for path in output.glob("*.json")}
    stale = sorted(
        name for name in actual.keys() | expected.keys() if actual.get(name) != expected.get(name)
    )
    if not check:
        output.mkdir(parents=True, exist_ok=True)
        # Remove only obsolete generated JSON files in the explicitly chosen output directory.
        for name in actual.keys() - expected.keys():
            (output / name).unlink()
        for name, content in expected.items():
            (output / name).write_text(content)
    return stale


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    stale = generate(args.output, check=args.check)
    if args.check and stale:
        parser.exit(1, "Stale contract schemas: " + ", ".join(stale) + "\nRun make gen.\n")
    print("Contract schemas are fresh." if args.check else "Generated contract schemas.")


if __name__ == "__main__":
    main()
