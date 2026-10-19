"""Ordinary EOF orchestration preparation. No authority creation or default CLI route.

Adapters must use genuine existing sessions at A's public image seams. Tests inject
synthetic adapters. Completion is independently reconsumed, never an adapter flag.
"""

from __future__ import annotations

import json
import signal
import time
from functools import partial
from pathlib import Path
from typing import Any, Protocol

from uarch_contract.hashing import canonical_json, sha256

from native.tools import component_container_guard as guardian
from validation.component.checks import need
from validation.component.ordinary_eof_acceptance import (
    GUARD_FILES,
    admit_replay,
    consume_attempt,
    consume_group,
    verify_closure,
)
from validation.component.runtime_campaign import POLICY as POLICY
from validation.component.runtime_campaign import helpers as helpers
from validation.component.runtime_campaign import schedule

METADATA_BYTES = 8 * 1024**2


def emergency(path: Path, value: dict[str, Any]) -> None:
    data = canonical_json(value).encode()
    if len(data) > METADATA_BYTES:
        # Retained raw attempts and ledgers remain authoritative for incident inspection.
        data = canonical_json(
            {"complete": False, "error": "metadata reserve exceeded", "raw_evidence_retained": True}
        ).encode()
    path.write_bytes(data)


class Adapter(Protocol):
    def preflight(self, selection: dict[str, Any], policy: dict[str, Any]) -> None: ...

    def call(
        self,
        slot: dict[str, Any],
        row: dict[str, Any],
        evidence_root: Path,
        initial_references: list[dict[str, Any]] | None,
        remaining_seconds: float,
    ) -> None: ...


class Deadline(BaseException):
    """Interrupt an owned worker call; outer supervision remains the backstop."""


def bounded_call(function: Any, seconds: float) -> Any:
    need(seconds > 0 and signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), "call deadline state")
    previous = signal.getsignal(signal.SIGALRM)

    def expired(*_: Any) -> None:
        raise Deadline("ordinary per-call deadline")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    started = time.monotonic()
    try:
        result = function()
        need(time.monotonic() - started < seconds, "call deadline exceeded")
        return result
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def reference(root: Path) -> dict[str, Any]:
    """Freeze retained producer bytes for independent readback, never for authority."""
    return {
        "path": str(root / "attempt.json"),
        "byte_hash": sha256((root / "attempt.json").read_bytes()),
        "guardian_files": {
            name: sha256((root / "container" / name).read_bytes()) for name in GUARD_FILES
        },
    }


def cleanup_owned(root: Path) -> dict[str, Any]:
    """Workers must be joined first. Never select containers by a shared label/name."""
    paths = list(root.rglob("*"))
    need(not root.is_symlink() and not any(p.is_symlink() for p in paths), "cleanup scope symlink")
    receipts, outstanding, ids = [], [], set()
    end = time.monotonic() + 35
    for intent in sorted(root.rglob("intent.json")):
        try:
            need(intent.parent.name == "container", "unexpected intent layout")
            owner = json.loads(intent.read_bytes())["owner"]
            rows = guardian.cleanup(intent.parent.parent, timeout=max(0, end - time.monotonic()))
            need(len(rows) == 1, "one guardian per call")
            value = rows[0]
            need(
                value["owner"] == owner
                and value["stopped"] is True
                and value["removed"] is True
                and not value.get("error")
                and not value.get("cleanup_error"),
                "parent guardian cleanup",
            )
            created = intent.parent / "created.json"
            if value.get("never_created"):
                need(
                    not created.exists() and value["container_id"] is None, "never-created evidence"
                )
            else:
                identity = json.loads(created.read_bytes())
                prior = json.loads((intent.parent / "pre-existing.json").read_bytes())
                cid = value["container_id"]
                need(
                    identity == {"container_id": cid, "owner": owner}
                    and isinstance(cid, str)
                    and len(cid) == 64
                    and set(cid) <= set("0123456789abcdef")
                    and cid not in ids
                    and cid not in {r["container_id"] for r in prior["containers"]},
                    "parent exact owner and new ID",
                )
                ids.add(cid)
            receipts.append(
                {
                    "intent": str(intent),
                    "intent_byte_hash": sha256(intent.read_bytes()),
                    "cleanup_byte_hash": sha256((intent.parent / "cleanup.json").read_bytes()),
                    "receipt": value,
                }
            )
        except Exception as error:
            outstanding.append({"intent": str(intent), "error": repr(error)})
    return {
        "format": "component-eof-cleanup-audit/1",
        "workers_joined": True,
        "receipts": receipts,
        "container_ids": sorted(ids),
        "outstanding": outstanding,
        "complete": not outstanding,
    }


