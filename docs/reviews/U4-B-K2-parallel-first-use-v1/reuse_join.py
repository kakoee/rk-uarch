"""Private A/B candidate join using saved genuine outputs; never native executions."""

import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from parallel_core import Store, digest, require, run_workers

sys.path.insert(0, "/campaign")
import entrypoint as base
import parallel_case_reuse as grouped

RUNNER = HOSTS = CONTEXT = SAMPLES = ANSWERS = None
EXCHANGES = []
FAULT_AT = None


def forbidden(*args, **kwargs):
    raise RuntimeError("private join forbids native/process execution except owned worker fork")


def exchange(fd, request, limits):
    from uarch_contract.hashing import canonical_json, content_hash

    case = json.loads(request)["admission"]["case_id"]
    sample = SAMPLES[case]
    require(request == sample["request"], "captured immutable request changed")
    path = os.readlink("/proc/self/fd/" + str(fd))
    mode = next(m for m, h in HOSTS.items() if str(h.root / h.executable.path) == path)
    data = bytearray()
    offset = 0
    while chunk := os.pread(fd, 1024 * 1024, offset):
        data.extend(chunk)
        offset += len(chunk)
    require(digest(data) == HOSTS[mode].executable.byte_hash, "actual mode-specific descriptor")
    EXCHANGES.append(
        {
            "case": case,
            "mode": mode,
            "request_hash": digest(request),
            "saved_debug_stdout_hash": digest(sample["stdout"]),
        }
    )
    output = sample["stdout"]
    if FAULT_AT is not None and len(EXCHANGES) == FAULT_AT:
        bad = json.loads(output)
        bad["duration_ps"] += 1
        bad["result_hash"] = content_hash(bad, exclude=("result_hash",))
        output = canonical_json(bad).encode()
    return output, sample["stderr"], 0


class DiagnosticStore(Store):
    def json(self, name, value):
        value = {**value, "diagnostic_only": True, "fresh_native_process": False}
        return super().json(name, value)


def group(task):
    global EXCHANGES, FAULT_AT
    case = task.split(":")[0]
    EXCHANGES, FAULT_AT = [], (6 if task.endswith(":final-fault") else None)
    out = Path("/receipts/groups") / task
    out.mkdir(parents=True)
    store = DiagnosticStore(out, 32 * 1024**2)
    cases = {x["case_id"]: x for x in CONTEXT[1]["case_membership"]}
    grouped.STATE = base, CONTEXT, HOSTS, cases, ANSWERS, store
    RUNNER._exchange = exchange
    result = grouped.perform_case(case)
    require(
        len(EXCHANGES) == 6 and [x["mode"] for x in EXCHANGES] == ["debug"] * 3 + ["release"] * 3,
        "exact six API replays with separate real mode descriptors",
    )
    return {
        **result,
        "validation_replays": EXCHANGES,
        "native_calls": 0,
        "output_origin": "original debug-0 saved result for this case; no new release result",
    }


def controls():
    global EXCHANGES, FAULT_AT
    case = "K01"
    raw = json.loads(SAMPLES[case]["request"])
    RUNNER._exchange = exchange
    results = []
    for corrupt in (2, 3):
        EXCHANGES = []
        FAULT_AT = corrupt
        with RUNNER.admitted_case(raw, host=HOSTS["debug"]) as execute:
            for _ in range(corrupt - 1):
                value, _ = execute()
                CONTEXT[8](
                    value, CONTEXT[7].model_validate_json(SAMPLES[case]["request"]), ANSWERS[case]
                )
            try:
                execute()
            except RUNNER.ProtocolViolation:
                pass
            else:
                raise AssertionError("corrupt later result accepted")
        require(len(EXCHANGES) == corrupt, "fresh response validation at later repetition")
        results.append(
            {
                "control": "corrupt result " + str(corrupt),
                "prior_positive_passes": corrupt - 1,
                "refused": True,
            }
        )
    FAULT_AT = None
    EXCHANGES = []
    caller = copy.deepcopy(raw)
    with RUNNER.admitted_case(caller, host=HOSTS["debug"]) as execute:
        caller["owners"][0]["resource"] = "changed nested caller after admission"
        execute()
        require(len(EXCHANGES) == 1, "captured snapshot positive")
        for kwargs in [
            {"host": HOSTS["release"]},
            {"value": json.loads(SAMPLES["K02"]["request"])},
        ]:
            try:
                execute(**kwargs)
            except TypeError:
                pass
            else:
                raise AssertionError("operation allowed authority/case replacement")
        before = len(EXCHANGES)
        profiles = HOSTS["debug"].profiles.copy()
        try:
            HOSTS["debug"].profiles.clear()
            try:
                execute()
            except ValueError:
                pass
            else:
                raise AssertionError("changed nested authority accepted")
        finally:
            HOSTS["debug"].profiles.update(profiles)
        require(len(EXCHANGES) == before, "authority drift refused before transport")
    before = len(EXCHANGES)
    try:
        execute()
    except ValueError:
        pass
    else:
        raise AssertionError("expired operation accepted")
    require(len(EXCHANGES) == before, "expired operation reached transport")
    try:
        with RUNNER.admitted_case(caller, host=HOSTS["debug"]):
            raise AssertionError("changed bytes newly admitted without hash correction")
    except ValueError:
        pass
    with RUNNER.admitted_case(raw, host=HOSTS["debug"]) as restored:
        restored()
    results.append(
        {
            "control": "nested caller snapshot; changed authority/case/mode/bytes; expiry",
            "refused_before_transport": True,
            "restored_positive": True,
        }
    )
    return results


