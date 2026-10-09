"""BP1 regressions: actual A capture, synthetic literals/reviews, no real eligibility."""

import base64
import json
from pathlib import Path

import pytest
from uarch_contract.evidence import ReviewRecord, SourceRecord, VerificationRecord
from uarch_contract.report_context import ReportContext
from uarch_contract.table import UarchCostTable

from rkuarch.provenance.proof import ProofRefusal, ProofUnsupported, interpret_verification
from rkuarch.table.artifacts import load_verified_report_inputs, verify_report_inputs
from tests.fixtures.u2_b.b2_support import put, review
from tests.fixtures.u2_b.proof_support import mr, raw_json, source, verification_fixture


@pytest.fixture(scope="module")
def inputs():
    return load_verified_report_inputs(
        Path(__file__).resolve().parents[2] / "tests/fixtures/u2_b/a3-proof-capture/table.json"
    )


def assembled(inputs, mode="local", mutation=None):
    """Rehash explicit synthetic source graphs; never change A's captured computation."""
    v, identity = verification_fixture(inputs)
    store = dict(v.artifacts)
    w = next(w for w in v.verifications if w.verification_hash == identity)
    ew = next(w for w in v.verifications if w.verification_hash != identity)

    def unpack(source_hash):
        return {
            m["name"]: base64.b64decode(m["base64"])
            for m in json.loads(store[store[source_hash]["raw_blob_sha256"]])["members"]
        }

    observed, expected = unpack(w.source_hash), unpack(ew.source_hash)
    plan = json.loads(observed["suite-plan.json"])
    inv = json.loads(observed["capture-inventory.json"])
    links = json.loads(observed["capture-links.json"])
    if mutation == "original_role":
        record = json.loads(expected["independent-expected.json"])
        expected["original-compiler.txt"] = expected.pop("original-expected.txt")
        record["cases"][0]["original_reference"] = mr(
            "original-compiler.txt", expected["original-compiler.txt"]
        )
        expected["independent-expected.json"] = raw_json(record)
    if mode != "local":
        observed.pop("suite-plan.json")
        plan["cases"][0]["independent_expected"] = mr(
            "independent-expected.json", expected["independent-expected.json"]
        )
        expected["suite-plan.json"] = raw_json(plan)
        if mode == "external_inventory":
            observed.pop("capture-inventory.json")
            inv["suite_plan"] = mr("suite-plan.json", expected["suite-plan.json"])
            expected["capture-inventory.json"] = raw_json(inv)
    es = source(store, expected, "capture_support", "B-independent-literal-q")
    eref = mr("independent-expected.json", expected["independent-expected.json"], es["source_hash"])
    if mode == "local":
        plan["cases"][0]["independent_expected"] = eref
        observed["suite-plan.json"] = raw_json(plan)
        pref = mr("suite-plan.json", observed["suite-plan.json"])
    else:
        pref = mr("suite-plan.json", expected["suite-plan.json"], es["source_hash"])
    links["suite_plan"] = pref
    if mode == "external_inventory":
        links["capture_inventory"] = mr(
            "capture-inventory.json", expected["capture-inventory.json"], es["source_hash"]
        )
    else:
        inv["suite_plan"] = pref
        observed["capture-inventory.json"] = raw_json(inv)
        links["capture_inventory"] = mr(
            "capture-inventory.json", observed["capture-inventory.json"]
        )
    links["entries"][0]["independent_reference"] = eref
    if mutation == "inventory_role":
        links["capture_inventory"] = pref
    elif mutation == "plan_role":
        links["suite_plan"] = links["capture_inventory"]
    elif mutation == "expected_role":
        plan["cases"][0]["independent_expected"] = mr(
            "original-expected.txt", expected["original-expected.txt"], es["source_hash"]
        )
        links["entries"][0]["independent_reference"] = plan["cases"][0]["independent_expected"]
        observed["suite-plan.json"] = raw_json(plan)
        pref = mr("suite-plan.json", observed["suite-plan.json"])
        links["suite_plan"] = pref
        inv["suite_plan"] = pref
        observed["capture-inventory.json"] = raw_json(inv)
        links["capture_inventory"] = mr(
            "capture-inventory.json", observed["capture-inventory.json"]
        )
    elif mutation == "compiler_role":
        links["entries"][0]["role"] = "fidelity_count"
        plan["cases"][0]["required_roles"] = ["fidelity_count"]
        observed["suite-plan.json"] = raw_json(plan)
        pref = mr("suite-plan.json", observed["suite-plan.json"])
        links["suite_plan"] = pref
        inv["suite_plan"] = pref
        observed["capture-inventory.json"] = raw_json(inv)
        links["capture_inventory"] = mr(
            "capture-inventory.json", observed["capture-inventory.json"]
        )
    elif mutation == "local_expected_wrong_owner":
        # Same expected bytes available locally: null still denotes the WRONG source.
        observed.update({k: v for k, v in expected.items() if k != "suite-plan.json"})
        links["entries"][0]["independent_reference"] = mr(
            "independent-expected.json", expected["independent-expected.json"]
        )
    elif mutation == "explicit_expected_wrong_owner":
        # Another closed, reviewed source has the identical expected member bytes.
        links["entries"][0]["independent_reference"] = mr(
            "independent-expected.json", expected["independent-expected.json"], ew.source_hash
        )
    elif mutation == "expected_hash":
        links["entries"][0]["independent_reference"] = dict(
            eref, member_sha256="sha256:" + "0" * 64
        )
    elif mutation == "inventory_plan_hash":
        inv["suite_plan"] = dict(pref, member_sha256="sha256:" + "0" * 64)
        observed["capture-inventory.json"] = raw_json(inv)
        links["capture_inventory"] = mr(
            "capture-inventory.json", observed["capture-inventory.json"]
        )
    observed["capture-links.json"] = raw_json(links)
    obs = source(store, observed, "verification", "B-observed-q")
    records = []
    for old, new in ((w, obs), (ew, es)):
        record = old.model_dump(mode="json")
        record["source_hash"] = new["source_hash"]
        records.append(review(store, record, "verification_hash"))
    if mutation == "explicit_expected_wrong_owner":
        records.append(ew.model_dump(mode="json"))
    context = v.context.model_dump(mode="json")
    context["verification_hashes"] = [r["verification_hash"] for r in records]
    put(store, context, "context_hash")
    table = v.table.model_dump(mode="json")
    table["artifacts"]["report_context_hash"] = context["context_hash"]
    put(store, table, "table_hash")
    sources = [obs, es]
    if mutation == "explicit_expected_wrong_owner":
        sources.append(store[ew.source_hash])
    return v._replace(
        table=UarchCostTable.model_validate(table),
        context=ReportContext.model_validate(context),
        artifacts=store,
        sources=tuple(SourceRecord.model_validate(s) for s in sources),
        verifications=tuple(VerificationRecord.model_validate(r) for r in records),
        reviews=tuple(
            ReviewRecord.model_validate(r)
            for r in store.values()
            if isinstance(r, dict) and r.get("format") == "uarch-evidence-review/1"
        ),
    ), records[0]["verification_hash"]


