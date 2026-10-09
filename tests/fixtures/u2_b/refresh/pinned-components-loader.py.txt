"""Component library loader; rejects any param that is not a SourcedValue. Sprint 1 (P1).

The loader lands in P1 (build-spec §3 marks it S1); the library YAMLs it reads land in P3.

**The rejection is the project's spine, not a lint preference** (CLAUDE.md invariant 1).
If a load fails because someone wrote a bare number, the fix is to source the number or
mark it STUB — never to relax this module. Every error below names the component id, the
parameter, and what was wrong, because an agent or a human staring at "validation error"
will reach for the loader rather than for the source.

Scope of the rule, per ADR 0003 §5: it covers claims about the world — the hardware
parameters in `library/`. `ModelSpec.n_layers` and friends are plain ints; they define the
run and assert nothing about reality.

This module reads files, which is precisely why it lives here and not in `rk/engine/`.
The engine is pure — `(config, plan, workload, seed) -> result`, no I/O (rk/engine/README
invariant 1) — so somebody outside it has to do the reading, and that somebody is here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from rk.provenance import Calibration, SourcedValue
from rk.schema import ComponentDescriptor

__all__ = [
    "ComponentLoadError",
    "check_badges_are_supported",
    "load_component_file",
    "load_library",
]

# `SourcedValue` has exactly five fields and there is no `note` (build-spec §2.3.1).
# Commentary goes in a YAML comment or in `source`.
_SOURCED_VALUE_KEYS = frozenset({"value", "unit", "provenance", "source", "date"})
_REQUIRED_SOURCED_VALUE_KEYS = ("value", "unit", "provenance")

_DESCRIPTOR_KEYS = frozenset(
    {"id", "kind", "role", "params", "execution_model", "fidelity_available", "calibration"}
)


class ComponentLoadError(ValueError):
    """A component YAML that the library will not accept, and why."""


def _fail(path: Path, component_id: str, message: str) -> ComponentLoadError:
    return ComponentLoadError(f"{path}: component {component_id!r}: {message}")


def _describe(raw: object) -> str:
    """What the offending value actually was, for the error message."""
    return f"{type(raw).__name__} {raw!r}"


def _parse_sourced_value(path: Path, component_id: str, where: str, raw: object) -> SourcedValue:
    """One `{value, unit, provenance, source, date}` mapping, or a loud refusal.

    Four rejections, and CLAUDE.md invariant 1 is all four of them:
      a bare float                 -> it is not a mapping
      a mapping missing provenance -> a number with no statement of how it is known
      an unknown key               -> the schema is five fields; a sixth is a lie about
                                      what the library records
      a boolean `value`            -> pydantic would take it, and that is the problem

    The fourth is the only one that does not fail on its own. A string `value` is refused
    by pydantic; a boolean is not, because Python's `bool` subclasses `int`, so `false`
    becomes `0.0` and a categorical fact enters the library wearing a badge with nothing
    to announce it. Silent coercion is a worse failure than rejection — see ADR 0010 §9.
    """
    if not isinstance(raw, dict):
        raise _fail(
            path,
            component_id,
            f"{where} is {_describe(raw)}, not a SourcedValue. Every component parameter "
            f"is {{value, unit, provenance, source, date}} — a bare number carries no "
            f"statement of how it is known, and CLAUDE.md invariant 1 is that no such "
            f"number enters the system. Source it, or write provenance: stub with "
            f"source: null.",
        )

    keys = set(raw)
    unknown = sorted(keys - _SOURCED_VALUE_KEYS)
    if unknown:
        raise _fail(
            path,
            component_id,
            f"{where} carries unknown key(s) {unknown}. A SourcedValue has exactly five "
            f"fields: {sorted(_SOURCED_VALUE_KEYS)}. There is no `note` — commentary goes "
            f"in a YAML comment or in `source` (build-spec §2.3.1).",
        )

    missing = [key for key in _REQUIRED_SOURCED_VALUE_KEYS if key not in keys]
    if missing:
        raise _fail(
            path,
            component_id,
            f"{where} is missing {missing}. `provenance` in particular is not optional: "
            f"it is the whole point of the type, and a value that omits it is a number "
            f"claiming to be known without saying how.",
        )

    written = raw["value"]
    if isinstance(written, bool):
        raise _fail(
            path,
            component_id,
            f"{where} is {_describe(written)} inside an otherwise well-formed SourcedValue. "
            f"`SourcedValue.value` is a float and Python's bool subclasses int, so pydantic "
            f"would ACCEPT this and store {float(written)} — a badged number standing in for "
            f"a yes/no fact, with nothing anywhere to announce the substitution. A string in "
            f"this position fails on its own; a boolean does not, which is why it is refused "
            f"here. A categorical fact about a component belongs in `role` "
            f"(build-spec §2.3.1), or in a schema field asked for at a sprint boundary — "
            f"never in `params`.",
        )

    try:
        return SourcedValue(**raw)
    except ValidationError as exc:
        raise _fail(path, component_id, f"{where} is not a valid SourcedValue: {exc}") from exc


def _parse_execution_model(path: Path, component_id: str, raw: object) -> dict[str, Any]:
    """`execution_model` holds a SourcedValue too, and it is the repo's weakest number.

    Letting a bare float through here would be the worst place to let one through:
    `scalar_efficiency` is the dominant term in every cross-vendor comparison
    (build-spec §2.3.4), so it is the value most in need of a visible badge.
    """
    if not isinstance(raw, dict):
        raise _fail(
            path,
            component_id,
            f"execution_model is {_describe(raw)}, not a mapping. It takes a `kind` "
            f"discriminator and a `value` SourcedValue (build-spec §2.3.4).",
        )
    parsed = dict(raw)
    # ADR 0015 §3's second union member, taught to this parser on 2026-09-18 by P14 S3
    # lane A finding F1. It was refused here from the pre-P3b schema PR onward with a
    # message promising "P3b wires it" — and P3b landed without doing so, which left
    # `SplitEfficiency` reachable only from Python. P3b task 4's deliverable is a PLACE for
    # evidence, and a place evidence cannot be written to is not one: the library is where
    # evidence goes.
    #
    # BOTH MEMBERS ARE REQUIRED AND BOTH ARE SourcedValues, which is the reason this shape
    # exists at all — a `memory` that could be omitted would default to 1.0, making "no
    # memory term declared" and "a memory term measured at 1.0" the same bytes on the page.
    if parsed.get("kind") == "split_efficiency":
        missing = [member for member in ("compute", "memory") if member not in parsed]
        if missing:
            raise _fail(
                path,
                component_id,
                f"execution_model kind `split_efficiency` is missing "
                f"{' and '.join(f'`{m}`' for m in missing)}. It takes BOTH members as "
                f"SourcedValues (ADR 0015 §3): `compute` multiplies the compute roof and "
                f"`memory` the memory roof. The two are exactly orthogonal, so an omitted "
                f"member would silently mean 1.0 — indistinguishable from a measurement "
                f"of 1.0. Declare both, or use kind: scalar_efficiency for one number.",
            )
        for member in ("compute", "memory"):
            parsed[member] = _parse_sourced_value(
                path, component_id, f"execution_model.{member}", parsed[member]
            )
        return parsed
    if "value" not in parsed:
        raise _fail(
            path,
            component_id,
            "execution_model is missing `value`, the SourcedValue holding the "
            "realized-vs-peak ratio. Without it the roofline would run at peak FLOPs, "
            "which no real stack achieves.",
        )
    parsed["value"] = _parse_sourced_value(
        path, component_id, "execution_model.value", parsed["value"]
    )
    return parsed


# --------------------------------------------------------------------------------------
# The badge check ADR 0009 §5 leaves open and names P3 for
# --------------------------------------------------------------------------------------
#
# ADR 0009's rule, in its own words: **"A badge that `combine()` did not compute is a badge
# nothing has checked. Every surface that hand-writes one needs a mechanical cross-check
# against its contributors."** §5 lists the library as the one surface still uncovered.
#
# WHAT "ITS CONTRIBUTORS" MEANS FOR A LIBRARY ENTRY, AND WHERE THE ANALOGY STOPS. In a
# `Metric`, contributors are a field, so `badge <= combine(contributors)` is computable.
# A `SourcedValue` has no contributors field and `params` declares no derivation between
# entries, so the literal arithmetic check has nothing to read — and a check that reads
# nothing passes everything, which would be this defect one level up. That gap is stated
# in P3's report rather than papered over with a check that cannot fail.
#
# What IS mechanically checkable is the rung a badge claims against the evidence the entry
# actually carries. `library/README.md`'s provenance table already states the requirement
# per rung; until now it was prose, and prose is what `spec_derived` with no openable
# citation slips past. Each rung demands strictly more than the one below it, so a badge
# whose evidence is missing is exactly "stronger than what it is built from":
#
#   measured      the entry must carry a `calibration` ref — the anchor id that promoted
#                 it. `rk calibrate promote` writes those; a hand-typed `measured` with no
#                 anchor is the strongest badge in the system claiming a measurement that
#                 nothing in the repo records.
#   spec_derived  `source` must be a URL. "the datasheet" is not a datasheet; the badge
#                 means somebody can open the page and read the row.
#   estimated     `source` must name evidence AND point at the derivation, which
#                 library/README.md says "lives in docs/decisions/".
#   stub          `source` must be absent — already enforced by SourcedValue itself.
#
# Scoped to the LOADER and therefore to YAML, deliberately. Objects built in Python (test
# builders, fixtures) are not library entries and are not claims about the world.

_BADGE_EVIDENCE_HINT = "rk/components/library/README.md's provenance table"


def _looks_like_a_url(source: str) -> bool:
    return source.startswith(("http://", "https://"))


def _cites_a_derivation(source: str) -> bool:
    """Does this source point at a written derivation? `docs/decisions/` or an ADR number."""
    lowered = source.lower()
    return "docs/decisions/" in lowered or "adr " in lowered


def check_badges_are_supported(
    path: Path, descriptor: ComponentDescriptor
) -> None:
    """Refuse a hand-written badge the entry's own evidence does not support.

    Raises `ComponentLoadError` naming the component, the parameter, the badge and what
    the badge would need. See the block comment above for what this covers and what it
    deliberately does not.
    """
    has_anchor = bool(descriptor.calibration)
    values: list[tuple[str, SourcedValue]] = list(descriptor.params.items())
    if descriptor.execution_model is not None:
        values.extend(descriptor.execution_model.sourced_values)

    for name, value in values:
        source = (value.source or "").strip()
        if value.provenance is Calibration.MEASURED and not has_anchor:
            raise _fail(
                path,
                descriptor.id,
                f"{name} is badged 'measured' and this component carries no `calibration` "
                f"anchor. `measured` is the strongest badge in the system and it means the "
                f"value came out of measure/results/ with an anchor id "
                f"({_BADGE_EVIDENCE_HINT}). Promotion happens through `rk calibrate "
                f"promote`, never by hand — a typed 'measured' with nothing recording the "
                f"measurement is a badge no anchor can be checked against.",
            )
        if value.provenance is Calibration.SPEC_DERIVED and not _looks_like_a_url(source):
            raise _fail(
                path,
                descriptor.id,
                f"{name} is badged 'spec_derived' with source {source!r}, which is not a "
                f"URL. `spec_derived` means a vendor datasheet somebody can open and read "
                f"the row from ({_BADGE_EVIDENCE_HINT}); a description of a datasheet is "
                f"not one. Cite the document, or drop to 'estimated' with the derivation "
                f"in docs/decisions/.",
            )
        if value.provenance is Calibration.ESTIMATED and not _cites_a_derivation(source):
            raise _fail(
                path,
                descriptor.id,
                f"{name} is badged 'estimated' with source {source!r}, which names no "
                f"derivation. `estimated` means derived from indirect public evidence, and "
                f"{_BADGE_EVIDENCE_HINT} requires the derivation to live in "
                f"docs/decisions/ — so the source must point at it. Without that the badge "
                f"is a claim that reasoning happened somewhere nobody can find. "
                f"ADR 0006 §4 is what this rule exists to keep repeatable.",
            )


def load_component_file(path: Path) -> ComponentDescriptor:
    """Read one component YAML into a ComponentDescriptor, or refuse it by name.

    path   a `library/**/*.yaml` file holding exactly one component

    Every parameter must be a full SourcedValue; see the module docstring for why that
    is not negotiable.
    """
    text = path.read_text()
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ComponentLoadError(f"{path}: is not valid YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise ComponentLoadError(
            f"{path}: expected one component mapping per file, got {_describe(raw)}."
        )

    component_id = raw.get("id")
    if not isinstance(component_id, str) or not component_id.strip():
        raise ComponentLoadError(
            f"{path}: has no `id`. Every component needs one — it is what a SystemConfig "
            f"references and what the fidelity map and every badge contributor name."
        )

    unknown = sorted(set(raw) - _DESCRIPTOR_KEYS)
    if unknown:
        raise _fail(
            path,
            component_id,
            f"unknown top-level key(s) {unknown}. A component is "
            f"{sorted(_DESCRIPTOR_KEYS)} and nothing else.",
        )

    fields: dict[str, Any] = {key: value for key, value in raw.items() if key != "params"}

    params_raw = raw.get("params", {})
    if not isinstance(params_raw, dict):
        raise _fail(
            path,
            component_id,
            f"`params` is {_describe(params_raw)}, expected a mapping of name -> "
            f"SourcedValue.",
        )
    # P7 migration-only archive. Reconstruct the legacy import shape before the
    # SAME strict value/evidence checks; run resolution consumes and removes it.
    # Archived v1 descriptors elsewhere continue to carry their own values.
    shipped = Path(__file__).resolve().parent / 'library'
    if path.resolve().is_relative_to(shipped):
        archive_path = shipped.parent / 'legacy-economics-v1.yaml'
        archived = yaml.safe_load(archive_path.read_text())
        defaults = archived.get(component_id, {})
        overlap = set(defaults) & set(params_raw)
        if overlap:
            raise _fail(path, component_id, f'duplicate archived economics: {sorted(overlap)}')
        params_raw = {**defaults, **params_raw}
    fields["params"] = {
        name: _parse_sourced_value(path, component_id, f"params.{name}", value)
        for name, value in params_raw.items()
    }

    if raw.get("execution_model") is not None:
        fields["execution_model"] = _parse_execution_model(
            path, component_id, raw["execution_model"]
        )

    try:
        descriptor = ComponentDescriptor(**fields)
    except ValidationError as exc:
        raise _fail(path, component_id, f"is not a valid ComponentDescriptor: {exc}") from exc

    check_badges_are_supported(path, descriptor)
    return descriptor


def load_library(directory: Path) -> dict[str, ComponentDescriptor]:
    """Load every `*.yaml` under `directory`, keyed by component id.

    directory   a library root; subdirectories are walked (compute/, memory/, links/, ...)

    A duplicate id is an error naming both files: two components answering to one id means
    a SystemConfig referencing it gets whichever the filesystem happened to yield first,
    and a run whose components depend on directory ordering is not reproducible.
    """
    if not directory.is_dir():
        raise ComponentLoadError(f"{directory}: is not a directory")

    loaded: dict[str, ComponentDescriptor] = {}
    seen_in: dict[str, Path] = {}
    for path in sorted(directory.rglob("*.yaml")):
        descriptor = load_component_file(path)
        if descriptor.id in seen_in:
            raise ComponentLoadError(
                f"{path}: duplicate component id {descriptor.id!r}, already defined in "
                f"{seen_in[descriptor.id]}. Ids are what a SystemConfig references, so a "
                f"duplicate makes a run depend on directory order."
            )
        seen_in[descriptor.id] = path
        loaded[descriptor.id] = descriptor
    return loaded