def run_campaign(
    selection: dict[str, Any],
    adapter: Adapter,
    output: Path,
    *,
    acceptance: dict[str, Any],
    cases: list[str] | None = None,
) -> dict[str, Any]:
    """Finite orchestration; calling this requires separate execution authorization.

    No public bypass/authority flag or resource overrides. Per-call producer streams
    have their own reviewed caps; budget overshoot is retained and refuses completion.
    """
    output = output.resolve()
    output.mkdir(exist_ok=False)
    h = helpers()
    store = h["Store"](output, POLICY["receipt_bytes"])
    slots = schedule(selection, cases)
    ids = sorted({s["case_id"] for s in slots})
    rows = {r["case_id"]: r for r in selection["rows"]}
    start = time.monotonic()
    launch = {
        "format": "component-eof-launch/1",
        "complete": False,
        "authority": None,
        "selection_byte_hash": sha256(canonical_json(selection).encode()),
        "acceptance_byte_hash": sha256(canonical_json(acceptance).encode()),
        "slots": slots,
        "policy": POLICY,
        "started_monotonic": start,
    }
    store.json("launch.json", launch)
    workers_joined = False
    failure: BaseException | None = None
    results: list[dict[str, Any]] = []
    cleanup: dict[str, Any] = {"complete": False, "outstanding": ["workers not joined"]}
    try:
        need(
            acceptance["selection_byte_hash"] == launch["selection_byte_hash"],
            "frozen campaign selection",
        )
        verify_closure(acceptance)
        bounded_call(
            partial(adapter.preflight, selection, dict(POLICY)),
            POLICY["total_seconds"] - (time.monotonic() - start),
        )
        resources = h["discover"](POLICY, len(ids))
        workers = min(POLICY["max_workers"], resources["workers"], len(ids))
        need(workers > 0, "positive measured resource budget")
        store.json("resources.json", resources)

        def group(case: str) -> dict[str, Any]:
            group_root = output / "groups" / sha256(case.encode()).split(":")[1]
            group_root.mkdir(parents=True, exist_ok=False)
            refs: list[dict[str, Any]] = []
            initial: list[dict[str, Any]] = []
            began = time.monotonic()
            active = None
            try:
                for slot in (s for s in slots if s["case_id"] == case):
                    active = slot
                    verify_closure(acceptance)
                    store.check_budget()
                    prior = None
                    if slot["phase"] == "replay":
                        admit_replay(initial, rows[case], acceptance)
                        prior = initial
                    left = min(
                        POLICY["per_call_seconds"],
                        POLICY["case_seconds"] - (time.monotonic() - began),
                        POLICY["total_seconds"] - (time.monotonic() - start),
                    )
                    need(left > 0, "case/global deadline exhausted")
                    call_root = group_root / ("call-" + str(slot["ordinal"]))
                    name = str(group_root.relative_to(output))
                    store.json(
                        name + f"/dispatch-{slot['ordinal']}.json",
                        {"slot": slot, "remaining_seconds": left},
                    )
                    bounded_call(
                        partial(adapter.call, slot, rows[case], call_root, prior, left), left
                    )
                    store.check_budget()
                    need(
                        time.monotonic() - began < POLICY["case_seconds"]
                        and time.monotonic() - start < POLICY["total_seconds"],
                        "case/global deadline after call",
                    )
                    ref = reference(call_root)
                    if prior is not None:
                        ref["initial_receipts"] = list(prior)
                    observed_slot = {k: slot[k] for k in ("phase", "mode", "repetition")}
                    consume_attempt(ref, rows[case], observed_slot, acceptance)
                    refs.append(ref)
                    if slot["phase"] == "initial":
                        initial.append(ref)
                    store.json(
                        name + f"/accepted-{slot['ordinal']}.json", {"reference": ref, "slot": slot}
                    )
                return {"case_id": case, "references": refs, "root": str(group_root)}
            except BaseException as error:
                store.json(
                    str(group_root.relative_to(output)) + "/failed.json",
                    {
                        "complete": False,
                        "error": repr(error),
                        "slot": active,
                        "accepted_references": refs,
                    },
                )
                raise

        try:
            results = h["run_workers"](
                ids,
                group,
                workers=workers,
                task_timeout=POLICY["case_seconds"],
                total_timeout=max(0.001, POLICY["total_seconds"] - (time.monotonic() - start)),
            )
        finally:
            # Reviewed helper joins/terminates all worker children in its finally.
            workers_joined = True
        need(time.monotonic() - start < POLICY["total_seconds"], "global deadline after workers")
        store.check_budget()
    except BaseException as error:
        failure = error
    finally:
        # Preflight failure has launched no worker; the fresh task scope is still inspected.
        workers_joined = workers_joined or not results
        try:
            cleanup = cleanup_owned(output)
        except BaseException as error:
            cleanup = {"complete": False, "outstanding": [repr(error)]}
        # Cleanup/terminal metadata uses a small explicit emergency reserve after
        # data-budget failure; it cannot turn the failed group into success.
        emergency(output / "cleanup.json", cleanup)
    try:
        need(failure is None, "ordinary campaign failed: " + repr(failure))
        need(workers_joined and cleanup["complete"], "parent cleanup unresolved")
        summaries = []
        for result in results:
            refs, group_root = result["references"], Path(result["root"])
            cids = [json.loads(Path(ref["path"]).read_bytes())["container_id"] for ref in refs]
            parent = {
                "format": "component-eof-parent-cleanup/1",
                "workers_joined": True,
                "outstanding": [],
                "complete": True,
                "attempts": refs,
                "container_ids": cids,
            }
            path = group_root / "parent.json"
            store.json(str(path.relative_to(output)), parent)
            consumed = consume_group(
                refs,
                {"path": str(path), "byte_hash": sha256(path.read_bytes())},
                rows[result["case_id"]],
                acceptance,
            )
            summaries.append(
                {
                    "case_id": result["case_id"],
                    "calls": consumed["calls"],
                    "parent": consumed["parent"],
                }
            )
        need(sum(s["calls"] for s in summaries) == len(slots), "exact campaign population")
        need(
            time.monotonic() - start < POLICY["total_seconds"], "global deadline after consumption"
        )
        store.check_budget()
        complete = dict(
            launch,
            complete=True,
            groups=summaries,
            cleanup_sha256=sha256((output / "cleanup.json").read_bytes()),
            ended_monotonic=time.monotonic(),
        )
        actual = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
        need(
            actual + len(canonical_json(complete).encode()) + 8192 < POLICY["receipt_bytes"],
            "terminal receipt budget",
        )
        store.json("complete.json", complete)
        return complete
    except BaseException as error:
        # Emergency terminal evidence has a separate small reserve; it never rescues success.
        incomplete = dict(
            launch,
            complete=False,
            error=repr(error),
            original_failure=repr(failure),
            cleanup=cleanup,
            ended_monotonic=time.monotonic(),
            unresolved_cases=ids,
            transported_cases=[r["case_id"] for r in results],
        )
        emergency(output / "incomplete.json", incomplete)
        raise


