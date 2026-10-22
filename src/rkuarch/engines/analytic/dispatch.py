"""Explicit protocol routing, without parser retry, upgrade or public v2 table API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from uarch_contract.assumptions import AssumptionSet
from uarch_contract.hashing import canonical_json, strict_json_loads

from rkuarch.engines.protocol import EngineJob, EngineResult
from rkuarch.engines.protocol_v2 import EngineResultV2
from rkuarch.workload.prepared_v2 import raw

from . import core, rotary_v2


def execute(
    value: object, *, bundle: object = None, assumptions: AssumptionSet | None = None
) -> EngineResult | EngineResultV2:
    payload = raw(value)
    if not isinstance(payload, dict):
        raise ValueError("UnsupportedEngineProtocol: explicit object/tag required")
    protocol = payload.get("protocol")
    if protocol == "uarch-engine/1":
        if bundle is not None or assumptions is not None:
            raise ValueError("UnsupportedEngineProtocol: v2 closure supplied to legacy execution")
        return core.run_analytic(EngineJob.model_validate(payload))
    if protocol == "uarch-engine/2":
        if bundle is None or assumptions is None:
            raise ValueError("MissingClosure: v2 bundle and active assumptions required")
        return rotary_v2.run_analytic(payload, bundle=bundle, assumptions=assumptions)
    raise ValueError("UnsupportedEngineProtocol: no fallback")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--assumptions", type=Path)
    args = parser.parse_args()
    try:
        bundle = strict_json_loads(args.bundle.read_bytes()) if args.bundle else None
        assumptions = (
            AssumptionSet.model_validate(strict_json_loads(args.assumptions.read_bytes()))
            if args.assumptions
            else None
        )
        value = strict_json_loads(sys.stdin.buffer.read())
        result = execute(value, bundle=bundle, assumptions=assumptions)
        sys.stdout.buffer.write(canonical_json(result).encode() + b"\n")
    except (ValueError, TypeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def resolve_reference(bundle: Any) -> Any:
    """Explicit versioned reference profile; historical analytic dispatch is unchanged."""
    from .reference import resolve_reference as resolve

    return resolve(bundle)
