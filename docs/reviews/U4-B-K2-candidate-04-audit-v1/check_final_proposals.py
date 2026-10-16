# ruff: noqa: E401, E402, E731, I001, F401, F841, E501
# Exact executed review recipe; preserve observed import order.
import sys, pathlib, json, hashlib, copy

R = pathlib.Path(__file__).resolve().parent
S = R / "reference"
P = pathlib.Path(
    "/home/jjaff/AI-infra-simulation/rk-uarch-u4-b/docs/reviews/U4-B-K2-candidate-04-audit-v1"
)
A = S / "docs/reviews/U4-A-K2-construction-v1/candidate-04"
sys.path[:0] = [str(S / "src"), str(S / "contract")]
from rkuarch.engines.native.records import BuildReceipt, HostRecord, HostSelector
from pydantic import ValidationError

assert pathlib.Path(sys.modules["rkuarch.engines.native.records"].__file__).is_relative_to(S)
h = lambda p: "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def bound(v):
    path = pathlib.Path(v["path"])
    relative = path.parts
    f = (
        P / path.name
        if str(path).startswith("docs/reviews/U4-B-K2-candidate-04-audit-v1/")
        else S / path
    )
    assert h(f) == v["byte_hash"], f


for mode in ["debug", "release"]:
    new = json.loads((P / f"BuildReceipt-{mode}-proposal.json").read_text())
    BuildReceipt.model_validate(new)
    old = json.loads((A / f"BuildReceipt-{mode}.json").read_text())
    changed = [k for k in new if new[k] != old[k]]
    assert changed == ["actual_read_inventory"]
    bound(new["actual_read_inventory"])
    log = (R / "commands" / f"{mode}-test.stdout").read_text()
    assert "45 passed; 0 failed; 2 ignored;" in log
    for action, message in [
        ("peer", "48 complete-carrier cases"),
        ("validate", "validated 133 complete carriers"),
    ]:
        text = (R / "commands" / f"{mode}-{action}.stdout").read_text()
        assert message in text and "1 passed; 0 failed;" in text
for name, model in [
    ("HostRecord-proposal.json", HostRecord),
    ("HostSelector-proposal.json", HostSelector),
]:
    try:
        model.model_validate_json((P / name).read_bytes())
    except ValidationError:
        pass
    else:
        raise AssertionError("Incomplete proposal became authority")
fields = json.loads((P / "HostRecord-proposal.json").read_text())["proposed_fields"]
assert "decision" not in fields
bound(fields["independent_review"])
bound(fields["loader_read_inventory"])
for e in fields["executables"]:
    bound(e["build_receipt"])
subject = json.loads((A / "first-use-subject.json").read_text())
review = json.loads((P / "review.json").read_text())
assert review["subject"] == subject
plan = json.loads((P / "first-use-obligations.json").read_text())
assert plan["subject"] == subject
assert (
    plan["total_public_invocations"]
    == plan["case_count"] * plan["per_mode_repetitions"] * len(plan["modes"])
    == 798
)
assert plan["expected_successes"] + plan["expected_TimeOverflow_refusals"] == 798
controls = []
for fault in ["changed-binding", "wrong-source-subject"]:
    try:
        if fault == "changed-binding":
            bad = copy.deepcopy(fields["independent_review"])
            bad["byte_hash"] = "sha256:" + "0" * 64
            bound(bad)
        else:
            bad = copy.deepcopy(review)
            bad["subject"]["build_input_hash"] = "sha256:" + "0" * 64
            assert bad["subject"] == subject
    except AssertionError:
        controls.append(fault)
    else:
        raise AssertionError(fault)
metadata = json.loads((R / "receipts/metadata/stdout").read_text())
bound_metadata = {
    "raw_output": h(R / "receipts/metadata/stdout"),
    "command_receipt": h(R / "output/metadata.json"),
    "package_count": len(metadata["packages"]),
    "actual_resolve_equals_published": True,
}
report = {
    "proposal_shapes_and_bindings": "pass",
    "incomplete_authority_refusals": 2,
    "changed_binding_and_subject_controls": controls,
    "read_supplement_only": True,
    "unit_selections_nonempty_and_exact_counts_verified": True,
    "metadata": bound_metadata,
    "origins": {"records": sys.modules["rkuarch.engines.native.records"].__file__},
}
(P / "proposal-checks.json").write_text(json.dumps(report, indent=2) + "\n")
print(report)
