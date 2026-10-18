"""Offline prospective F2 classification only, never execution/admission authority.

Direction cannot establish safety. The current conservative policy has no timed-safe
exception for an engine with multiple requests. A separate reviewed complete timing
proof and explicit selection approval would be required to add such an exception.
"""

import hashlib
import json
from collections import Counter

KNOWN_AFFECTED = {
    "722d0ffb51df53d362ac765c1b7846ed68dd2f3c00d9894db7429cad69d1e253": "cc0-v1",
    "effb5beb75f13e9de13e31666fc810d60f3edbb1e83dd27071d3ce9c1364dd76": "ww0-v1",
}


def classify(raw_job: bytes) -> dict:
    """Requires the ordinary exact-input/profile validation independently.

    Returned absence evidence only covers the F2 class; it is not a runnable selection.
    The job's declared request graph supplies a direction-independent static proof when
    no engine can have two acquired releases. Missing/invalid inventories fail closed.
    """
    digest = hashlib.sha256(raw_job).hexdigest()
    report = {"raw_job_sha256": digest, "execution_authorized": False}
    job = json.loads(raw_job)
    model = job.get("engine", {}).get("model", {})
    pair = (model.get("name"), model.get("version"))
    if pair == ("native-intervals", "2"):
        return dict(
            report, status="outside_F2_model2", reason="/3 behavior unchanged; F4 still required"
        )
    if pair != ("native-intervals", "1"):
        return dict(report, status="blocked_unclassified", reason="unknown model")
    if digest in KNOWN_AFFECTED:
        return dict(report, status="blocked_affected", reproducer=KNOWN_AFFECTED[digest])
    try:
        counts: Counter[int] = Counter()
        seen: set[str] = set()
        jobs = job["mapped_point"]["task_graph"]["jobs"]
        if not isinstance(jobs, list):
            raise ValueError("job inventory")
        for task in jobs:
            if task["kind"] != "dma":
                if task["kind"] not in ("compute", "barrier", "noc_transfer"):
                    raise ValueError("unknown task")
                continue
            engine = task["dma_engine_id"]
            if type(engine) is not int or engine < 0 or not task["fragments"]:
                raise ValueError("DMA inventory")
            for fragment in task["fragments"]:
                request = fragment["request_id"]
                if not isinstance(request, str) or not request or request in seen:
                    raise ValueError("request inventory")
                seen.add(request)
                counts[engine] += 1
    except (KeyError, TypeError, ValueError):
        return dict(
            report, status="blocked_unclassified", reason="incomplete request/engine inventory"
        )
    if any(n > 1 for n in counts.values()):
        return dict(
            report,
            status="blocked_unclassified",
            reason="multiple requests on one engine; no reviewed complete timing classification",
            broader_conservative_policy=True,
        )
    return dict(
        report,
        status="outside_F2_static_proof",
        proof={
            "request_count_by_engine": dict(sorted(counts.items())),
            "argument": (
                "At most one declared request per engine: "
                "two same-engine acquired releases are impossible."
            ),
        },
    )
