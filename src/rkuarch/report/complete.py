"""Deterministic offline evidence report over A's existing verified inputs."""

from __future__ import annotations

import html
import re
from collections.abc import Iterator
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined
from uarch_contract.hashing import content_hash, resolve_pointer, verify_identity
from uarch_contract.report_context import DependencySelector, RenderSpec
from uarch_contract.sourced import SourcedValue

from rkuarch.provenance.applicability import EvidenceAssessment
from rkuarch.provenance.badge import MetricAssessment, badge_for
from rkuarch.table.artifacts import (
    VerifiedReportInputs,
    load_verified_report_inputs,
    verify_report_inputs,
)
from rkuarch.table.build import CapturedWork, consumed_energy_families

from .badged import Badged, badged
from .evaluation import Evaluator, combine_assessments
from .plot import Plot, roofline
from .proofs import proof_statuses
from .prose import CapturedIdentifier, safe_prose
from .render import _markdown, lint_template

VERSION = "u2-complete-report/2"
TEMPLATES = Path(__file__).with_name("templates")


def hardware_quotes(
    node: Any, label: str = "", pointer: str = ""
) -> Iterator[tuple[str, str, SourcedValue]]:
    """Traverse exact member keys; dotted map keys must not become pointer separators."""
    if isinstance(node, dict):
        if {"value", "unit", "kind"} <= node.keys():
            yield label, pointer, SourcedValue.model_validate(node)
        else:
            for key, child in node.items():
                token = str(key).replace("~", "~0").replace("/", "~1")
                yield from hardware_quotes(
                    child, label + "." + key if label else key, pointer + "/" + token
                )
    elif isinstance(node, list):
        for i, child in enumerate(node):
            yield from hardware_quotes(child, label + f"[{i}]", pointer + "/" + str(i))


@dataclass(frozen=True)
class ReportOutput:
    html: str
    markdown: str
    render_spec: RenderSpec
    metrics: dict[str, Badged]


def permissions(v: VerifiedReportInputs, show: bool, synthetic: bool) -> RenderSpec:
    data = dict(
        format="uarch-render/1",
        renderer_version=VERSION,
        table_hash=v.table.table_hash,
        report_context_hash=v.context.context_hash,
        show_unvalidated_predictions=show,
        allow_synthetic_presentation=synthetic,
        locale="en",
        number_format="roundtrip-display/1",
    )
    return RenderSpec.model_validate(dict(data, render_hash=content_hash(data)))


