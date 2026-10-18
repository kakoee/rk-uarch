"""Bounded private campaign orchestration proposal, not a public authority entry point.

The future installed-runtime adapter is deliberately absent. Tests supply toy adapters.
Only private-synthetic-test sessions may run here. Receipt validation never grants authority.
"""

from __future__ import annotations

import hashlib
import resource
import runpy
from pathlib import Path
from typing import Any

from uarch_contract.hashing import canonical_json

from validation.component.runtime_evidence import STREAM_CAP, consume_attempt, replay_admission

ROOT = Path(__file__).resolve().parents[2]
HELPERS = {
    "parallel_core.py": "bbe3746760753c388ac1fa3f3420016f008281a1014638863320e073e15348b1",
    "resource_limits.py": "8dca3caa49d30eb54788d06f728e2a22fdabcb664fb92f78609f4539ccbdfa74",
}
POLICY = dict(
    max_workers=4,
    memory_reserve_bytes=512 * 1024**2,
    per_worker_memory_bytes=1024**3,
    nofile=256,
    per_call_seconds=30,
    case_seconds=390,
    total_seconds=24000,
    receipt_bytes=48 * 1024**3,
    process_limit_required=64,
)


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def helpers() -> dict[str, Any]:
    base = ROOT / "docs/reviews/U4-B-K2-parallel-first-use-v1"
    loaded = {}
    for name, pin in HELPERS.items():
        require(digest((base / name).read_bytes()) == pin, "unchanged orchestration helper")
        loaded.update(runpy.run_path(str(base / name)))
    return loaded


def schedule(selection: dict[str, Any], cases: list[str] | None = None) -> list[dict[str, Any]]:
    rows = {r["case_id"]: r for r in selection["rows"]}
    require(len(rows) == len(selection["rows"]), "unique case selection")
    chosen = sorted(rows) if cases is None else sorted(cases)
    require(
        bool(chosen) and len(set(chosen)) == len(chosen) and set(chosen) <= rows.keys(),
        "exact nonempty case subset",
    )
    slots: list[dict[str, Any]] = []
    for case in chosen:
        for phase in (
            ("initial", "replay") if rows[case]["expected_layer"] == "result" else ("initial",)
        ):
            for mode in ("debug", "release"):
                for repetition in range(3):
                    slots.append(
                        dict(
                            ordinal=len(slots),
                            case_id=case,
                            phase=phase,
                            mode=mode,
                            repetition=repetition,
                        )
                    )
    return slots


def verify_group(rows: list[dict[str, Any]], *, replay: bool) -> None:
    wanted = {
        (phase, mode, repeat)
        for phase in (("initial", "replay") if replay else ("initial",))
        for mode in ("debug", "release")
        for repeat in range(3)
    }
    observed = [(r["phase"], r["mode"], r["repetition"]) for r in rows]
    require(
        len(observed) == len(wanted) and set(observed) == wanted,
        "exact fresh-process slot membership",
    )
    require(
        len({r["process_identity"] for r in rows}) == len(rows), "fresh process identity required"
    )
    require(
        len({r["raw_input_sha256"] for r in rows}) == 1, "saved input identity across modes/replay"
    )
    require(
        len({(r["stdout_sha256"], r["stderr_sha256"]) for r in rows}) == 1,
        "six-way complete canonical output equality",
    )
    require(all(r["validation_passed"] is True for r in rows), "consumer outcome required")


