"""Prospective offline acceptance recipe only; no invocation, placement, authority or adoption.
The caller explicitly names its checker; a result format cannot select weaker validation.
"""

import hashlib
from pathlib import Path

ROUTES = {
    ("native-intervals", "1"): (
        "uarch-native-observations/2",
        "validation.component.observations_v2:check_v2",
    ),
    ("native-intervals", "2"): (
        "uarch-native-observations/3",
        "validation.component.observations_v3:check_v3",
    ),
}


def required_route(job, result, checker_id):
    model = job["engine"]["model"]
    required = ROUTES.get((model["name"], model["version"]))
    if required is None or (result["observations"]["format"], checker_id) != required:
        raise ValueError("prospective model / observation format / independent checker mismatch")
    return required


def verify_files(source, pinned):
    if not pinned:
        raise ValueError("missing prospective checker/structural closure")
    for name, wanted in pinned.items():
        p = (Path(source) / name).resolve()
        if not p.is_relative_to(Path(source).resolve()):
            raise ValueError("closure path escape")
        if hashlib.sha256(p.read_bytes()).hexdigest() != wanted:
            raise ValueError("prospective consumer source identity mismatch: " + name)


def consume(job, result, checker_id, expected, source, pinned):
    # Route identity is checked before invoking either validation layer. This never
    # releases a case for public use: F2 selection restriction and genuine authority
    # must be resolved independently before an external scheduler may run anything.
    required_route(job, result, checker_id)
    verify_files(source, pinned)
    from uarch_contract.mapped import MappedEngineJob, validate_result

    validate_result(result, MappedEngineJob.model_validate(job))
    if checker_id == ROUTES[("native-intervals", "2")][1]:
        from validation.component.observations_v3 import check_v3

        return check_v3(job, result, expected)
    from validation.component.observations_v2 import check_v2

    return check_v2(job, result, expected)
