"""Interpret only already-approved raw profiles, without making real evidence eligible."""

from __future__ import annotations

from uarch_contract.hashing import strict_json_loads

from rkuarch.provenance.proof import (
    ProofUnsupported,
    bind_prediction,
    decode_proof,
    interpret_measurement,
    interpret_verification,
)
from rkuarch.table.artifacts import VerifiedReportInputs


def proof_statuses(
    v: VerifiedReportInputs, *, allow_synthetic: bool
) -> tuple[tuple[str, str], ...]:
    statuses = []
    for source in v.sources:
        raw = v.artifacts[source.raw_blob_sha256]
        if not isinstance(raw, bytes):
            raise ValueError("RawSourceBindingMismatch")
        try:
            header = strict_json_loads(raw)
        except (ValueError, UnicodeError):
            statuses.append(
                (source.source_hash, "unsupported source-specific raw parser; no eligibility")
            )
            continue
        if not isinstance(header, dict) or not str(header.get("format", "")).startswith(
            "u2-proof-bundle/"
        ):
            statuses.append(
                (source.source_hash, "unsupported source-specific raw parser; no eligibility")
            )
            continue
        try:
            proof = decode_proof(raw)
            if proof.kind == "measurement":
                bind_prediction(v, source.source_hash)
                interpret_measurement(raw)
            elif proof.kind == "verification":
                records = [w for w in v.verifications if w.source_hash == source.source_hash]
                if not records:
                    raise ProofUnsupported("UNSUPPORTED_VERIFICATION_RECORD")
                for record in records:
                    result = interpret_verification(
                        v, record.verification_hash, allow_synthetic=allow_synthetic
                    )
                    statuses.append(
                        (
                            record.verification_hash,
                            "synthetic verification " + result.outcome + "; not model accuracy",
                        )
                    )
            else:
                statuses.append(
                    (source.source_hash, "structural capture support only; no accuracy claim")
                )
        except ProofUnsupported as exc:
            statuses.append((source.source_hash, str(exc) + "; ineligible"))
        # Recognized malformed/contradictory proofs deliberately propagate ProofRefusal.
    return tuple(statuses)
