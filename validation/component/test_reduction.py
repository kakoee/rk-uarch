"""SYNTHETIC reducer inputs, no native receipt or actual execution claims."""

from copy import deepcopy

from validation.component.reduction import reduce_native


def fake_rows():
    return [
        dict(
            origin="actual_public_native",
            invocation_id=str(i),
            case_id="c",
            applicable=True,
            role="qualifying_replay",
            replay_index=i,
            outcome="passed",
            input_hash="SYNTHETIC-i",
            result_hash="SYNTHETIC-r",
            implementation_hash="SYNTHETIC-code",
            assumptions_hash="SYNTHETIC-a",
            suite_hash="SYNTHETIC-s",
            receipt_hash="SYNTHETIC-receipt",
        )
        for i in range(2)
    ]


def test_conservative_retained_ledger_reduction():
    rows = fake_rows()
    assert (
        reduce_native(rows, {"c"}, call_cap=2, required_mutants=set()) == "passed"
    )  # reducer unit only
    assert reduce_native(rows, {"c", "missing"}, call_cap=2, required_mutants=set()) == "not_run"
    assert reduce_native(rows, {"c"}, call_cap=1, required_mutants=set()) == "not_run"
    assert reduce_native(rows[:1], {"c"}, call_cap=2, required_mutants=set()) == "not_run"
    mutated = deepcopy(rows)
    mutated[1]["input_hash"] = "changed"
    assert reduce_native(mutated, {"c"}, call_cap=2, required_mutants=set()) == "not_run"
    mutated = deepcopy(rows)
    mutated[1]["origin"] = "synthetic_checker"
    assert reduce_native(mutated, {"c"}, call_cap=2, required_mutants=set()) == "not_run"
    mutated = deepcopy(rows)
    mutated[1]["invocation_id"] = "0"
    assert reduce_native(mutated, {"c"}, call_cap=2, required_mutants=set()) == "not_run"
    for outcome in ("failed", "surviving_mutant"):
        discovery = dict(rows[0], invocation_id="discovery", role="discovery", outcome=outcome)
        assert (
            reduce_native([discovery, *rows], {"c"}, call_cap=2, required_mutants=set()) == "failed"
        )
    setup = dict(rows[0], invocation_id="setup", role="setup", outcome="setup_error")
    assert reduce_native([setup, *rows], {"c"}, call_cap=3, required_mutants=set()) == "not_run"


def test_required_mutant_and_restored_controls_cannot_disappear():
    rows = fake_rows()
    assert reduce_native(rows, {"c"}, call_cap=5, required_mutants={"credits"}) == "not_run"
    for role, outcome in (
        ("positive_control", "passed"),
        ("mutant", "mutant_killed"),
        ("restored_control", "passed"),
    ):
        rows.append(
            dict(rows[0], invocation_id=role, role=role, outcome=outcome, mutant_id="credits")
        )
    assert reduce_native(rows, {"c"}, call_cap=5, required_mutants={"credits"}) == "passed"
    assert reduce_native(rows[:-1], {"c"}, call_cap=5, required_mutants={"credits"}) == "not_run"
