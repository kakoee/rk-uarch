"""Single numeric presentation boundary. It accepts full assessments, never a badge alone."""

from __future__ import annotations

import math
from dataclasses import dataclass

from uarch_contract.hashing import verify_identity
from uarch_contract.report_context import RenderSpec

from rkuarch.provenance.badge import MetricAssessment


@dataclass(frozen=True)
class Badged:
    number: str | None
    text: str
    unit: str
    assessment: MetricAssessment
    render_hash: str


def badged(
    value: float | None,
    unit: str,
    assessment: MetricAssessment,
    permissions: RenderSpec,
    *,
    execution: str,
) -> Badged:
    verify_identity(permissions, "render_hash")
    if value is not None and (isinstance(value, bool) or not math.isfinite(value)):
        raise ValueError("NonFinitePrediction: cannot render")
    if execution not in ("executed", "not_run", "refused", "execution_failed"):
        raise ValueError("UnknownExecutionState")
    eligible = (
        value is not None
        and execution == "executed"
        and assessment.complete
        and assessment.display_recipe
        and assessment.nonempty
    )
    if assessment.badge == "stub" and not permissions.show_unvalidated_predictions:
        eligible = False
    if assessment.synthetic and not permissions.allow_synthetic_presentation:
        eligible = False
    number = repr(0.0 if value == 0 else float(value)) if eligible and value is not None else None
    label = (
        "STUB — unvalidated model prediction" if assessment.badge == "stub" else assessment.badge
    )
    if assessment.synthetic:
        label = assessment.badge.upper() + "; synthetic fixture — not executed"
    text = (
        f"{number} {unit} · {label}"
        if number is not None
        else f"{'unknown / not modelled' if value is None else 'magnitude hidden'} · {label}"
    )
    if any(model.purpose == "energy" for model in assessment.models):
        text += "; energy unverified"
    if assessment.conditional_on:
        text += "; conditional on stipulated inputs"
    # Observed bands are not synthetic confidence intervals and obey the same permission.
    if number is not None and assessment.error_band is not None:
        low, high = assessment.error_band
        text += f"; observed relative error bounds [{repr(low)}, {repr(high)}]"
    else:
        text += "; error unknown"
    return Badged(number, text, unit, assessment, permissions.render_hash)