class Document:
    def __init__(self, v: VerifiedReportInputs, p: RenderSpec):
        self.v = v
        self.p = p
        self.evaluator = Evaluator(v)
        self.metrics: dict[str, Badged] = {}
        self.sections: list[tuple[str, list[tuple[str, Badged]]]] = []
        self.empty = replace(
            badge_for((), (), design_status=v.hardware.design_status),
            complete=False,
            display_recipe=False,
        )

    def text(self, text: str, *, identity: bool = False) -> Badged:
        return Badged(
            None, text if identity else safe_prose(text), "", self.empty, self.p.render_hash
        )

    def section(self, title: str, entries: list[tuple[str, Badged]]) -> None:
        self.sections.append((title, entries))

    def number(
        self,
        path: str,
        value: float | None,
        unit: str,
        *,
        assessment: MetricAssessment | None = None,
        execution: str = "executed",
    ) -> Badged:
        declaration = self.declared_input(path, value) if assessment is None else None
        a = assessment if assessment is not None else declaration or self.evaluator.metric(path)
        rendered = badged(value, unit, a, self.p, execution=execution)
        if declaration is not None and value is not None:
            # Exact captured input metadata is not a computed prediction. Only the
            # closed declared_input pointer allow-list can reach this branch.
            number = str(value) if type(value) is int else repr(float(value))
            source = declaration.contributors[0]
            rendered = replace(
                rendered,
                number=number,
                text=f"{number} {unit} · declared captured input; not a measurement; "
                f"source={source.artifact_hash}{source.json_pointer}",
            )
        if not a.display_recipe:
            rendered = replace(
                rendered,
                text=rendered.text + "; no reviewed numeric recipe: unsupported presentation",
            )
        self.metrics[path] = rendered
        return rendered

    def declared_input(self, path: str, value: Any) -> MetricAssessment | None:
        """Quote a fixed existing captured input pointer, never authorize a result field."""
        match = re.fullmatch(
            r"/comparisons/(0|[1-9][0-9]*)/fixtures/(0|[1-9][0-9]*)/"
            r"(tp|query/(batch|total_context_tokens|n_prompts|prompt_tokens)|"
            r"projection_scope/(global_kv_heads|global_vocab|padded_vocab))",
            path,
        )
        if match:
            comparison = self.v.comparisons[int(match[1])]
            fixture = comparison.fixtures[int(match[2])]
            inventory = self.v.artifacts[comparison.reference_inventory_hash]
            matches = [
                i
                for i, f in enumerate(inventory["fixtures"])
                if f["fixture_id"] == fixture.fixture_id
            ]
            if len(matches) != 1:
                raise ValueError("CapturedInputBindingMismatch: fixture identity")
            reference_pointer = f"/fixtures/{matches[0]}/" + match[3]
            if (
                resolve_pointer(inventory, reference_pointer) != value
                or resolve_pointer(fixture.model_dump(mode="json"), "/" + match[3]) != value
            ):
                raise ValueError("CapturedInputBindingMismatch: fixture coordinate")
            model = EvidenceAssessment(
                "stub",
                content_hash(comparison.reference_model),
                "input",
                "input",
                reasons=("declared reference fixture coordinate; not a prediction",),
            )
            return replace(
                badge_for((), (model,), design_status=self.v.hardware.design_status),
                contributors=(
                    DependencySelector(
                        kind="prepared_content",
                        artifact_hash=comparison.reference_inventory_hash,
                        json_pointer=reference_pointer,
                    ),
                    DependencySelector(
                        kind="model_evidence",
                        artifact_hash=comparison.reference_inventory_hash,
                        json_pointer="/reference_model",
                    ),
                ),
            )
        pointer = None
        if path.startswith("/kv_layout/") or path == "/tp":
            pointer = "/intent" + path
        elif path.startswith("/request/model/"):
            pointer = "/intent" + path.removeprefix("/request")
        else:
            match = re.fullmatch(
                r"/rows/(0|[1-9][0-9]*)/(frequency_ratio|batch|total_context_tokens|n_prompts|prompt_tokens)",
                path,
            )
            if match:
                row = self.v.table.rows[int(match[1])]
                index = next(
                    i
                    for i, p in enumerate(self.v.bundle.points)
                    if p.payload_hash == row.point_hash
                )
                pointer = f"/points/{index}/" + (
                    "frequency_ratio" if match[2] == "frequency_ratio" else "query/" + match[2]
                )
        if pointer is None:
            return None
        artifact = self.v.bundle.model_dump(mode="json")
        if resolve_pointer(artifact, pointer) != value:
            raise ValueError("CapturedInputBindingMismatch")
        selector = DependencySelector(
            kind="prepared_content", artifact_hash=self.v.bundle.bundle_hash, json_pointer=pointer
        )
        model_selector = DependencySelector(
            kind="model_evidence",
            artifact_hash=self.v.assumptions.assumptions_hash,
            json_pointer="/model",
        )
        model = EvidenceAssessment(
            "stub",
            content_hash(self.v.assumptions.model),
            "input",
            "input",
            reasons=("declared captured input; not an accuracy assertion",),
        )
        return replace(
            badge_for((), (model,), design_status=self.v.hardware.design_status),
            contributors=(selector, model_selector),
        )

    def fields(
        self, value: Any, path: str, unit: str = "recorded value"
    ) -> list[tuple[str, Badged]]:
        if hasattr(value, "model_dump"):
            value = value.model_dump(mode="json")
        rows = []
        if isinstance(value, dict):
            for k, x in sorted(value.items()):
                rows.extend(self.fields(x, path + "/" + k, unit))
        elif isinstance(value, (tuple, list)):
            for n, x in enumerate(value):
                rows.extend(self.fields(x, path + "/" + str(n), unit))
        elif type(value) in (int, float) or value is None:
            field = path.rsplit("/", 1)[-1]
            units = {
                "matrix_ops": "op",
                "vector_ops": "op",
                "memory_read_bytes": "byte",
                "memory_write_bytes": "byte",
                "instances": "instances",
                "n_samples": "samples",
                "frequency_ratio": "ratio",
                "block_size_tokens": "tokens",
            }
            selected_unit = units.get(
                field, "ratio" if field.endswith("_rel") or field.endswith("_ratio") else unit
            )
            rows.append((path, self.number(path, value, selected_unit)))
        else:
            rows.append(
                (
                    path,
                    self.text(
                        str(value),
                        identity=bool(
                            isinstance(value, str)
                            and (
                                re.fullmatch(r"sha256:[0-9a-f]{64}", value)
                                or path == "/request/model/name"
                                or re.fullmatch(r"/rows/[0-9]+/op_results/[0-9]+/id", path)
                            )
                        ),
                    ),
                )
            )
        return rows

    def provenance(self) -> None:
        v = self.v
        entries = []
        for path, pointer, value in hardware_quotes(v.hardware.model_dump(mode="json")):
            selector = DependencySelector(
                kind="hardware_leaf",
                artifact_hash=v.table.hardware_spec_hash,
                json_pointer=pointer,
            )
            if resolve_pointer(
                v.hardware.model_dump(mode="json"), selector.json_pointer
            ) != value.model_dump(mode="json"):
                raise ValueError("HardwareInputBindingMismatch")
            a = replace(
                badge_for((value,), (), design_status=v.hardware.design_status),
                contributors=(selector,),
            )
            # The original input is quoted, never represented as an executed prediction.
            metric = self.number("/hardware/" + path, value.value, value.unit, assessment=a)
            text = metric.text.replace(
                "STUB — unvalidated model prediction", "STUB — unvalidated input assumption"
            )
            text += (
                "; kind="
                + value.kind
                + "; provenance="
                + str(value.provenance)
                + "; not a hardware measurement"
            )
            text += "; source=" + str(value.source) + "; date=" + str(value.date)
            text += "; rationale=" + safe_prose(str(value.rationale))
            if value.rationale and safe_prose(value.rationale) != value.rationale:
                text += "; original rationale retained at hardware source identity"
            metric = replace(metric, text=text)
            self.metrics["/hardware/" + path] = metric
            entries.append((path, metric))
        conditions = v.table.provenance.conditional_on
        stipulations = tuple(m for _, m in entries if m.assessment.conditional_on)
        count_value = len(stipulations)
        count = Badged(
            str(count_value),
            f"conditional · {count_value} stipulations; input inventory; not a prediction",
            "stipulations",
            combine_assessments(
                tuple(m.assessment for m in stipulations), v.hardware.design_status
            ),
            self.p.render_hash,
        )
        self.metrics["/hardware/stipulation_inventory_count"] = count
        entries.insert(0, ("Stipulation inventory count", count))
        self.section(
            "Conditional hardware inputs and original claim provenance",
            [
                (
                    "Conditions",
                    self.text(
                        "conditional: if built as specified; stipulated inputs listed below"
                        if conditions
                        else "No stipulated hardware inputs."
                    ),
                ),
                (
                    "Ceiling",
                    self.text(
                        "A chip that does not exist is never badged better than ESTIMATED."
                        " This can be commercially uncomfortable; it is the thesis applied"
                        " without exceptions."
                    ),
                ),
            ]
            + entries,
        )

    def context(self) -> None:
        v = self.v
        self.section(
            "Report identity",
            [
                (name, self.text(value, identity=True))
                for name, value in (
                    ("RenderSpec", self.p.render_hash),
                    ("Renderer", VERSION),
                    ("Number format", self.p.number_format),
                    ("Table", v.table.table_hash),
                    ("ReportContext", v.context.context_hash),
                    ("Request", v.table.request_hash),
                    ("Hardware", v.table.hardware_spec_hash),
                    ("Prepared bundle", v.bundle.bundle_hash),
                )
            ],
        )
        entries = [
            ("Initial state", self.text(v.table.initial_state)),
            ("Composite fidelity", self.text(v.table.composite_fidelity, identity=True)),
            ("Mapping policy", self.text(v.request.mapping_policy, identity=True)),
            ("Producer", self.text(v.table.preparation.name, identity=True)),
            ("Producer version", self.text(v.table.preparation.version, identity=True)),
            (
                "Producer implementation",
                self.text(v.table.preparation.implementation_hash, identity=True),
            ),
            (
                "Mapping interpretation",
                self.text(
                    "Imported prepared inputs remain authoritative. A mapping policy "
                    "name does not establish compiler match; mapping correspondence "
                    "remains unknown."
                ),
            ),
        ]
        for k, x in v.table.fidelity_detail.model_dump(mode="json").items():
            # Fidelity levels are named categories, not estimated numerical magnitudes.
            entries.append(
                (
                    "Fidelity " + k,
                    self.text("level " + str(x) if type(x) is int else str(x), identity=True),
                )
            )
        entries.extend(self.fields(v.table.kv_layout, "/kv_layout", "tokens"))
        entries.extend(self.fields(v.request.precision, "/precision"))
        entries.extend(self.fields(v.request.model, "/request/model"))
        entries.extend(self.fields(v.table.tp, "/tp", "ranks"))
        self.section("Request, state, KV layout and producer context", entries)
        self.section(
            "Model card and evidence",
            [
                ("Model identity", self.text(content_hash(v.assumptions.model), identity=True)),
                ("Model", self.text(v.assumptions.model.name, identity=True)),
                ("Engine", self.text(v.model_card.model_id.engine, identity=True)),
                ("Engine version", self.text(v.model_card.model_id.engine_version, identity=True)),
                (
                    "Model mapping policy",
                    self.text(v.model_card.model_id.mapping_policy, identity=True),
                ),
                ("Supplied card badge (not eligibility)", self.text(v.model_card.badge)),
                ("Model badge", self.text("STUB — no positive real proof profile is implemented")),
                ("Validated model error", self.text("unknown")),
                (
                    "Evidence status",
                    self.text(
                        "Verification is not model accuracy. Synthetic reviews of captured"
                        " computations do not validate the production model. Real "
                        "measurement/history/collector/compiler proof remains unsupported."
                    ),
                ),
            ]
            + [
                (eid, self.text(identity, identity=True))
                for eid, identity in sorted(v.context.evidence_index.items())
            ],
        )
        self.section(
            "Four supplied error records",
            self.fields(
                v.table.measured_error, "/measured_error", "relative error or sample count"
            ),
        )
        captured = CapturedWork(v.bundle, v.assumptions, v.request, v.derivation, v.jobs, v.results)
        known_empty = consumed_energy_families(captured) == ()
        self.section(
            "Energy",
            [
                ("Energy status", self.text("energy unverified; no energy quantity produced")),
                (
                    "Consumed families",
                    self.text(
                        "Known empty for this exact analytic model only; not a general "
                        "consumption claim."
                        if known_empty
                        else "Nonempty-family interpretation unsupported."
                    ),
                ),
            ],
        )
        evidence_entries = []
        for source in v.sources:
            evidence_entries.extend(
                [
                    ("Source identity", self.text(source.source_hash, identity=True)),
                    ("Raw source identity", self.text(source.raw_blob_sha256, identity=True)),
                    ("Source kind", self.text(source.kind)),
                    ("Reference identity", self.text(source.reference_identity)),
                    ("Reference version", self.text(source.reference_version, identity=True)),
                    (
                        "Declared independence",
                        self.text(
                            str(source.independence_from_candidate)
                            + "; assertion alone is not measurement proof"
                        ),
                    ),
                    ("Source limitation", self.text(source.limitation)),
                ]
            )
        for review in v.reviews:
            evidence_entries.extend(
                [
                    ("Review identity", self.text(review.review_hash, identity=True)),
                    ("Review decision", self.text(review.decision)),
                    ("Reviewer", self.text(review.reviewer)),
                    ("Review rationale", self.text(review.rationale)),
                ]
            )
        for ordering in v.orderings:
            evidence_entries.extend(
                [
                    ("Ordering identity", self.text(ordering.ordering_hash, identity=True)),
                    ("Prediction tree", self.text(ordering.prediction_tree_hash, identity=True)),
                    (
                        "Ordering eligibility",
                        self.text(
                            "Real history unsupported; declared booleans do not prove ancestry."
                        ),
                    ),
                ]
            )
        self.section(
            "Source, review and ordering declarations",
            evidence_entries
            or [("Status", self.text("No source/review/ordering declarations supplied."))],
        )
        self.section(
            "Verification records",
            [
                (
                    w.verification_hash,
                    self.text(
                        "Declared "
                        + w.rung
                        + " "
                        + w.purpose
                        + " outcome: "
                        + w.outcome
                        + "; declaration only; see raw proof interpretation; no accuracy promotion"
                    ),
                )
                for w in v.verifications
            ]
            or [("Status", self.text("No verification records supplied; unknown."))],
        )

    def rows(self) -> list[Plot]:
        v = self.v
        plots = []
        for ri, row in enumerate(v.table.rows):
            prefix = f"/rows/{ri}"
            items = []
            for field, value in row.model_dump(
                mode="json",
                exclude={
                    "op_results",
                    "diagnostics",
                    "counts",
                    "ext_counts",
                    "attribution_s",
                    "peak_resident_bytes",
                },
            ).items():
                if field.endswith("_hash"):
                    items.append((field, self.text(value, identity=True)))
                else:
                    items.extend(
                        self.fields(
                            value, prefix + "/" + field, "s" if field.endswith("_s") else "input"
                        )
                    )
            items.extend(self.fields(row.counts, prefix + "/counts", "op or byte"))
            items.extend(self.fields(row.attribution_s, prefix + "/attribution_s", "s"))
            items.extend(self.fields(row.ext_counts, prefix + "/ext_counts", "byte or flit-hop"))
            items.extend(
                self.fields(row.peak_resident_bytes, prefix + "/peak_resident_bytes", "byte")
            )
            items.extend(self.fields(row.diagnostics, prefix + "/diagnostics", "diagnostic"))
            self.section("Row " + str(ri) + " — " + row.phase, items)
            points = []
            for oi, op in enumerate(row.op_results):
                opath = prefix + f"/op_results/{oi}"
                fields = []
                for field, value in op.model_dump(
                    mode="json", exclude={"scope", "id", "group_id"}
                ).items():
                    fields.extend(
                        self.fields(
                            value,
                            opath + "/" + field,
                            "op/byte"
                            if field.endswith("ops_per_byte")
                            else "op/s"
                            if field.endswith("ops_per_s")
                            else "ps"
                            if field.endswith("_ps")
                            else "byte/s"
                            if field.endswith("bytes_per_s")
                            else "op or byte",
                        )
                    )
                # Ratios keep both numerator and denominator sources. Values themselves
                # are captured A fields, never recomputed workload arithmetic.
                ratios = {
                    "operational_intensity_ops_per_byte": (
                        "counts/matrix_ops",
                        "counts/memory_read_bytes",
                        "counts/memory_write_bytes",
                    ),
                    "achieved_ops_per_s": ("counts/matrix_ops", "duration_ps"),
                    "ridge_ops_per_byte": ("matrix_peak_ops_per_s", "dram_bw_bytes_per_s"),
                }
                for name, deps in ratios.items():
                    current = self.metrics[opath + "/" + name]
                    a = combine_assessments(
                        (current.assessment,)
                        + tuple(self.metrics[opath + "/" + d].assessment for d in deps),
                        v.hardware.design_status,
                    )
                    guarded = self.number(
                        opath + "/" + name, getattr(op, name), current.unit, assessment=a
                    )
                    fields = [(k, guarded if k == opath + "/" + name else m) for k, m in fields]
                fields.extend(self.fields(op.scope, opath + "/scope"))
                fields.append(("Source identity", self.text(row.result_hash, identity=True)))
                self.section("Operator " + op.id, fields)
                points.append(
                    (
                        CapturedIdentifier("op_id", op.id),
                        self.metrics[opath + "/operational_intensity_ops_per_byte"],
                        self.metrics[opath + "/achieved_ops_per_s"],
                        self.metrics[opath + "/ridge_ops_per_byte"],
                        self.metrics[opath + "/matrix_peak_ops_per_s"],
                    )
                )
            plots.append(roofline(tuple(points), self.p))
        return plots

    def comparisons(self) -> None:
        for track, title in (
            ("nominal_compatibility", "Nominal compatibility"),
            ("physical_discrepancy", "Physical discrepancies"),
        ):
            entries = []
            for ci, c in enumerate(self.v.comparisons):
                if c.track != track:
                    continue
                entries.extend(
                    [
                        ("Comparison identity", self.text(c.comparison_hash, identity=True)),
                        ("Candidate model", self.text(content_hash(c.candidate), identity=True)),
                        (
                            "Reference model",
                            self.text(content_hash(c.reference_model), identity=True),
                        ),
                        ("Gate", self.text(c.gate_outcome)),
                        ("Evidence outcome", self.text(c.evidence_outcome)),
                        ("Classification", self.text(c.classification)),
                        ("Reference basis", self.text(c.reference_basis)),
                    ]
                )
                for fi, f in enumerate(c.fixtures):
                    entries.append((f.fixture_id, self.text(f.execution + "; " + f.outcome)))
                    for ki, ch in enumerate(f.channels):
                        path = f"/comparisons/{ci}/fixtures/{fi}/channels/{ki}"
                        entries.append(
                            (
                                ch.channel,
                                self.text(
                                    ch.outcome
                                    + "; reference "
                                    + ch.reference.state
                                    + "; actual "
                                    + ch.actual.state
                                    + "; "
                                    + ch.reason
                                ),
                            )
                        )
                        inventory = self.v.artifacts[c.reference_inventory_hash]
                        ref_index = next(
                            j
                            for j, item in enumerate(inventory["fixtures"])
                            if item["fixture_id"] == f.fixture_id
                        )
                        ref_key = (
                            c.reference_inventory_hash,
                            f"/fixtures/{ref_index}/values/{ch.channel}/value",
                        )
                        for side, value, key in (
                            (
                                "actual",
                                ch.actual.value,
                                (ch.actual.source_hash, ch.actual.source_pointer),
                            ),
                            ("reference", ch.reference.value, ref_key),
                        ):
                            a = (
                                self.evaluator.source(key)
                                if key in self.evaluator.sources
                                else self.empty
                            )
                            # Source recipes preserve provenance, but do not grant a new
                            # raw-value display surface without its own reviewed recipe (D04).
                            a = combine_assessments(
                                (a, self.evaluator.metric(path + "/" + side + "/value")),
                                self.v.hardware.design_status,
                            )
                            a = replace(
                                a,
                                synthetic=a.synthetic
                                or c.classification == "synthetic_presentation",
                            )
                            execution = {"pre_call_refusal": "refused"}.get(
                                f.execution, f.execution
                            )
                            entries.append(
                                (
                                    path + "/" + side + "/value",
                                    self.number(
                                        path + "/" + side + "/value",
                                        value,
                                        ch.unit,
                                        assessment=a,
                                        execution=execution,
                                    ),
                                )
                            )
                        for name in (
                            "raw_rel",
                            "residual_rel",
                            "signed_adjustment_rel",
                            "absolute_adjustment_rel",
                        ):
                            a = self.evaluator.metric(path + "/" + name)
                            if c.classification == "synthetic_presentation":
                                a = replace(a, synthetic=True)
                            state = {"pre_call_refusal": "refused"}.get(f.execution, f.execution)
                            entries.append(
                                (
                                    path + "/" + name,
                                    self.number(
                                        path + "/" + name,
                                        getattr(ch, name),
                                        "relative",
                                        assessment=a,
                                        execution=state,
                                    ),
                                )
                            )
                        entries.extend(
                            self.fields(
                                ch.declared_deviations, path + "/declared_deviations", "relative"
                            )
                        )
                    entries.extend(
                        self.fields(f.precision, f"/comparisons/{ci}/fixtures/{fi}/precision")
                    )
                    entries.extend(
                        self.fields(f.tp, f"/comparisons/{ci}/fixtures/{fi}/tp", "ranks")
                    )
                    entries.extend(self.fields(f.query, f"/comparisons/{ci}/fixtures/{fi}/query"))
                    entries.extend(
                        self.fields(
                            f.projection_scope, f"/comparisons/{ci}/fixtures/{fi}/projection_scope"
                        )
                    )
                    entries.append(
                        ("Component binding", self.text(f.component_binding_hash, identity=True))
                    )
                for refusal in c.precision_refusal_observations:
                    entries.extend(self.fields(refusal, "/precision_refusal"))
                entries.extend(("Limitation", self.text(x)) for x in c.limitations)
            self.section(
                title,
                entries
                or [
                    (
                        "Status",
                        self.text(
                            self.v.table.comparison_state
                            + "; no comparison record supplied — unassessed."
                        ),
                    )
                ],
            )

    def contributors(self) -> None:
        entries = []
        for path, metric in sorted(self.metrics.items()):
            if not metric.assessment.contributors:
                continue
            names = "; ".join(
                s.kind + " " + s.artifact_hash + " " + s.json_pointer
                for s in metric.assessment.contributors
            )
            entries.append((path, self.text(names, identity=True)))
            for model in metric.assessment.models:
                entries.append(
                    (
                        "Source model",
                        self.text(
                            model.model_identity_hash
                            + "; "
                            + model.purpose
                            + "; "
                            + model.granularity,
                            identity=True,
                        ),
                    )
                )
                entries.append(
                    (
                        "Applicability",
                        self.text(
                            "; ".join(model.reasons)
                            or "No applicable real model accuracy evidence."
                        ),
                    )
                )
        self.section("Complete numeric contributors and independent source applicability", entries)