@pytest.mark.parametrize(
    "mutation", ["inventory_role", "plan_role", "expected_role", "original_role", "compiler_role"]
)
def test_wrong_member_roles_are_classified_contradictions(inputs, mutation):
    v, identity = assembled(inputs, mutation=mutation)
    with pytest.raises(ProofRefusal, match="MALFORMED_MEMBER_ROLE") as error:
        interpret_verification(v, identity, allow_synthetic=True)
    assert not isinstance(error.value, ProofUnsupported)


@pytest.mark.parametrize("mode", ["local", "external_plan", "external_inventory"])
def test_source_relative_plan_and_inventory_controls(inputs, mode):
    v, identity = assembled(inputs, mode=mode)
    if mode == "external_inventory":
        v = verify_report_inputs(v.table, v.artifacts)
    result = interpret_verification(v, identity, allow_synthetic=True)
    assert result.outcome == "passed"
    assert result.cases == (("q-count", "passed"),)
    assert result.synthetic is True
    with pytest.raises(ProofUnsupported, match="UNSUPPORTED_EXPECTED_SOURCE_PARSER"):
        interpret_verification(v, identity)


@pytest.mark.parametrize(
    "mutation",
    [
        "local_expected_wrong_owner",
        "explicit_expected_wrong_owner",
        "expected_hash",
        "inventory_plan_hash",
    ],
)
def test_different_resolved_member_identity_refuses(inputs, mutation):
    v, identity = assembled(inputs, mode="external_plan", mutation=mutation)
    with pytest.raises(
        ProofRefusal, match="MISMATCH_(VERIFICATION_LINK|SUITE_PLAN|MEMBER_HASH)"
    ) as error:
        interpret_verification(v, identity, allow_synthetic=True)
    assert not isinstance(error.value, ProofUnsupported)
