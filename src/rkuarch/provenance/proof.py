"""Bounded raw /2 capture and synthetic verification semantics over A's closed inputs.

No real collector/history/expected-source interpreter and no accuracy promotion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from uarch_contract.assumptions import ModelIdentity
from uarch_contract.evidence import EvidencePrecision, EvidenceScopeCase, SourceRecord
from uarch_contract.hashing import (
    content_hash,
    resolve_artifact,
    resolve_pointer,
    sha256,
    verify_declared_artifact_closure,
)
from uarch_contract.prepared import PreparedBundle
from uarch_contract.request import CharacterizationRequest

from rkuarch.engines.protocol import validate_engine_job, validate_engine_result
from rkuarch.table.artifacts import VerifiedReportInputs

from .applicability import _accepted_review, match_scope
from .proof_raw import (  # Re-export the bounded public entry points.
    SCHEMAS,
    DecodedProof,
    ProofRefusal,
    ProofUnsupported,
    decimal_text,
    decimal_value,
    decode_proof,
    error_band,
    exact_scalar,
    json_bytes,
    require,
    shape,
)

__all__ = [
    "ProofRefusal",
    "ProofUnsupported",
    "decode_proof",
    "exact_scalar",
    "decimal_text",
    "error_band",
    "bind_capture",
    "interpret_verification",
    "interpret_measurement",
    "interpret_ordering",
    "bind_prediction",
    "check_target_applicability",
]


@dataclass(frozen=True)
class BoundCapture:
    value: Fraction
    model_identity_hash: str
    purpose: str
    granularity: str
    scopes: tuple[EvidenceScopeCase, ...]
    artifact_hash: str
    pointer: str


@dataclass(frozen=True)
class VerificationAssessment:
    """Local outcome, not a shared carrier, badge, or a claim of real model accuracy."""

    outcome: str
    cases: tuple[tuple[str, str], ...]
    synthetic: bool
    model_identity_hash: str
    purpose: str


def _closure(v: VerifiedReportInputs) -> frozenset[str]:
    try:
        return frozenset(verify_declared_artifact_closure(v.table.table_hash, v.artifacts))
    except (ValueError, KeyError) as e:
        raise ProofUnsupported("UNSUPPORTED_CAPTURE_CLOSURE") from e


def _artifact(v: VerifiedReportInputs, identity: str, closed: frozenset[str]) -> dict[str, Any]:
    if identity not in closed or identity not in v.artifacts:
        raise ProofUnsupported("UNSUPPORTED_CAPTURE_NOT_IN_CLOSURE")
    try:
        return resolve_artifact(identity, v.artifacts)
    except ValueError as e:
        raise ProofRefusal("MISMATCH_CAPTURE_HASH") from e


def bind_capture(
    v: VerifiedReportInputs, ref: dict[str, Any], case: dict[str, Any]
) -> BoundCapture:
    """Resolve a particular historical capture, never the requesting row's equal scalar."""
    capture_spec = SCHEMAS["suite-records"]["anyOf"][1]["properties"]["cases"]["items"][
        "properties"
    ]["capture"]
    shape(ref, capture_spec)
    for key in (
        "model_identity_hash",
        "input_hash",
        "kind",
        "group_id",
        "operator_id",
        "quantity",
        "source_unit",
    ):
        require(ref[key] == case[key], "MISMATCH_CAPTURE_" + key.upper())
    require(ref["value"]["json_pointer"] == case["metric_pointer"], "MISMATCH_CAPTURE_POINTER")
    closed = _closure(v)
    identity, pointer = ref["value"]["artifact_hash"], ref["value"]["json_pointer"]
    output = _artifact(v, identity, closed)
    sources = [
        s
        for s in v.dependencies.source_recipes
        if (s.artifact_hash, s.recipe.metric_path) == (identity, pointer)
    ]
    if not sources:
        raise ProofUnsupported("UNSUPPORTED_CAPTURE_RECIPE")
    require(len(sources) == 1, "MISMATCH_CAPTURE_RECIPE")
    source = sources[0]
    require(
        source.model_identity_hash == ref["model_identity_hash"]
        and source.recipe.purpose == case["purpose"]
        and source.recipe.granularity == case["granularity"],
        "MISMATCH_SOURCE_RECIPE",
    )
    # Contributors are not replaced by the terminal scalar. Require the full typed graph.
    from uarch_contract.report_context import validate_metric_dependencies

    validate_metric_dependencies(v.dependencies, v.artifacts)
    quantity = ref["quantity"]
    require(
        case["purpose"] == ("duration" if quantity == "duration" else "counts"),
        "MISMATCH_CAPTURE_PURPOSE",
    )
    scopes: tuple[EvidenceScopeCase, ...] = ()
    if ref["kind"] == "engine_result":
        require(
            output.get("protocol") == "uarch-engine/1" and "result_hash" in output,
            "MISMATCH_CAPTURE_KIND",
        )
        require(output["job_hash"] == ref["input_hash"], "MISMATCH_CAPTURE_INPUT")
        job_data = _artifact(v, ref["input_hash"], closed)
        require(
            job_data["bundle_hash"] == ref["bundle_hash"]
            and job_data["point_hash"] == ref["point_hash"],
            "MISMATCH_CAPTURE_RUN",
        )
        bundle = PreparedBundle.model_validate(_artifact(v, ref["bundle_hash"], closed))
        request = CharacterizationRequest(
            **bundle.intent.model_dump(mode="json"), prepared_input_hash=bundle.bundle_hash
        )
        try:
            job = validate_engine_job(job_data, bundle, request)
            result = validate_engine_result(output, job)
        except ValueError as e:
            raise ProofRefusal("MISMATCH_CAPTURE_VALIDATION") from e
        require(
            content_hash(job.engine.model) == ref["model_identity_hash"], "MISMATCH_CAPTURE_MODEL"
        )
        index = re.fullmatch(r"/per_op/(0|[1-9][0-9]*)/(duration_ps|counts/[a-z_]+)", pointer)
        if index:
            i = int(index[1])
            require(i < len(result.per_op), "MISMATCH_CAPTURE_OPERATOR")
            op = result.per_op[i]
            require(
                (op.group_id, op.id) == (ref["group_id"], ref["operator_id"])
                and case["granularity"] == "operator",
                "MISMATCH_CAPTURE_OPERATOR",
            )
            ops = [op]
            prefix = f"/per_op/{i}"
        else:
            require(
                ref["group_id"] is None
                and ref["operator_id"] is None
                and case["granularity"] == "whole_iteration",
                "MISMATCH_CAPTURE_GRANULARITY",
            )
            ops = list(result.per_op)
            prefix = ""
        expected_pointer = prefix + (
            "/duration_ps" if quantity == "duration" else "/counts/" + quantity
        )
        expected_unit = (
            "ps"
            if quantity == "duration"
            else "byte"
            if quantity in ("memory_read_bytes", "memory_write_bytes")
            else "count"
        )
        require(
            pointer == expected_pointer and ref["source_unit"] == expected_unit,
            "MISMATCH_CAPTURE_CHANNEL_OR_UNIT",
        )
        if not _accepted_review(v.registry, v.artifacts):
            raise ProofUnsupported("UNSUPPORTED_FAMILY_REVIEW")
        families = [
            e.family
            for e in v.registry.entries
            if e.hardware_spec_hash == job.hardware.hardware_spec_hash
        ]
        if len(families) != 1:
            raise ProofUnsupported("UNSUPPORTED_FAMILY")
        # Exactly the A3 captured field correspondence, for this historical job/bundle.
        scopes = tuple(
            EvidenceScopeCase(
                family=families[0],
                hardware_spec_hash=job.hardware.hardware_spec_hash,
                prepared_bundle_hash=bundle.bundle_hash,
                model_identity_hash=ref["model_identity_hash"],
                frequency_ratio=job.point.frequency_ratio,
                initial_state=job.initial_state,
                kv_block_size_tokens=request.kv_layout.block_size_tokens,
                mapping_correspondence_hash=None,
                precision=EvidencePrecision.model_validate(op.scope.precision_roles.model_dump()),
                **op.scope.model_dump(exclude={"precision_roles"}),
            )
            for op in ops
        )
    else:
        # These are the actual delivered nominal carrier fields, validated by A's loader.
        require(output.get("format") == "uarch-nominal-output/1", "MISMATCH_CAPTURE_KIND")
        input_value = _artifact(v, ref["input_hash"], closed)
        require(
            input_value.get("format") == "uarch-nominal-input/1"
            and output["input_hash"] == ref["input_hash"],
            "MISMATCH_CAPTURE_INPUT",
        )
        # Preserve the delivered nominal execution/component identity even when
        # memory-bound duration happens to remain numerically unchanged.
        from uarch_contract.exports import (
            ExecutionModelInput,
            ExportBinding,
            UpstreamComponentBinding,
        )
        from uarch_contract.hashing import verify_identity

        execution = ExecutionModelInput.model_validate(input_value["execution_model"])
        verify_identity(execution, "execution_model_hash")
        binding_data = _artifact(v, input_value["component_binding_hash"], closed)
        binding: ExportBinding | UpstreamComponentBinding
        if binding_data.get("format") == "uarch-export-binding/1":
            binding = ExportBinding.model_validate(binding_data)
        elif binding_data.get("format") == "uarch-upstream-component/1":
            binding = UpstreamComponentBinding.model_validate(binding_data)
        else:
            raise ProofUnsupported("UNSUPPORTED_NOMINAL_COMPONENT_BINDING")
        require(
            binding.execution_model_hash == execution.execution_model_hash,
            "MISMATCH_NOMINAL_EXECUTION_BINDING",
        )
        require(
            output["model_identity"] == input_value["model_identity"]
            and content_hash(ModelIdentity.model_validate(output["model_identity"]))
            == ref["model_identity_hash"],
            "MISMATCH_CAPTURE_MODEL",
        )
        require(
            all(ref[k] is None for k in ("bundle_hash", "point_hash", "group_id", "operator_id")),
            "MISMATCH_NOMINAL_SCOPE",
        )
        if quantity != "duration":
            raise ProofUnsupported("UNSUPPORTED_NOMINAL_BASIS")
        require(
            pointer == "/duration_s"
            and ref["source_unit"] == "s"
            and case["granularity"] == "whole_iteration",
            "MISMATCH_CAPTURE_CHANNEL_OR_UNIT",
        )
    try:
        scalar = resolve_pointer(output, pointer)
    except ValueError as e:
        raise ProofRefusal("MISMATCH_CAPTURE_POINTER") from e
    return BoundCapture(
        exact_scalar(scalar, ref["source_unit"]),
        ref["model_identity_hash"],
        case["purpose"],
        case["granularity"],
        scopes,
        identity,
        pointer,
    )