def _render(v: VerifiedReportInputs, p: RenderSpec) -> ReportOutput:
    verify_identity(p, "render_hash")
    if (p.table_hash, p.report_context_hash, p.renderer_version) != (
        v.table.table_hash,
        v.context.context_hash,
        VERSION,
    ):
        raise ValueError("RenderIdentityBindingMismatch")
    d = Document(v, p)
    d.context()
    d.section(
        "Raw proof interpretation",
        [
            (identity, d.text(status))
            for identity, status in proof_statuses(
                v, allow_synthetic=p.allow_synthetic_presentation
            )
        ]
        or [("Status", d.text("No raw evidence supplied; unknown."))],
    )
    d.provenance()
    plots = d.rows()
    d.comparisons()
    d.contributors()
    warnings = tuple(
        dict.fromkeys(
            v.table.warnings
            + v.context.limitations
            + tuple(x for r in v.results for x in r.unrepresented)
        )
    )
    d.section("Warnings and omissions", [(safe_prose("Warning"), d.text(w)) for w in warnings])
    d.section(
        "What this table does not claim",
        [
            (
                "Limits",
                d.text(
                    "These are captured analytic computations, not executed hardware "
                    "measurements. STUB predictions have no demonstrated model "
                    "accuracy. Proposed hardware is capped at ESTIMATED. Error is "
                    "unknown unless independently supplied and eligible; deterministic"
                    " predictions provide no confidence interval. Energy is "
                    "unverified. Isolated per-op roofline estimates; durations do not "
                    "add to aggregate latency. " + " ".join(warnings)
                ),
            )
        ],
    )
    for _, entries in d.sections:
        for _, metric in entries:
            if not isinstance(metric, Badged) or metric.render_hash != p.render_hash:
                raise ValueError("RenderPermissionMismatch")
    if any(not isinstance(plot, Plot) or plot.render_hash != p.render_hash for plot in plots):
        raise ValueError("RenderPermissionMismatch: plot")
    env = Environment(undefined=StrictUndefined, autoescape=True, keep_trailing_newline=True)
    for name in ("complete.html.j2", "complete.md.j2"):
        lint_template((TEMPLATES / name).read_text())
    html_out = env.from_string((TEMPLATES / "complete.html.j2").read_text()).render(
        sections=d.sections, plots=plots
    )
    md_env = Environment(undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True)
    sections = [
        (
            _markdown(title),
            [
                (_markdown(label), replace(metric, text=html.escape(_markdown(metric.text))))
                for label, metric in entries
            ],
        )
        for title, entries in d.sections
    ]
    md_out = md_env.from_string((TEMPLATES / "complete.md.j2").read_text()).render(
        sections=sections, plots=plots
    )
    return ReportOutput(html_out, md_out, p, d.metrics)


