"""Bounded private campaign orchestration proposal, not a public authority entry point.

The future installed-runtime adapter is deliberately absent. Tests supply toy adapters.
Only private-synthetic-test sessions may run here. Receipt validation never grants authority.
"""

from __future__ import annotations

import hashlib
import json
import resource
import runpy
from pathlib import Path
from typing import Any

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
    slots = []
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
        len({r["stdout_sha256"] for r in rows}) == 1, "six-way complete canonical output equality"
    )
    require(all(r["checked"] is True for r in rows), "consumer outcome required")
    require(
        all(r["producers_disabled"] is True for r in rows if r["phase"] == "replay"),
        "producer-disabled replay required",
    )


def check_replay_admission(
    receipt: dict[str, Any], *, input_sha256: str, execution_binding: str, evidence_kind: str
) -> None:
    require(
        receipt.get("complete") is True and receipt.get("outcome") == "success",
        "successful complete receipt required for replay",
    )
    require(
        receipt.get("evidence_kind") == evidence_kind
        and receipt.get("execution_binding") == execution_binding
        and receipt.get("raw_input_sha256") == input_sha256,
        "replay source/input/evidence binding",
    )
    # Public replay must be joined to A's real authority/receipt verifier. A claimed
    # digest/status in an arbitrary dict is not that capability. This proposal cannot
    # admit public replay until that separately reviewed integration exists.
    require(evidence_kind == "private-synthetic-test", "public replay authority join unavailable")


def run_private(
    selection: dict[str, Any],
    adapter: Any,
    output: Path,
    *,
    cases: list[str] | None = None,
    resources: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adapter owns exact binary/host/import/framing checks; this function owns scheduling.

    adapter.preflight must bind its source/build/import inputs and enforce container CPU,
    RAM, PID and FD bounds. adapter.call launches a new bounded process; it returns raw
    input/stdout/stderr bytes and verified outcome metadata. No public adapter is supplied.
    """
    require(output.resolve().is_relative_to(Path("/tmp")), "private output path required")
    output.mkdir(exist_ok=False)
    h = helpers()
    store = h["Store"](output, POLICY["receipt_bytes"])
    slots = schedule(selection, cases)
    ids = sorted({s["case_id"] for s in slots})
    rows = {r["case_id"]: r for r in selection["rows"]}
    launch = dict(
        format="component-private-launch/1",
        complete=False,
        evidence_kind="private-synthetic-test",
        selection_hash=selection["selection_hash"],
        cases=ids,
        planned_calls=len(slots),
        acceptance_gate=False,
        policy=POLICY,
    )
    store.json("launch.json", launch)
    try:
        setup = adapter.preflight(dict(selection, rows=[rows[k] for k in ids]), POLICY)
        require(
            setup["evidence_kind"] == "private-synthetic-test", "no public execution in proposal"
        )
        require(
            setup["pids_limit"] <= POLICY["process_limit_required"] and setup["pids_limit"] > 0,
            "bounded outer process limit required",
        )
        require(
            bool(setup["execution_binding"]) and bool(setup["files"]),
            "exact private setup required",
        )

        def verify_setup():
            for path, pin in setup["files"].items():
                require(digest(Path(path).read_bytes()) == pin, "current setup bytes changed")

        verify_setup()
        require(set(setup["input_hashes"]) == set(ids), "exact selected input binding inventory")
        budget = resources if resources is not None else h["discover"](POLICY, len(ids))
        workers = min(POLICY["max_workers"], budget["workers"], len(ids))
        require(workers > 0, "positive worker budget")
        store.json("setup.json", dict(setup=setup, resources=budget, workers=workers))

        def group(case):
            resource.setrlimit(resource.RLIMIT_NOFILE, (POLICY["nofile"], POLICY["nofile"]))
            results = []
            initial = None
            for slot in [s for s in slots if s["case_id"] == case]:
                verify_setup()
                if slot["phase"] == "replay":
                    require(initial is not None, "no replay before successful receipt")
                    check_replay_admission(
                        initial,
                        input_sha256=initial["raw_input_sha256"],
                        execution_binding=setup["execution_binding"],
                        evidence_kind="private-synthetic-test",
                    )
                raw = adapter.call(slot, rows[case], initial, POLICY)
                require(
                    digest(raw["raw_input"]) == setup["input_hashes"][case],
                    "immutable selected raw input mismatch",
                )
                record = dict(
                    slot,
                    process_identity=raw["process_identity"],
                    checked=raw["checked"],
                    outcome=raw["outcome"],
                    producers_disabled=raw["producers_disabled"],
                    complete=True,
                    evidence_kind="private-synthetic-test",
                    execution_binding=setup["execution_binding"],
                )
                require(
                    raw["outcome"] == rows[case]["expected_code"], "wrong refusal/result outcome"
                )
                for key in ("raw_input", "stdout", "stderr"):
                    require(isinstance(raw[key], bytes), "raw bytes receipt required")
                    require(len(raw[key]) <= 64 * 1024**2, "per-stream byte cap")
                    record[key + "_sha256"] = digest(raw[key])
                    record[key + "_blob"] = store.blob(raw[key])
                require(record["checked"] is True, "independent/structural acceptance required")
                if rows[case]["expected_layer"] != "result":
                    require(
                        raw["expected_pointer_verified"] is True, "exact refusal pointer required"
                    )
                    record["zero_dispatch_evidence"] = raw["zero_dispatch_evidence"]
                    require(
                        bool(record["zero_dispatch_evidence"]),
                        "separate native zero-dispatch evidence",
                    )
                verify_setup()
                store.json(f"calls/{slot['ordinal']:05d}.json", record)
                results.append(record)
                if slot["phase"] == "initial" and raw["outcome"] == "success":
                    initial = record
            verify_group(results, replay=rows[case]["expected_layer"] == "result")
            return dict(case_id=case, slots=[r["ordinal"] for r in results])

        def progress(case, result):
            print(
                json.dumps(dict(event="case_complete", case_id=case, calls=len(result["slots"]))),
                flush=True,
            )

        finished = h["run_workers"](
            ids,
            group,
            workers=workers,
            task_timeout=POLICY["case_seconds"],
            total_timeout=POLICY["total_seconds"],
            progress=progress,
        )
        verify_setup()
        store.check_budget()
        require(sum(len(r["slots"]) for r in finished) == len(slots), "complete launch membership")
        result = dict(launch, complete=True, completed_calls=len(slots), results=finished)
        store.json("complete.json", result)
        return result
    except BaseException as error:
        store.json(
            "incomplete.json",
            dict(
                launch,
                reason=type(error).__name__ + ": " + str(error),
                completed_receipts=len(list((output / "calls").glob("*.json"))),
            ),
        )
        raise