class _Members:
    def __init__(self, v: VerifiedReportInputs, owner: str):
        self.v = v
        self.owner = owner
        self.closed = _closure(v)
        self.used: dict[str, set[str]] = {}

    def source(self, identity: str) -> tuple[SourceRecord, DecodedProof]:
        data = _artifact(self.v, identity, self.closed)
        source = SourceRecord.model_validate(data)
        require(any(s == source for s in self.v.sources), "MISMATCH_SOURCE_INVENTORY")
        raw = self.v.artifacts.get(source.raw_blob_sha256)
        if not isinstance(raw, bytes) or source.raw_blob_sha256 not in self.closed:
            raise ProofUnsupported("UNSUPPORTED_RAW_CLOSURE")
        require(sha256(raw) == source.raw_blob_sha256, "MALFORMED_RAW_HASH")
        return source, decode_proof(raw)

    def reference_identity(
        self, ref: dict[str, Any], *, owner: str, role: str | None = None
    ) -> tuple[str, str, str]:
        """Null is relative to the containing member, never implicitly to the proof root."""
        shape(ref, SCHEMAS["capture-links"]["properties"]["suite_plan"])
        if role is not None:
            require(ref["member_name"] == role, "MALFORMED_MEMBER_ROLE: " + role)
        return (ref["source_record_hash"] or owner, ref["member_name"], ref["member_sha256"])

    def member(
        self, ref: dict[str, Any], *, owner: str, role: str | None = None
    ) -> tuple[SourceRecord, DecodedProof, bytes]:
        identity, name, digest = self.reference_identity(ref, owner=owner, role=role)
        # decode_proof validates the exact schema for each named member before use.
        source, proof = self.source(identity)
        if name not in proof.members:
            raise ProofUnsupported("UNSUPPORTED_MEMBER_ABSENT")
        raw = proof.members[name]
        require(sha256(raw) == digest, "MISMATCH_MEMBER_HASH")
        self.used.setdefault(identity, set()).add(name)
        return source, proof, raw

    def audit(self) -> None:
        """Follow only declared raw MemberRefs; reject unused optional members, including cycles."""
        from .proof_raw import REQUIRED, SUPPORT, json_bytes

        _, root = self.source(self.owner)
        queue = [(self.owner, n) for n in REQUIRED[root.kind] if n.endswith(".json")]
        visited: set[tuple[str, str]] = set()
        while queue:
            owner, name = queue.pop()
            if (owner, name) in visited:
                continue
            visited.add((owner, name))
            _, proof = self.source(owner)
            self.used.setdefault(owner, set()).add(name)
            if not name.endswith(".json"):
                continue
            stack = [json_bytes(proof.members[name])]
            while stack:
                value = stack.pop()
                if isinstance(value, dict):
                    if set(value) == {"source_record_hash", "member_name", "member_sha256"}:
                        target = dict(value)
                        target["source_record_hash"] = target["source_record_hash"] or owner
                        self.member(target, owner=owner)
                        queue.append((target["source_record_hash"], target["member_name"]))
                    else:
                        for key, child in value.items():
                            role = {
                                "suite_plan": "suite-plan.json",
                                "capture_inventory": "capture-inventory.json",
                                "independent_expected": "independent-expected.json",
                                "original_reference": "original-expected.txt",
                                "original_output": "original-compiler.txt",
                            }.get(key)
                            if key == "independent_reference":
                                role = {
                                    "verification_observed": "independent-expected.json",
                                    "fidelity_count": "compiler-counts.json",
                                }.get(value.get("role", ""))
                            if role is not None and child is not None:
                                self.reference_identity(child, owner=owner, role=role)
                            stack.append(child)
                elif isinstance(value, list):
                    stack.extend(value)
        for owner, used in self.used.items():
            _, proof = self.source(owner)
            require(not ((set(proof.members) & SUPPORT) - used), "MALFORMED_UNREFERENCED_MEMBER")