class SessionAdapter:
    """Bridge only to A's genuine-session public functions; no prepared-core fallback.

    The caller supplies already authorized session providers and frozen saved paths.
    B does not construct HostRecords, selectors or authority. D3 is importable only
    after its separately reviewed installation; absence is a refusal, not a bypass.
    """

    def __init__(
        self, saved: dict[str, Path], session_for: Any, *, negative_session_for: Any = None
    ):
        self.saved = saved
        self.session_for = session_for
        self.negative_session_for = negative_session_for

    def preflight(self, selection: dict[str, Any], policy: dict[str, Any]) -> None:
        need(policy == POLICY, "ordinary campaign policy")
        need(
            all(row["case_id"] in self.saved for row in selection["rows"]), "saved input population"
        )

    def call(
        self,
        slot: dict[str, Any],
        row: dict[str, Any],
        evidence_root: Path,
        initial_references: list[dict[str, Any]] | None,
        remaining_seconds: float,
    ) -> None:
        from rkuarch.engines.native.component_image import (
            replay_component_image,
            run_component_image,
        )

        need(remaining_seconds > 0, "remaining campaign deadline")
        if row["expected_layer"] != "result":
            import importlib

            need(self.negative_session_for is not None, "separate genuine D3 session provider")
            module = importlib.import_module("rkuarch.engines.native.component_negative")
            module.run_negative(
                row["case_id"],
                session=self.negative_session_for(slot),
                evidence_root=evidence_root,
                repetition=slot["repetition"],
            )
        elif initial_references is None:
            run_component_image(
                self.saved[row["case_id"]],
                session=self.session_for(slot),
                evidence_root=evidence_root,
                repetition=slot["repetition"],
            )
        else:
            replay_component_image(
                [(Path(r["path"]), r["byte_hash"]) for r in initial_references],
                session=self.session_for(slot),
                evidence_root=evidence_root,
                repetition=slot["repetition"],
            )