def render_verified(
    inputs: VerifiedReportInputs,
    *,
    show_unvalidated_predictions: bool = False,
    allow_synthetic_presentation: bool = False,
    render_spec: RenderSpec | None = None,
) -> ReportOutput:
    verified = verify_report_inputs(inputs.table, inputs.artifacts)
    if verified != inputs:
        raise ValueError("VerifiedInputMismatch: carrier aggregate was substituted")
    p = render_spec or permissions(
        verified, show_unvalidated_predictions, allow_synthetic_presentation
    )
    return _render(verified, p)


def write_report(
    table_path: Path,
    *,
    html_path: Path | None = None,
    markdown_path: Path | None = None,
    artifact_dir: Path | None = None,
    show_unvalidated_predictions: bool = False,
    allow_synthetic_presentation: bool = False,
) -> ReportOutput:
    table_path = Path(table_path)
    outputs = (
        Path(html_path) if html_path is not None else table_path.with_suffix(".report.html"),
        Path(markdown_path) if markdown_path is not None else table_path.with_suffix(".report.md"),
    )
    if outputs[0].resolve() == outputs[1].resolve() or any(
        p.exists() or p.is_symlink() or not p.parent.is_dir() for p in outputs
    ):
        raise ValueError(
            "OutputConflict: distinct absent output files with existing parent directories required"
        )
    v = load_verified_report_inputs(table_path, artifact_dir=artifact_dir)
    result = _render(v, permissions(v, show_unvalidated_predictions, allow_synthetic_presentation))
    # Exclusive creation refuses late collisions too; a multi-file filesystem transaction
    # is not claimed under concurrent mutation or I/O failure.
    for path, text in zip(outputs, (result.html, result.markdown), strict=True):
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    return result