def _case_inventory(m: _Members) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    _, proof = m.source(m.owner)
    links = proof.json("capture-links.json")
    plan_source, _, plan_raw = m.member(links["suite_plan"], owner=m.owner, role="suite-plan.json")
    inventory_source, _, inventory_raw = m.member(
        links["capture_inventory"], owner=m.owner, role="capture-inventory.json"
    )
    plan, inventory = json_bytes(plan_raw), json_bytes(inventory_raw)
    require(
        m.reference_identity(
            inventory["suite_plan"], owner=inventory_source.source_hash, role="suite-plan.json"
        )
        == m.reference_identity(links["suite_plan"], owner=m.owner, role="suite-plan.json"),
        "MISMATCH_SUITE_PLAN",
    )
    for values in (plan["cases"], inventory["cases"]):
        require(len({c["case_id"] for c in values}) == len(values), "MALFORMED_DUPLICATE_CASE")
    require(
        len({(c["case_id"], c["role"]) for c in links["entries"]}) == len(links["entries"]),
        "MALFORMED_DUPLICATE_LINK",
    )
    _, proof = m.source(m.owner)
    model = content_hash(ModelIdentity.model_validate(proof.json("model.json")))
    if proof.kind == "verification":
        subject = proof.json("verification.json")
        relevant = [
            c
            for c in plan["cases"]
            if c["model_identity_hash"] == model and c["purpose"] == subject["purpose"]
        ]
    else:
        subject = proof.json("prediction.json")
        relevant = [
            c
            for c in plan["cases"]
            if c["model_identity_hash"] == model and c["benchmark_id"] == subject["benchmark_id"]
        ]
    ids = {c["case_id"] for c in relevant}
    require(
        bool(ids) and {c["case_id"] for c in inventory["cases"]} == ids, "INCOMPLETE_RELEVANT_SUITE"
    )
    roles = {(c["case_id"], role) for c in relevant for role in c["required_roles"]}
    require(
        roles == {(c["case_id"], c["role"]) for c in links["entries"]}, "INCOMPLETE_SUITE_ROLES"
    )
    m.audit()
    return plan_source.source_hash, plan, inventory, links


