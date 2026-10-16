"""Standalone C2 exact stream comparator. No native execution or mutable baseline."""

import hashlib
import json
import re


def sha(data):
    return hashlib.sha256(data).hexdigest()


def records(raw):
    if not isinstance(raw, bytes) or not raw or not raw.endswith(b"\n"):
        raise ValueError("nonempty LF-framed bytes required")

    def pairs(items):
        obj = {}
        for k, v in items:
            if k in obj:
                raise ValueError("duplicate JSON key")
            obj[k] = v
        return obj

    def constant(token):
        raise ValueError("nonfinite JSON token: " + token)

    result = []
    for line in raw[:-1].split(b"\n"):
        if not line or line.endswith(b"\r"):
            raise ValueError("blank record or CRLF framing")
        obj = json.loads(line.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str) or not obj["id"]:
            raise ValueError("object with nonempty string id required")
        result.append(obj)
    return result


def compare(vectors, actual, refusals):
    ids = [v["id"] for v in vectors]
    if not ids or len(ids) != len(set(ids)) or [a["id"] for a in actual] != ids:
        raise ValueError("nonempty unique ordered exact selection required")
    bad, observed = [], []
    for v, a in zip(vectors, actual, strict=True):
        want = v["expected"]
        if a.get("status") == "ok":
            keys = {"id", "status", "sha256"} | ({"canonical"} if v["op"] != "sha" else set())
            if (
                set(a) != keys
                or not isinstance(a["sha256"], str)
                or not re.fullmatch("[0-9a-f]{64}", a["sha256"])
            ):
                raise ValueError("malformed successful output")
            if "canonical" in keys:
                if (
                    not isinstance(a["canonical"], str)
                    or sha(a["canonical"].encode()) != a["sha256"]
                ):
                    raise ValueError("malformed canonical bytes/hash")
        elif a.get("status") == "refuse":
            if set(a) != {"id", "status", "layer", "error"} or not all(
                isinstance(a[k], str) and a[k] for k in ("layer", "error")
            ):
                raise ValueError("malformed refusal output")
        else:
            raise ValueError("unknown output status")
        same = a["status"] == want["status"]
        if same and want["status"] == "ok":
            same = all(a.get(k) == want[k] for k in ("canonical", "sha256") if k in want)
        elif same:
            rule = refusals[v["id"]]
            same = (
                a["layer"] == rule["layer"]
                and re.fullmatch(rule["error_pattern"], a["error"]) is not None
            )
            observed.append({"id": v["id"], "expected": rule, "actual": a, "matches": same})
        if not same:
            bad.append({"id": v["id"], "expected": want, "actual": a})
    return {
        "count": len(vectors),
        "mismatch_count": len(bad),
        "mismatches": bad,
        "refusals": observed,
    }
