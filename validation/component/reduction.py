"""Conservative U0006 reduction of retained execution records, never execution authority."""

from collections.abc import Mapping, Sequence
from typing import Any


def reduce_native(
    records: Sequence[Mapping[str, Any]],
    required_cases: set[str],
    *,
    call_cap: int,
    required_mutants: set[str],
    qualifying_replays: int = 2,
) -> str:
    """All real calls, including discovery/shrink/fault/restored, consume the frozen cap.

    The caller retains immutable raw inputs/outputs and genuine transport/authority receipts.
    Digests here bind that ledger; they do not authenticate a human or an execution by themselves.
    Synthetic checker records never discharge a native cell. Applicable discoveries dominate.
    """
    native = [r for r in records if r.get("origin") == "actual_public_native"]
    if any(
        r.get("applicable") is True and r.get("outcome") in ("failed", "surviving_mutant")
        for r in native
    ):
        return "failed"
    if not required_cases or call_cap <= 0 or qualifying_replays < 2 or len(native) > call_cap:
        return "not_run"
    ids = [r.get("invocation_id") for r in native]
    if len(ids) != len(set(ids)) or any(x is None for x in ids):
        return "not_run"
    if any(
        not all(
            r.get(key)
            for key in (
                "input_hash",
                "result_hash",
                "implementation_hash",
                "assumptions_hash",
                "suite_hash",
                "receipt_hash",
            )
        )
        or r.get("outcome") not in ("passed", "expected_refusal", "mutant_killed")
        for r in native
    ):
        return "not_run"
    for case in required_cases:
        rows = [r for r in native if r.get("case_id") == case and r.get("applicable") is True]
        # Discovery or a mutant's correct refusal cannot stand in for an unchanged replay.
        replays = {
            r.get("replay_index")
            for r in rows
            if r.get("role") == "qualifying_replay" and r.get("outcome") == "passed"
        }
        if replays != set(range(qualifying_replays)):
            return "not_run"
        bindings = {
            (r["input_hash"], r["implementation_hash"], r["assumptions_hash"], r["suite_hash"])
            for r in rows
            if r.get("role") == "qualifying_replay"
        }
        if len(bindings) != 1:
            return "not_run"
    for mutant in required_mutants:
        controls = [r for r in native if r.get("mutant_id") == mutant]
        for role, outcome in (
            ("positive_control", "passed"),
            ("mutant", "mutant_killed"),
            ("restored_control", "passed"),
        ):
            if not any(r.get("role") == role and r.get("outcome") == outcome for r in controls):
                return "not_run"
    return "passed"