def bind_prediction(v: VerifiedReportInputs, source_hash: str) -> BoundCapture:
    """Bind frozen prediction assertions to their own capture; not collector eligibility."""
    m = _Members(v, source_hash)
    source, proof = m.source(source_hash)
    require(proof.kind == "measurement", "MISMATCH_PROOF_KIND")
    records = [
        e
        for e in v.evidence
        if e.source_hash == source_hash and e.evidence_hash in v.context.evidence_index.values()
    ]
    if not records or not source.independence_from_candidate:
        raise ProofUnsupported("UNSUPPORTED_PREDICTION_REVIEW")
    if not all(_accepted_review(e, v.artifacts) for e in records):
        raise ProofUnsupported("UNSUPPORTED_PREDICTION_REVIEW")
    prediction = proof.json("prediction.json")
    scope_record = EvidenceScopeCase.model_validate(proof.json("scope.json"))
    require(
        all(
            e.classification == proof.classification
            and e.purpose == prediction["purpose"]
            and e.channel == prediction["channel"]
            and e.granularity == prediction["granularity"]
            and e.scope == (scope_record,)
            for e in records
        ),
        "MISMATCH_PREDICTION_SUBJECT",
    )
    plan_owner, plan, inventory, links = _case_inventory(m)
    selected = [
        c
        for c in plan["cases"]
        if c["benchmark_id"] == prediction["benchmark_id"]
        and c["model_identity_hash"] == prediction["model_identity_hash"]
        and "prediction" in c["required_roles"]
    ]
    require(len(selected) == 1, "MISMATCH_PREDICTION_CASE")
    case = selected[0]
    items = [c for c in inventory["cases"] if c["case_id"] == case["case_id"]]
    entries = [
        c for c in links["entries"] if c["case_id"] == case["case_id"] and c["role"] == "prediction"
    ]
    require(len(items) == len(entries) == 1, "INCOMPLETE_PREDICTION_CAPTURE")
    link = entries[0]
    require(
        link["proof_member"] == "prediction.json"
        and link["proof_pointer"] == "/value"
        and link["benchmark_id"] == items[0]["benchmark_id"] == case["benchmark_id"]
        and link["independent_reference"] is None,
        "MISMATCH_PREDICTION_LINK",
    )
    bound = bind_capture(v, items[0]["capture"], case)
    require(decimal_value(prediction["value"]) == bound.value, "MISMATCH_PREDICTION_SCALAR")
    expected_unit = "s" if case["quantity"] == "duration" else case["source_unit"]
    require(
        prediction["purpose"] == bound.purpose
        and prediction["granularity"] == bound.granularity
        and prediction["unit"] == expected_unit
        and prediction["channel"]
        == ("duration_s" if case["quantity"] == "duration" else case["quantity"]),
        "MISMATCH_PREDICTION_CHANNEL",
    )
    require(
        prediction["source_identity"] == source.reference_identity
        and prediction["source_version"] == source.reference_version,
        "MISMATCH_SOURCE",
    )
    require(
        prediction["suite_sha256"] == sha256(proof.members["suite.json"])
        and prediction["scope_sha256"] == sha256(proof.members["scope.json"])
        and content_hash(ModelIdentity.model_validate(proof.json("model.json")))
        == bound.model_identity_hash,
        "MISMATCH_PREDICTION_MEMBERS",
    )
    suite = proof.json("suite.json")
    require(
        all(
            suite[k] == prediction[k]
            for k in ("benchmark_id", "purpose", "channel", "granularity", "unit")
        ),
        "MISMATCH_SUITE",
    )
    scope = EvidenceScopeCase.model_validate(proof.json("scope.json"))
    if not bound.scopes:
        raise ProofUnsupported("UNSUPPORTED_NOMINAL_SCOPE")
    require(all(s == scope for s in bound.scopes), "MISMATCH_CAPTURE_SCOPE")
    return bound