def main():
    global RUNNER, HOSTS, CONTEXT, SAMPLES, ANSWERS
    context = list(base.common())
    out = Store("/receipts", 64 * 1024**2)
    out.json("join-start.json", {"status": "resolving unchanged real authority", "native_calls": 0})
    HOSTS = base.authority(context[1], context[3])
    candidate = Path("/join/source/src/rkuarch/engines/native/runner.py")
    require(
        digest(candidate.read_bytes())
        == "sha256:a6b46c3ddfb5f713ac33ee6d906b5bf25fcee6272c47a0b919133ce864f7b938",
        "exact A postimage",
    )
    spec = importlib.util.spec_from_file_location(
        "rkuarch.engines.native.b_review_runner", candidate
    )
    RUNNER = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = RUNNER
    spec.loader.exec_module(RUNNER)
    context[4] = RUNNER
    CONTEXT = tuple(context)
    subprocess.Popen = forbidden

    def audit(event, args):
        if event in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn"):
            forbidden()

    sys.addaudithook(audit)
    ANSWERS = base.read_json(
        base.ROOT / "docs/reviews/U4-A-K2-construction-v1/corpus/expectations.json"
    )
    SAMPLES = {}
    for case in ["K01", "K02"]:
        row = json.loads((Path("/saved/calls") / f"debug-0-{case}.json").read_bytes())
        data = {k: (Path("/saved") / row[k]).read_bytes() for k in ("request", "stdout", "stderr")}
        require(all(digest(v) == row[k + "_hash"] for k, v in data.items()), "genuine saved bytes")
        SAMPLES[case] = data
    groups = run_workers(
        ["K01", "K02"],
        group,
        workers=2,
        task_timeout=180,
        total_timeout=300,
        executable_paths=tuple(str(h.root / h.executable.path) for h in HOSTS.values()),
    )
    try:
        run_workers(
            ["K01:final-fault"],
            group,
            workers=1,
            task_timeout=180,
            total_timeout=240,
            executable_paths=tuple(str(h.root / h.executable.path) for h in HOSTS.values()),
        )
    except ValueError:
        failed_root = Path("/receipts/groups/K01:final-fault")
        require(
            len(list((failed_root / "calls").glob("*.json"))) == 5,
            "five earlier checked validation replays preserved",
        )
        require(
            len(list((failed_root / "transport").glob("*.json"))) == 6,
            "corrupt final saved transport preserved",
        )
    else:
        raise AssertionError("final response corruption did not stop grouped worker")
    checks = controls()
    checks.append(
        {
            "control": "actual grouped candidate final-response corruption",
            "checked_slots_preserved": 5,
            "transport_slots_preserved": 6,
            "complete_group": False,
        }
    )
    origins = {
        n: m.__file__
        for n, m in sys.modules.copy().items()
        if n.startswith(("rkuarch", "uarch_contract")) and getattr(m, "__file__", None)
    }
    require(origins[spec.name] == str(candidate), "explicit private candidate origin")
    require(
        all(
            Path(path).is_relative_to("/candidate")
            for name, path in origins.items()
            if name != spec.name
        ),
        "unchanged baseline module origins",
    )
    # End the explicitly private alias lifetime; do not relax the original
    # runtime's import guard to make a proposal look like installed source.
    del sys.modules[spec.name]
    base.common()
    out.json(
        "join.json",
        {
            "status": "private candidate API/scheduler join passed",
            "A_runner_hash": digest(candidate.read_bytes()),
            "B_candidate_helper_hash": digest(Path("/join/parallel_case_reuse.py").read_bytes()),
            "groups": groups,
            "controls": checks,
            "native_calls": 0,
            "actual_mode_descriptor_checks": True,
            "protected_hardware_import": "unchanged accepted source",
            "origins": origins,
            "limitation": (
                "Saved debug outputs replayed through both mode contexts; no new "
                "debug/release execution, runtime installation or authority is claimed."
            ),
        },
    )


if __name__ == "__main__":
    main()