def run_private(
    selection: dict[str, Any],
    adapter: Any,
    output: Path,
    *,
    acceptance: dict[str, Any],
    cases: list[str] | None = None,
    resources: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Private transport plus independently supplied frozen acceptance configuration.

    Adapter owns actual process/container cleanup and trusted instrumentation. B checks
    retained bytes, witness joins and semantics; those checks do not authenticate a
    malicious instrumentation producer. Public invocation remains unavailable.
    """
    require(output.resolve().is_relative_to(Path("/tmp")), "private output path required")
    output.mkdir(exist_ok=False)
    h = helpers()
    store = h["Store"](output, POLICY["receipt_bytes"])
    slots = schedule(selection, cases)
    ids = sorted({s["case_id"] for s in slots})
    rows = {r["case_id"]: r for r in selection["rows"]}
    launch = dict(
        format="component-private-launch/2",
        complete=False,
        evidence_kind="private-synthetic-test",
        selection_hash=selection["selection_hash"],
        acceptance_sha256=digest(canonical_json(acceptance).encode()),
        cases=ids,
        planned_calls=len(slots),
        acceptance_gate=False,
        policy=POLICY,
    )
    store.json("launch.json", launch)

    def group_name(case: str) -> str:
        return digest(case.encode())

    def cleanup() -> None:
        receipt = adapter.cleanup()
        store.json("cleanup.json", receipt)
        require(
            receipt.get("verified_stopped") is True and receipt.get("outstanding") == [],
            "parent actual cleanup incomplete",
        )

    try:
        require(acceptance["format"] == "component-private-acceptance/1", "acceptance version")
        require(
            acceptance["selection_sha256"] == digest(canonical_json(selection).encode()),
            "separately frozen selection",
        )
        require(acceptance["evidence_kind"] == "private-synthetic-test", "no public execution")
        setup = adapter.preflight(dict(selection, rows=[rows[k] for k in ids]), POLICY)
        require(
            setup["evidence_kind"] == "private-synthetic-test", "no public execution in proposal"
        )
        require(
            0 < setup["pids_limit"] <= POLICY["process_limit_required"],
            "bounded outer process limit",
        )
        require(
            setup["execution_binding"] == acceptance["execution_binding"] and bool(setup["files"]),
            "independent execution binding",
        )

        def verify_setup() -> None:
            for path, pin in setup["files"].items():
                require(digest(Path(path).read_bytes()) == pin, "current setup bytes changed")

        verify_setup()
        require(set(setup["input_hashes"]) == set(ids), "exact selected input binding inventory")
        require(
            all(
                setup["input_hashes"][case] == acceptance["inputs"][case]["raw_input_sha256"]
                for case in ids
            ),
            "independent input inventory",
        )
        budget = resources if resources is not None else h["discover"](POLICY, len(ids))
        workers = min(POLICY["max_workers"], budget["workers"], len(ids))
        require(workers > 0, "positive worker budget")
        store.json("setup.json", dict(setup=setup, resources=budget, workers=workers))

        def group(case: str) -> dict[str, Any]:
            resource.setrlimit(resource.RLIMIT_NOFILE, (POLICY["nofile"], POLICY["nofile"]))
            results: list[dict[str, Any]] = []
            initial_refs: list[dict[str, str]] = []
            case_slots = [s for s in slots if s["case_id"] == case]
            store.json(
                f"groups/{group_name(case)}/started.json", dict(case_id=case, slots=case_slots)
            )
            failure_stage = "setup"
            failure_slot = None
            try:
                for slot in case_slots:
                    failure_slot = slot
                    verify_setup()
                    initial = None
                    if slot["phase"] == "replay":
                        failure_stage = "replay-admission"
                        initial = replay_admission(output, initial_refs, rows[case], acceptance)
                    failure_stage = "transport"
                    raw = adapter.call(slot, rows[case], initial, POLICY)
                    record = dict(
                        slot,
                        execution_binding=setup["execution_binding"],
                        evidence_kind="private-synthetic-test",
                        transport_complete=True,
                        validation_passed=False,
                    )
                    # Preserve bounded data BEFORE interpreting outcome/JSON/claims. Oversize
                    # streams retain their bounded prefix and original length, then refuse.
                    oversize = False
                    for key in ("raw_input", "stdout", "stderr"):
                        require(isinstance(raw[key], bytes), "raw bytes receipt required")
                        data = raw[key]
                        record[key + "_length"] = len(data)
                        record[key + "_truncated"] = len(data) > STREAM_CAP
                        oversize |= len(data) > STREAM_CAP
                        kept = data[:STREAM_CAP]
                        record[key + "_sha256"] = digest(kept)
                        record[key + "_blob"] = store.blob(kept)
                    # Publish the slot/blob join before untrusted metadata can fail.
                    store.json(f"attempts/{slot['ordinal']:05d}.json", record)
                    for key in ("process_identity", "status", "witness", "cleanup"):
                        record[key] = raw.get(key)
                    metadata = canonical_json(record).encode()
                    require(len(metadata) <= STREAM_CAP, "bounded receipt metadata")
                    store.json(f"attempt-metadata/{slot['ordinal']:05d}.json", record)
                    require(not oversize, "per-stream byte cap")
                    failure_stage = "attempt-validation"
                    outcome = consume_attempt(raw, rows[case], slot, acceptance)
                    verify_setup()
                    record.update(validation_passed=True, outcome=outcome)
                    name = f"calls/{slot['ordinal']:05d}.json"
                    store.json(name, record)
                    results.append(record)
                    if slot["phase"] == "initial":
                        initial_refs.append(
                            dict(path=name, sha256=digest((output / name).read_bytes()))
                        )
                failure_stage = "group-validation"
                verify_group(results, replay=rows[case]["expected_layer"] == "result")
                summary = dict(case_id=case, complete=True, slots=[r["ordinal"] for r in results])
                store.json(f"groups/{group_name(case)}/complete.json", summary)
                return summary
            except BaseException as error:
                store.json(
                    f"groups/{group_name(case)}/failed.json",
                    dict(
                        case_id=case,
                        complete=False,
                        reason=repr(error),
                        failure_stage=failure_stage,
                        failed_slot=failure_slot,
                        validated_slots=[r["ordinal"] for r in results],
                        unresolved_slots=[
                            s["ordinal"]
                            for s in case_slots
                            if s["ordinal"] not in {r["ordinal"] for r in results}
                        ],
                    ),
                )
                raise

        finished = h["run_workers"](
            ids,
            group,
            workers=workers,
            task_timeout=POLICY["case_seconds"],
            total_timeout=POLICY["total_seconds"],
        )
        verify_setup()
        cleanup()
        store.check_budget()
        require(sum(len(r["slots"]) for r in finished) == len(slots), "complete launch membership")
        result = dict(launch, complete=True, completed_calls=len(slots), results=finished)
        store.json("complete.json", result)
        return result
    except BaseException as error:
        cleanup_error = None
        if not (output / "cleanup.json").exists():
            try:
                cleanup()
            except BaseException as failure:
                cleanup_error = repr(failure)
        # A killed worker cannot write its own terminal record. The parent records it,
        # and failed group acceptance remains distinct from validated call receipts.
        incomplete_groups = []
        for case in ids:
            base = f"groups/{group_name(case)}"
            if (output / base / "complete.json").exists():
                continue
            unresolved = [
                s["ordinal"]
                for s in slots
                if s["case_id"] == case and not (output / f"calls/{s['ordinal']:05d}.json").exists()
            ]
            summary = dict(
                case_id=case, complete=False, reason=repr(error), unresolved_slots=unresolved
            )
            store.json(base + "/incomplete.json", summary)
            incomplete_groups.append(summary)
        store.json(
            "incomplete.json",
            dict(
                launch,
                reason=repr(error),
                cleanup_error=cleanup_error,
                validated_calls=len(list((output / "calls").glob("*.json"))),
                transported_attempts=len(list((output / "attempts").glob("*.json"))),
                incomplete_groups=incomplete_groups,
            ),
        )
        raise