def check_target_applicability(
    bound: BoundCapture, target: tuple[EvidenceScopeCase, ...], dimensions: tuple[str, ...]
) -> tuple[dict[str, str], ...]:
    """Separate source/target applicability; nulls stay UNKNOWN, never borrowed bins."""
    if not target:
        raise ProofUnsupported("UNSUPPORTED_TARGET_SCOPE")
    require(
        all(t.model_identity_hash == bound.model_identity_hash for t in target),
        "MISMATCH_TARGET_SOURCE_MODEL",
    )
    if not bound.scopes:
        raise ProofUnsupported("UNSUPPORTED_CAPTURE_SCOPE")
    mandatory = (
        "model_identity_hash",
        "family",
        "precision",
        "mapping_match",
        "initial_state",
        "kv_block_size_tokens",
        "frequency_ratio",
    )
    dims = tuple(
        sorted(
            set(
                dimensions
                + mandatory
                + (
                    ("prepared_bundle_hash",)
                    if bound.granularity == "whole_iteration"
                    else ("op_class",)
                )
            )
        )
    )
    return tuple(match_scope(s, t, dims) for t in target for s in bound.scopes)


def interpret_verification(
    v: VerifiedReportInputs, identity: str, *, allow_synthetic: bool = False
) -> VerificationAssessment:
    """Complete observed-suite reduction; real source-specific expected parsers stay unsupported."""
    records = [w for w in v.verifications if w.verification_hash == identity]
    if len(records) != 1 or identity not in v.context.verification_hashes:
        raise ProofUnsupported("UNSUPPORTED_VERIFICATION_RECORD")
    w = records[0]
    _artifact(v, identity, _closure(v))
    if not _accepted_review(w, v.artifacts):
        raise ProofUnsupported("UNSUPPORTED_VERIFICATION_REVIEW")
    m = _Members(v, w.source_hash)
    source, proof = m.source(w.source_hash)
    require(proof.kind == "verification", "MISMATCH_PROOF_KIND")
    raw, checks = proof.json("verification.json"), proof.json("checks.json")
    require(
        raw["model_identity_hash"]
        == checks["model_identity_hash"]
        == w.model_identity_hash
        == content_hash(ModelIdentity.model_validate(proof.json("model.json")))
        and raw["purpose"] == checks["purpose"] == w.purpose
        and raw["rung"] == checks["rung"] == w.rung
        and raw["outcome"] == w.outcome
        and raw["source_identity"] == source.reference_identity
        and raw["source_version"] == source.reference_version
        and raw["checks_sha256"] == sha256(proof.members["checks.json"])
        and raw["scope_sha256"] == checks["scope_sha256"] == sha256(proof.members["scope.json"]),
        "MISMATCH_VERIFICATION_METADATA",
    )
    scope = EvidenceScopeCase.model_validate(proof.json("scope.json"))
    require(tuple(w.scope) == (scope,), "MISMATCH_VERIFICATION_SCOPE")
    if w.purpose == "energy":
        raise ProofUnsupported("UNSUPPORTED_ENERGY_FAMILY_CAPTURE")
    require(raw["family"] is None and checks["family"] is None, "MISMATCH_FAMILY")
    require(
        not checks["candidate_used_for_expected"] and source.independence_from_candidate,
        "MISMATCH_EXPECTED_INDEPENDENCE",
    )
    plan_owner, plan, inventory, links = _case_inventory(m)
    selected = [
        c
        for c in plan["cases"]
        if c["model_identity_hash"] == w.model_identity_hash and c["purpose"] == w.purpose
    ]
    require(bool(selected), "INCOMPLETE_RELEVANT_SUITE")
    ids = {c["case_id"] for c in selected}
    require(
        {c["case_id"] for c in inventory["cases"]}
        == ids
        == {c["case_id"] for c in links["entries"]}
        == {c["case_id"] for c in checks["cases"]},
        "INCOMPLETE_RELEVANT_SUITE",
    )
    require(len(checks["cases"]) == len(ids), "MALFORMED_DUPLICATE_CHECK")
    results: list[tuple[str, str]] = []
    for case in selected:
        cid = case["case_id"]
        require(case["required_roles"] == ["verification_observed"], "MISMATCH_SUITE_ROLES")
        item = next(c for c in inventory["cases"] if c["case_id"] == cid)
        entries = [c for c in links["entries"] if c["case_id"] == cid]
        require(len(entries) == 1, "INCOMPLETE_SUITE_ROLE")
        link = entries[0]
        ci = next(i for i, c in enumerate(checks["cases"]) if c["case_id"] == cid)
        check = checks["cases"][ci]
        require(
            link["role"] == "verification_observed"
            and link["proof_member"] == "checks.json"
            and link["proof_pointer"] == f"/cases/{ci}/observed"
            and link["benchmark_id"] == item["benchmark_id"] == case["benchmark_id"]
            and (
                link["independent_reference"] is None
                and case["independent_expected"] is None
                or link["independent_reference"] is not None
                and case["independent_expected"] is not None
                and m.reference_identity(
                    link["independent_reference"], owner=m.owner, role="independent-expected.json"
                )
                == m.reference_identity(
                    case["independent_expected"], owner=plan_owner, role="independent-expected.json"
                )
            ),
            "MISMATCH_VERIFICATION_LINK",
        )
        bound = bind_capture(v, item["capture"], case)
        if not bound.scopes:
            raise ProofUnsupported("UNSUPPORTED_NOMINAL_SCOPE")
        require(all(s == scope for s in bound.scopes), "MISMATCH_CAPTURE_SCOPE")
        if case["independent_expected"] is None:
            raise ProofUnsupported("UNSUPPORTED_EXPECTED_SOURCE")
        expected_source, expected_proof, expected_raw = m.member(
            case["independent_expected"], owner=plan_owner, role="independent-expected.json"
        )
        require(
            expected_source.source_hash != source.source_hash
            and expected_source.independence_from_candidate,
            "MISMATCH_EXPECTED_INDEPENDENCE",
        )
        require(
            checks["reference_identity"] == expected_source.reference_identity
            and checks["reference_version"] == expected_source.reference_version,
            "MISMATCH_REFERENCE_IDENTITY",
        )
        references = [
            record
            for record in v.verifications
            if record.source_hash == expected_source.source_hash
            and record.verification_hash in m.closed
            and record.model_identity_hash == w.model_identity_hash
            and record.purpose == w.purpose
            and record.scope == w.scope
        ]
        if not any(_accepted_review(record, v.artifacts) for record in references):
            raise ProofUnsupported("UNSUPPORTED_EXPECTED_SOURCE_REVIEW")
        expected = json_bytes(expected_raw)
        require(
            expected["suite_id"] == plan["suite_id"]
            and expected["suite_version"] == plan["suite_version"],
            "MISMATCH_EXPECTED_SUITE",
        )
        expected_cases = [c for c in expected["cases"] if c["case_id"] == cid]
        require(len(expected_cases) == 1, "INCOMPLETE_EXPECTED_CASE")
        ec = expected_cases[0]
        require(
            ec["model_input_hash"] == case["input_hash"]
            and ec["quantity"] == case["quantity"]
            and ec["source_unit"] == case["source_unit"],
            "MISMATCH_EXPECTED_KEY",
        )
        # The only initial source interpreter is explicitly synthetic literal test mode.
        # No real normalized assertions are trusted as original measurement/compiler truth.
        if not (
            allow_synthetic
            and source.kind == expected_source.kind == "synthetic_fixture"
            and proof.classification == expected_proof.classification == "synthetic_fixture"
        ):
            raise ProofUnsupported("UNSUPPORTED_EXPECTED_SOURCE_PARSER")
        external = _Members(v, expected_source.source_hash)
        original_source, _, original = external.member(
            ec["original_reference"],
            owner=expected_source.source_hash,
            role="original-expected.txt",
        )
        require(
            original_source.source_hash == expected_source.source_hash,
            "MISMATCH_EXPECTED_ORIGINAL_SOURCE",
        )
        try:
            literal = decimal_value(original.decode("ascii"))
        except UnicodeError as e:
            raise ProofRefusal("MALFORMED_SYNTHETIC_EXPECTED") from e
        expected_value = decimal_value(ec["value_decimal"])
        require(literal == expected_value, "MISMATCH_EXPECTED_ORIGINAL")
        tolerance = decimal_value(ec["absolute_tolerance_decimal"])
        require(tolerance >= 0, "MALFORMED_TOLERANCE")
        if case["source_unit"] == "ps":
            expected_value /= 10**12
            tolerance /= 10**12
        require(
            decimal_value(check["expected"]) == expected_value
            and decimal_value(check["absolute_tolerance"]) == tolerance
            and check["unit"] == ("s" if case["quantity"] == "duration" else case["source_unit"]),
            "MISMATCH_CHECK_EXPECTATION",
        )
        if item["outcome"] == "not_run":
            outcome = "not_run"
        else:
            require(decimal_value(check["observed"]) == bound.value, "MISMATCH_OBSERVED_SCALAR")
            passed = abs(bound.value - expected_value) <= tolerance
            outcome = "passed" if passed and item["outcome"] == "passed" else "failed"
        results.append((cid, outcome))
    outcome = (
        "failed"
        if any(s == "failed" for _, s in results)
        else ("not_run" if any(s == "not_run" for _, s in results) else "passed")
    )
    require(outcome == w.outcome, "MISMATCH_VERIFICATION_OUTCOME")
    return VerificationAssessment(outcome, tuple(results), True, w.model_identity_hash, w.purpose)


def interpret_ordering(raw: bytes) -> None:
    """No flat-object or boolean path can stand in for the accepted project lifecycle."""
    raise ProofUnsupported("UNSUPPORTED_PROJECT_HISTORY")


def interpret_measurement(raw: bytes) -> None:
    proof = decode_proof(raw)
    require(proof.kind == "measurement", "MISMATCH_PROOF_KIND")
    # Recognize retained aggregate syntax, never translate it into named channels.
    try:
        lines = proof.members["device.csv"].decode("ascii").split("\n")
    except UnicodeError as e:
        raise ProofRefusal("MALFORMED_DEVICE_CSV") from e
    require(
        lines[-1] == "" and lines[0] == "sample_id,start_s,end_s,flops,bytes",
        "MALFORMED_DEVICE_CSV",
    )
    rows = [line.split(",") for line in lines[1:-1]]
    suite = proof.json("suite.json")
    require(len(rows) > 0 and all(len(r) == 5 for r in rows), "MALFORMED_DEVICE_CSV")
    require(
        [r[0] for r in rows] == suite["sample_ids"] and len({r[0] for r in rows}) == len(rows),
        "MALFORMED_SAMPLE_INVENTORY",
    )
    for sample, start, end, flops, count_bytes in rows:
        require(re.fullmatch(r"[A-Za-z0-9_-]+", sample) is not None, "MALFORMED_SAMPLE_ID")
        for text in (start, end, flops, count_bytes):
            require(decimal_value(text) >= 0, "MALFORMED_DEVICE_NUMBER")
        require(
            decimal_value(flops).denominator == decimal_value(count_bytes).denominator == 1,
            "MALFORMED_AGGREGATE_INTEGER",
        )
        require(decimal_value(end) > decimal_value(start), "MISMATCH_TIMING")
    raise ProofUnsupported("UNSUPPORTED_AGGREGATE_FIDELITY_MAPPING")
